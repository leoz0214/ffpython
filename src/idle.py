"""GUI for when the audio player is in an idle state."""
import tkinter as tk

import main
from utils import inter
from widgets import Button


class IdleFrame(tk.Frame):
    """GUI state for when audio has not been loaded and is not playing."""
    
    def __init__(self, master: main.AudioPlayer) -> None:
        super().__init__(master)
        self.open_file_button = Button(
            self, "Open File", font=inter(25), command=master.open)
        self.open_file_button.pack(padx=100, pady=100)
