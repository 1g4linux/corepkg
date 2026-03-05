# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import corepkg
from corepkg import os


def _eroot_join(*parts):
    return os.path.join(corepkg.settings["EROOT"], *parts)


def _remove_self_referential_portage_link(out):
    """
    Remove stale /etc/corepkg/portage -> portage links (or equivalent),
    which can appear after partial/manual migration attempts.
    """
    stale_link = _eroot_join("etc", "corepkg", "portage")
    if not os.path.islink(stale_link):
        return

    try:
        target = os.readlink(stale_link)
    except OSError as e:
        out.ewarn(f"Unable to inspect stale compat symlink {stale_link}: {e}")
        return

    norm_target = os.path.normpath(target)
    if norm_target != "portage":
        return

    out.einfo(f"Removing stale compat symlink: {stale_link} -> {target}")
    try:
        os.unlink(stale_link)
    except OSError as e:
        out.ewarn(f"Unable to remove stale compat symlink {stale_link}: {e}")


def _normalize_corepkg_layout(out):
    """
    Convert legacy symlink layout:
      /etc/corepkg -> /etc/portage (dir)
    to canonical layout:
      /etc/corepkg (dir), /etc/portage -> corepkg
    """
    corepkg_path = _eroot_join("etc", "corepkg")
    portage_path = _eroot_join("etc", "portage")

    if not os.path.islink(corepkg_path):
        return True

    try:
        corepkg_target_real = os.path.realpath(corepkg_path)
        same_as_portage = os.path.samefile(corepkg_target_real, portage_path)
    except OSError as e:
        out.ewarn(
            f"Unable to resolve current config symlink layout ({corepkg_path}): {e}"
        )
        return False

    if not same_as_portage:
        return True

    if not os.path.isdir(portage_path):
        out.ewarn(
            f"Expected legacy compat target to be a directory, found: {portage_path}"
        )
        return False

    out.einfo(
        "Normalizing config layout: converting /etc/corepkg symlink to real directory"
    )

    removed_corepkg_link = False
    moved_portage_dir = False
    try:
        os.unlink(corepkg_path)
        removed_corepkg_link = True

        os.rename(portage_path, corepkg_path)
        moved_portage_dir = True

        # Keep legacy path working.
        os.symlink("corepkg", portage_path)
    except OSError as e:
        out.ewarn(f"Unable to normalize /etc/corepkg layout automatically: {e}")

        # Best-effort rollback.
        if moved_portage_dir and not os.path.lexists(portage_path):
            try:
                os.rename(corepkg_path, portage_path)
                moved_portage_dir = False
            except OSError:
                pass

        if removed_corepkg_link and not os.path.lexists(corepkg_path):
            try:
                os.symlink("portage", corepkg_path)
            except OSError:
                pass

        return False

    out.einfo("Config layout normalized: /etc/corepkg now owns config directory")
    return True


def main():
    out = corepkg.output.EOutput()
    _remove_self_referential_portage_link(out)
    return _normalize_corepkg_layout(out)
