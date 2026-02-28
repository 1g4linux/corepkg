# Copyright 2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import (
    ResolverPlayground,
    ResolverPlaygroundTestCase,
)


class OrDowngradeInstalledTestCase(TestCase):
    def testOrDowngradeInstalled(self):
        ebuilds = {
            "net-misc/foo-1": {
                "EAPI": "8",
                "RDEPEND": "|| ( sys-libs/glibc[rpc(-)]  net-libs/libtirpc )",
            },
            "net-libs/libtirpc-1": {
                "EAPI": "8",
            },
            "sys-libs/glibc-2.26": {"EAPI": "8", "IUSE": ""},
            "sys-libs/glibc-2.24": {"EAPI": "8", "IUSE": "+rpc"},
        }

        installed = {
            "sys-libs/glibc-2.26": {"EAPI": "8", "IUSE": ""},
        }

        world = ["sys-libs/glibc"]

        test_cases = (
            # Test bug 635540, where we need to install libtirpc
            # rather than downgrade glibc.
            ResolverPlaygroundTestCase(
                ["net-misc/foo"],
                success=True,
                mergelist=[
                    "net-libs/libtirpc-1",
                    "net-misc/foo-1",
                ],
            ),
        )

        playground = ResolverPlayground(
            debug=False, ebuilds=ebuilds, installed=installed, world=world
        )

        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.debug = False
            playground.cleanup()

        # In some cases it's necessary to downgrade due to
        # the installed package being masked (glibc is a
        # not an ideal example because it's usually not
        # practical to downgrade it).
        user_config = {
            "package.mask": (">=sys-libs/glibc-2.26",),
        }

        test_cases = (
            ResolverPlaygroundTestCase(
                ["net-misc/foo"],
                success=True,
                mergelist=[
                    "sys-libs/glibc-2.24",
                    "net-misc/foo-1",
                ],
            ),
        )

        playground = ResolverPlayground(
            debug=False,
            ebuilds=ebuilds,
            installed=installed,
            world=world,
            user_config=user_config,
        )

        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.debug = False
            playground.cleanup()
