# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import time
import corepkg
from corepkg import os
from corepkg import _encodings
from corepkg import _unicode_decode
from corepkg import _unicode_encode
from corepkg.data import secpass
from corepkg.output import xtermTitle

# We disable emergelog by default, since it's called from
# dblink.merge() and we don't want that to trigger log writes
# unless it's really called via emerge.
_disable = True
_emerge_log_dir = "/var/log"


def emergelog(xterm_titles, mystr, short_msg=None):
    if _disable:
        return

    mystr = _unicode_decode(mystr)

    if short_msg is not None:
        short_msg = _unicode_decode(short_msg)

    if xterm_titles and short_msg:
        xtermTitle(short_msg)
    try:
        file_path = os.path.join(_emerge_log_dir, "emerge.log")
        existing_log = os.path.exists(file_path)
        mylogfile = open(
            _unicode_encode(file_path, encoding=_encodings["fs"], errors="strict"),
            mode="a",
            encoding=_encodings["content"],
            errors="backslashreplace",
        )
        if not existing_log:
            corepkg.util.apply_secpass_permissions(
                file_path, uid=corepkg.corepkg_uid, gid=corepkg.corepkg_gid, mode=0o660
            )
        mylock = corepkg.locks.lockfile(file_path)
        try:
            mylogfile.write(f"{int(time.time())}: {mystr}\n")
            mylogfile.close()
        finally:
            corepkg.locks.unlockfile(mylock)
    except (OSError, corepkg.exception.CorepkgException) as e:
        if secpass >= 1:
            corepkg.util.writemsg(f"emergelog(): {e}\n", noiselevel=-1)
