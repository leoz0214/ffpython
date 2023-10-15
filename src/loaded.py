"""Main handler of the GUI whilst audio is playing."""
import math
import tkinter as tk
from timeit import default_timer as timer
from typing import Callable, Any

import main
from colours import (
    PROGRESS_BAR_REMAINING_COLOUR, PROGRESS_BAR_DONE_COLOURS,
    PROGRESS_CIRCLE_COLOURS, BG)
from utils import inter, format_seconds, load_image, bool_to_state
from widgets import Button, HorizontalLine


PROGRESS_BAR_WIDTH = 500
PROGRESS_CIRCLE_RADIUS = 6
PROGRESS_BAR_HEIGHT = 6
STATE_CHANGE_REFRESH_RATE = 0.1
ARROW_SEEK_CHANGE_REFRESH_RATE = 0.25
MAX_LOOPS = 99 # Before infinite


class LoadedFrame(tk.Frame):
    """(Main) GUI state for when audio has been loaded or is playing."""

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        audio = master.current
        master.root.title(
            f"{main.DEFAULT_TITLE} - Playback - {audio.name_display}")
        self.name_label = tk.Label(
            self, font=inter(25, True), text=audio.name_display)
        self.file_path_label = tk.Label(
            self, font=inter(10), text=audio.file_path_display)
        
        self.separator = HorizontalLine(self, 750)
        
        self.play_progress_frame = PlayProgressFrame(self)
        self.play_controls_frame = PlayControlsFrame(self)
        self.play_looping_frame = PlayLoopingFrame(self)

        self.separator2 = HorizontalLine(self, 750)
        
        self.open_file_button = Button(
            self, "Open File", font=inter(12), command=master.open)
        self.stop_button = Button(
            self, "Stop Playback", font=inter(12), command=master.stop)
        
        self.menu = LoadedMenu(self)
        
        self.name_label.grid(row=0, column=0, sticky="w", padx=5, pady=(100, 2))
        self.file_path_label.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.separator.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.play_progress_frame.grid(
            row=3, column=0, columnspan=2, padx=5, pady=(25, 5))
        self.play_controls_frame.grid(
            row=4, column=0, columnspan=2, padx=5, pady=(5, 25))
        self.play_looping_frame.grid(
            row=5, column=0, padx=5, pady=(25, 5), sticky="w")
        self.separator2.grid(
            row=6, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.open_file_button.grid(
            row=7, column=1, sticky="e", padx=(25, 5), pady=5)
        self.stop_button.grid(
            row=8, column=1, sticky="e", padx=(25, 5), pady=5)
        
        master.root.config(menu=self.menu)
    
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


class LoadedMenu(tk.Menu):
    """Toplevel menu for when the audio is loaded."""

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Open (Ctrl+O)", font=inter(12), command=master.master.open)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12), command=main.quit_app)
        self.add_cascade(label="File", menu=self.file_menu)

        self.playback_menu = tk.Menu(self, tearoff=False)
        self.playback_menu.add_command(
            label="Pause (space)", font=inter(12),
            command=lambda: self.change_state(True))
        self.playback_menu.add_separator()
        self.playback_menu.add_command(
            label="Seek Back (←)", font=inter(12),
            command=self.master.play_controls_frame.seek_back)
        self.playback_menu.add_command(
            label="Seek Forward (→)", font=inter(12),
            command=self.master.play_controls_frame.seek_forward)
        self.playback_menu.add_separator()
        self.playback_menu.add_command(
            label="Stop Playback", font=inter(12), command=master.master.stop)
        self.add_cascade(label="Playback", menu=self.playback_menu)

        self.playlists_menu = tk.Menu(self, tearoff=False)
        self.playlists_menu.add_command(
            label="Create", font=inter(12),
            command=master.master.create_playlist)
        self.playlists_menu.add_command(
            label="View", font=inter(12), command=master.master.view_playlists)
        self.add_cascade(label="Playlists", menu=self.playlists_menu)
    
    def change_state(self, from_menu: bool = False) -> None:
        """
        Changes state if invoked from the menu,
        and then updates the command name pause/resume/replay
        based on the current playback state.
        """
        if from_menu:
            self.master.play_controls_frame.change_state()
        paused = self.master.play_controls_frame.paused
        change_state_label = {
            True: "Resume",
            False: "Pause",
            None: "Replay"
        }[paused] + " (space)"
        self.playback_menu.entryconfig(0, label=change_state_label)
        # Can only seek forward if playback not complete.
        self.playback_menu.entryconfig(
            3, state=bool_to_state(paused is not None))
        self.playback_menu.entryconfig(
            5, label=f"{'Exit' if paused is None else 'Stop'} Playback")


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
    Includes a moving circle indicating progress too.
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
        self.drag_seeking = False
        self.drag_fraction = None
        self.bind("<B1-Motion>", self.drag_seek)
        self.bind("<Button-1>", self.click_seek)
    
    def drag_seek(self, event: tk.Event) -> None:
        "Seeks to a point in the audio by dragging the progress circle."""
        x = event.x
        if not self.drag_seeking:
            # Check if cursor lies in progress circle (radius check).
            y = event.y
            distance_from_centre = math.hypot(
                self.circle_mid_x - x, self.circle_mid_y - y)
            if distance_from_centre > PROGRESS_CIRCLE_RADIUS:
                # Not in the circle.
                return
            self.drag_seeking = True
            self.bind("<ButtonRelease-1>", lambda *_: self.drag_release())
        audio = self.master.master.master.current
        audio.stop()
        self.drag_fraction = (
            x - PROGRESS_CIRCLE_RADIUS * 2) / (
                PROGRESS_BAR_WIDTH - PROGRESS_CIRCLE_RADIUS)
        # 0 <= fraction <= 1
        self.drag_fraction = max(min(self.drag_fraction, 1), 0)
        seconds = self.drag_fraction * audio.duration
        self.master.current_time_label.config(text=format_seconds(seconds))
        self.display_progress(self.drag_fraction)
    
    def drag_release(self) -> None:
        """Drag seek complete - resume audio at that point."""
        duration = self.master.master.master.current.duration
        seek_seconds = self.drag_fraction * duration
        self.drag_seeking = False
        self.drag_fraction = None
        self.unbind("<ButtonRelease-1>")
        self.master.master.master.seek(seek_seconds)
    
    def click_seek(self, event: tk.Event) -> None:
        """Seeks to a given timestamp by clicking on the progress bar."""
        x = event.x
        y = event.y
        if not (
            PROGRESS_CIRCLE_RADIUS <= x
                <= PROGRESS_BAR_WIDTH + PROGRESS_CIRCLE_RADIUS
            and PROGRESS_CIRCLE_RADIUS <= y
                <= PROGRESS_BAR_WIDTH + PROGRESS_BAR_HEIGHT
        ):
            # Did not click on actual progress rectangle.
            return
        distance_from_centre = math.hypot(
            self.circle_mid_x - x, self.circle_mid_y - y)
        if distance_from_centre <= PROGRESS_CIRCLE_RADIUS:
            # In the circle. Hence, do not register the click seek.
            return
        audio = self.master.master.master.current
        fraction = (
            x - PROGRESS_CIRCLE_RADIUS * 2) / (
                PROGRESS_BAR_WIDTH - PROGRESS_CIRCLE_RADIUS)
        fraction = max(min(fraction, 1), 0)
        seek_seconds = fraction * audio.duration
        self.master.master.master.seek(seek_seconds)
    
    def display_progress(self, fraction: float) -> None:
        """Displays a given fraction of progress in the progress frame."""
        self.delete("progress")
        # Safety. Keeps fraction in the range 0 <= fraction <= 1
        fraction = max(min(fraction, 1), 0)

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
            (PROGRESS_BAR_WIDTH - PROGRESS_CIRCLE_RADIUS) * fraction
            + PROGRESS_CIRCLE_RADIUS * 2)
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
        self.back_button = ArrowSeekButton(
            self, "back.png", "backhover.png", self.seek_back)
        self.state_button = PlayStateButton(self)
        self.forward_button = ArrowSeekButton(
            self, "forward.png", "forwardhover.png", self.seek_forward)
        self.last_change = None

        self.back_button.grid(row=0, column=0, padx=10)
        self.state_button.grid(row=0, column=1, padx=10)
        self.forward_button.grid(row=0, column=2, padx=10)
    
    @staticmethod
    def change(delay: float) -> Callable:
        """Decorator to limit rate of changes due to threading instability."""
        def inner(method: Callable) -> Callable:
            def wrapper(self: "PlayControlsFrame", forced: bool = False) -> Any:
                timestamp = timer()
                if (
                    (not forced) and self.last_change is not None
                    and timestamp - self.last_change < delay
                ):
                    return
                self.last_change = timestamp
                return method(self)
            return wrapper
        return inner
    
    @change(STATE_CHANGE_REFRESH_RATE)
    def change_state(self) -> None:
        """Pauses the audio if playing, resumes the audio if paused."""
        if self.paused is None:
            # No longer playing - new playback.
            self.master.master.replay()
            self.state_button.set_pause_image()
            self.paused = False
        else:
            if self.paused:
                # Paused, so now resume.
                self.master.master.resume()
                self.state_button.set_pause_image()
            else:
                # Playing, so now pause.
                self.master.master.pause()
                self.state_button.set_resume_image()
            self.paused = not self.paused
        # Updates toplevel menu display.
        self.master.menu.change_state()
    
    @change(ARROW_SEEK_CHANGE_REFRESH_RATE)
    def seek_back(self) -> None:
        """Moves back in playback."""
        self.master.master.seek_back()

    @change(ARROW_SEEK_CHANGE_REFRESH_RATE)
    def seek_forward(self) -> None:
        """Moves forward in playback."""
        self.master.master.seek_forward()


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


class ArrowSeekButton(Button):
    """Allows the user to move back or forward in playback."""

    def __init__(
        self, master: PlayControlsFrame, image: str, hover_image: str,
        command: Callable
    ):
        self.image = load_image(image)
        self.hover_image = load_image(hover_image)
        super().__init__(
            master, None, None, None, bg=BG, activebg=BG,
            command=command, image=self.image)

        self.bind("<Enter>", lambda *_: self.on_enter())
        self.bind("<Leave>", lambda *_: self.on_exit())
    
    def on_enter(self) -> None:
        """Hovering over the image button."""
        self.config(image=self.hover_image)
    
    def on_exit(self) -> None:
        """No longer hovering over the image button."""
        self.config(image=self.image)


class PlayLoopingFrame(tk.Frame):
    """
    Handles looping, allowing turning looping off, 
    infinite loops and a fixed number of loops.
    """

    def __init__(self, master: LoadedFrame) -> None:
        super().__init__(master)
        self.loop_image = load_image("loop.png")
        self.image = tk.Label(self, image=self.loop_image)
        self.off_button = Button(
            self, "❌", inter(12), width=2, border=1, command=self.off)
        self.decrement_button = Button(
            self, "-", inter(12), width=2, command=self.decrement)
        self.count_label = tk.Label(
            self, font=inter(12), text="OFF", width=4)
        self.increment_button = Button(
            self, "+", inter(12), width=2, command=self.increment)
        self.infinite_button = Button(
            self, "∞", inter(12), width=2, border=1, command=self.infinite)
        self.update_display()

        self.image.grid(row=0, column=0, padx=(5, 10), pady=5)
        self.off_button.grid(row=0, column=1, pady=5)
        self.decrement_button.grid(row=0, column=2, pady=5)
        self.count_label.grid(row=0, column=3, pady=5)
        self.increment_button.grid(row=0, column=4, pady=5)
        self.infinite_button.grid(row=0, column=5, pady=5)
    
    def off(self) -> None:
        """Turns looping off."""
        self.master.master.loops = None
        self.update_display()
    
    def decrement(self) -> None:
        """Removes a loop (-1)."""
        if self.master.master.loops == float("inf"):
            # Decrease infinty to the highest allowed finite number.
            self.master.master.loops = MAX_LOOPS
        else:
            self.master.master.loops -= 1
        self.update_display()

    def increment(self) -> None:
        """Adds a loop (+1)."""
        self.master.master.loops = (self.master.master.loops or 0) + 1
        if self.master.master.loops > MAX_LOOPS:
            # Increase highest allowed finite number to infinity.
            self.master.master.loops = float("inf")
        self.update_display()
    
    def infinite(self) -> None:
        """Sets looping to infinite (forever)."""
        self.master.master.loops = float("inf")
        self.update_display()

    def update_display(self) -> None:
        """Updates display and button states."""
        loops = self.master.master.loops
        # None -> OFF, inf -> ∞, otherwise display fixed number of loops.
        display = {None: "OFF", float("inf"): "∞"}.get(loops, str(loops))
        self.count_label.config(text=display)
        self.off_button.config(state=bool_to_state(loops is not None))
        self.decrement_button.config(state=bool_to_state(bool(loops)))
        is_finite = loops != float("inf")
        self.increment_button.config(state=bool_to_state(is_finite))
        self.infinite_button.config(state=bool_to_state(is_finite))
