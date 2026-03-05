# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import glob
import shutil

import corepkg
from corepkg import os
from corepkg.const import VDB_PATH

LEGACY_SPLIT_PACKAGES = (
    ("app-var", "eselect-*", "legacy eselect"),
    ("app-core", "gentoo-functions-*", "legacy gentoo-functions"),
    ("app-port", "elt-patches-*", "legacy elt-patches"),
)

FALLBACK_PATH_PATTERNS = {
    "legacy eselect": (
        "/usr/bin/eselect",
        "/usr/bin/kernel-config",
        "/usr/bin/profile-config",
        "/usr/bin/rc-config",
        "/usr/share/eselect",
    ),
    "legacy gentoo-functions": (
        "/usr/bin/consoletype",
        "/usr/bin/shquote",
        "/usr/lib/gentoo/functions.sh",
        "/usr/lib/gentoo/functions",
        "/usr/share/man/man1/consoletype.1*",
    ),
    "legacy elt-patches": (
        "/usr/bin/eltpatch",
        "/usr/share/elt-patches",
    ),
}


def _live_path(path):
    return os.path.join(corepkg.settings["EROOT"], path.lstrip(os.sep))


def _live_glob(pattern):
    return os.path.join(corepkg.settings["EROOT"], pattern.lstrip(os.sep))


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


def _remove_file_or_link(path, package_desc, out, failed):
    if os.path.islink(path) or os.path.isfile(path):
        try:
            os.unlink(path)
        except OSError as e:
            failed.append(path)
            out.ewarn(f"Unable to remove {package_desc} file: {path}: {e}")


def _remove_tree(path, package_desc, out, failed):
    if os.path.isdir(path):
        try:
            shutil.rmtree(path)
        except OSError as e:
            failed.append(path)
            out.ewarn(f"Unable to remove {package_desc} directory: {path}: {e}")


def _remove_vdb_entry(vdb_entry, package_desc, out):
    files, dirs = _read_contents(vdb_entry)
    failed = []

    # Remove tracked file and symlink entries first.
    for relpath in files:
        live = _live_path(relpath)
        _remove_file_or_link(live, package_desc, out, failed)

    # Try to remove tracked directories if they are empty.
    for relpath in sorted(dirs, key=len, reverse=True):
        live = _live_path(relpath)
        if os.path.isdir(live):
            try:
                os.rmdir(live)
            except OSError:
                pass

    # Fallback sweeps for known legacy paths in case CONTENTS was incomplete.
    fallback_matches = []
    for pattern in FALLBACK_PATH_PATTERNS.get(package_desc, ()):
        fallback_matches.extend(sorted(glob.glob(_live_glob(pattern))))

    for live in fallback_matches:
        _remove_file_or_link(live, package_desc, out, failed)
        _remove_tree(live, package_desc, out, failed)

    # Verify known legacy paths are gone before dropping the VDB entry.
    leftovers = []
    for relpath in files:
        live = _live_path(relpath)
        if os.path.lexists(live):
            leftovers.append(live)
    for live in fallback_matches:
        if os.path.lexists(live):
            leftovers.append(live)

    if failed or leftovers:
        problems = sorted(set(failed + leftovers))
        preview = ", ".join(problems[:5])
        raise RuntimeError(
            f"{package_desc}: cleanup incomplete for {vdb_entry}; sample leftovers: {preview}"
        )

    out.einfo(f"Removing {package_desc} VDB entry: {vdb_entry}")
    try:
        shutil.rmtree(vdb_entry)
    except OSError as e:
        raise RuntimeError(
            f"{package_desc}: unable to remove VDB entry {vdb_entry}: {e}"
        ) from e


def main():
    out = corepkg.output.EOutput()
    vdb_root = os.path.join(corepkg.settings["EROOT"], VDB_PATH)

    for category, pattern, package_desc in LEGACY_SPLIT_PACKAGES:
        matches = sorted(glob.glob(os.path.join(vdb_root, category, pattern)))
        for vdb_entry in matches:
            if os.path.isdir(vdb_entry):
                _remove_vdb_entry(vdb_entry, package_desc, out)
