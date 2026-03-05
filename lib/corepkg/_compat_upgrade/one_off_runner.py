# Copyright 2026 1g4 Authors
# Distributed under the terms of the GNU General Public License v2

import importlib
import pkgutil

import corepkg
from corepkg import os
from corepkg.const import PRIVATE_PATH

STATE_DIR = "compat_upgrade/one_off"


def _state_root():
    return os.path.join(corepkg.settings["EROOT"], PRIVATE_PATH, STATE_DIR)


def _iter_migrations():
    pkg_name = "corepkg._compat_upgrade.one_off"
    pkg = importlib.import_module(pkg_name)
    for module_info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda x: x.name):
        if module_info.ispkg or not module_info.name[0].isdigit():
            continue
        module = importlib.import_module(f"{pkg_name}.{module_info.name}")
        if hasattr(module, "main"):
            yield module_info.name, module.main


def main():
    out = corepkg.output.EOutput()
    state_root = _state_root()
    try:
        os.makedirs(state_root, exist_ok=True)
    except OSError as e:
        out.ewarn(f"Unable to create one-off compat state directory: {state_root}: {e}")
        return

    for migration_name, migration_main in _iter_migrations():
        stamp = os.path.join(state_root, f"{migration_name}.done")
        if os.path.exists(stamp):
            continue

        out.einfo(f"Running one-off compat upgrade: {migration_name}")
        try:
            migration_main()
        except Exception as e:
            out.ewarn(f"One-off compat upgrade failed: {migration_name}: {e}")
            continue

        try:
            with open(stamp, "w") as f:
                f.write("done\n")
        except OSError as e:
            out.ewarn(f"Unable to write one-off compat stamp: {stamp}: {e}")


if __name__ == "__main__":
    main()
