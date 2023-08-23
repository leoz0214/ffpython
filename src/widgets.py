"""Custom widgets to use in the app, extended from Tkinter widgets."""
import tkinter as tk
from typing import Callable

from colours import BUTTON_COLOURS, LINE_COLOURS
from utils import inter


class Button(tk.Button):
    """Standard button widget for the app."""

    def __init__(
        self, master: tk.Widget, text: str, font: tuple = inter(15),
        width: int = 15, border: int = 0,
        bg: str = BUTTON_COLOURS["background"],
        activebg: str = BUTTON_COLOURS["activebackground"],
        command: Callable = lambda: None, cursor: str = "hand2",
        disabled_cursor: str = "X_cursor", **kwargs
    ) -> None:
        super().__init__(
            master, text=text, font=font, width=width, border=border,
            command=command, bg=bg, activebackground=activebg,
            **kwargs)
        self.normal_bg = bg
        self.normal_cursor = cursor
        self.disabled_cursor = disabled_cursor
        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
        self.update_cursor()
    
    def on_enter(self) -> None:
        """Hovering over the button."""
        self.config(bg=self["activebackground"])

    def on_exit(self) -> None:
        """No longer hovering over the button."""
        self.config(bg=self.normal_bg)
    
    def config(self, *args, **kwargs) -> None:
        """Config wrapper."""
        super().config(*args, **kwargs)
        self.update_cursor()
    
    def update_cursor(self) -> None:
        """Changes cursor depending on state."""
        cursor = (
            self.normal_cursor if self["state"] == "normal"
            else self.disabled_cursor)
        super().config(self, cursor=cursor)


class HorizontalLine(tk.Canvas):
    """
    Represents a horizontal line,
    which can be used as a separator, for example.
    """

    def __init__(
        self, master: tk.Widget, width: int, height: int = 1,
        colour: str = LINE_COLOURS["background"],
        active_colour: str = LINE_COLOURS["activebackground"]
    ) -> None:
        super().__init__(
            master, width=width, height=height, bg=colour)
        self.colour = colour
        self.active_colour = active_colour
        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    def on_enter(self) -> None:
        """Hovering over the line."""
        self.config(bg=self.active_colour)
    
    def on_exit(self) -> None:
        """No longer hovering over the line."""
        self.config(bg=self.colour)
