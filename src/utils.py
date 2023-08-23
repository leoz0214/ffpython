"""Utilities for the program."""
import pathlib

import pyglet
from PIL import ImageTk


APP_FOLDER = pathlib.Path(__file__).parent.parent
IMAGES_FOLDER = APP_FOLDER / "images"
FONT_FOLDER = APP_FOLDER / "font"


# Load Inter font downloaded online.
pyglet.font.add_file(str(FONT_FOLDER / "Inter.ttf"))

# Maximum lengths to display in the GUI.
MAX_AUDIO_NAME_DISPLAY_LENGTH = 24
MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH = 64


def inter(size: int, bold: bool = False, italic: bool = False) -> tuple:
    """Creates a Inter font option."""
    font = ("Inter", size)
    if bold:
        font += ("bold",)
    if italic:
        font += ("italic",)
    return font


def limit_length(string: str, max_length: int) -> str:
    """
    Reduces a string's display length as required, 
    based on the maximum display length.
    """
    if len(string) <= max_length:
        # No length issue.
        return string
    # Must shorten: first part .... last part
    left = string[:max_length//2 - 2]
    right = string[-max_length//2 + 2:]
    return f"{left}....{right}"


def format_seconds(seconds: float) -> str:
    """
    Converts seconds to either HH:MM:SS or MM:SS,
    whichever one is appropriate.
    """
    seconds = int(seconds)
    hours = str(seconds // 3600).zfill(2)
    minutes = str(seconds // 60 % 60).zfill(2)
    seconds = str(seconds % 60).zfill(2)
    if hours != "00":
        return f"{hours}:{minutes}:{seconds}"
    return f"{minutes}:{seconds}"


def load_image(image_name: str) -> ImageTk.PhotoImage:
    """Loads an image from a given file name, ready to be displayed."""
    image_file_path = IMAGES_FOLDER / image_name
    return ImageTk.PhotoImage(file=image_file_path)


def bool_to_state(expression: bool) -> str:
    """Returns 'normal' if True, else 'disabled'."""
    return "normal" if expression else "disabled"
