# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.dep import Atom
from corepkg.exception import InvalidAtom
from corepkg.tests import TestCase
from corepkg._sets.base import WildcardPackageSet


class WildcardPackageSetTestCase(TestCase):
    """Test case for WildcardPackageSet"""

    def testWildcardPackageSet(self):
        ambig_atoms = {"A", "B", "C"}
        norm_atoms = {"dev-libs/A", ">=dev-libs/A-1"}
        wild_atoms = {"dev-libs/*", "*/B"}
        sets = {"@world", "@installed", "@system"}

        w1 = WildcardPackageSet(initial_atoms=norm_atoms)
        w2 = WildcardPackageSet(initial_atoms=wild_atoms)
        self.assertRaises(InvalidAtom, WildcardPackageSet, initial_atoms=sets)

        self.assertEqual(w1.getAtoms(), norm_atoms)
        self.assertEqual(w2.getAtoms(), wild_atoms)

        w3 = WildcardPackageSet(initial_atoms=ambig_atoms)
        self.assertEqual(w3.getAtoms(), {"*/" + a for a in ambig_atoms})

        w4 = WildcardPackageSet(initial_atoms=(Atom(a) for a in norm_atoms))
        self.assertEqual(w4.getAtoms(), norm_atoms)
