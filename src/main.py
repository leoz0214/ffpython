"""Main module of the app."""
import threading
import time
import tkinter as tk
from contextlib import suppress
from tkinter import filedialog
from tkinter import messagebox

import idle
import loaded
from audio import load_audio
from colours import FG, BG


TITLE = "FFPython"
ALLOWED_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".ogg",
    ".oga",
    ".m4a",
    ".mp4"
)
ALLOWED_EXTENSIONS_DICT = {
    ".mp3": "MP3",
    ".wav": "WAV",
    ".ogg": "OGG",
    ".oga": "OGG",
    ".m4a": "M4A",
    ".mp4": "MP4 (Audio only)"
}
MIN_WIDTH = 400
MIN_HEIGHT = 300
SPACEBAR_MIN_DELAY = 0.5
SEEK_SECONDS = 10


class AudioPlayer(tk.Frame):
    """
    Holds the main audio player GUI,
    which the user can load audio files and play them.
    """

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.title(TITLE)
        self.root.bind("<Control-o>", lambda *_: self.open())

        self.current = None
        self.last_spacebar_input = None

        self.frame = idle.IdleFrame(self)
        self.frame.pack(padx=25, pady=25)
    
    def open(self) -> None:
        """Opens an audio file in the GUI."""
        file_path = filedialog.askopenfilename(
            filetypes=(
                *(("Audio", extension) for extension in ALLOWED_EXTENSIONS),
                *(
                    (name, extension)
                    for extension, name in ALLOWED_EXTENSIONS_DICT.items())))
        if not file_path:
            # Cancelled.
            return
        if not any(
            file_path.endswith(extension) for extension in ALLOWED_EXTENSIONS
        ):
            # Bypassed file extension filter, not allowed.
            messagebox.showerror(
                "Error",
                    "Invalid file provided - "
                    "the file extension is not supported.")
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
                "Error",
                    f"Failed to load audio due to the following error: {e}")
            return
        self.update_state()

        # Binds playback control keys.
        self.root.bind(
            "<space>",
            lambda *_: self.frame.play_controls_frame.change_state())
        self.root.bind(
            "<Left>", lambda *_: self.frame.play_controls_frame.seek_back())
        self.root.bind(
            "<Right>",
            lambda *_: self.frame.play_controls_frame.seek_forward())

        # Playback thread (daemon - stops when the app is closed).
        playback_thread = threading.Thread(target=self.play, daemon=True)
        playback_thread.start()
    
    def update_state(self) -> None:
        """
        Moves to idle frame if no audio is loaded, 
        or else, displays the main frame.
        """
        self.frame.destroy()
        self.frame = (
            idle.IdleFrame if self.current is None else loaded.LoadedFrame
        )(self)
        self.frame.pack(padx=25, pady=25)

    def play(self, from_seek: bool = False) -> None:
        """Plays the audio. Must be called through a thread."""
        try:
            if not (
                from_seek
                and self.current.current_seconds + 0.5 >= self.current.duration
            ):
                self.current.play(self.current.current_seconds)
                with suppress(tk.TclError):
                    # Main audio loop.
                    while self.current.is_playing:
                        time.sleep(0.1)
                        if not self.current.is_playing:
                            break
                        self.frame.update_progress(self.current.current_seconds)
            if (
                not self.current.paused
                and self.current.current_seconds + 0.5 >= self.current.duration
            ):
                self.frame.stop_button.config(text="Exit Playback")
                # Make progress 100% to indicate completion.
                self.frame.update_progress(self.current.duration)
                # Resets current audio in case of replay.
                self.current.reset()
                # Sets 'paused' to None (neither paused not resumed.)
                self.frame.play_controls_frame.paused = None
                # Sets resume image to replay audio if clicked.
                self.frame.play_controls_frame.state_button.set_resume_image()
        except Exception as e:
            if self.current is None:
                # Already stopped prematurely.
                return
            messagebox.showerror(
                "Playback Error",
                    "Unfortunately, an error has "
                    f"occurred while playing audio: {e}")
            self.stop()
    
    def pause(self) -> None:
        """Pauses the audio."""
        self.current.pause()
    
    def resume(self) -> None:
        """Resumes the audio."""
        self.current.resume()
        playback_thread = threading.Thread(target=self.play, daemon=True)
        playback_thread.start()
    
    def stop(self) -> None:
        """Terminates audio playback."""
        # Unbinds audio playback control keys.
        for key in ("space", "Left", "Right"):
            self.root.unbind(f"<{key}>")
        # Stops and returns None, so current becomes None.
        self.current = self.current.stop()
        self.update_state()
    
    def replay(self) -> None:
        """Replays the audio."""
        self.frame.update_progress(0)
        self.frame.stop_button.config(text="Stop Playback")
        playback_thread = threading.Thread(target=self.play, daemon=True)
        playback_thread.start()
    
    def seek_back(self) -> None:
        """Seeks back in the audio."""
        if self.current.start_time is None:
            # At end, seeking back, so no longer will be.
            self.frame.stop_button.config(text="Stop Playback")
            self.frame.play_controls_frame.paused = False
            self.frame.play_controls_frame.state_button.set_pause_image()
        if self.current.paused:
            self.frame.play_controls_frame.change_state(forced=True)
        self.current.seek_back(SEEK_SECONDS)
        playback_thread = threading.Thread(
            target=lambda: self.play(from_seek=True), daemon=True)
        playback_thread.start()
    
    def seek_forward(self) -> None:
        """Seeks forward in the audio."""
        if self.current.start_time is None:
            # End already reached, cannot seek any further.
            return
        if self.current.paused:
            self.frame.play_controls_frame.change_state(forced=True)
        self.current.seek_forward(SEEK_SECONDS)
        playback_thread = threading.Thread(
            target=lambda: self.play(from_seek=True), daemon=True)
        playback_thread.start()   


def main() -> None:
    """Main procedure of the program."""
    root = tk.Tk()
    root.tk_setPalette(foreground=FG, background=BG)
    audio_player = AudioPlayer(root)
    audio_player.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
