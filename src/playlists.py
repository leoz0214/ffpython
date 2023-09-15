"""Handles playlist creation, playing, viewing, editing and deleting."""
import pathlib
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from typing import Callable

import main
from colours import ENTRY_COLOURS, FG, CHECKBUTTON_COLOURS
from utils import inter, open_audio_file, ALLOWED_EXTENSIONS
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
        self.import_folder_button = Button(
            self, "Import Folder", command=self.import_folder)
        self.files = []
        
        self.listbox.grid(row=0, column=0, padx=10, pady=5, columnspan=2)
        self.add_file_button.grid(row=1, column=0, pady=5)
        self.import_folder_button.grid(row=1, column=1, pady=5)
    
    @staticmethod
    def check_playlist_length(method: Callable) -> None:
        """Decorator to refuse adding more files if the limit is reached."""
        def wrapper(self: "CreatePlaylistAudioFrame") -> None:
            if len(self.files) == MAX_PLAYLIST_LENGTH:
                messagebox.showerror(
                    "Error",
                        "Maximum number of "
                        f"audio files reached: {MAX_PLAYLIST_LENGTH}")
                return
            method(self)
        return wrapper       
    
    @check_playlist_length
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
    
    @check_playlist_length
    def import_folder(self) -> None:
        """Gateway to the import folder toplevel."""
        ImportFolderToplevel()


class CreatePlaylistListbox(Listbox):
    """Holds the list of audio files in the playlist."""

    def __init__(self, master: CreatePlaylistAudioFrame) -> None:
        super().__init__(master, height=10, horizontal_scrollbar=True)


class ImportFolderToplevel(tk.Toplevel):
    """
    Popup window to allow the user to import a folder of audio files
    with various configurations.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(
            f"{main.DEFAULT_TITLE} - Playlists - Create - Import Folder")
        self.grab_set()
        self.resizable(False, False)
        self.title_label = tk.Label(
            self, font=inter(30, True), text="Import Folder")
        self.folder_label = tk.Label(self, font=inter(15), text="Folder:")
        # Approximate Windows file length limit is 260 characters.
        self.folder_entry = StringEntry(
            self, max_length=260, state="disabled",
            disabledbackground=ENTRY_COLOURS["background"],
            disabledforeground=FG, initial_value="Not Set")
        self.select_folder_button = Button(
            self, "Select", inter(12), command=self.select_folder)
        
        self.file_types_label = tk.Label(
            self, font=inter(15), text="File types to include:")
        self.file_types_input = FileTypesFrame(self)

        self.title_label.grid(row=0, column=0, padx=10, pady=10, columnspan=3)
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.select_folder_button.grid(row=1, column=2, padx=5, pady=5)
        self.file_types_label.grid(
            row=2, column=0, padx=5, pady=5, sticky="ne")
        self.file_types_input.grid(row=2, column=1, columnspan=2, sticky="nw")
    
    def select_folder(self) -> None:
        """Allows the user to select the import folder."""
        folder = filedialog.askdirectory(mustexist=True)
        if not folder:
            # Cancelled
            return
        self.folder_entry.variable.set(folder)


class FileTypesFrame(tk.Frame):
    """Handles the selection of file types to include in the file import."""

    def __init__(self, master: ImportFolderToplevel) -> None:
        super().__init__(master)
        # Stores enabled/disabled for each file extension.
        self.states = {
            extension: tk.BooleanVar(value=True)
            for extension in ALLOWED_EXTENSIONS
        }
        for i, (extension, variable) in enumerate(self.states.items()):
            checkbutton = tk.Checkbutton(
                self, font=inter(12), text=extension, variable=variable,
                selectcolor=CHECKBUTTON_COLOURS["background"])
            checkbutton.grid(row=i//2, column=i%2, padx=5, pady=5)

    @property
    def selected(self) -> list[str]:
        """Returns the selected extensions."""
        return [
            extension
            for extension, state in self.states.items() if state.get()]
