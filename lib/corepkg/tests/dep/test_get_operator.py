# test_get_operator.py -- Corepkg Unit Testing Functionality
# Copyright 2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.dep import get_operator


class GetOperator(TestCase):
    def testGetOperator(self):
        # get_operator does not validate operators
        tests = [
            ("~", "~"),
            ("=", "="),
            (">", ">"),
            (">=", ">="),
            ("<=", "<="),
        ]

        test_cpvs = ["sys-apps/corepkg-2.1"]
        slots = [None, "1", "linux-2.5.6"]
        for cpv in test_cpvs:
            for test in tests:
                for slot in slots:
                    atom = cpv[:]
                    if slot:
                        atom += ":" + slot
                    result = get_operator(test[0] + atom)
                    self.assertEqual(
                        result,
                        test[1],
                        msg=f"get_operator({test[0] + atom}) != {test[1]}",
                    )

        result = get_operator("sys-apps/corepkg")
        self.assertEqual(result, None)

        result = get_operator("=sys-apps/corepkg-2.1*")
        self.assertEqual(result, "=*")
