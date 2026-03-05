# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import glob
import shutil

import corepkg
from corepkg import os
from corepkg.const import VDB_PATH


def _live_path(path):
    return os.path.join(corepkg.settings["EROOT"], path.lstrip(os.sep))


def _read_contents(vdb_entry):
    contents_file = os.path.join(vdb_entry, "CONTENTS")
    files = []
    dirs = []
    if not os.path.exists(contents_file):
        return files, dirs

    with open(contents_file, encoding="utf8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("obj "):
                files.append(line.split(" ", 2)[1])
            elif line.startswith("sym "):
                files.append(line[4:].split(" -> ", 1)[0])
            elif line.startswith("dir "):
                dirs.append(line.split(" ", 1)[1].split(" ", 1)[0])
    return files, dirs


def main():
    out = corepkg.output.EOutput()
    vdb_app_var = os.path.join(corepkg.settings["EROOT"], VDB_PATH, "app-var")
    pattern = os.path.join(vdb_app_var, "eselect-*")
    matches = sorted(glob.glob(pattern))

    if not matches:
        return

    for vdb_entry in matches:
        if not os.path.isdir(vdb_entry):
            continue

        files, dirs = _read_contents(vdb_entry)
        for relpath in files:
            live = _live_path(relpath)
            if os.path.islink(live) or os.path.isfile(live):
                try:
                    os.unlink(live)
                except OSError as e:
                    out.ewarn(f"Unable to remove legacy eselect file: {live}: {e}")

        # Remove empty directories from deepest to shallowest.
        for relpath in sorted(dirs, key=len, reverse=True):
            live = _live_path(relpath)
            if os.path.isdir(live):
                try:
                    os.rmdir(live)
                except OSError:
                    pass

        out.einfo(f"Removing legacy VDB entry: {vdb_entry}")
        try:
            shutil.rmtree(vdb_entry)
        except OSError as e:
            out.ewarn(f"Unable to remove legacy VDB entry: {vdb_entry}: {e}")
