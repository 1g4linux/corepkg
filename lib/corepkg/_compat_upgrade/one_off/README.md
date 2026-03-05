# One-Off Compat Upgrades

Drop single-use upgrade scripts in this directory with a numeric prefix, for example:

- `20260305_drop_eselect_vdb.py`

Each script must expose a `main()` function.

`corepkg._compat_upgrade.one_off_runner` executes these modules in lexical order and
creates a stamp file in:

- `${EROOT}/var/lib/corepkg/compat_upgrade/one_off/<script>.done`

Stamped scripts are skipped on future upgrades.
