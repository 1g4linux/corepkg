# validators.py Corepkg File Loader Code
# Copyright 2007-2020 Gentoo Authors

from corepkg.dep import isvalidatom

ValidAtomValidator = isvalidatom


def PackagesFileValidator(atom):
    """This function mutates atoms that begin with - or *
    It then checks to see if that atom is valid, and if
    so returns True, else it returns False.

    Args:
        atom: a string representing an atom such as sys-apps/corepkg-2.1
    """
    if atom.startswith("*") or atom.startswith("-"):
        atom = atom[1:]
    if not isvalidatom(atom):
        return False
    return True
