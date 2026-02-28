# test_uniqueArray.py -- Corepkg Unit Testing Functionality
# Copyright 2006-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg import os
from corepkg.tests import TestCase
from corepkg.util import unique_array


class UniqueArrayTestCase(TestCase):
    def testUniqueArrayPass(self):
        """
        test corepkg.util.uniqueArray()
        """

        tests = [
            (["a", "a", "a", os, os, [], [], []], ["a", os, []]),
            ([1, 1, 1, 2, 3, 4, 4], [1, 2, 3, 4]),
        ]

        for test in tests:
            result = unique_array(test[0])
            for item in test[1]:
                number = result.count(item)
                self.assertFalse(
                    number != 1,
                    msg=f"{result} contains {number} of {item}, should be only 1",
                )
