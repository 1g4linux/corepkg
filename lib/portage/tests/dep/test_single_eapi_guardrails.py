# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.dep import check_required_use, use_reduce
from corepkg.exception import InvalidDependString
from corepkg.tests import TestCase


class SingleEapiDepGuardrailsTestCase(TestCase):
    def test_eapi8_src_uri_arrow_is_accepted(self):
        result = use_reduce(
            "https://example.invalid/dist.tar.xz -> dist.tar.xz",
            is_src_uri=True,
            eapi="8",
        )
        self.assertEqual(
            result,
            ["https://example.invalid/dist.tar.xz", "->", "dist.tar.xz"],
        )

    def test_old_src_uri_arrow_semantics_rejected(self):
        with self.assertRaisesRegex(
            InvalidDependString, "SRC_URI arrow not allowed in EAPI 0"
        ):
            use_reduce(
                "https://example.invalid/dist.tar.xz -> dist.tar.xz",
                is_src_uri=True,
                eapi="0",
            )

    def test_invalid_required_use_context_has_deterministic_error(self):
        with self.assertRaises(InvalidDependString) as ctx:
            check_required_use(
                "?? ( a b )",
                ["a"],
                lambda flag: flag in {"a", "b"},
                eapi="4",
            )

        self.assertEqual(
            str(ctx.exception), "Operator '??' is not supported with EAPI '4'"
        )
        self.assertIsNotNone(ctx.exception.errors)
        self.assertEqual(len(ctx.exception.errors), 1)
        self.assertEqual(ctx.exception.errors[0].category, "EAPI.incompatible")
