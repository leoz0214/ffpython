"""Main module of the app."""
import threading
import time
import tkinter as tk
from contextlib import suppress
from timeit import default_timer as timer
from tkinter import filedialog
from tkinter import messagebox

import idle
import loaded
from audio import load_audio
from colours import FG, BG


TITLE = "FFPython"
ALLOWED_EXTENSIONS = {
    ".mp3": "MP3",
    ".wav": "WAV",
    ".ogg": "OGG",
    ".oga": "OGG",
    ".m4a": "M4A",
    ".mp4": "MP4 (Audio only)"
}
MIN_WIDTH = 400
MIN_HEIGHT = 300


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
        self.start_time = None

        self.frame = idle.IdleFrame(self)
        self.frame.pack(padx=25, pady=25)
    
    def open(self) -> None:
        """Opens an audio file in the GUI."""
        file_path = filedialog.askopenfilename(
            filetypes=(
                (name, extension)
                for extension, name in ALLOWED_EXTENSIONS.items()))
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
        if self.current is not None and file_path == self.current.file_path:
            # Already opened in the program.
            return

        try:
            self.current = load_audio(file_path)
        except Exception as e:
            messagebox.showerror(
                "Error",
                    f"Failed to load audio due to the following error: {e}")
            return
        self.update_state()

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

    def play(self) -> None:
        """Plays the audio. Must be called though a thread."""
        self.start_time = timer()

        with suppress(tk.TclError):
            # Main audio loop.
            while True:
                time.sleep(0.1)
                current_seconds = timer() - self.start_time
                self.frame.update_progress(current_seconds)


def main() -> None:
    """Main procedure of the program."""
    root = tk.Tk()
    root.tk_setPalette(foreground=FG, background=BG)
    audio_player = AudioPlayer(root)
    audio_player.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
