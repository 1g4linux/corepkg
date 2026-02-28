# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import subprocess

import corepkg
from corepkg import os
from corepkg.const import PORTAGE_PYM_PATH, USER_CONFIG_PATH
from corepkg.exception import UnsupportedAPIException
from corepkg.process import find_binary
from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import ResolverPlayground
from corepkg.util import ensure_dirs


class UnsupportedEAPIEmergeTestCase(TestCase):
    def _run_emerge_for_eapi(self, eapi):
        ebuilds = {"dev-libs/A-1": {"EAPI": eapi}}

        playground = ResolverPlayground(ebuilds=ebuilds, debug=False)
        try:
            settings = playground.settings
            eprefix = settings["EPREFIX"]
            var_cache_edb = os.path.join(eprefix, "var", "cache", "edb")
            user_config_dir = os.path.join(eprefix, USER_CONFIG_PATH)

            corepkg_python = corepkg._python_interpreter
            emerge_cmd = (
                corepkg_python,
                "-b",
                "-Wd",
                os.path.join(str(self.bindir), "emerge"),
                "--oneshot",
                "=dev-libs/A-1",
            )

            fake_bin = os.path.join(eprefix, "bin")
            corepkg_tmpdir = os.path.join(eprefix, "var", "tmp", "corepkg")

            path = settings.get("PATH")
            if path is not None and not path.strip():
                path = None
            if path is None:
                path = ""
            else:
                path = ":" + path
            path = fake_bin + path

            pythonpath = os.environ.get("PYTHONPATH")
            if pythonpath is not None and not pythonpath.strip():
                pythonpath = None
            if pythonpath is not None and pythonpath.split(":")[0] == PORTAGE_PYM_PATH:
                pass
            else:
                if pythonpath is None:
                    pythonpath = ""
                else:
                    pythonpath = ":" + pythonpath
                pythonpath = PORTAGE_PYM_PATH + pythonpath

            env = {
                "PORTAGE_OVERRIDE_EPREFIX": eprefix,
                "PATH": path,
                "PORTAGE_PYTHON": corepkg_python,
                "PORTAGE_REPOSITORIES": settings.repositories.config_string(),
                "PYTHONDONTWRITEBYTECODE": os.environ.get(
                    "PYTHONDONTWRITEBYTECODE", ""
                ),
                "PYTHONPATH": pythonpath,
                "PORTAGE_INST_GID": str(os.getgid()),
                "PORTAGE_INST_UID": str(os.getuid()),
            }

            if "__PORTAGE_TEST_HARDLINK_LOCKS" in os.environ:
                env["__PORTAGE_TEST_HARDLINK_LOCKS"] = os.environ[
                    "__PORTAGE_TEST_HARDLINK_LOCKS"
                ]

            dirs = [
                playground.distdir,
                fake_bin,
                corepkg_tmpdir,
                user_config_dir,
                var_cache_edb,
            ]
            true_binary = find_binary("true")
            self.assertIsNotNone(true_binary, "true command not found")

            for d in dirs:
                ensure_dirs(d)
            for x in ("chown", "chgrp"):
                os.symlink(true_binary, os.path.join(fake_bin, x))
            with open(os.path.join(var_cache_edb, "counter"), "wb") as f:
                f.write(b"100")

            proc = subprocess.Popen(
                emerge_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, _ = proc.communicate()
            output = corepkg._unicode_decode(stdout)
            return proc.returncode, output
        finally:
            playground.cleanup()

    def testEmergeRejectsUnsupportedEapiPackage(self):
        returncode, output = self._run_emerge_for_eapi("9999")

        self.assertNotEqual(returncode, os.EX_OK)
        self.assertIn("unsupported EAPI: '9999' (expected EAPI='8')", output)

    def testEmergeRejectsLegacyAndFutureEapis(self):
        for eapi in ("7", "9"):
            with self.subTest(eapi=eapi):
                returncode, output = self._run_emerge_for_eapi(eapi)
                self.assertNotEqual(returncode, os.EX_OK)
                self.assertIn(
                    f"unsupported EAPI: '{eapi}' (expected EAPI='8')", output
                )

    def testUnsupportedApiExceptionMessageIsDeterministic(self):
        msg = str(UnsupportedAPIException("dev-libs/A-1", "9"))
        self.assertEqual(
            msg,
            "Unable to do any operations on 'dev-libs/A-1': "
            "unsupported EAPI: '9' (expected EAPI='8')",
        )
