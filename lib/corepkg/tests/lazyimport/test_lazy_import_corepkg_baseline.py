# Copyright 2010-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import re
import corepkg
from corepkg import os
from corepkg.const import PORTAGE_PYM_PATH
from corepkg.tests import TestCase
from corepkg.util._eventloop.global_event_loop import global_event_loop

from _emerge.PipeReader import PipeReader
from _emerge.SpawnProcess import SpawnProcess


class LazyImportCorepkgBaselineTestCase(TestCase):
    _module_re = re.compile(r"^(corepkg|_emerge)\.")

    _baseline_imports = frozenset(
        [
            "corepkg.const",
            "corepkg.installation",
            "corepkg.localization",
            "corepkg.proxy",
            "corepkg.proxy.lazyimport",
            "corepkg.proxy.objectproxy",
            "corepkg._selinux",
        ]
    )

    _baseline_import_cmd = [
        corepkg._python_interpreter,
        "-c",
        """
import os
import sys
sys.path.insert(0, os.environ["PORTAGE_PYM_PATH"])
import corepkg
sys.stdout.write(" ".join(k for k in sys.modules
	if sys.modules[k] is not None))
""",
    ]

    def testLazyImportCorepkgBaseline(self):
        """
        Check what modules are imported by a baseline module import.
        """

        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH")
        if pythonpath is not None and not pythonpath.strip():
            pythonpath = None
        if pythonpath is None:
            pythonpath = ""
        else:
            pythonpath = ":" + pythonpath
        pythonpath = PORTAGE_PYM_PATH + pythonpath
        env["PYTHONPATH"] = pythonpath

        # If python is patched to insert the path of the
        # currently installed corepkg module into sys.path,
        # then the above PYTHONPATH override doesn't help.
        env["PORTAGE_PYM_PATH"] = PORTAGE_PYM_PATH

        scheduler = global_event_loop()
        master_fd, slave_fd = os.pipe()
        master_file = os.fdopen(master_fd, "rb", 0)
        slave_file = os.fdopen(slave_fd, "wb")
        producer = SpawnProcess(
            args=self._baseline_import_cmd,
            env=env,
            fd_pipes={1: slave_fd},
            scheduler=scheduler,
        )
        producer.start()
        slave_file.close()

        consumer = PipeReader(
            input_files={"producer": master_file}, scheduler=scheduler
        )

        consumer.start()
        consumer.wait()
        self.assertEqual(producer.wait(), os.EX_OK)
        self.assertEqual(consumer.wait(), os.EX_OK)

        output = consumer.getvalue().decode("ascii", "replace").split()

        unexpected_modules = " ".join(
            sorted(
                x
                for x in output
                if self._module_re.match(x) is not None
                and x not in self._baseline_imports
            )
        )

        self.assertEqual("", unexpected_modules)
