#!/usr/bin/env python
# Copyright 2010-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import os
import sys


def main(args):
    sys.path.insert(0, os.environ["PORTAGE_PYM_PATH"])
    import corepkg

    corepkg._internal_caller = True
    corepkg._disable_legacy_globals()

    if args and isinstance(args[0], bytes):
        for i, x in enumerate(args):
            args[i] = corepkg._unicode_decode(x, errors="strict")

    # Make locks quiet since unintended locking messages displayed on
    # stdout would corrupt the intended output of this program.
    corepkg.locks._quiet = True
    lock_obj = corepkg.locks.lockfile(args[0], wantnewlockfile=True)
    sys.stdout.write("\0")
    sys.stdout.flush()
    sys.stdin.read(1)
    corepkg.locks.unlockfile(lock_obj)
    return corepkg.os.EX_OK


if __name__ == "__main__":
    rval = main(sys.argv[1:])
    sys.exit(rval)
