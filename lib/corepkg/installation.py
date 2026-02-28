# corepkg: Installation
# Copyright 2023 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from enum import Enum

TYPES = Enum(
    "InstallationType",
    [
        "SOURCE",  # Corepkg is not installed, but running from its source tree.
        "MODULE",  # Corepkg is installed solely as a Python module.
        "SYSTEM",  # Corepkg is fully installed to the system, possibly prefixed.
    ],
)

if "@INSTALL_TYPE@" == "MODULE":
    TYPE = TYPES.MODULE
elif "@INSTALL_TYPE@" == "SYSTEM":
    TYPE = TYPES.SYSTEM
else:
    TYPE = TYPES.SOURCE
