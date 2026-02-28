# test_isvalidatom.py -- Corepkg Unit Testing Functionality
# Copyright 2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.dep import ExtendedAtomDict


class TestExtendedAtomDict(TestCase):
    def testExtendedAtomDict(self):
        d = ExtendedAtomDict(dict)
        d["*/*"] = {"test1": "x"}
        d["dev-libs/*"] = {"test2": "y"}
        d.setdefault("sys-apps/corepkg", {})["test3"] = "z"
        self.assertEqual(d.get("dev-libs/A"), {"test1": "x", "test2": "y"})
        self.assertEqual(d.get("sys-apps/corepkg"), {"test1": "x", "test3": "z"})
        self.assertEqual(d["dev-libs/*"], {"test2": "y"})
        self.assertEqual(d["sys-apps/corepkg"], {"test1": "x", "test3": "z"})
