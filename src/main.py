"""Main module of the app."""
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from colours import *
from utils import inter
from widgets import Button


TITLE = "FFPython"
ALLOWED_EXTENSIONS = {
    ".mp3": "MP3",
    ".wav": "WAV",
    ".ogg": "OGG",
    ".m4a": "M4A",
    ".mp4": "MP4 (Audio)"
}


class AudioPlayer(tk.Frame):
    """
    Holds the main audio player GUI,
    which the user can load audio files and play them.
    """

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root
        self.root.title(TITLE)

        self.open_file_button = Button(
            self, "Open File", font=inter(25), command=self.open)
        self.root.bind("<Control-o>", lambda *_: self.open())
        self.open_file_button.pack(padx=100, pady=100)
    
    def open(self) -> None:
        """Opens an audio file in the GUI."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                (name, extension)
                for extension, name in ALLOWED_EXTENSIONS.items()])
        if not file_path:
            return
        if not any(
            file_path.endswith(extension) for extension in ALLOWED_EXTENSIONS
        ):
            messagebox.showerror(
                "Error",
                    "Invalid file provided - "
                    "the file extension is not supported.")
            return
        print(file_path)


def main() -> None:
    """Main procedure of the program."""
    root = tk.Tk()
    root.tk_setPalette(foreground=FG, background=BG)
    audio_player = AudioPlayer(root)
    audio_player.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
