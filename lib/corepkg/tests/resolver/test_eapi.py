# Copyright 2010-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import (
    ResolverPlayground,
    ResolverPlaygroundTestCase,
)


class EAPITestCase(TestCase):
    def testEAPI(self):
        ebuilds = {
            "dev-libs/A-1.0": {"EAPI": 8, "IUSE": "+foo"},
            "dev-libs/A-2.0": {"EAPI": 8, "DEPEND": "dev-libs/B:0"},
            "dev-libs/A-3.0": {"EAPI": 8, "DEPEND": "dev-libs/B[foo]"},
            "dev-libs/A-4.0": {"EAPI": 8, "DEPEND": "!!dev-libs/C"},
            "dev-libs/A-5.0": {"EAPI": 8, "DEPEND": "dev-libs/B[bar(+)]"},
            "dev-libs/A-6.0": {
                "EAPI": 8,
                "IUSE": "foo +bar",
                "REQUIRED_USE": "|| ( foo bar )",
            },
            "dev-libs/B-1": {"EAPI": 8, "IUSE": "+foo"},
            "dev-libs/C-1": {"EAPI": 8},
        }

        test_cases = (
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-1.0"], success=True, mergelist=["dev-libs/A-1.0"]
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-2.0"],
                success=True,
                mergelist=["dev-libs/B-1", "dev-libs/A-2.0"],
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-3.0"],
                success=True,
                mergelist=["dev-libs/B-1", "dev-libs/A-3.0"],
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-4.0"], success=True, mergelist=["dev-libs/A-4.0"]
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-5.0"],
                success=True,
                mergelist=["dev-libs/B-1", "dev-libs/A-5.0"],
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-6.0"], success=True, mergelist=["dev-libs/A-6.0"]
            ),
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def testBdepend(self):
        ebuilds = {
            "dev-libs/A-1.0": {"EAPI": 8},
            "dev-libs/B-1.0": {"EAPI": 8, "BDEPEND": "dev-libs/A"},
        }

        # Verify that BDEPEND is considered at all.
        test_case = ResolverPlaygroundTestCase(
            ["=dev-libs/B-1.0"],
            success=True,
            mergelist=["dev-libs/A-1.0", "dev-libs/B-1.0"],
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def testIdepend(self):
        ebuilds = {
            "dev-libs/A-1.0": {"EAPI": 8},
            "dev-libs/B-1.0": {"EAPI": 8, "IDEPEND": "dev-libs/A"},
        }

        test_cases = (
            # Verify that IDEPEND is considered at all.
            ResolverPlaygroundTestCase(
                ["=dev-libs/B-1.0"],
                success=True,
                mergelist=["dev-libs/A-1.0", "dev-libs/B-1.0"],
            ),
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()
