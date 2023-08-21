"""
Internal handling of audio, including loading and playing.
This app relies fully on FFmpeg software, so it expected that
ffmpeg is fully installed and added to PATH.
"""
import json
import pathlib
import subprocess
import time
from timeit import default_timer as timer
from typing import Callable, Any

from utils import (
    MAX_AUDIO_NAME_DISPLAY_LENGTH, MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH,
    limit_length
)


class Audio:
    """
    Represents an audio object in the app, providing key information
    Such as file path, name and metadata including duration.

    Also allows the audio to be played, paused, stopped, sought etc.
    """

    def __init__(self, file_path: str, duration: float) -> None:
        self.file_path = file_path
        self.file_path_display = limit_length(
            self.file_path, MAX_AUDIO_FILE_PATH_DISPLAY_LENGTH)
        self.name = pathlib.Path(self.file_path).stem
        self.name_display = limit_length(
            self.name, MAX_AUDIO_NAME_DISPLAY_LENGTH)
        self.duration = duration
        self.reset()

    def reset(self) -> None:
        """Resets all playback attributes."""
        self.start_time = None
        # Flag to indicate if currently starting/stopping process.
        self.handling_process = False
        self.pause_start_time = None
        self.paused_time = 0
        self.paused = False
        self.process = None
    
    def play(self, seek: float = 0) -> None:
        """Begins or resumes audio playback."""
        command = (
            "ffplay", self.file_path, "-nodisp",
            "-autoexit", "-vn", "-ss", str(seek))
        # Start command.
        self.handling_process = True
        self.process = subprocess.Popen(
            command, creationflags=subprocess.CREATE_NO_WINDOW)
        # Gives some time for audio to start. Due to subprocess.
        # Does not need to be perfect, just reasonable.
        time.sleep(0.5)
        if self.start_time is None:
            self.start_time = timer()
        self.handling_process = False
    
    def terminate(self) -> None:
        """Terminates the process."""
        self.handling_process = True
        self.process.terminate()
        self.handling_process = False
        self.process = None
    
    @staticmethod
    def wait(method: Callable) -> Callable:
        """Decorator to wait for process creation/termination."""
        def wrapper(self: "Audio", *args, **kwargs) -> Any:
            # Wait until process handling done.
            while self.handling_process:
                time.sleep(0.01)
            return method(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def handle_seek(method: Callable) -> Callable:
        """Decorator for common tasks while seeking."""
        def wrapper(self: "Audio", *args, **kwargs) -> Any:
            if self.paused:
                self.resume()
            if self.process is not None:
                self.handling_process = True
                self.terminate()
                self.handling_process = False
            return method(self, *args, **kwargs)
        return wrapper
    
    @wait
    def pause(self) -> None:
        """Pauses audio playback."""
        self.pause_start_time = timer()
        self.paused = True
        if self.process is not None:
            self.terminate()
    
    @wait
    def resume(self) -> None:
        """Prepares to resume audio playback."""
        self.paused_time += timer() - self.pause_start_time
        self.paused = False
    
    @wait
    def stop(self) -> None:
        """Stops audio playback."""
        if self.process is not None:
            self.terminate()
        self.reset()
    
    @wait
    @handle_seek
    def seek_back(self, seconds: int) -> None:
        """Seeks back a given number of seconds, ready to be played."""
        # Easiest way to seek backwards is to increase the start time.
        # Also ensure cannot seek to negative numbers (Required: t >= 0).
        if self.start_time is None:
            # Was reset upon completion, now no longer.
            self.start_time = timer() - self.duration
            self.start_time += min(self.duration, seconds)
        else:
            self.start_time += min(self.current_seconds, seconds)

    @wait
    @handle_seek
    def seek_forward(self, seconds: int) -> None:
        """Seeks forward a given number of seconds, ready to be played."""
        # Easiest way to seek forwards is to decrease the start time.
        # Also ensure cannot seek beyond duration (Required: t <= duration).
        remaining_seconds = self.duration - self.current_seconds
        self.start_time -= min(remaining_seconds, seconds)
    
    @wait
    @handle_seek
    def seek_to(self, seconds: float) -> None:
        """Seeks to a given timestamp in the audio, ready to be played."""
        if self.start_time is None:
            self.start_time = timer() - seconds
        else:
            self.start_time += self.current_seconds - seconds
    
    @property
    def current_seconds(self) -> float:
        """Current time in the audio playback."""
        if self.start_time is None:
            return 0
        return timer() - self.start_time - self.paused_time
    
    @property
    def is_playing(self) -> bool:
        return self.process is not None and self.process.poll() is None


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
