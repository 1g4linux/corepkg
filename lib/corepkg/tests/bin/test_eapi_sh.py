# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import subprocess

from corepkg.const import PORTAGE_BIN_PATH
from corepkg.tests import TestCase


class TestEapiSh(TestCase):
    def test_bash_compat_predicates_are_eapi8_only(self):
        script = f"""
source "{PORTAGE_BIN_PATH}"/eapi.sh
for fn in ___eapi_bash_3_2 ___eapi_bash_4_2 ___eapi_bash_5_0 ___eapi_bash_5_3; do
\tif $fn; then
\t\techo "$fn=1"
\telse
\t\techo "$fn=0"
\tfi
done
"""

        proc = subprocess.run(
            ["bash", "-c", script],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.stdout.splitlines(),
            [
                "___eapi_bash_3_2=0",
                "___eapi_bash_4_2=0",
                "___eapi_bash_5_0=1",
                "___eapi_bash_5_3=0",
            ],
        )
