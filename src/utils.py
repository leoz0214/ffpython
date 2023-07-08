"""Utilities for the program."""
import pathlib

import pyglet


# Load Inter font downloaded online.
FONT_FOLDER = pathlib.Path(__file__).parent.parent / "font"
pyglet.font.add_file(str(FONT_FOLDER / "Inter.ttf"))


def inter(size: int, bold: bool = False, italic: bool = False) -> tuple:
    """Creates a Inter font option."""
    font = ("Inter", size)
    if bold:
        font += ("bold",)
    if italic:
        font += ("italic",)
    return font
