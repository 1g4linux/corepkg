# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import glob
import shutil

import corepkg
from corepkg import os
from corepkg.const import VDB_PATH


def main():
    out = corepkg.output.EOutput()
    vdb_app_var = os.path.join(corepkg.settings["EROOT"], VDB_PATH, "app-var")
    pattern = os.path.join(vdb_app_var, "eselect-*")
    matches = sorted(glob.glob(pattern))

    if not matches:
        return

    for path in matches:
        if not os.path.isdir(path):
            continue
        out.einfo(f"Removing stale VDB entry: {path}")
        try:
            shutil.rmtree(path)
        except OSError as e:
            out.ewarn(f"Unable to remove stale VDB entry: {path}: {e}")
