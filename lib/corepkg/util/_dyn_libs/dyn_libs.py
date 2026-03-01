# Copyright 2021-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re
import stat

import corepkg

_LIB_SONAME_RE = re.compile(r"^lib[^/]*\.so(?:\..+)?$")


def installed_dynlibs(directory):
    """
    Traverse installed library-style soname files (lib*.so and
    lib*.so.*) and return True if any resolve to a regular file.
    If a symlink target is outside of the top directory, traversal
    follows the corresponding file inside the top directory if it
    exists, and otherwise stops following the symlink.
    """
    directory_prefix = f"{directory.rstrip(os.sep)}{os.sep}"
    for parent, _dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if _LIB_SONAME_RE.match(filename) is None:
                continue
            filename_abs = os.path.join(parent, filename)
            target = filename_abs
            levels = 0
            while True:
                try:
                    st = os.lstat(target)
                except OSError:
                    break
                if stat.S_ISREG(st.st_mode):
                    return True
                elif stat.S_ISLNK(st.st_mode):
                    levels += 1
                    if levels == 40:
                        corepkg.writemsg(
                            f"too many levels of symbolic links: {filename_abs}\n",
                            noiselevel=-1,
                        )
                        break
                    target = corepkg.abssymlink(target)
                    if not target.startswith(directory_prefix):
                        # If target is outside the top directory, then follow the
                        # corresponding file inside the top directory if it exists,
                        # and otherwise stop following.
                        target = os.path.join(directory_prefix, target.lstrip(os.sep))
                else:
                    break
    return False


def check_dyn_libs_inconsistent(directory, provides):
    """Checks directory for whether any dynamic libraries were installed and
    if PROVIDES corresponds."""

    # Let's check if we've got inconsistent results.
    # If we're installing dynamic libraries (.so files), we should
    # really have a PROVIDES.
    # (This is a complementary check at the point of ingestion for the
    # creation check in doebuild.py)
    # Note: we could check a non-empty PROVIDES against the list of .sos,
    # but this doesn't gain us anything. We're interested in failure
    # to properly parse the installed files at all, which should really
    # be a global problem (e.g. bug #811462)
    return not provides and installed_dynlibs(directory)


def fallback_multilib_category(arch):
    """
    Derive a stable single-ABI category from a scanelf architecture token.
    Returns None if the token is not usable as a category.
    """
    if not arch:
        return None

    arch = arch.strip().lower().replace("-", "_")
    if arch.startswith("em_"):
        arch = arch[3:]

    if not arch or re.fullmatch(r"[a-z0-9_]+", arch) is None:
        return None

    return arch
