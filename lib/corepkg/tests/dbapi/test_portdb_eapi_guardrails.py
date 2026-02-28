# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.exception import InvalidDependString
from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import ResolverPlayground


class PortdbEapiGuardrailsTestCase(TestCase):
    def test_fetch_map_accepts_eapi_8(self):
        ebuilds = {
            "dev-libs/A-1": {
                "EAPI": "8",
                "SRC_URI": "https://example.invalid/distfiles/A-1.tar.xz",
            }
        }

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            portdb = playground.trees[playground.eroot]["porttree"].dbapi
            fetch_map = portdb.getFetchMap("dev-libs/A-1")
            self.assertIn("A-1.tar.xz", fetch_map)
            self.assertEqual(
                fetch_map["A-1.tar.xz"],
                ("https://example.invalid/distfiles/A-1.tar.xz",),
            )
        finally:
            playground.cleanup()

    def test_fetch_map_rejects_unsupported_eapi(self):
        ebuilds = {
            "dev-libs/A-1": {
                "EAPI": "9999",
                "SRC_URI": "https://example.invalid/distfiles/A-1.tar.xz",
            }
        }

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            portdb = playground.trees[playground.eroot]["porttree"].dbapi
            with self.assertRaisesRegex(
                InvalidDependString,
                "unsupported EAPI: '9999' \\(expected EAPI='8'\\)",
            ):
                portdb.getFetchMap("dev-libs/A-1")
        finally:
            playground.cleanup()

    def test_fetch_map_rejects_legacy_eapis(self):
        for eapi in ("7", "9"):
            with self.subTest(eapi=eapi):
                ebuilds = {
                    "dev-libs/A-1": {
                        "EAPI": eapi,
                        "SRC_URI": "https://example.invalid/distfiles/A-1.tar.xz",
                    }
                }

                playground = ResolverPlayground(ebuilds=ebuilds)
                try:
                    portdb = playground.trees[playground.eroot]["porttree"].dbapi
                    with self.assertRaisesRegex(
                        InvalidDependString,
                        rf"unsupported EAPI: '{eapi}' \(expected EAPI='8'\)",
                    ):
                        portdb.getFetchMap("dev-libs/A-1")
                finally:
                    playground.cleanup()

    def test_fetch_map_missing_eapi_is_accepted(self):
        ebuilds = {
            "dev-libs/A-1": {
                "SRC_URI": "https://example.invalid/distfiles/A-1.tar.xz",
            }
        }

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            portdb = playground.trees[playground.eroot]["porttree"].dbapi
            fetch_map = portdb.getFetchMap("dev-libs/A-1")
            self.assertIn("A-1.tar.xz", fetch_map)
            self.assertEqual(
                fetch_map["A-1.tar.xz"],
                ("https://example.invalid/distfiles/A-1.tar.xz",),
            )
        finally:
            playground.cleanup()
