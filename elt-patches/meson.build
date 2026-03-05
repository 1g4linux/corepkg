eltpatch_conf = configuration_data({
    'ELT_patchdir' : eprefix + prefixdir + '/share/elt-patches/patches',
    'ELT_libdir' : 'lib',
    'ELT_corefuncs' : eprefix + prefixdir + '/lib/corepkg/functions/functions.sh',
})

eltpatch = configure_file(
    input : 'eltpatch.in',
    output : 'eltpatch',
    configuration : eltpatch_conf
)

install_data(
    [eltpatch],
    install_dir : get_option('bindir'),
    install_mode : 'rwxr-xr-x',
)

install_subdir(
    'patches',
    install_dir : datadir / 'elt-patches'
)
