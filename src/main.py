"""Main module of the app."""
import atexit
import sys
import threading
import time
import tkinter as tk
from contextlib import suppress
from tkinter import messagebox
from typing import Callable, Any

import idle
import loaded
import playlists
from audio import load_audio
from colours import FG, BG
from fileh import set_up_database
from utils import open_audio_file, IMAGES_FOLDER


DEFAULT_TITLE = "FFPython"
# App icon.
ICON = IMAGES_FOLDER / "icon.ico"
# Reasonable minimum window dimensions.
MIN_WIDTH = 400
MIN_HEIGHT = 300
# Hard-coded *for now) number of seconds to seek back/forward with arrows.
SEEK_SECONDS = 10


class AudioPlayer(tk.Frame):
    """
    Holds the main audio player GUI,
    where the user can load audio files and play them.
    """

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root
        self.root.bind("<Control-o>", lambda *_: self.open())

        # Current Audio object. Is None when not loaded.
        self.current = None
        # Looping: None - OFF, int - fixed, inf - forever.
        self.loops = None
        # Playlist object tracking playlist playback info.
        # Is None when not loaded.
        self.playlist = None
        # Set initial frame: the home screen.
        self.frame = idle.IdleFrame(self)
        self.frame.pack(padx=25, pady=25)
        # Starting file passed in as first argumnt
        # - play upon app initialisation.
        if len(sys.argv) > 1:
            self.open(sys.argv[1])
    
    def open(self, file_path: str | None = None) -> None:
        """Opens an audio file in the GUI."""
        file_path = open_audio_file(file_path)
        if file_path is None:
            return

        if self.current is not None:
            if file_path == self.current.file_path:
                # Already opened in the program.
                return
            self.stop()

        try:
            self.current = load_audio(file_path)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while trying to load audio: {e}")
            return

        self.update_state()
        self.bind_playback_keys()
        self.start_playback_thread()
    
    def bind_playback_keys(self) -> None:
        """Binds playback control keys."""
        # The spacebar allows pause, resume, replay.
        self.root.bind(
            "<space>",
            lambda *_: self.frame.play_controls_frame.change_state())
        # The left arrow allows seek back.
        self.root.bind(
            "<Left>", lambda *_: self.frame.play_controls_frame.seek_back())
        # The right arrow allows seek forward.
        self.root.bind(
            "<Right>",
            lambda *_: self.frame.play_controls_frame.seek_forward())
    
    def start_playback_thread(self, from_seek: bool = False) -> None:
        """Starts the playback thread."""
        playback_thread = threading.Thread(
            target=lambda: self.play(from_seek=from_seek), daemon=True)
        playback_thread.start()
    
    def update_state(self, frame: tk.Frame | Callable | None = None) -> None:
        """
        Moves to a given frame, or to the idle frame if no audio is loaded,
        or else, displays the main loaded frame.
        """
        self.frame.destroy()
        self.root.unbind("<Control-o>")
        if frame is not None:
            self.frame = frame(self)
        else:
            # By default, launch the idle or loaded frame as required.
            self.frame = (
                idle.IdleFrame if self.current is None else loaded.LoadedFrame
            )(self)
            self.root.bind("<Control-o>", lambda *_: self.open())
        self.frame.pack(padx=25, pady=25)
    
    @property
    def stop_button_keyword(self) -> str:
        return "Playlist" if self.in_playlist else "Playback"
    
    @staticmethod
    def block_gui_command(command: Callable) -> Callable:
        """
        Decorator which blocks the GUI while a command
        is running, by faking a button click. Useful in a thread
        to avoid race conditions.
        """
        def wrapper(self, *args, **kwargs) -> Any:
            return tk.Button(
                 command=lambda: command(self, *args, **kwargs)).invoke()
        return wrapper

    @block_gui_command
    def play_current(self) -> None:
        """Plays the current file in the playlist."""
        try:
            self.current = load_audio(self.playlist.current)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while trying to load audio: {e}")
            self.stop()
            return
        self.frame.update_file()
        self.frame.playlist_frame.update_select()
        self.start_playback_thread()
    
    def play_at_position(self, position: int) -> None:
        """Plays the file in a playlist at the given index."""
        self.current.stop()
        self.current = None
        # Resets looping by turning it off.
        self.frame.play_looping_frame.off()
        # If audio is paused while the switch takes place, reset state.
        if self.frame.play_controls_frame.paused is not False:
            self.frame.play_controls_frame.change_state(from_file_change=True)
        self.frame.stop_button.config(text=f"Stop {self.stop_button_keyword}")
        self.playlist.position = position
        self.play_current()

    def play(self, from_seek: bool = False) -> None:
        """Plays the audio. Must be called through a thread."""
        current = self.current
        try:
            # Should not play anything if playing from a seek and virtually
            # already done.
            if not (
                from_seek
                and self.current.current_seconds + 0.5 >= self.current.duration
            ):
                self.current.play(self.current.current_seconds)
                with suppress(tk.TclError):
                    # Main audio loop.
                    while self.current.is_playing:
                        time.sleep(0.1)
                        # Performs another check before updating the frame.
                        if not self.current.is_playing:
                            break
                        self.frame.update_progress(self.current.current_seconds)
            if (
                not self.current.paused
                and self.current.current_seconds + 0.5 >= self.current.duration
            ):
                # PLAYBACK OF CURRENT AUDIO DONE.
                # Resets current audio in case of replay.
                self.current.reset()
                if self.loops:
                    # Looping - repeat.
                    self.replay(from_loop=True)
                    # Be safe - prevent 0 being decremented to -1
                    # or None raising an error (thread issues).
                    if self.loops:
                        self.loops -= 1
                    self.frame.play_looping_frame.update_display()
                    return
                if self.in_playlist:
                    if (not self.playlist.at_end) or self.playlist.loops:
                        if not self.playlist.at_end:
                            # Increment to next playlist file
                            self.playlist.position += 1
                        else:
                            # Decrements loops and restarts the playlist.
                            self.playlist.loops -= 1
                            playlist_frame = self.frame.playlist_frame
                            playlist_frame.looping_frame.update_display()
                            self.playlist.position = 0
                        self.play_current()
                        return
                # Once playback/playlists completely finishes, this is reached.
                self.frame.stop_button.config(
                    text=f"Exit {self.stop_button_keyword}")
                # Make progress 100% to indicate completion.
                self.frame.update_progress(self.current.duration)
                # Sets 'paused' to None (neither paused nor resumed).
                self.frame.play_controls_frame.paused = None
                # Sets resume image to replay audio if clicked.
                self.frame.play_controls_frame.state_button.set_resume_image()
                # Set the state update in menu as 'Replay'.
                self.frame.menu.change_state()
        except Exception as e:
            if self.current is not current:
                # Already stopped or another file loaded, so ignore the error.
                return
            messagebox.showerror(
                "Playback Error",
                    f"A playback error has occurred: {e}")
            self.stop()
    
    def pause(self) -> None:
        """Pauses the audio."""
        self.current.pause()
    
    def resume(self) -> None:
        """Resumes the audio."""
        self.current.resume()
        self.start_playback_thread()
    
    def stop(self, update_state: bool = True) -> None:
        """Terminates audio/playlist playback."""
        # Unbinds audio playback control keys.
        for key in ("space", "Left", "Right"):
            self.root.unbind(f"<{key}>")
        self.current.stop()
        # Dereference Audio object and reset loop variable.
        self.current = None
        self.loops = None
        self.playlist = None
        if update_state:
            self.update_state()
    
    def replay(self, from_loop: bool = False) -> None:
        """Replays the audio, or the entire playlist."""
        self.frame.stop_button.config(text=f"Stop {self.stop_button_keyword}")
        if from_loop or not self.in_playlist:
            # Repeat audio.
            self.frame.update_progress(0)
            self.start_playback_thread()
            return
        # Repeat playlist.
        self.frame.play_controls_frame.change_state(from_file_change=True)
        self.playlist.position = 0
        self.play_current()
    
    def seek_after_end(self) -> None:
        """
        Method to update the state whenever playback has reached the end
        but the user seeks backs into the audio, so the audio will no longer
        be at the end.
        """
        self.frame.stop_button.config(text=f"Stop {self.stop_button_keyword}")
        # Manually sets the state to playing.
        self.frame.play_controls_frame.paused = False
        self.frame.play_controls_frame.state_button.set_pause_image()
        self.frame.menu.change_state()

    def seek(self, seconds: float) -> None:
        """Seeks at a given point in the audio."""
        if self.current.start_time is None:
            self.seek_after_end()
        if self.current.paused:
            self.frame.play_controls_frame.change_state(forced=True)
        self.current.seek_to(seconds)
        self.start_playback_thread(from_seek=True)
    
    def seek_back(self) -> None:
        """Seeks back in the audio."""
        if self.current.start_time is None:
            self.seek_after_end()
        if self.current.paused:
            self.frame.play_controls_frame.change_state(forced=True)
        self.current.seek_back(SEEK_SECONDS)
        self.start_playback_thread(from_seek=True)
    
    def seek_forward(self) -> None:
        """Seeks forward in the audio."""
        if self.current.start_time is None:
            # End already reached, cannot seek any further.
            return
        if self.current.paused:
            self.frame.play_controls_frame.change_state(forced=True)
        self.current.seek_forward(SEEK_SECONDS)
        self.start_playback_thread(from_seek=True)
    
    def create_playlist(self) -> None:
        """Navigate to the playlist creation part of the app."""
        if self.current is not None:
            # Stop current playback first.
            self.stop()
        self.update_state(playlists.PlaylistForm)
    
    def view_playlists(self) -> None:
        """Navigate to the playlists part of the app."""
        if self.current is not None:
            self.stop()
        self.update_state(playlists.ViewPlaylists)

    @property
    def in_playlist(self) -> bool:
        """Returns True if a playlist is loaded, else False."""
        return self.playlist is not None
    
    def start_playlist(self, playlist: playlists.PlaylistPlayback) -> None:
        """Starts the playlist playback."""
        self.playlist = playlist
        try:
            self.current = load_audio(self.playlist.current)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while trying to load audio: {e}")
            return
        self.update_state()
        self.bind_playback_keys()
        self.start_playback_thread()


def main() -> None:
    """Main procedure of the program."""
    set_up_database()
    root = tk.Tk()
    root.tk_setPalette(foreground=FG, background=BG)
    root.minsize(MIN_WIDTH, MIN_HEIGHT)
    root.iconbitmap(ICON, ICON)
    root.protocol("WM_DELETE_WINDOW", lambda: quit_app(root))
    audio_player = AudioPlayer(root)
    audio_player.pack()
    atexit.register(terminate, root)
    root.mainloop()


def quit_app(root: tk.Tk | None = None) -> None:
    """Performs required cleanup and gracefully terminates the app."""
    # If root is indeed not passed in, it is not important.
    # In that case, just quit.
    # Otherwise check a few things before quitting.
    if root is not None:
        # Gets the child frame of the Audio Player.
        audio_player = root.winfo_children()[0]
        # Ensure FFplay process is stopped before closing the program.
        if audio_player.current is not None:
            audio_player.current.stop()
            audio_player.current = None
        frame = audio_player.winfo_children()[0]
        if isinstance(frame, playlists.PlaylistForm):
            if not messagebox.askyesnocancel(
                "Confirm Exit App",
                    "Are you sure you would like to exit the app?\n"
                    "The current playlist form will be lost."
            ):
                return
    sys.exit(0)


def terminate(root: tk.Tk) -> None:
    """Final cleanup function."""
    # Ensure FFplay process is killed before closing the program.
    # It is also done in quit_app, but this handles KeyboardInterrupt exit.
    audio_player = root.winfo_children()[0]
    if audio_player.current is not None:
        audio_player.current.stop()


if __name__ == "__main__":
    main()
