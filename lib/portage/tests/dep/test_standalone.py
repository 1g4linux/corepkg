# Copyright 2010-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.dep import cpvequal
from corepkg.exception import CorepkgException


class TestStandalone(TestCase):
    """Test some small functions corepkg.dep"""

    def testCPVequal(self):
        test_cases = (
            ("sys-apps/corepkg-2.1", "sys-apps/corepkg-2.1", True),
            ("sys-apps/corepkg-2.1", "sys-apps/corepkg-2.0", False),
            ("sys-apps/corepkg-2.1", "sys-apps/corepkg-2.1-r1", False),
            ("sys-apps/corepkg-2.1-r1", "sys-apps/corepkg-2.1", False),
            ("sys-apps/corepkg-2.1_alpha3", "sys-apps/corepkg-2.1", False),
            ("sys-apps/corepkg-2.1_alpha3_p6", "sys-apps/corepkg-2.1_alpha3", False),
            ("sys-apps/corepkg-2.1_alpha3", "sys-apps/corepkg-2.1", False),
            ("sys-apps/corepkg-2.1", "sys-apps/X-2.1", False),
            ("sys-apps/corepkg-2.1", "corepkg-2.1", False),
        )

        test_cases_xfail = (
            ("sys-apps/corepkg", "sys-apps/corepkg"),
            ("sys-apps/corepkg-2.1-6", "sys-apps/corepkg-2.1-6"),
        )

        for cpv1, cpv2, expected_result in test_cases:
            self.assertEqual(
                cpvequal(cpv1, cpv2),
                expected_result,
                f"cpvequal('{cpv1}', '{cpv2}') != {expected_result}",
            )

        for cpv1, cpv2 in test_cases_xfail:
            self.assertRaisesMsg(
                f"cpvequal({cpv1}, {cpv2})",
                CorepkgException,
                cpvequal,
                cpv1,
                cpv2,
            )
