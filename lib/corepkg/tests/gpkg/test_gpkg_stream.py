# Copyright Gentoo Foundation 2006-2020
# Corepkg Unit Testing Functionality

import tempfile
import io
import tarfile
from os import urandom

import corepkg.gpkg
from corepkg import os
from corepkg import shutil
from corepkg.tests import TestCase
from corepkg.exception import CompressorOperationFailed


class test_gpkg_stream_case(TestCase):
    def test_gpkg_stream_reader(self):
        data = urandom(1048576)
        data_io = io.BytesIO(data)
        data_io.seek(0)
        with corepkg.gpkg.tar_stream_reader(data_io, ["cat"]) as test_reader:
            data2 = test_reader.read()
        data_io.close()
        self.assertEqual(data, data2)

    def test_gpkg_stream_reader_without_cmd(self):
        data = urandom(1048576)
        data_io = io.BytesIO(data)
        data_io.seek(0)
        with corepkg.gpkg.tar_stream_reader(data_io) as test_reader:
            data2 = test_reader.read()
        data_io.close()
        self.assertEqual(data, data2)

    def test_gpkg_stream_reader_kill(self):
        data = urandom(1048576)
        data_io = io.BytesIO(data)
        data_io.seek(0)
        with corepkg.gpkg.tar_stream_reader(data_io, ["cat"]) as test_reader:
            try:
                test_reader.kill()
            except CompressorOperationFailed:
                pass
        data_io.close()
        self.assertNotEqual(test_reader.proc.poll(), None)

    def test_gpkg_stream_reader_kill_without_cmd(self):
        data = urandom(1048576)
        data_io = io.BytesIO(data)
        data_io.seek(0)
        with corepkg.gpkg.tar_stream_reader(data_io) as test_reader:
            test_reader.kill()
        data_io.close()
        self.assertEqual(test_reader.proc, None)

    def test_gpkg_stream_writer(self):
        tmpdir = tempfile.mkdtemp()
        try:
            gpkg_file_loc = os.path.join(tmpdir, "test.gpkg.tar")
            data = urandom(1048576)
            with tarfile.open(gpkg_file_loc, "w") as test_tar:
                test_tarinfo = tarfile.TarInfo("test")
                with corepkg.gpkg.tar_stream_writer(
                    test_tarinfo, test_tar, tarfile.USTAR_FORMAT, ["cat"]
                ) as test_writer:
                    test_writer.write(data)

            with tarfile.open(gpkg_file_loc, "r") as test_tar:
                test_tarinfo = test_tar.getmember("test")
                data2 = test_tar.extractfile(test_tarinfo).read()
                self.assertEqual(data, data2)
        finally:
            shutil.rmtree(tmpdir)

    def test_gpkg_stream_writer_without_cmd(self):
        tmpdir = tempfile.mkdtemp()

        try:
            gpkg_file_loc = os.path.join(tmpdir, "test.gpkg.tar")
            data = urandom(1048576)
            with tarfile.open(gpkg_file_loc, "w") as test_tar:
                test_tarinfo = tarfile.TarInfo("test")
                with corepkg.gpkg.tar_stream_writer(
                    test_tarinfo, test_tar, tarfile.USTAR_FORMAT
                ) as test_writer:
                    test_writer.write(data)

            with tarfile.open(gpkg_file_loc, "r") as test_tar:
                test_tarinfo = test_tar.getmember("test")
                data2 = test_tar.extractfile(test_tarinfo).read()
                self.assertEqual(data, data2)
        finally:
            shutil.rmtree(tmpdir)

    def test_tar_safe_extract_detects_dot_slash_duplicate(self):
        tmpdir = tempfile.mkdtemp()
        tar_path = os.path.join(tmpdir, "dup.tar")
        extract_path = os.path.join(tmpdir, "extract")

        os.mkdir(extract_path)

        try:
            with tarfile.open(tar_path, "w") as archive:
                for name in ("./image/dup", "image/dup"):
                    data = b"x"
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))

            with tarfile.open(tar_path, "r") as archive:
                safe_extract = corepkg.gpkg.tar_safe_extract(archive, "image")
                self.assertRaises(ValueError, safe_extract.extractall, extract_path)
        finally:
            shutil.rmtree(tmpdir)
