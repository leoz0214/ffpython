"""Main handler of the GUI whilst audio is playing."""
import tkinter as tk
from timeit import default_timer as timer

import main
from colours import (
    PROGRESS_BAR_REMAINING_COLOUR, PROGRESS_BAR_DONE_COLOURS,
    PROGRESS_CIRCLE_COLOURS, BG)
from utils import inter, format_seconds, load_image
from widgets import Button, HorizontalLine


PROGRESS_BAR_WIDTH = 500
PROGRESS_CIRCLE_RADIUS = 6
PROGRESS_BAR_HEIGHT = 6
STATE_CHANGE_REFRESH_RATE = 0.1


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
        self.play_controls_frame = PlayControlsFrame(self)

        self.separator2 = HorizontalLine(self, 750)
        
        self.open_file_button = Button(
            self, "Open File", font=inter(12), command=master.open)
        self.stop_button = Button(
            self, "Stop Playback", font=inter(12), command=master.stop)
        
        self.name_label.grid(row=0, column=0, sticky="w", padx=5, pady=(100, 2))
        self.file_path_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.separator.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.play_progress_frame.grid(
            row=3, column=0, columnspan=2, padx=5, pady=(25, 5))
        self.play_controls_frame.grid(
            row=4, column=0, columnspan=2, padx=5, pady=(5, 25))
        self.separator2.grid(
            row=5, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.open_file_button.grid(
            row=6, column=1, sticky="e", padx=(25, 5), pady=5)
        self.stop_button.grid(
            row=7, column=1, sticky="e", padx=(25, 5), pady=5)
    
    def update_progress(self, current_seconds: float) -> None:
        """
        Updates the progress of the playback
        based on the current time in the audio file.
        """
        duration = self.master.current.duration
        self.play_progress_frame.current_time_label.config(
            text=format_seconds(min(duration, current_seconds)))
        progress = current_seconds / duration
        self.play_progress_frame.progress_bar.display_progress(progress)


class PlayProgressFrame(tk.Frame):
    """
    Displays the playback progress,
    including the current time, progress bar and total time.
    """

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        audio = master.master.current
        # Either HH:MM:SS or MM:SS, select a suitable width based on that.
        width = 5 if audio.duration < 3600 else 8

        self.current_time_label = tk.Label(
            self, font=inter(12), width=width,
            text=format_seconds(0), anchor="w")
        
        self.progress_bar = PlayProgressBar(self)

        self.total_time_label = tk.Label(
            self, font=inter(12), width=width,
            text=format_seconds(audio.duration), anchor="w")
        
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
        self.display_progress(0)
    
    def display_progress(self, fraction: float) -> None:
        """Displays a given fraction of progress in the progress frame."""
        self.delete("progress")
        fraction = min(fraction, 1)

        rect_width = PROGRESS_BAR_WIDTH * fraction
        self.create_rectangle(
            PROGRESS_CIRCLE_RADIUS, PROGRESS_CIRCLE_RADIUS,
            PROGRESS_CIRCLE_RADIUS + rect_width,
            PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS,
            fill=PROGRESS_BAR_DONE_COLOURS["background"],
            outline=PROGRESS_BAR_DONE_COLOURS["background"],
            activefill=PROGRESS_BAR_DONE_COLOURS["activebackground"],
            activeoutline=PROGRESS_BAR_DONE_COLOURS["activebackground"],
            tags="progress")

        self.circle_mid_x = (
            PROGRESS_BAR_WIDTH * fraction + PROGRESS_CIRCLE_RADIUS)
        self.circle_mid_y = (
            PROGRESS_BAR_HEIGHT + PROGRESS_CIRCLE_RADIUS * 2) / 2
        self.create_oval(
            self.circle_mid_x - PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_y - PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_x + PROGRESS_CIRCLE_RADIUS,
            self.circle_mid_y + PROGRESS_CIRCLE_RADIUS,
            fill=PROGRESS_CIRCLE_COLOURS["background"],
            activefill=PROGRESS_CIRCLE_COLOURS["activebackground"],
            outline=PROGRESS_CIRCLE_COLOURS["outline"], tags="progress")


class PlayControlsFrame(tk.Frame):
    """
    Handles playback controls e.g. pause, resume, seek back, seek forward etc.
    """

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        self.paused = False
        self.state_button = PlayStateButton(self)
        self.last_state_change = None

        self.state_button.grid(row=0, column=0)
    
    def change_state(self) -> None:
        """Pauses the audio if playing, resumes the audio if paused."""
        timestamp = timer()
        if (
            self.last_state_change is not None
            and timestamp - self.last_state_change < STATE_CHANGE_REFRESH_RATE
        ):
            return
        self.last_state_change = timestamp
        if self.paused is None:
            # No longer playing - new playback.
            self.master.master.replay()
            self.state_button.set_pause_image()
            self.paused = False
            return
        if self.paused:
            # Paused, so now resume.
            self.master.master.resume()
            self.state_button.set_pause_image()
        else:
            # Playing, so now pause.
            self.master.master.pause()
            self.state_button.set_resume_image()
        self.paused = not self.paused


class PlayStateButton(Button):
    """A button to allow the playback to be paused and resumed."""

    def __init__(self, master: PlayControlsFrame) -> None:
        self.pause_image = load_image("pause.png")
        self.resume_image = load_image("resume.png")
        self.pause_hover_image = load_image("pausehover.png")
        self.resume_hover_image = load_image("resumehover.png")
        self.image = self.pause_image
        self.hover_image = self.pause_hover_image
        super().__init__(
            master, None, None, None, bg=BG, activebg=BG,
            command=master.change_state, image=self.image)

        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    def set_pause_image(self) -> None:
        """Displays the pause button."""
        self.image = self.pause_image
        self.hover_image = self.pause_hover_image
        self.config(image=self.image)
    
    def set_resume_image(self) -> None:
        """Displays the resume button."""
        self.image = self.resume_image
        self.hover_image = self.resume_hover_image
        self.config(image=self.image)
    
    def on_enter(self) -> None:
        """Hovering over the image."""
        self.config(image=self.hover_image)

    def on_exit(self) -> None:
        """No longer hovering over the image."""
        self.config(image=self.image)
