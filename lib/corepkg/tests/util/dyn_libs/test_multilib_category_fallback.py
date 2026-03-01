# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.util._dyn_libs.dyn_libs import fallback_multilib_category


class FallbackMultilibCategoryTestCase(TestCase):
    def testFallbackMultilibCategoryNormalize(self):
        self.assertEqual(fallback_multilib_category("X86_64"), "x86_64")
        self.assertEqual(fallback_multilib_category("EM_AARCH64"), "aarch64")
        self.assertEqual(fallback_multilib_category("riscv-64"), "riscv_64")

    def testFallbackMultilibCategoryInvalid(self):
        self.assertEqual(fallback_multilib_category(""), None)
        self.assertEqual(fallback_multilib_category("x86 64"), None)
        self.assertEqual(fallback_multilib_category(None), None)
