# Copyright 2006-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg import os
from corepkg.tests import TestCase
from corepkg.env.config import CorepkgModulesFile
from tempfile import mkstemp


class CorepkgModulesFileTestCase(TestCase):
    keys = ["foo.bar", "baz", "bob", "extra_key"]
    invalid_keys = ["", ""]
    modules = ["spanky", "zmedico", "antarus", "ricer", "5", "6"]

    def setUp(self):
        super().setUp()
        self.items = {}
        for k, v in zip(self.keys + self.invalid_keys, self.modules):
            self.items[k] = v

    def testCorepkgModulesFile(self):
        self.BuildFile()
        f = CorepkgModulesFile(self.fname)
        f.load()
        for k in self.keys:
            self.assertEqual(f[k], self.items[k])
        for ik in self.invalid_keys:
            self.assertEqual(False, ik in f)
        self.NukeFile()

    def BuildFile(self):
        fd, self.fname = mkstemp()
        f = os.fdopen(fd, "w")
        for k, v in self.items.items():
            f.write(f"{k}={v}\n")
        f.close()

    def NukeFile(self):
        os.unlink(self.fname)
