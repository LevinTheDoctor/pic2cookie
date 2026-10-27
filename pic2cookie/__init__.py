"""Pic2Cookie: turn a picture into a 3D-printable cookie cutter."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pic2cookie")
except PackageNotFoundError:
    __version__ = "0.0.0"
