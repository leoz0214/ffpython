"""
Internal handling of audio, including loading and playing.
This app relies fully on FFmpeg software, so it expected that
ffmpeg is fully installed and added to PATH.
"""
import json
import pathlib
import subprocess

from utils import (
    MAX_AUDIO_NAME_DISPLAY_LENGTH, MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH,
    limit_length
)


class Audio:
    """
    Represents an audio object in the app, providing key information
    Such as file path, name and metadata including duration.
    """

    def __init__(self, file_path: str, duration: float) -> None:
        self.file_path = file_path
        self.file_path_display = limit_length(
            self.file_path, MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH)
        self.name = pathlib.Path(self.file_path).stem
        self.name_display = limit_length(
            self.name, MAX_AUDIO_NAME_DISPLAY_LENGTH)
        self.duration = duration


def load_audio(file_path: str) -> Audio:
    """Loads an audio file into the program."""
    # Command line ffprobe parts.
    commands = (
        "ffprobe", "-print_format", "json", 
        "-show_format", "-show_streams", file_path)
    # Run the command and load the JSON string.
    json_data = json.loads(
        subprocess.check_output(
            commands, creationflags=subprocess.CREATE_NO_WINDOW).decode())

    try:
        duration = float(json_data["format"]["duration"])
    except (KeyError, ValueError):
        raise ValueError("Invalid audio file - duration not found.")

    # Expect at least some audio in the file for it to be 'valid'.
    if not any(
        stream["codec_type"] == "audio" for stream in json_data["streams"]
    ):
        raise ValueError("Invalid file - no audio found.")
    
    return Audio(file_path, duration)
