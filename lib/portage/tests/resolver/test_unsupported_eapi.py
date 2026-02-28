# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import (
    ResolverPlayground,
    ResolverPlaygroundTestCase,
)


class UnsupportedEAPITestCase(TestCase):
    def test_supported_candidate_is_selected(self):
        ebuilds = {
            "app-misc/A-1": {"EAPI": "8"},
            "app-misc/A-2": {"EAPI": "9999"},
        }

        test_case = ResolverPlaygroundTestCase(
            ["app-misc/A"],
            options={"--autounmask": "n"},
            success=True,
            mergelist=["app-misc/A-1"],
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def test_only_unsupported_candidate_is_rejected(self):
        ebuilds = {
            "app-misc/A-1": {"EAPI": "9999"},
        }

        test_case = ResolverPlaygroundTestCase(
            ["=app-misc/A-1"],
            options={"--autounmask": "n"},
            success=False,
        )

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            playground.run_TestCase(test_case)
            self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()
