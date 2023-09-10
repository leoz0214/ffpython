"""Handles playlist creation, playing, viewing, editing and deleting."""
import tkinter as tk

import main
from utils import inter
from widgets import Button, StringEntry, Textbox


MAX_PLAYLIST_NAME_LENGTH = 100
MAX_PLAYLIST_DESCRIPTION_LENGTH = 2000


class CreatePlaylist(tk.Frame):
    """Allows the user to create a new playlist."""

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        master.root.title(f"{main.DEFAULT_TITLE} - Playlists - Create")
        self.title = tk.Label(
            self, font=inter(30, True), text="Create Playlist")
        self.metadata_frame = CreatePlaylistMetadataFrame(self)

        self.title.pack(padx=10, pady=5)
        self.metadata_frame.pack(padx=10, pady=5)


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
