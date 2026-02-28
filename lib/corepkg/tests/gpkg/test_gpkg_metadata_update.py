# Copyright Gentoo Foundation 2006-2020
# Corepkg Unit Testing Functionality

import tempfile
from os import urandom

from corepkg import os
from corepkg import shutil
from corepkg.util._compare_files import compare_files
from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import ResolverPlayground
from corepkg.gpkg import gpkg


class test_gpkg_metadata_case(TestCase):
    def test_gpkg_update_metadata(self):
        playground = ResolverPlayground(
            user_config={
                "make.conf": ('BINPKG_COMPRESS="gzip"', 'FEATURES="-binpkg-signing"'),
            }
        )
        tmpdir = tempfile.mkdtemp()

        try:
            settings = playground.settings
            orig_full_path = os.path.join(tmpdir, "orig/")
            os.makedirs(orig_full_path)
            with open(os.path.join(orig_full_path, "test"), "wb") as test_file:
                test_file.write(urandom(1048576))

            gpkg_file_loc = os.path.join(tmpdir, "test.gpkg.tar")
            test_gpkg = gpkg(settings, "test", gpkg_file_loc)

            meta = {"test1": b"1234567890", "test2": b"abcdef"}

            test_gpkg.compress(os.path.join(tmpdir, "orig"), meta)

            meta_result = test_gpkg.get_metadata()
            self.assertEqual(meta, meta_result)

            meta_new = {"test3": b"0987654321", "test4": b"XXXXXXXX"}
            test_gpkg.update_metadata(meta_new)

            meta_result = test_gpkg.get_metadata()
            self.assertEqual(meta_new, meta_result)

            test_gpkg.decompress(os.path.join(tmpdir, "test"))
            r = compare_files(
                os.path.join(tmpdir, "orig/" + "test"),
                os.path.join(tmpdir, "test/" + "test"),
                skipped_types=("atime", "mtime", "ctime"),
            )
            self.assertEqual(r, ())
        finally:
            shutil.rmtree(tmpdir)
            playground.cleanup()
