# test_dep_getcpv.py -- Corepkg Unit Testing Functionality
# Copyright 2006-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.dep import dep_getcpv


class DepGetCPV(TestCase):
    """A simple testcase for isvalidatom"""

    def testDepGetCPV(self):
        prefix_ops = ["<", ">", "=", "~", "<=", ">=", "!=", "!<", "!>", "!~"]

        bad_prefix_ops = [">~", "<~", "~>", "~<"]
        postfix_ops = [
            ("=", "*"),
        ]

        cpvs = ["sys-apps/corepkg-2.1", "sys-apps/corepkg-2.1", "sys-apps/corepkg-2.1"]
        slots = [None, ":foo", ":2"]
        for cpv in cpvs:
            for slot in slots:
                for prefix in prefix_ops:
                    mycpv = prefix + cpv
                    if slot:
                        mycpv += slot
                    self.assertEqual(dep_getcpv(mycpv), cpv)

                for prefix, postfix in postfix_ops:
                    mycpv = prefix + cpv + postfix
                    if slot:
                        mycpv += slot
                    self.assertEqual(dep_getcpv(mycpv), cpv)
