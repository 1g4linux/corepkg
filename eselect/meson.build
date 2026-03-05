eselect_bins = [
    'eselect',
    'kernel-config',
    'profile-config',
    'rc-config'
]

install_data(
    eselect_bins,
    install_dir : get_option('bindir'),
    install_mode : 'rwxr-xr-x',
)

install_subdir(
    'libs',
    install_dir : datadir / 'eselect'
)

install_subdir(
    'modules',
    install_dir : datadir / 'eselect'
)
