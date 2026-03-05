# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import glob
import shutil

import corepkg
from corepkg import os
from corepkg.const import VDB_PATH

LEGACY_PATH_PATTERNS = (
    "/usr/bin/eselect",
    "/usr/bin/kernel-config",
    "/usr/bin/profile-config",
    "/usr/bin/rc-config",
    "/usr/share/eselect",
    "/usr/bin/consoletype",
    "/usr/bin/shquote",
    "/usr/lib/gentoo/functions.sh",
    "/usr/lib/gentoo/functions",
    "/usr/share/man/man1/consoletype.1*",
    "/usr/bin/eltpatch",
    "/usr/share/elt-patches",
)


def _live_glob(pattern):
    return os.path.join(corepkg.settings["EROOT"], pattern.lstrip(os.sep))


def _to_relpath(live_path):
    eroot = corepkg.settings["EROOT"].rstrip(os.sep) or os.sep
    if eroot != os.sep and live_path.startswith(eroot + os.sep):
        rel = live_path[len(eroot) :]
    else:
        rel = live_path
    if not rel.startswith(os.sep):
        rel = os.sep + rel
    return rel


def _read_vdb_contents_paths(vdb_entry):
    contents_file = os.path.join(vdb_entry, "CONTENTS")
    owned = set()
    if not os.path.exists(contents_file):
        return owned

    with open(contents_file, encoding="utf8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("obj "):
                owned.add(line.split(" ", 2)[1])
            elif line.startswith("sym "):
                owned.add(line[4:].split(" -> ", 1)[0])
            elif line.startswith("dir "):
                owned.add(line.split(" ", 1)[1].split(" ", 1)[0])
    return owned


def _current_corepkg_owned_paths():
    vdb_root = os.path.join(corepkg.settings["EROOT"], VDB_PATH, "app-core")
    entries = sorted(glob.glob(os.path.join(vdb_root, "corepkg-*")))
    if not entries:
        return set()
    return _read_vdb_contents_paths(entries[-1])


def _path_owned_or_contains_owned(relpath, owned):
    if relpath in owned:
        return True
    prefix = relpath.rstrip(os.sep) + os.sep
    for candidate in owned:
        if candidate.startswith(prefix):
            return True
    return False


def main():
    out = corepkg.output.EOutput()
    owned = _current_corepkg_owned_paths()
    failures = []

    for pattern in LEGACY_PATH_PATTERNS:
        for live in sorted(glob.glob(_live_glob(pattern))):
            relpath = _to_relpath(live)
            if _path_owned_or_contains_owned(relpath, owned):
                continue

            if os.path.islink(live) or os.path.isfile(live):
                out.einfo(f"Pruning unowned legacy path: {live}")
                try:
                    os.unlink(live)
                except OSError as e:
                    failures.append(f"{live}: {e}")
            elif os.path.isdir(live):
                out.einfo(f"Pruning unowned legacy directory: {live}")
                try:
                    shutil.rmtree(live)
                except OSError as e:
                    failures.append(f"{live}: {e}")

    if failures:
        raise RuntimeError(
            "Failed pruning some unowned legacy paths: " + "; ".join(failures[:5])
        )
