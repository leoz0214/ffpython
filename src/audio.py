"""
Internal handling of audio, including loading and playing.
This app relies fully on FFmpeg software, so it expected that
ffmpeg is fully installed and added to PATH.
"""

class Audio:
    """
    Represents an audio object in the app, providing key information
    Such as file path, name and metadata including duration.
    """
    pass


def load_audio(file_path: str) -> Audio:
    """Loads an audio file into the program."""
