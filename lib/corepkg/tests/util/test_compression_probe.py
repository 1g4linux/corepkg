# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg.tests import TestCase
from corepkg.util.compression_probe import _compressors


class CompressionProbeTestCase(TestCase):
    def test_zstd_decompress_command_uses_jobs_placeholder(self):
        self.assertIn("-T{JOBS}", _compressors["zstd"]["decompress"])
