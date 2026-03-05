py.install_sources(
    [
        'binpkg_compression.py',
        'binpkg_format.py',
        'binpkg_multi_instance.py',
        'default_locations.py',
        'one_off_runner.py',
        '__init__.py',
    ],
    subdir : 'corepkg/_compat_upgrade',
    pure : not native_extensions
)

py.install_sources(
    [
        'one_off/__init__.py',
        'one_off/20260305_drop_legacy_split_packages_vdb.py',
        'one_off/20260305_normalize_corepkg_config_layout.py',
        'one_off/20260305_prune_unowned_legacy_paths.py',
        'one_off/20260305_transition_portage_to_corepkg.py',
    ],
    subdir : 'corepkg/_compat_upgrade/one_off',
    pure : not native_extensions
)
