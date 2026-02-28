# SOCKSv5 proxy manager for network-sandbox
# Copyright 2015-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import asyncio
import errno
import os
import socket

import corepkg
import corepkg.data
from corepkg import _python_interpreter
from corepkg.data import corepkg_gid, corepkg_uid, userpriv_groups
from corepkg.process import atexit_register, spawn


class ProxyManager:
    """
    A class to start and control a single running SOCKSv5 server process
    for Corepkg.
    """

    def __init__(self):
        self.socket_path = None
        self._proc = None
        self._proc_waiter = None

    def start(self, settings):
        """
        Start the SOCKSv5 server.

        @param settings: Corepkg settings instance (used to determine
        paths)
        @type settings: corepkg.config
        """

        tmpdir = os.path.join(settings["PORTAGE_TMPDIR"], "corepkg")
        ensure_dirs_kwargs = {}
        if corepkg.secpass >= 1:
            ensure_dirs_kwargs["gid"] = corepkg_gid
            ensure_dirs_kwargs["mode"] = 0o70
            ensure_dirs_kwargs["mask"] = 0
        corepkg.util.ensure_dirs(tmpdir, **ensure_dirs_kwargs)

        self.socket_path = os.path.join(
            tmpdir, ".corepkg.%d.net.sock" % corepkg.getpid()
        )
        server_bin = os.path.join(settings["PORTAGE_BIN_PATH"], "socks5-server.py")
        spawn_kwargs = {}
        # The corepkg_uid check solves EPERM failures in Travis CI.
        if corepkg.data.secpass > 1 and os.geteuid() != corepkg_uid:
            spawn_kwargs.update(
                uid=corepkg_uid, gid=corepkg_gid, groups=userpriv_groups, umask=0o077
            )
        self._proc = spawn(
            [_python_interpreter, server_bin, self.socket_path],
            returnproc=True,
            **spawn_kwargs,
        )

    async def stop(self):
        """
        Stop the SOCKSv5 server. This method is a coroutine.
        """
        if self._proc is not None:
            self._proc.terminate()
            if self._proc_waiter is None:
                self._proc_waiter = asyncio.ensure_future(self._proc.wait())
            await self._proc_waiter

        self.socket_path = None
        self._proc = None
        self._proc_waiter = None

    def is_running(self):
        """
        Check whether the SOCKSv5 server is running.

        @return: True if the server is running, False otherwise
        """
        return self.socket_path is not None

    async def ready(self):
        """
        Wait for the proxy socket to become ready. This method is a coroutine.
        """
        if self._proc_waiter is None:
            self._proc_waiter = asyncio.ensure_future(self._proc.wait())

        while True:
            if self._proc_waiter.done():
                raise OSError(3, "No such process")

            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(self.socket_path)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
                await asyncio.sleep(0.2)
            else:
                break
            finally:
                s.close()


proxy = ProxyManager()


def get_socks5_proxy(settings):
    """
    Get UNIX socket path for a SOCKSv5 proxy. A new proxy is started if
    one isn't running yet, and an atexit event is added to stop the proxy
    on exit.

    @param settings: Corepkg settings instance (used to determine paths)
    @type settings: corepkg.config
    @return: (string) UNIX socket path
    """

    if not proxy.is_running():
        proxy.start(settings)
        atexit_register(proxy.stop)

    return proxy.socket_path
