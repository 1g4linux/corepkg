# test_normalizePath.py -- Corepkg Unit Testing Functionality
# Copyright 2006-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase


class NormalizePathTestCase(TestCase):
    def testNormalizePath(self):
        from corepkg.util import normalize_path

        path = "///foo/bar/baz"
        good = "/foo/bar/baz"
        self.assertEqual(normalize_path(path), good)
