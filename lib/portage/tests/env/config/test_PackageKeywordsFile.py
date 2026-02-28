# test_PackageKeywordsFile.py -- Corepkg Unit Testing Functionality
# Copyright 2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg import os
from corepkg.tests import TestCase
from corepkg.env.config import PackageKeywordsFile
from tempfile import mkstemp


class PackageKeywordsFileTestCase(TestCase):
    cpv = ["sys-apps/corepkg"]
    keywords = ["~x86", "amd64", "-mips"]

    def testPackageKeywordsFile(self):
        """
        A simple test to ensure the load works properly
        """

        self.BuildFile()
        try:
            f = PackageKeywordsFile(self.fname)
            f.load()
            i = 0
            for cpv, keyword in f.items():
                self.assertEqual(cpv, self.cpv[i])
                [k for k in keyword if self.assertTrue(k in self.keywords)]
                i = i + 1
        finally:
            self.NukeFile()

    def BuildFile(self):
        fd, self.fname = mkstemp()
        f = os.fdopen(fd, "w")
        for c in self.cpv:
            f.write(f"{c} {' '.join(self.keywords)}\n")
        f.close()

    def NukeFile(self):
        os.unlink(self.fname)
