"""
This is part of the Ego MSS Python's module.
Source: https://github.com/GavriloviciEduard/ego-mss
"""
import platform
from typing import Any

from mss.base import MSSBase
from mss.exception import ScreenShotError


def ego_mss(**kwargs: Any) -> MSSBase:
    """Factory returning a proper Ego MSS class instance.

    It detects the platform we are running on
    and chooses the most adapted mss_class to take
    screenshots.

    It then proxies its arguments to the class for
    instantiation.
    """
    # pylint: disable=import-outside-toplevel

    os_ = platform.system().lower()

    if os_ == "windows":
        from . import windows

        return windows.EgoMSS(**kwargs)

    raise ScreenShotError(f"System {os_!r} not (yet?) implemented.")
