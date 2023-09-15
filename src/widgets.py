"""Custom widgets to use in the app, extended from Tkinter widgets."""
import tkinter as tk
from typing import Callable

from colours import (
    BUTTON_COLOURS, LINE_COLOURS, ENTRY_COLOURS, TEXTBOX_COLOURS,
    LISTBOX_COLOURS
)
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


class StringEntry(tk.Entry):
    """String entry convenience class."""

    def __init__(
        self, master: tk.Widget, font: tuple = inter(15),
        bg: str = ENTRY_COLOURS["background"],
        width: int = 32, max_length: int = 256, initial_value: str = "",
        **kwargs
    ) -> None:
        self.variable = tk.StringVar(value=initial_value)
        self.variable.trace("w", lambda *_: self.validate())
        self.max_length = max_length
        super().__init__(
            master, font=font, bg=bg, width=width, textvariable=self.variable,
            **kwargs)
    
    def validate(self) -> None:
        """Performs length validation on the string."""
        self.variable.set(self.variable.get()[:self.max_length])


class Textbox(tk.Frame):
    """Textbox convenience class, including support for scrollbars."""

    def __init__(
        self, master: tk.Widget, font: tuple = inter(11),
        bg: str = TEXTBOX_COLOURS["background"],
        width: int = 64, height: int = 16, max_length: int = 4096,
        vertical_scrollbar: bool = True, horizontal_scrollbar: bool = False,
        wrap: str = "word"
    ):
        super().__init__(master)
        self.max_length = max_length
        self.previous_text = ""
        self.textbox = tk.Text(
            self, font=font, bg=bg, width=width, height=height, wrap=wrap)
        self.textbox.grid(row=0, column=0)

        if vertical_scrollbar:
            self.vertical_scrollbar = tk.Scrollbar(
                self, orient="vertical", command=self.textbox.yview)
            self.textbox.config(yscrollcommand=self.vertical_scrollbar.set)
            self.vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        if horizontal_scrollbar:
            self.horizontal_scrollbar = tk.Scrollbar(
                self, orient="horizontal", command=self.textbox.xview)
            self.textbox.config(xscrollcommand=self.horizontal_scrollbar.set)
            self.horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        self.after(500, self.validate)

    @property
    def text(self) -> str:
        """Returns the current text."""
        # Slice off trailing new line.
        return self.textbox.get("1.0", "end")[:-1]

    @property
    def is_valid(self) -> bool:
        return len(self.text) <= self.max_length
    
    def validate(self) -> None:
        """Validates the current text input."""
        current_text = self.text
        if len(current_text) > self.max_length:
            # Force trim excess text to remain in length range.
            trimmed = current_text[:self.max_length]
            self.textbox.replace("1.0", "end", trimmed)
            self.previous_text = trimmed
        elif current_text != self.previous_text:
            # Updates text only when it has changed, saving
            # processing power.
            self.textbox.replace("1.0", "end", current_text)
            self.previous_text = current_text
        # Keep on validating at regular intervals.
        self.after(500, self.validate)


class Listbox(tk.Frame):
    """Listbox convenience wrapper, including scrollbar support."""

    def __init__(
        self, master: tk.Widget, font: tuple = inter(11),
        bg: str = LISTBOX_COLOURS["background"], width: int = 64,
        height: int = 16, vertical_scrollbar: bool = True,
        horizontal_scrollbar: bool = False
    ):
        super().__init__(master)
        self.listbox = tk.Listbox(
            self, font=font, bg=bg, width=width, height=height)
        self.listbox.grid(row=0, column=0)

        if vertical_scrollbar:
            self.vertical_scrollbar = tk.Scrollbar(
                self, orient="vertical", command=self.listbox.yview)
            self.listbox.config(yscrollcommand=self.vertical_scrollbar.set)
            self.vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        if horizontal_scrollbar:
            self.horizontal_scrollbar = tk.Scrollbar(
                self, orient="horizontal", command=self.listbox.xview)
            self.listbox.config(xscrollcommand=self.horizontal_scrollbar.set)
            self.horizontal_scrollbar.grid(row=1, column=0, sticky="ew") 

    def append(self, text: str) -> None:
        """Appends a value."""
        self.listbox.insert("end", text)
