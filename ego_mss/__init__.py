"""
A module for taking screenshots of applications searched by their names,
based on tried-and-true Python MSS.
"""
from mss.exception import ScreenShotError

from .factory import ego_mss

__all__ = ("ScreenShotError", "ego_mss")
