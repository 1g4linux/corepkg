# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import shutil
import tempfile

from corepkg.tests import TestCase
from corepkg.util.listdir import cacheddir, listdir


class ListdirTestCase(TestCase):
    def setUp(self):
        self._tempdir = tempfile.mkdtemp()
        self._paths = {
            "regular_file": os.path.join(self._tempdir, "regular_file"),
            "regular_dir": os.path.join(self._tempdir, "regular_dir"),
            "symlink_file": os.path.join(self._tempdir, "symlink_file"),
            "symlink_dir": os.path.join(self._tempdir, "symlink_dir"),
            "broken_link": os.path.join(self._tempdir, "broken_link"),
            "vcs_dir": os.path.join(self._tempdir, ".git"),
            "nested_file": os.path.join(self._tempdir, "regular_dir", "nested_file"),
        }

        with open(self._paths["regular_file"], "w", encoding="utf8") as file_obj:
            file_obj.write("x")

        os.mkdir(self._paths["regular_dir"])
        with open(self._paths["nested_file"], "w", encoding="utf8") as file_obj:
            file_obj.write("y")

        os.mkdir(self._paths["vcs_dir"])

        try:
            os.symlink(self._paths["regular_file"], self._paths["symlink_file"])
            os.symlink(self._paths["regular_dir"], self._paths["symlink_dir"])
            os.symlink(
                os.path.join(self._tempdir, "does-not-exist"), self._paths["broken_link"]
            )
        except (NotImplementedError, OSError):
            self.skipTest("symlink support is required for listdir type tests")

    def tearDown(self):
        shutil.rmtree(self._tempdir)

    def test_cacheddir_follow_symlinks_true(self):
        names, types = cacheddir(
            self._tempdir,
            ignorecvs=False,
            ignorelist=[],
            EmptyOnError=True,
            followSymlinks=True,
        )
        type_map = dict(zip(names, types))
        self.assertEqual(type_map["regular_file"], 0)
        self.assertEqual(type_map["regular_dir"], 1)
        self.assertEqual(type_map["symlink_file"], 0)
        self.assertEqual(type_map["symlink_dir"], 1)
        self.assertEqual(type_map["broken_link"], 3)

    def test_cacheddir_follow_symlinks_false(self):
        names, types = cacheddir(
            self._tempdir,
            ignorecvs=False,
            ignorelist=[],
            EmptyOnError=True,
            followSymlinks=False,
        )
        type_map = dict(zip(names, types))
        self.assertEqual(type_map["symlink_file"], 2)
        self.assertEqual(type_map["symlink_dir"], 2)
        self.assertEqual(type_map["broken_link"], 2)

    def test_listdir_recursive_and_ignorecvs(self):
        results = listdir(
            self._tempdir,
            recursive=True,
            filesonly=True,
            ignorecvs=True,
            followSymlinks=True,
            EmptyOnError=True,
        )
        self.assertIn("regular_file", results)
        self.assertIn(os.path.join("regular_dir", "nested_file"), results)
        self.assertNotIn(".git", results)
