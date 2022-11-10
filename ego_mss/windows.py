"""
This is part of the Ego MSS Python's module.
Source: https://github.com/GavriloviciEduard/ego-mss
"""
import ctypes
import threading
from ctypes import wintypes
from typing import Any, Dict, Optional

from mss.exception import ScreenShotError
from mss.screenshot import ScreenShot
from mss.tools import to_png
from mss.windows import MSS

__all__ = ("EgoMSS",)

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
SW_RESTORE = 9
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 32
WS_EX_TOOLWINDOW = 128
LWA_ALPHA = 0x00000002


class EgoMSS(MSS):
    """Ego MSS implementation for Microsoft Windows."""

    def __init__(self, window_title: str, silent: bool) -> None:
        self.hwnd: Optional[int] = None
        self.window_style: Optional[Any] = None
        self.window_title = window_title
        self.silent = silent
        self.user32 = ctypes.WinDLL("user32")
        self._set_hwnd_from_title(window_title)
        if not self.hwnd:
            raise ScreenShotError("Window not found!")

        super().__init__()

    def __del__(self) -> None:
        self._show_window()

    # pylint: disable=arguments-differ
    def grab(self) -> ScreenShot:
        """Retrieve screen pixels for a given window.

        Returns:
            ScreenShot: Bytearray containing pixel data.
        """

        self._hide_window()
        return super().grab(self._get_window_dimensions())

    # pylint: disable=arguments-differ
    def save(self, output: str) -> str:
        """Grab a screen shot and save it to a file.

        Args:
            output (str): Name of file to be saved.

        Returns:
            str: Name of saved file.
        """

        sct = self.grab()
        to_png(sct.rgb, sct.size, level=self.compression_level, output=f"{output}.png")
        return output

    # pylint: disable=arguments-differ
    def shot(self) -> str:
        """Helper to save the screen shot of window with file name
            defaulting to window title.

        Returns:
            str:  Name of saved file.
        """

        return self.save(self.window_title)

    def _get_srcdc(self) -> int:
        """Get thread-safe device context for hwnd.

        Returns:
            int: Device context for hwnd.
        """

        cur_thread, main_thread = threading.current_thread(), threading.main_thread()
        cur_srcdc = MSS._srcdc_dict.get(cur_thread) or MSS._srcdc_dict.get(main_thread)
        if cur_srcdc:
            srcdc = cur_srcdc
        else:
            srcdc = self.user32.GetWindowDC(self.hwnd)
            MSS._srcdc_dict[cur_thread] = srcdc
        return srcdc

    def _get_window_dimensions(self) -> Dict[str, int]:
        """Get width and height for window.

        Returns:
            dict[str, int]: Width and height
        """

        rect = wintypes.RECT()
        self.user32.GetWindowRect(self.hwnd, ctypes.pointer(rect))
        return {
            "left": 0,
            "top": 0,
            "width": int(rect.right) - int(rect.left),
            "height": int(rect.bottom) - int(rect.top),
        }

    def _set_hwnd_from_title(self, window_title: str) -> None:
        """Save handle as class member from a given window title.

        Args:
            window_title (str): Given window title.
        """

        def _callback(hwnd: int, _: int) -> bool:
            length = self.user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(length)
            self.user32.GetWindowTextW(hwnd, buffer, length)
            if (
                not self.user32.IsIconic(hwnd)
                and self.user32.IsWindowVisible(hwnd)
                and buffer.value
                and window_title.lower() in buffer.value.lower()
            ):
                self.hwnd = hwnd
                return False
            return True

        self.user32.EnumWindows(WNDENUMPROC(_callback), 0)

    def _show_window(self) -> None:
        """Show window by restoring its initial style."""

        if self.silent:
            self.user32.SetWindowLongA(
                self.hwnd,
                GWL_EXSTYLE,
                self.window_style,
            )

    def _hide_window(self) -> None:
        """Hide everything related to window while taking a screenshot."""

        if self.silent:
            self.window_style = self.user32.GetWindowLongA(
                self.hwnd,
                GWL_EXSTYLE,
            )
            self.user32.SetWindowLongA(
                self.hwnd,
                GWL_EXSTYLE,
                int(self.window_style) | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
            )
            self.user32.SetLayeredWindowAttributes(
                self.hwnd,
                wintypes.COLORREF(0),
                0,
                LWA_ALPHA,
            )
