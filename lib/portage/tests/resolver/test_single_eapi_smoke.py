# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import (
    ResolverPlayground,
    ResolverPlaygroundTestCase,
)


class SingleEapiSmokeTestCase(TestCase):
    def test_normal_dependency_solve(self):
        ebuilds = {
            "dev-libs/A-1": {"EAPI": "8", "RDEPEND": "dev-libs/B"},
            "dev-libs/B-1": {"EAPI": "8"},
        }

        test_case = ResolverPlaygroundTestCase(
            ["dev-libs/A"],
            options={"--autounmask": "n"},
            success=True,
            mergelist=["dev-libs/B-1", "dev-libs/A-1"],
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def test_blocker_handling(self):
        ebuilds = {
            "dev-libs/A-1": {"EAPI": "8", "RDEPEND": "!dev-libs/B"},
            "dev-libs/B-1": {"EAPI": "8"},
        }

        test_case = ResolverPlaygroundTestCase(
            ["dev-libs/A", "dev-libs/B"],
            options={"--autounmask": "n"},
            success=False,
            mergelist=["dev-libs/A-1", "dev-libs/B-1", "!dev-libs/B"],
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def test_slot_subslot_path(self):
        ebuilds = {
            "dev-libs/A-1": {"EAPI": "8", "RDEPEND": "dev-libs/B:0="},
            "dev-libs/B-1": {"EAPI": "8", "SLOT": "0/1"},
            "dev-libs/B-2": {"EAPI": "8", "SLOT": "0/2"},
        }

        test_case = ResolverPlaygroundTestCase(
            ["dev-libs/A"],
            options={"--autounmask": "n"},
            success=True,
            mergelist=["dev-libs/B-2", "dev-libs/A-1"],
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()
