# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from dataclasses import dataclass, field

from _emerge.PackageVirtualDbapi import PackageVirtualDbapi
from corepkg.tests import TestCase


@dataclass
class _FakePackage:
    cpv: str
    cp: str
    slot_atom: str
    _metadata: dict = field(default_factory=dict)


class PackageVirtualDbapiTestCase(TestCase):
    def testCpvRemoveDropsEmptyCpBucket(self):
        db = PackageVirtualDbapi(settings=None)
        pkg = _FakePackage("cat/pkg-1", "cat/pkg", "cat/pkg:0")

        db.cpv_inject(pkg)

        self.assertEqual(db.cp_all(), ["cat/pkg"])
        self.assertEqual(db.categories, ("cat",))

        db.cpv_remove(pkg)

        self.assertEqual(db.cp_all(), [])
        self.assertEqual(db.cpv_all(), [])
        self.assertEqual(db.categories, ())
