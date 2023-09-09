"""GUI for when the audio player is in an idle state."""
import tkinter as tk

import main
from utils import inter
from widgets import Button


class IdleFrame(tk.Frame):
    """GUI state for when audio has not been loaded and is not playing."""
    
    def __init__(self, master: main.AudioPlayer) -> None:
        super().__init__(master)
        self.menu = IdleMenu(self)
        self.open_file_button = Button(
            self, "Open File", font=inter(25), command=master.open)
        self.open_file_button.pack(padx=100, pady=100)
        master.root.config(menu=self.menu)


class IdleMenu(tk.Menu):
    """Toplevel menu when the program is in an idle state."""

    def __init__(self, master: IdleFrame) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Open (Ctrl+O)", font=inter(12), command=master.master.open)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12), command=main.quit_app)

        self.add_cascade(label="File", font=inter(12), menu=self.file_menu)
