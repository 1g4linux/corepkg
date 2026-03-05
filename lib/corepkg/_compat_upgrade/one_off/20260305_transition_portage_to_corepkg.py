# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import glob
import shutil

import corepkg
from corepkg import os
from corepkg.const import PRIVATE_PATH, VDB_PATH

SNAPSHOT_FILE = "compat_upgrade/one_off/portage_transition_paths.txt"


def _state_path():
    return os.path.join(corepkg.settings["EROOT"], PRIVATE_PATH, SNAPSHOT_FILE)


def _vdb_entries():
    vdb_root = os.path.join(corepkg.settings["EROOT"], VDB_PATH, "app-core")
    return sorted(glob.glob(os.path.join(vdb_root, "portage-*")))


def _read_contents_paths(vdb_entry):
    contents_file = os.path.join(vdb_entry, "CONTENTS")
    paths = []
    if not os.path.exists(contents_file):
        return paths

    with open(contents_file, encoding="utf8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("obj "):
                paths.append(line.split(" ", 2)[1])
            elif line.startswith("sym "):
                paths.append(line[4:].split(" -> ", 1)[0])
    return paths


def _all_owned_paths():
    vdb_root = os.path.join(corepkg.settings["EROOT"], VDB_PATH)
    owned = set()
    for category in glob.glob(os.path.join(vdb_root, "*")):
        if not os.path.isdir(category):
            continue
        for pkg in glob.glob(os.path.join(category, "*")):
            if not os.path.isdir(pkg):
                continue
            for relpath in _read_contents_paths(pkg):
                owned.add(relpath)
    return owned


def _to_live(relpath):
    return os.path.join(corepkg.settings["EROOT"], relpath.lstrip(os.sep))


def _save_snapshot(paths):
    snapshot = _state_path()
    os.makedirs(os.path.dirname(snapshot), exist_ok=True)
    with open(snapshot, "w", encoding="utf8") as f:
        for path in sorted(set(paths)):
            f.write(f"{path}\n")


def _load_snapshot():
    snapshot = _state_path()
    if not os.path.exists(snapshot):
        return []
    with open(snapshot, encoding="utf8") as f:
        return [line.strip() for line in f if line.strip()]


def _remove_vdb_entry(vdb_entry):
    shutil.rmtree(vdb_entry)


def _cleanup_snapshot_paths(out):
    paths = _load_snapshot()
    if not paths:
        return

    owned = _all_owned_paths()
    failures = []
    leftovers = []
    for relpath in paths:
        if relpath in owned:
            continue
        live = _to_live(relpath)
        if os.path.islink(live) or os.path.isfile(live):
            try:
                os.unlink(live)
            except OSError as e:
                failures.append(f"{live}: {e}")
        if os.path.lexists(live) and relpath not in owned:
            leftovers.append(live)

    if failures or leftovers:
        sample = ", ".join((failures + leftovers)[:5])
        raise RuntimeError(f"portage transition cleanup incomplete: {sample}")

    os.unlink(_state_path())
    out.einfo("Completed legacy portage transition file cleanup")


def main():
    out = corepkg.output.EOutput()
    entries = [entry for entry in _vdb_entries() if os.path.isdir(entry)]

    if entries:
        snapshot_paths = []
        for entry in entries:
            snapshot_paths.extend(_read_contents_paths(entry))

        _save_snapshot(snapshot_paths)

        for entry in entries:
            out.einfo(f"Removing legacy portage VDB entry: {entry}")
            _remove_vdb_entry(entry)

        out.ewarn(
            "Legacy app-core/portage files were kept for safety during this run. "
            "Re-merge app-core/corepkg once to complete replacement cleanup."
        )
        return False

    _cleanup_snapshot_paths(out)
