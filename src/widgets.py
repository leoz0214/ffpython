"""Custom widgets to use in the app, extended from Tkinter widgets."""
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable, Iterable, Any

from colours import (
    BUTTON_COLOURS, LINE_COLOURS, ENTRY_COLOURS, TEXTBOX_COLOURS,
    LISTBOX_COLOURS, RADIOBUTTON_COLOURS, CHECKBUTTON_COLOURS, TABLE_COLOURS,
    FG
)
from utils import inter


# Table Column dataclass for the Table widget.
@dataclass
class TableColumn:
    id: str
    heading: str
    width: int = 250
    anchor: str = "center"
    command: Callable = lambda: None


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
            command=command, bg=bg, activebackground=activebg, **kwargs)
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
        activebg: str = ENTRY_COLOURS["activebackground"],
        width: int = 32, max_length: int = 256, initial_value: str = "",
        **kwargs
    ) -> None:
        self.variable = tk.StringVar(value=initial_value)
        self.variable.trace("w", lambda *_: self.validate())
        self.max_length = max_length
        self.normal_bg = bg
        self.active_bg = activebg
        super().__init__(
            master, font=font, bg=bg, width=width, textvariable=self.variable,
            disabledbackground=bg, **kwargs)
        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    @property
    def value(self) -> str:
        return self.variable.get()
    
    def validate(self) -> None:
        """Performs length validation on the string."""
        self.variable.set(self.variable.get()[:self.max_length])
    
    def on_enter(self) -> None:
        """Hovering over the entry."""
        self.config(bg=self.active_bg, disabledbackground=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the entry."""
        self.config(bg=self.normal_bg, disabledbackground=self.normal_bg)


class Textbox(tk.Frame):
    """Textbox convenience class, including support for scrollbars."""

    def __init__(
        self, master: tk.Widget, font: tuple = inter(11),
        bg: str = TEXTBOX_COLOURS["background"],
        activebg: str = TEXTBOX_COLOURS["activebackground"],
        width: int = 64, height: int = 16, max_length: int = 4096,
        vertical_scrollbar: bool = True, horizontal_scrollbar: bool = False,
        wrap: str = "word"
    ):
        super().__init__(master)
        self.max_length = max_length
        self.previous_text = ""
        self.normal_bg = bg
        self.active_bg = activebg
        self.textbox = tk.Text(
            self, font=font, bg=bg, width=width, height=height, wrap=wrap,)
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
        self.textbox.bind("<Enter>", lambda *_: self.on_enter())
        self.textbox.bind("<Leave>", lambda *_: self.on_exit())

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

    def on_enter(self) -> None:
        """Hovering over the textbox."""
        self.textbox.config(bg=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the textbox."""
        self.textbox.config(bg=self.normal_bg)


class Listbox(tk.Frame):
    """Listbox convenience wrapper, including scrollbar support."""

    def __init__(
        self, master: tk.Widget, font: tuple = inter(11),
        bg: str = LISTBOX_COLOURS["background"],
        activebg: str = LISTBOX_COLOURS["activebackground"],
        width: int = 64, height: int = 16,
        vertical_scrollbar: bool = True, horizontal_scrollbar: bool = False
    ):
        self.normal_bg = bg
        self.active_bg = activebg
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
    
        self.listbox.bind("<Enter>", lambda *_: self.on_enter())
        self.listbox.bind("<Leave>", lambda *_: self.on_exit())
    
    @property
    def current_index(self) -> int | None:
        """Currently selected index."""
        # Returns first selected index or None otherwise.
        return (self.listbox.curselection() or (None,))[0]
    
    @property
    def size(self) -> int:
        """Number of items in the listbox."""
        return self.listbox.size()

    def append(self, text: str) -> None:
        """Appends a value."""
        self.listbox.insert("end", text)

    def extend(self, iterable: Iterable[str]) -> None:
        """Adds multiple values."""
        self.listbox.insert("end", *iterable)
    
    def pop(self, index: int) -> None:
        """Removes the element at the given index."""
        self.listbox.delete(index)
    
    def swap(
        self, index1: int, index2: int, keep_select: bool = True
    ) -> None:
        """Swaps 2 values at given indexes."""
        index1_text = self.listbox.get(index1)
        index2_text = self.listbox.get(index2)
        self.listbox.delete(index1)
        self.listbox.insert(index1, index2_text)
        self.listbox.delete(index2)
        self.listbox.insert(index2, index1_text)
        if keep_select:
            self.listbox.select_set(index2)

    def on_enter(self) -> None:
        """Hovering over the listbox."""
        self.listbox.config(bg=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the listbox."""
        self.listbox.config(bg=self.normal_bg)


class Radiobutton(tk.Radiobutton):
    """Convenient radiobutton wrapper."""

    def __init__(
        self, master: tk.Widget, text: str, variable: tk.Variable, value: Any,
        font: tuple = inter(12), bg: str = RADIOBUTTON_COLOURS["background"],
        activebg: str = RADIOBUTTON_COLOURS["activebackground"],
        cursor: str = "hand2"
    ):
        self.normal_bg = bg
        self.active_bg = activebg
        super().__init__(
            master, text=text, variable=variable, value=value,
            font=font, selectcolor=bg, cursor=cursor)
        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    def on_enter(self) -> None:
        """Hovering over the radiobutton."""
        self.config(selectcolor=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the radiobutton."""
        self.config(selectcolor=self.normal_bg)


class Checkbutton(tk.Checkbutton):
    """Convenient checkbutton wrapper."""

    def __init__(
        self, master: tk.Widget, text: str, variable: tk.BooleanVar,
        font: tuple = inter(12), bg: str = CHECKBUTTON_COLOURS["background"],
        activebg: str = CHECKBUTTON_COLOURS["activebackground"],
        cursor: str = "hand2", **kwargs
    ):
        self.normal_bg = bg
        self.active_bg = activebg
        super().__init__(
            master, text=text, variable=variable,
            font=font, selectcolor=bg, cursor=cursor, **kwargs)
        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    def on_enter(self) -> None:
        """Hovering over the checkbutton."""
        self.config(selectcolor=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the checkbutton."""
        self.config(selectcolor=self.normal_bg)


class Table(tk.Frame):
    """Simulates a table using a treeview, along with a scrollbar."""

    def __init__(
        self, master: tk.Widget, columns: Iterable[TableColumn],
        heading_font: tuple = inter(15), row_font: tuple = inter(11),
        bg: str = TABLE_COLOURS["background"],
        active_bg: str = TABLE_COLOURS["activebackground"],
        height: int = 16, vertical_scrollbar: bool = True
    ) -> None:
        super().__init__(master)
        self.normal_bg = bg
        self.active_bg = active_bg
        self.treeview = ttk.Treeview(
            self, columns=[column.id for column in columns],
            height=height, show="headings")
        # Sets the table font and background.
        style = ttk.Style()
        # Required for Treeview colour.
        style.theme_use("clam")
        style.configure(
            "Treeview", background=bg, fieldbackground=bg,
            foreground=FG, font=row_font)
        style.configure(
            "Treeview.Heading", background=bg, fieldbackground=bg,
            foreground=FG, font=heading_font)
        style.map(
            "Treeview.Heading", background=(
                ("pressed", "!focus", bg),
                ("active", active_bg)
            ))
        # Configures the columns and adds the headings.
        for column in columns:
            self.treeview.column(
                column.id, width=column.width, anchor=column.anchor)
            self.treeview.heading(
                column.id, text=column.heading, command=column.command)
        
        if vertical_scrollbar:
            self.scrollbar = tk.Scrollbar(
                self, command=self.treeview.yview, orient="vertical")
            self.treeview.config(yscrollcommand=self.scrollbar.set)
            self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.treeview.grid(row=0, column=0)

        self.treeview.bind("<Enter>", lambda *_: self.on_enter())
        self.treeview.bind("<Leave>", lambda *_: self.on_exit())
    
    def on_enter(self) -> None:
        """Hovering over the table."""
        style = ttk.Style()
        for name in ("Treeview", "Treeview.Heading"):
            style.configure(
                name, background=self.active_bg, fieldbackground=self.active_bg)
    
    def on_exit(self) -> None:
        """No longer hovering over the table."""
        style = ttk.Style()
        for name in ("Treeview", "Treeview.Heading"):
            style.configure(
                name, background=self.normal_bg,
                fieldbackground=self.normal_bg)
    
    def append(self, values: tuple) -> None:
        """Appends a record to the table."""
        self.treeview.insert("", "end", values=values)
    
    def extend(self, records: Iterable[tuple]) -> None:
        """Adds multiple records to the table."""
        for record in records:
            self.append(record)
    
    def clear(self) -> None:
        """Removes all records from the table."""
        self.treeview.delete(*self.treeview.get_children())

    def get(self) -> tuple[str]:
        """
        Returns the currently selected record.
        Warning: all original values are now strings.
        """
        item = self.treeview.selection()[0]
        return self.treeview.item(item, "value")
