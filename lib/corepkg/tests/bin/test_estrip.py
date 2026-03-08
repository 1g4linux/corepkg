# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import corepkg
from corepkg.const import PORTAGE_BIN_PATH, PORTAGE_PYM_PATH
from corepkg.tests import TestCase


class TestEstrip(TestCase):
    def setUp(self):
        super().setUp()
        self._tempdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self._tempdir)
        super().tearDown()

    def _base_env(self):
        env = os.environ.copy()
        env.update(
            {
                "EAPI": "8",
                "PORTAGE_BIN_PATH": PORTAGE_BIN_PATH,
                "PORTAGE_PYM_PATH": PORTAGE_PYM_PATH,
                "PORTAGE_PYTHON": corepkg._python_interpreter,
                "PATH": PORTAGE_BIN_PATH + os.pathsep + env["PATH"],
                "D": str(self._tempdir / "image"),
                "ED": str(self._tempdir / "image"),
                "T": str(self._tempdir / "temp"),
                "PORTAGE_BUILDDIR": str(self._tempdir / "build"),
                "CATEGORY": "app-misc",
                "PF": "stripcheck-1",
                "SLOT": "0",
                "ARCH": "amd64",
                "CHOST": "x86_64-pc-linux-gnu",
                "WORKDIR": str(self._tempdir / "work"),
                "FEATURES": "",
                "PORTAGE_RESTRICT": "",
            }
        )
        Path(env["D"]).mkdir()
        Path(env["T"]).mkdir()
        Path(env["PORTAGE_BUILDDIR"], "build-info").mkdir(parents=True)
        Path(env["WORKDIR"]).mkdir()
        return env

    def _run_estrip(self, env, *args):
        proc = subprocess.run(
            [os.path.join(PORTAGE_BIN_PATH, "estrip"), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def _make_archive(self, env, relpath):
        source_dir = Path(env["WORKDIR"]) / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        c_file = source_dir / "demo.c"
        o_file = source_dir / "demo.o"
        archive = Path(env["ED"]) / relpath.lstrip("/")
        archive.parent.mkdir(parents=True, exist_ok=True)
        c_file.write_text("int demo(void) { return 42; }\n", encoding="ascii")
        subprocess.run(
            ["cc", "-c", str(c_file), "-o", str(o_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["ar", "cr", str(archive), str(o_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return archive

    def test_queue_respects_path_boundaries(self):
        env = self._base_env()

        exact_file = Path(env["ED"]) / "usr/bin/foo"
        exact_file.parent.mkdir(parents=True, exist_ok=True)
        exact_file.write_text("", encoding="ascii")

        sibling_file = Path(env["ED"]) / "usr/bin/foobar"
        sibling_file.write_text("", encoding="ascii")

        exact_dir_file = Path(env["ED"]) / "usr/lib/libkeep.so"
        exact_dir_file.parent.mkdir(parents=True, exist_ok=True)
        exact_dir_file.write_text("", encoding="ascii")

        sibling_dir_file = Path(env["ED"]) / "usr/lib64/libskip.so"
        sibling_dir_file.parent.mkdir(parents=True, exist_ok=True)
        sibling_dir_file.write_text("", encoding="ascii")

        needed = Path(env["PORTAGE_BUILDDIR"]) / "build-info/NEEDED"
        needed.write_text(
            "\n".join(
                (
                    "/usr/bin/foo libc.so.6",
                    "/usr/bin/foobar libc.so.6",
                    "/usr/lib/libkeep.so libc.so.6",
                    "/usr/lib64/libskip.so libc.so.6",
                )
            )
            + "\n",
            encoding="ascii",
        )

        self._run_estrip(env, "--queue", "/usr/bin/foo", "/usr/lib")

        self.assertTrue(exact_file.with_suffix(exact_file.suffix + ".estrip").exists())
        self.assertFalse(sibling_file.with_suffix(sibling_file.suffix + ".estrip").exists())
        self.assertTrue(exact_dir_file.with_suffix(exact_dir_file.suffix + ".estrip").exists())
        self.assertFalse(
            sibling_dir_file.with_suffix(sibling_dir_file.suffix + ".estrip").exists()
        )

    def test_strip_mask_is_not_shell_evaluated(self):
        env = self._base_env()
        env["PORTAGE_RESTRICT"] = "binchecks"
        archive = self._make_archive(env, "/usr/lib/libdemo.a")
        marker = Path(env["T"]) / "strip-mask-command-ran"
        env["STRIP_MASK"] = (
            f'$(touch "{marker}"; printf /usr/lib/libdemo.a)'
        )

        self._run_estrip(env, "--prepallstrip")

        self.assertFalse(marker.exists())
        self.assertTrue(archive.exists())

    def test_ldflags_sentinel_is_corepkg_specific(self):
        estrip_text = Path(PORTAGE_BIN_PATH, "estrip").read_text(encoding="utf8")
        ignored_flags_text = Path(
            PORTAGE_BIN_PATH, "install-qa-check.d", "10ignored-flags"
        ).read_text(encoding="utf8")

        for text in (estrip_text, ignored_flags_text):
            self.assertIn("__corepkg_check_ldflags__", text)
            self.assertNotIn("__gentoo_check_ldflags__", text)
