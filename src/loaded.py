"""Main handler of the GUI whilst audio is playing."""
import tkinter as tk

import main
from colours import PROGRESS_BAR_REMAINING_COLOUR, PROGRESS_BAR_DONE_COLOURS
from utils import inter, format_seconds
from widgets import Button, HorizontalLine


PROGRESS_BAR_WIDTH = 500
PROGRESS_BAR_HEIGHT = 8


class LoadedFrame(tk.Frame):
    """(Main) GUI state for when audio has been loaded or is playing."""

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        audio = master.current
        self.name_label = tk.Label(
            self, font=inter(25, True), text=audio.name_display)
        self.file_path_label = tk.Label(
            self, font=inter(10), text=audio.file_path_display)
        
        self.separator = HorizontalLine(self, 750)
        
        self.play_progress_frame = PlayProgressFrame(self)
        
        self.open_file_button = Button(
            self, "Open File", font=inter(12), command=master.open)
        
        self.name_label.grid(row=0, column=0, sticky="w", padx=5, pady=(100, 2))
        self.file_path_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.separator.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.play_progress_frame.grid(
            row=3, column=0, columnspan=2, padx=5, pady=(25, 5))
        self.open_file_button.grid(
            row=4, column=1, sticky="e", padx=(25, 5), pady=10)


class PlayProgressFrame(tk.Frame):
    """
    Displays the playback progress,
    including the current time, progress bar and total time.
    """

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        self.current_time_label = tk.Label(
            self, font=inter(12), width=9, text=format_seconds(0))
        
        self.progress_bar = PlayProgressBar(self)
        self.progress_bar.display_progress(30 / master.master.current.duration)

        audio = master.master.current
        self.total_time_label = tk.Label(
            self, font=inter(12), width=9,
            text=format_seconds(audio.duration))
        
        self.current_time_label.grid(row=0, column=0)
        self.progress_bar.grid(row=0, column=1)
        self.total_time_label.grid(row=0, column=2)


class PlayProgressBar(tk.Canvas):
    """
    Holds the progress bar denoting the progress through the audio file.
    Will also allow the user to seek to a given time in audio.
    """

    def __init__(self, master: PlayProgressFrame) -> None:
        super().__init__(
            master, width=PROGRESS_BAR_WIDTH, height=PROGRESS_BAR_HEIGHT,
            bg=PROGRESS_BAR_REMAINING_COLOUR)
        self.progress_rect = None
    
    def display_progress(self, fraction: float) -> None:
        """Displays a given fraction of progress in the progress frame."""
        if self.progress_rect is not None:
            self.delete(self.progress_rect)
        fraction = min(fraction, 1)
        # Adding 1 to rectangle width/height
        # to not have any remnants of the undone progress.
        rect_width = PROGRESS_BAR_WIDTH * fraction + 1
        self.progress_rect = self.create_rectangle(
            0, 0, rect_width, PROGRESS_BAR_HEIGHT + 1,
            fill=PROGRESS_BAR_DONE_COLOURS["background"],
            outline=PROGRESS_BAR_DONE_COLOURS["background"],
            activefill=PROGRESS_BAR_DONE_COLOURS["activebackground"],
            activeoutline=PROGRESS_BAR_DONE_COLOURS["activebackground"])
