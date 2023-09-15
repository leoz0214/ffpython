"""Handles playlist creation, playing, viewing, editing and deleting."""
import pathlib
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import main
from utils import inter, open_audio_file
from widgets import Button, StringEntry, Textbox, Listbox, HorizontalLine


MAX_PLAYLIST_NAME_LENGTH = 100
MAX_PLAYLIST_DESCRIPTION_LENGTH = 2000
MAX_PLAYLIST_LENGTH = 1000


class CreatePlaylist(tk.Frame):
    """Allows the user to create a new playlist."""

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        master.root.title(f"{main.DEFAULT_TITLE} - Playlists - Create")
        self.title = tk.Label(
            self, font=inter(30, True), text="Create Playlist")
        self.metadata_frame = CreatePlaylistMetadataFrame(self)
        self.separator = HorizontalLine(self, width=750)
        self.audio_frame = CreatePlaylistAudioFrame(self)

        self.title.pack(padx=10, pady=5)
        self.metadata_frame.pack(padx=10, pady=5)
        self.separator.pack(padx=10, pady=5)
        self.audio_frame.pack(padx=10, pady=5)


class CreatePlaylistMetadataFrame(tk.Frame):
    """Handles the name and description of a playlist."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.name_label = tk.Label(
            self, font=inter(15), text="Name of playlist:")
        self.name_entry = StringEntry(
            self, width=44, max_length=MAX_PLAYLIST_NAME_LENGTH,
            initial_value="Playlist 1")
        
        self.description_label = tk.Label(
            self, font=inter(15), text="Description (optional):")
        self.description_entry = Textbox(
            self, height=5, max_length=MAX_PLAYLIST_DESCRIPTION_LENGTH)
    
        self.name_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.description_label.grid(
            row=1, column=0, padx=5, pady=5, sticky="ne")
        self.description_entry.grid(
            row=1, column=1, padx=5, pady=5, sticky="w")


class CreatePlaylistAudioFrame(tk.Frame):
    """Handles the input of the audio files to include in the playlist."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.listbox = CreatePlaylistListbox(self)
        self.add_file_button = Button(self, "Add File", command=self.add_file)
        self.files = []
        
        self.listbox.grid(row=0, column=0, padx=10, pady=5, columnspan=3)
        self.add_file_button.grid(row=1, column=0, pady=5)
    
    def add_file(self) -> None:
        """Allows the user to add an audio file to the playlist."""
        file_path = open_audio_file()
        if file_path is None:
            return
        file_path = pathlib.Path(file_path)
        if file_path in self.files:
            messagebox.showinfo("Note", "File already added.")
            return
        self.files.append(file_path)
        self.listbox.append(file_path)


class CreatePlaylistListbox(Listbox):
    """Holds the list of audio files in the playlist."""

    def __init__(self, master: CreatePlaylistAudioFrame) -> None:
        super().__init__(master, height=10, horizontal_scrollbar=True)
