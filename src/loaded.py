"""Main handler of the GUI whilst audio is playing."""
import tkinter as tk

import main
from utils import inter, format_seconds
from widgets import Button


class LoadedFrame(tk.Frame):
    """(Main) GUI state for when audio has been loaded or is playing."""

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        audio = master.current
        self.name_label = tk.Label(
            self, font=inter(25, True), text=audio.name_display)
        self.file_path_label = tk.Label(
            self, font=inter(10), text=audio.file_path_display)
        
        self.play_progress_frame = PlayProgressFrame(self)
        
        self.open_file_button = Button(
            self, "Open File", font=inter(12), command=master.open)
        
        self.name_label.grid(row=0, column=0, sticky="w", padx=5, pady=(100, 2))
        self.file_path_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.play_progress_frame.grid(
            row=2, column=0, columnspan=2, padx=5, pady=2)
        self.open_file_button.grid(
            row=3, column=1, sticky="e", padx=(25, 5), pady=10)


class PlayProgressFrame(tk.Frame):
    """
    Displays the playback progress,
    including the current time, progress bar and total time.
    """

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        self.current_time_label = tk.Label(
            self, font=inter(12), width=10, text=format_seconds(0))

        audio = master.master.current
        self.total_time_label = tk.Label(
            self, font=inter(12), width=10,
            text=format_seconds(audio.duration))
        
        self.current_time_label.grid(row=0, column=0)
        self.total_time_label.grid(row=0, column=2)
