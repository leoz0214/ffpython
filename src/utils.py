"""Utilities for the program."""
import pathlib
import sys
from tkinter import filedialog
from tkinter import messagebox

import pyglet
from PIL import ImageTk


if hasattr(sys, "_MEIPASS"):
    APP_FOLDER = pathlib.Path(sys._MEIPASS)
else:
    APP_FOLDER = pathlib.Path(__file__).parent.parent
IMAGES_FOLDER = APP_FOLDER / "images"
FONT_FOLDER = APP_FOLDER / "font"
BINARY_FOLDER = APP_FOLDER / "bin"


# Load Inter font downloaded online.
pyglet.font.add_file(str(FONT_FOLDER / "Inter.ttf"))

# Maximum lengths to display in the GUI.
MAX_AUDIO_NAME_DISPLAY_LENGTH = 24
MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH = 64
# Max playlist name display length in the table.
MAX_PLAYLIST_NAME_DISPLAY_LENGTH = 48
# A list of permitted audio extensions.
ALLOWED_EXTENSIONS_DICT = {
    ".mp3": "MP3",
    ".ogg": "OGG",
    ".oga": "OGG",
    ".m4a": "M4A",
    ".wav": "WAV",
    ".wma": "WMA",
    ".aac": "AAC",
    ".flac": "FLAC",
    ".opus": "OPUS",
    ".mp4": "MP4 (Audio only)"
}
ALLOWED_EXTENSIONS = tuple(ALLOWED_EXTENSIONS_DICT)


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
    # Only display hours if hours > 0.
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


def open_audio_file(file_path: str | None = None) -> str | None:
    """
    Prompts the user for an audio,
    returns the path or None if invalid or cancelled.

    Can also take a file path but performs validation before
    accepting it into the program. This is useful in case of
    starting the script from the terminal with an initial file path.
    """
    if file_path is None:
        file_path = filedialog.askopenfilename(
            filetypes=(
                *(("Audio", extension) for extension in ALLOWED_EXTENSIONS),
                *(
                    (name, extension)
                    for extension, name in ALLOWED_EXTENSIONS_DICT.items())))
    if not file_path:
        # Cancelled.
        return None
    if not file_path.lower().endswith(ALLOWED_EXTENSIONS):
        # Bypassed file extension filter, not allowed.
        messagebox.showerror(
            "Error",
                "Invalid file provided - "
                "the file extension is not supported.")
        return None
    return file_path
