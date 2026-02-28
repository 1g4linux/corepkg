# Copyright 1998-2023 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import signal
from corepkg import _encodings, _unicode_decode, unsupported_eapi_message
from corepkg.localization import _


class CorepkgException(Exception):
    """General superclass for corepkg exceptions"""

    def __init__(self, value):
        self.value = value[:]

    def __str__(self):
        if isinstance(self.value, str):
            return self.value
        return repr(self.value)


class CorepkgKeyError(KeyError, CorepkgException):
    __doc__ = KeyError.__doc__

    def __init__(self, value):
        KeyError.__init__(self, value)
        CorepkgException.__init__(self, value)


class CorruptionError(CorepkgException):
    """Corruption indication"""


class CorruptionKeyError(CorruptionError, CorepkgKeyError):
    """KeyError raised when corruption is detected (cause should be accesssible as __cause__)"""


class InvalidDependString(CorepkgException):
    """An invalid depend string has been encountered"""

    def __init__(self, value, errors=None):
        CorepkgException.__init__(self, value)
        self.errors = errors


class InvalidVersionString(CorepkgException):
    """An invalid version string has been encountered"""


class SecurityViolation(CorepkgException):
    """An incorrect formatting was passed instead of the expected one"""


class IncorrectParameter(CorepkgException):
    """A parameter of the wrong type was passed"""


class MissingParameter(CorepkgException):
    """A parameter is required for the action requested but was not passed"""


class ParseError(CorepkgException):
    """An error was generated while attempting to parse the request"""


class InvalidData(CorepkgException):
    """An incorrect formatting was passed instead of the expected one"""

    def __init__(self, value, category=None):
        CorepkgException.__init__(self, value)
        self.category = category


class InvalidDataType(CorepkgException):
    """An incorrect type was passed instead of the expected one"""


class InvalidLocation(CorepkgException):
    """Data was not found when it was expected to exist or was specified incorrectly"""


class FileNotFound(InvalidLocation):
    """A file was not found when it was expected to exist"""


class DirectoryNotFound(InvalidLocation):
    """A directory was not found when it was expected to exist"""


class IsADirectory(CorepkgException):
    """A directory was found when it was expected to be a file"""

    from errno import EISDIR as errno


class OperationNotPermitted(CorepkgException):
    """An operation was not permitted operating system"""

    from errno import EPERM as errno


class OperationNotSupported(CorepkgException):
    """Operation not supported"""

    from errno import EOPNOTSUPP as errno


class PermissionDenied(CorepkgException):
    """Permission denied"""

    from errno import EACCES as errno


class TryAgain(CorepkgException):
    """Try again"""

    from errno import EAGAIN as errno


class TimeoutException(CorepkgException):
    """Operation timed out"""

    # NOTE: ETIME is undefined on FreeBSD (bug #336875)
    # from errno import ETIME as errno


class AlarmSignal(TimeoutException):
    def __init__(self, value, signum=None, frame=None):
        TimeoutException.__init__(self, value)
        self.signum = signum
        self.frame = frame

    @classmethod
    def register(cls, time):
        signal.signal(signal.SIGALRM, cls._signal_handler)
        signal.alarm(time)

    @classmethod
    def unregister(cls):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    @classmethod
    def _signal_handler(cls, signum, frame):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        raise AlarmSignal("alarm signal", signum=signum, frame=frame)


class ReadOnlyFileSystem(CorepkgException):
    """Read-only file system"""

    from errno import EROFS as errno


class CommandNotFound(CorepkgException):
    """A required binary was not available or executable"""


class AmbiguousPackageName(ValueError, CorepkgException):
    """Raised by corepkg.cpv_expand() when the package name is ambiguous due
    to the existence of multiple matches in different categories. This inherits
    from ValueError, for backward compatibility with calling code that already
    handles ValueError."""

    def __init__(self, *args, **kwargs):
        self.args = args
        super().__init__(*args, **kwargs)

    def __str__(self):
        return ValueError.__str__(self)


class CorepkgPackageException(CorepkgException):
    """Malformed or missing package data"""


class PackageNotFound(CorepkgPackageException):
    """Missing Ebuild or Binary"""


class PackageSetNotFound(CorepkgPackageException):
    """Missing package set"""


class InvalidPackageName(CorepkgPackageException):
    """Malformed package name"""


class InvalidBinaryPackageFormat(CorepkgPackageException):
    """Invalid Binary Package Format"""


class InvalidCompressionMethod(CorepkgPackageException):
    """Invalid or unsupported compression method"""


class CompressorNotFound(CorepkgPackageException):
    """A required compressor binary was not available or executable"""


class CompressorOperationFailed(CorepkgPackageException):
    """An error occurred during external operation"""


class SignedPackage(CorepkgPackageException):
    """Unable to update a signed package"""


class InvalidAtom(CorepkgPackageException):
    """Malformed atom spec"""

    def __init__(self, value, category=None):
        CorepkgPackageException.__init__(self, value)
        self.category = category


class UnsupportedAPIException(CorepkgPackageException):
    """Unsupported API"""

    def __init__(self, cpv, eapi):
        self.cpv, self.eapi = cpv, eapi

    def __str__(self):
        msg = _(
            f"Unable to do any operations on '{self.cpv}': "
            f"{unsupported_eapi_message(self.eapi)}"
        )
        return _unicode_decode(msg, encoding=_encodings["content"], errors="replace")


class SignatureException(CorepkgException):
    """Signature was not present in the checked file"""


class DigestException(SignatureException):
    """A problem exists in the digest"""


class GPGException(SignatureException):
    """GnuPG operation failed"""


class MissingSignature(SignatureException):
    """Signature was not present in the checked file"""


class InvalidSignature(SignatureException):
    """Signature was checked and was not a valid, current, nor trusted signature"""


class UntrustedSignature(SignatureException):
    """Signature was not certified to the desired security level"""
