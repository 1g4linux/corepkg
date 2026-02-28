# tests/__init__.py -- Corepkg Unit Test functionality
# Copyright 2006-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import argparse
import multiprocessing
import sys
import time
import unittest
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Optional

from unittest.runner import TextTestResult as _TextTestResult

import corepkg
from corepkg import os
from corepkg.util import no_color
from corepkg import _encodings
from corepkg import _unicode_decode
from corepkg.const import PORTAGE_PYM_PATH
from corepkg.output import colorize
from corepkg.proxy.objectproxy import ObjectProxy


# This remains constant when the real value is a mock.
EPREFIX_ORIG = corepkg.const.EPREFIX


@dataclass
class CommandStep:
    returncode: int
    command: tuple[str, ...]
    env: Optional[dict] = None
    cwd: Optional[str] = None


@dataclass
class FunctionStep:
    function: Callable[[int], Any]  # called with step index as argument


class lazy_value(ObjectProxy):
    __slots__ = ("_func",)

    def __init__(self, func):
        ObjectProxy.__init__(self)
        object.__setattr__(self, "_func", func)

    def _get_target(self):
        return object.__getattribute__(self, "_func")()


@lazy_value
def cnf_path():
    if corepkg._not_installed:
        return os.path.join(corepkg.const.PORTAGE_BASE_PATH, "cnf")
    return os.path.join(
        EPREFIX_ORIG or "/", corepkg.const.GLOBAL_CONFIG_PATH.lstrip(os.sep)
    )


@lazy_value
def cnf_etc_path():
    if corepkg._not_installed:
        return str(cnf_path)
    return os.path.join(EPREFIX_ORIG or "/", "etc")


@lazy_value
def cnf_bindir():
    if corepkg._not_installed:
        return corepkg.const.PORTAGE_BIN_PATH
    return os.path.join(corepkg.const.EPREFIX or "/", "usr", "bin")


@lazy_value
def cnf_sbindir():
    if corepkg._not_installed:
        return str(cnf_bindir)
    return os.path.join(corepkg.const.EPREFIX or "/", "usr", "sbin")


def get_pythonpath():
    """
    Prefix current PYTHONPATH with PORTAGE_PYM_PATH, and normalize.
    """
    pythonpath = os.environ.get("PYTHONPATH")
    if pythonpath is not None and not pythonpath.strip():
        pythonpath = None
    if pythonpath is not None and pythonpath.split(":")[0] == PORTAGE_PYM_PATH:
        pass
    else:
        if pythonpath is None:
            pythonpath = ""
        else:
            pythonpath = ":" + pythonpath
        pythonpath = PORTAGE_PYM_PATH + pythonpath
    return pythonpath


class TestCase(unittest.TestCase):
    """
    We need a way to mark a unit test as "ok to fail"
    This way someone can add a broken test and mark it as failed
    and then fix the code later.  This may not be a great approach
    (broken code!!??!11oneone) but it does happen at times.
    """

    def __init__(self, *pargs, **kwargs):
        unittest.TestCase.__init__(self, *pargs, **kwargs)
        self.cnf_path = cnf_path
        self.cnf_etc_path = cnf_etc_path
        self.bindir = cnf_bindir
        self.sbindir = cnf_sbindir

    def setUp(self):
        """
        Setup multiprocessing start method if needed. It needs to be
        done relatively late in order to work with the pytest-xdist
        plugin due to execnet usage.
        """
        if os.environ.get("PORTAGE_MULTIPROCESSING_START_METHOD") == "spawn":
            multiprocessing.set_start_method("spawn", force=True)

    def assertRaisesMsg(self, msg, excClass, callableObj, *args, **kwargs):
        """Fail unless an exception of class excClass is thrown
        by callableObj when invoked with arguments args and keyword
        arguments kwargs. If a different type of exception is
        thrown, it will not be caught, and the test case will be
        deemed to have suffered an error, exactly as for an
        unexpected exception.
        """
        try:
            callableObj(*args, **kwargs)
        except excClass:
            return
        else:
            if hasattr(excClass, "__name__"):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException(f"{excName} not raised: {msg}")

    def assertNotExists(self, path):
        """Make sure |path| does not exist"""
        path = Path(path)
        if path.exists():
            raise self.failureException(f"path exists when it should not: {path}")


test_cps = ["sys-apps/corepkg", "virtual/corepkg"]
test_versions = ["1.0", "1.0-r1", "2.3_p4", "1.0_alpha57"]
test_slots = [None, "1", "gentoo-sources-2.6.17", "spankywashere"]
test_usedeps = ["foo", "-bar", ("foo", "bar"), ("foo", "-bar"), ("foo?", "!bar?")]
