# xpak/test_decodeint.py
# Copyright 2006-2020 Gentoo Authors
# Corepkg Unit Testing Functionality

from corepkg.tests import TestCase
from corepkg.xpak import decodeint, encodeint


class testDecodeIntTestCase(TestCase):
    def testDecodeInt(self):
        for n in range(1000):
            self.assertEqual(decodeint(encodeint(n)), n)

        for n in (2**32 - 1,):
            self.assertEqual(decodeint(encodeint(n)), n)
