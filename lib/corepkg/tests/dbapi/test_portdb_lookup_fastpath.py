# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.dbapi.porttree import _is_valid_cp_components
from corepkg.dep import Atom
from corepkg.exception import InvalidAtom
from corepkg.tests import TestCase


class PortdbLookupFastpathTestCase(TestCase):
    def test_is_valid_cp_components_matches_atom_validation(self):
        samples = (
            ("dev-libs", "openssl"),
            ("dev-libs", "foo-bar"),
            ("dev-libs", "foo_bar"),
            ("dev-libs", "foo+bar"),
            ("dev-libs", "foo-r1"),
            ("dev-libs", "foo-"),
            ("dev-libs", "foo--bar"),
            ("dev-libs", "1foo"),
            ("dev-libs", "foo-1"),
            ("dev-libs", "foo-1a"),
            ("dev-libs", "foo-1-r2"),
            ("dev-libs", "+foo"),
            ("dev-libs", ".foo"),
            ("dev-libs", "foo/bar"),
            ("dev-libs", ""),
            (".bad", "foo"),
            ("+bad", "foo"),
            ("bad:cat", "foo"),
            ("xgui-lib", "mesa"),
        )

        for category, package in samples:
            cp = f"{category}/{package}"
            try:
                atom = Atom(cp)
            except InvalidAtom:
                expected = False
            else:
                expected = atom == atom.cp

            with self.subTest(cp=cp):
                self.assertEqual(
                    _is_valid_cp_components(category, package),
                    expected,
                )
