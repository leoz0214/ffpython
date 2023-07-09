"""Main handler of the GUI whilst audio is playing."""
import tkinter as tk

import main
from colours import (
    PROGRESS_BAR_REMAINING_COLOUR, PROGRESS_BAR_DONE_COLOURS,
    PROGRESS_CIRCLE_COLOURS, BG)
from utils import inter, format_seconds
from widgets import Button, HorizontalLine


PROGRESS_BAR_WIDTH = 500
PROGRESS_CIRCLE_RADIUS = 6
PROGRESS_BAR_HEIGHT = 6


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
    Includes a circle indicating progress too.
    """

    def __init__(self, master: PlayProgressFrame) -> None:
        # Must provide padding for circle to fit.
        super().__init__(
            master, width=PROGRESS_BAR_WIDTH + PROGRESS_CIRCLE_RADIUS * 2,
            height=PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS * 2, bg=BG)
        # Main progress bar, accounting for circle padding.
        self.create_rectangle(
            PROGRESS_CIRCLE_RADIUS, PROGRESS_CIRCLE_RADIUS,
            PROGRESS_BAR_WIDTH + PROGRESS_CIRCLE_RADIUS,
            PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS,
            fill=PROGRESS_BAR_REMAINING_COLOUR,
            outline=PROGRESS_BAR_REMAINING_COLOUR)
        self.progress_rect = None
        self.progress_circle = None
        self.bind("<Motion>", self.movement)
        self.display_progress(0)
    
    def display_progress(self, fraction: float) -> None:
        """Displays a given fraction of progress in the progress frame."""
        if self.progress_rect is not None:
            self.delete(self.progress_rect)
            self.delete(self.progress_circle)
        fraction = min(fraction, 1)

        rect_width = PROGRESS_BAR_WIDTH * fraction
        self.progress_rect = self.create_rectangle(
            PROGRESS_CIRCLE_RADIUS, PROGRESS_CIRCLE_RADIUS,
            PROGRESS_CIRCLE_RADIUS + rect_width,
            PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS,
            fill=PROGRESS_BAR_DONE_COLOURS["background"],
            outline=PROGRESS_BAR_DONE_COLOURS["background"],
            activefill=PROGRESS_BAR_DONE_COLOURS["activebackground"],
            activeoutline=PROGRESS_BAR_DONE_COLOURS["activebackground"])

        self.circle_mid_x = (
            PROGRESS_BAR_WIDTH * fraction + PROGRESS_CIRCLE_RADIUS)
        self.circle_mid_y = (
            PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS * 2) / 2
        self.progress_circle = self.create_oval(
            self.circle_mid_x - PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_y - PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_x + PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_y + PROGRESS_CIRCLE_RADIUS,
            fill=PROGRESS_CIRCLE_COLOURS["background"],
            activefill=PROGRESS_CIRCLE_COLOURS["activebackground"],
            outline=PROGRESS_CIRCLE_COLOURS["outline"])
    
    def movement(self, event) -> None:
        """Handles mouse movement within this progress bar."""
        if self.progress_circle is None:
            return
        x = event.x - self.circle_mid_x
        y = event.y - self.circle_mid_y
        if x ** 2 + y ** 2 <= PROGRESS_CIRCLE_RADIUS ** 2:
            self.config(cursor="hand2")
        else:
            self.config(cursor="")
