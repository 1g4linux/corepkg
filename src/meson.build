# We create symlinks to the native extensions in the source tree for the tests
# and for development. Meson does not allow you to build in-place and Python
# cannot create a single namespace from two identically-named paths.

whirlpool_ext = py.extension_module(
    '_whirlpool',
    'corepkg_util__whirlpool.c',
    dependencies : py.dependency(),
    subdir : 'corepkg' / 'util',
    install : true
)

run_command(
    [
        'ln', '-srnf',
        whirlpool_ext.full_path(),
        meson.project_source_root() / 'lib' / 'corepkg' / 'util/'
    ],
    capture : false,
    check : true
)
