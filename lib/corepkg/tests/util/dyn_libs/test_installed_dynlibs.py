# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import tempfile

from corepkg.const import BASH_BINARY
from corepkg.tests import TestCase
from corepkg.util import ensure_dirs
from corepkg.util._dyn_libs.dyn_libs import installed_dynlibs
from corepkg.util.file_copy import copyfile


class InstalledDynlibsTestCase(TestCase):
    def testInstalledDynlibsRegular(self):
        """
        Return True for *.so regular files.
        """
        with tempfile.TemporaryDirectory() as directory:
            bash_copy = os.path.join(directory, "lib", "libfoo.so")
            ensure_dirs(os.path.dirname(bash_copy))
            copyfile(BASH_BINARY, bash_copy)
            self.assertTrue(installed_dynlibs(directory))

    def testInstalledDynlibsOnlySymlink(self):
        """
        If a *.so symlink is installed but does not point to a regular
        file inside the top directory, installed_dynlibs should return
        False (bug 921170).
        """
        with tempfile.TemporaryDirectory() as directory:
            symlink_path = os.path.join(directory, "lib", "libfoo.so")
            ensure_dirs(os.path.dirname(symlink_path))
            os.symlink(BASH_BINARY, symlink_path)
            self.assertFalse(installed_dynlibs(directory))

    def testInstalledDynlibsSymlink(self):
        """
        Return True for a *.so symlink pointing to a regular file inside
        the top directory.
        """
        with tempfile.TemporaryDirectory() as directory:
            bash_copy = os.path.join(directory, BASH_BINARY.lstrip(os.sep))
            ensure_dirs(os.path.dirname(bash_copy))
            copyfile(BASH_BINARY, bash_copy)
            symlink_path = os.path.join(directory, "lib", "libfoo.so")
            ensure_dirs(os.path.dirname(symlink_path))
            os.symlink(bash_copy, symlink_path)
            self.assertTrue(installed_dynlibs(directory))

    def testInstalledDynlibsAbsoluteSymlink(self):
        """
        If a *.so symlink target is outside of the top directory,
        traversal follows the corresponding file inside the top
        directory if it exists, and otherwise stops following the
        symlink.
        """
        with tempfile.TemporaryDirectory() as directory:
            bash_copy = os.path.join(directory, BASH_BINARY.lstrip(os.sep))
            ensure_dirs(os.path.dirname(bash_copy))
            copyfile(BASH_BINARY, bash_copy)
            symlink_path = os.path.join(directory, "lib", "libfoo.so")
            ensure_dirs(os.path.dirname(symlink_path))
            os.symlink(BASH_BINARY, symlink_path)
            self.assertTrue(installed_dynlibs(directory))

    def testInstalledDynlibsPythonExtension(self):
        """
        Ignore extension modules that end in *.so but are not
        library-style soname files.
        """
        with tempfile.TemporaryDirectory() as directory:
            ext_path = os.path.join(
                directory,
                "usr",
                "lib",
                "python3.13",
                "site-packages",
                "nacl",
                "_sodium.cpython-313-x86_64-linux-gnu.so",
            )
            ensure_dirs(os.path.dirname(ext_path))
            copyfile(BASH_BINARY, ext_path)
            self.assertFalse(installed_dynlibs(directory))
