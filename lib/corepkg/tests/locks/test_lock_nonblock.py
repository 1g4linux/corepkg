# Copyright 2011-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import multiprocessing
import sys
import tempfile
import traceback

import corepkg
from corepkg import os
from corepkg import shutil
from corepkg.exception import TryAgain
from corepkg.tests import TestCase


class LockNonblockTestCase(TestCase):
    def _testLockNonblock(self, env=None):
        tempdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tempdir, "lock_me")
            lock1 = corepkg.locks.lockfile(path)
            proc = multiprocessing.Process(
                target=self._lock_subprocess, args=(path, env)
            )
            proc.start()
            self.assertEqual(proc.pid > 0, True)
            proc.join()
            self.assertEqual(proc.exitcode, os.EX_OK)

            corepkg.locks.unlockfile(lock1)
        finally:
            shutil.rmtree(tempdir)

    @staticmethod
    def _lock_subprocess(path, env):
        if env is not None:
            # This serves to implement __PORTAGE_TEST_HARDLINK_LOCKS
            # environment variable inheritance for the multiprocessing
            # forkserver start method.
            os.environ.update(env)
        corepkg.locks._close_fds()
        # Disable close_fds since we don't exec
        # (see _setup_pipes docstring).
        corepkg.process._setup_pipes({0: 0, 1: 1, 2: 2}, close_fds=False)
        rval = 2
        try:
            try:
                lock2 = corepkg.locks.lockfile(path, flags=os.O_NONBLOCK)
            except corepkg.exception.TryAgain:
                rval = os.EX_OK
            else:
                rval = 1
                corepkg.locks.unlockfile(lock2)
        except Exception:
            traceback.print_exc()
        sys.exit(rval)

    def testLockNonblock(self):
        self._testLockNonblock()

    def testLockNonblockHardlink(self):
        prev_state = os.environ.pop("__PORTAGE_TEST_HARDLINK_LOCKS", None)
        os.environ["__PORTAGE_TEST_HARDLINK_LOCKS"] = "1"
        try:
            self._testLockNonblock(env={"__PORTAGE_TEST_HARDLINK_LOCKS": "1"})
        finally:
            os.environ.pop("__PORTAGE_TEST_HARDLINK_LOCKS", None)
            if prev_state is not None:
                os.environ["__PORTAGE_TEST_HARDLINK_LOCKS"] = prev_state

    def test_competition_with_same_process(self):
        """
        Test that at attempt to lock the same file multiple times in the
        same process will behave as intended (bug 714480).
        """
        tempdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tempdir, "lock_me")
            lock = corepkg.locks.lockfile(path)
            self.assertRaises(
                TryAgain, corepkg.locks.lockfile, path, flags=os.O_NONBLOCK
            )
            corepkg.locks.unlockfile(lock)
        finally:
            shutil.rmtree(tempdir)
