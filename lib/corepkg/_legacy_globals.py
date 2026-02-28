# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import corepkg
from corepkg import os
from corepkg.const import CACHE_PATH, PROFILE_PATH


def _get_legacy_global(name):
    constructed = corepkg._legacy_globals_constructed
    if name in constructed:
        return getattr(corepkg, name)

    if name == "portdb":
        corepkg.portdb = corepkg.db[corepkg.root]["porttree"].dbapi
        constructed.add(name)
        return getattr(corepkg, name)

    if name in ("mtimedb", "mtimedbfile"):
        corepkg.mtimedbfile = os.path.join(
            corepkg.settings["EROOT"], CACHE_PATH, "mtimedb"
        )
        constructed.add("mtimedbfile")
        corepkg.mtimedb = corepkg.MtimeDB(corepkg.mtimedbfile)
        constructed.add("mtimedb")
        return getattr(corepkg, name)

    # Corepkg needs to ensure a sane umask for the files it creates.
    os.umask(0o22)

    kwargs = {}
    for k, envvar in (
        ("config_root", "PORTAGE_CONFIGROOT"),
        ("target_root", "ROOT"),
        ("sysroot", "SYSROOT"),
        ("eprefix", "EPREFIX"),
    ):
        kwargs[k] = os.environ.get(envvar)

    corepkg._initializing_globals = True
    corepkg.db = corepkg.create_trees(**kwargs)
    constructed.add("db")
    del corepkg._initializing_globals

    settings = corepkg.db[corepkg.db._target_eroot]["vartree"].settings

    corepkg.settings = settings
    constructed.add("settings")

    # Since corepkg.db now uses EROOT for keys instead of ROOT, we make
    # corepkg.root refer to EROOT such that it continues to work as a key.
    corepkg.root = corepkg.db._target_eroot
    constructed.add("root")

    # COMPATIBILITY
    # These attributes should not be used within
    # Corepkg under any circumstances.

    corepkg.archlist = settings.archlist()
    constructed.add("archlist")

    corepkg.features = settings.features
    constructed.add("features")

    corepkg.groups = settings.get("ACCEPT_KEYWORDS", "").split()
    constructed.add("groups")

    corepkg.pkglines = settings.packages
    constructed.add("pkglines")

    corepkg.selinux_enabled = settings.selinux_enabled()
    constructed.add("selinux_enabled")

    corepkg.thirdpartymirrors = settings.thirdpartymirrors()
    constructed.add("thirdpartymirrors")

    profiledir = os.path.join(settings["PORTAGE_CONFIGROOT"], PROFILE_PATH)
    if not os.path.isdir(profiledir):
        profiledir = None
    corepkg.profiledir = profiledir
    constructed.add("profiledir")

    return getattr(corepkg, name)
