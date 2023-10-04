"""Handles playlist creation, playing, viewing, editing and deleting."""
import pathlib
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from typing import Callable

import main
from colours import FG
from fileh import (
    get_import_folder_settings, update_import_folder_settings,
    create_playlist, playlist_exists, load_playlists_overview
)
from utils import inter, open_audio_file, bool_to_state, ALLOWED_EXTENSIONS
from widgets import (
    Button, StringEntry, Textbox, Listbox, HorizontalLine, Radiobutton,
    Checkbutton, Table, TableColumn
)


MAX_PLAYLIST_NAME_LENGTH = 100
MAX_PLAYLIST_DESCRIPTION_LENGTH = 2000
MAX_PLAYLIST_LENGTH = 1000
# Prevent performance issues - set a limit on the number of
# paths (files or folders) to scan before displaying an error message.
MAX_PATHS_TO_SCAN = 100_000
NOT_SET = "Not Set"
# Table displayed upon viewing data.
TABLE_COLUMNS = (
    TableColumn("id", "ID", 100),
    TableColumn("name", "Name", 600, "w"),
    TableColumn("length", "Length", 100),
    TableColumn("date_time_created", "Created", 175, "w")
)


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
        self.separator2 = HorizontalLine(self, width=750)
        self.buttons = CreatePlaylistButtons(self)
        self.menu = CreatePlaylistMenu(self)

        master.root.bind("<Control-o>", lambda *_: self.audio_frame.add_file())
        master.root.bind(
            "<Control-i>", lambda *_: self.audio_frame.import_folder())

        self.title.pack(padx=10, pady=2)
        self.metadata_frame.pack(padx=10, pady=2)
        self.separator.pack(padx=10, pady=2)
        self.audio_frame.pack(padx=10, pady=2)
        self.separator2.pack(padx=10, pady=2)
        self.buttons.pack(padx=10, pady=2)
        master.root.config(menu=self.menu)
    
    def create(self) -> None:
        """Creates the playlist upon confirmation."""
        name = self.metadata_frame.name
        if not name:
            messagebox.showerror("Empty Name", "Please enter a playlist name.")
            return
        description = self.metadata_frame.description
        # pathlib.Path -> str. Ready to be inserted into DB if needed.
        files = [str(file) for file in self.audio_frame.files]
        # Only makes sense for a playlist to have at least 2 files.
        if len(files) < 2:
            messagebox.showerror(
                "Insufficient Files",
                    "Please ensure the playlist "
                    "has at least 2 files.")
            return
        if playlist_exists(name):
            messagebox.showerror(
                "Existing Playlist",
                    "A playlist with the same name already exists.")
            return
        if not messagebox.askyesnocancel(
            "Confirm Playlist Creation",
                "Are you sure you would like to create this playlist?"
        ):
            return
        # Attempts playlist creation, shows error message if failed.
        try:
            create_playlist(name, description, files)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to create the playlist: {e}")
            return
        messagebox.showinfo("Success", "Playlist successfully created.")
        self.back(confirm=False)
    
    def back(self, confirm: bool = True) -> None:
        """Returns to main audio player."""
        # Safeguards in case user accidentally goes back unintentionally.
        if confirm and not messagebox.askyesnocancel(
            "Confirm Back",
                "Are you sure you no longer wish to create this playlist?"
        ):
            return
        for binding in ("Control-o", "control-i"):
            self.master.root.unbind(f"<{binding}>")
        self.master.update_state()


class CreatePlaylistMenu(tk.Menu):
    """Toplevel menu for the create playlist section of the program.."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Add File (Ctrl+O)",
            font=inter(12), command=master.audio_frame.add_file)
        self.file_menu.add_command(
            label="Import Folder (Ctrl+I)", font=inter(12),
            command=master.audio_frame.import_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Back", font=inter(12), command=master.back)
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12), command=main.quit_app)
        self.add_cascade(label="File", menu=self.file_menu)


class CreatePlaylistMetadataFrame(tk.Frame):
    """Handles the name and description of a playlist."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.name_label = tk.Label(
            self, font=inter(15), text="Name of playlist:")
        n = 1
        # Finds the first Playlist {n} name not in use.
        while playlist_exists(f"Playlist {n}"):
            n += 1
        self.name_entry = StringEntry(
            self, width=44, max_length=MAX_PLAYLIST_NAME_LENGTH,
            initial_value=f"Playlist {n}")
        
        self.description_label = tk.Label(
            self, font=inter(15), text="Description (optional):")
        self.description_entry = Textbox(
            self, height=5, max_length=MAX_PLAYLIST_DESCRIPTION_LENGTH)
    
        self.name_label.grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.description_label.grid(
            row=1, column=0, padx=5, pady=3, sticky="ne")
        self.description_entry.grid(
            row=1, column=1, padx=5, pady=3, sticky="w")
    
    @property
    def name(self) -> str:
        return self.name_entry.value.strip()
    
    @property
    def description(self) -> str:
        return self.description_entry.text.strip()[
            :MAX_PLAYLIST_DESCRIPTION_LENGTH]


class CreatePlaylistAudioFrame(tk.Frame):
    """Handles the input of the audio files to include in the playlist."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.listbox = Listbox(self, height=10, horizontal_scrollbar=True)
        self.add_file_button = Button(self, "Add File", command=self.add_file)
        self.import_folder_button = Button(
            self, "Import Folder", command=self.import_folder)
        self.file_handling_frame = FileHandlingFrame(self)
        self.file_count_label = tk.Label(self, font=inter(20), text="Files: 0")
        self.files = []
        self.opened_import_window = False
    
        self.listbox.listbox.bind(
            "<<ListboxSelect>>",
            lambda *_: self.file_handling_frame.update_state())
        
        self.listbox.grid(row=0, column=0, padx=10, pady=5, columnspan=2)
        self.add_file_button.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.import_folder_button.grid(
            row=1, column=1, padx=10, pady=5, sticky="w")
        self.file_handling_frame.grid(row=0, column=2)
        self.file_count_label.grid(row=1, column=2, padx=(10, 0), sticky="w")
    
    @staticmethod
    def validate(method: Callable) -> None:
        """
        Decorator to validate a user event,
        and refuses adding more files if the limit is reached.
        """
        def wrapper(self: "CreatePlaylistAudioFrame") -> None:
            # Cannot override toplevel window. Do not allow
            # events from the main window during this.
            if self.opened_import_window:
                return
            if len(self.files) == MAX_PLAYLIST_LENGTH:
                messagebox.showerror(
                    "Error",
                        "Maximum number of "
                        f"audio files reached: {MAX_PLAYLIST_LENGTH}")
                return
            method(self)
        return wrapper       
    
    @validate
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
        self.update_file_count_label()
    
    @validate
    def import_folder(self) -> None:
        """Gateway to the import folder toplevel."""
        self.opened_import_window = True
        ImportFolderToplevel(self)
    
    def update_file_count_label(self) -> None:
        """Updates the file count display."""
        self.file_count_label.config(text=f"Files: {len(self.files)}")


class ImportFolderToplevel(tk.Toplevel):
    """
    Popup window to allow the user to import a folder of audio files
    with various configurations.
    """

    def __init__(self, master: CreatePlaylistAudioFrame) -> None:
        super().__init__(master)
        self.title(
            f"{main.DEFAULT_TITLE} - Playlists - Create - Import Folder")
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title_label = tk.Label(
            self, font=inter(30, True), text="Import Folder")
        self.folder_label = tk.Label(self, font=inter(15), text="Folder:")
        # Approximate Windows file length limit is 260 characters.
        self.folder_entry = StringEntry(
            self, max_length=260, state="disabled", disabledforeground=FG,
            initial_value=NOT_SET)
        self.select_folder_button = Button(
            self, "Select", inter(12), command=self.select_folder)
        self.bind("<Control-o>", lambda *_: self.select_folder())

        settings = get_import_folder_settings()
        
        self.file_types_label = tk.Label(
            self, font=inter(15), text="File types to include:")
        self.file_types_input = FileTypesFrame(self, settings["extensions"])

        self.scope_label = tk.Label(self, font=inter(15), text="Search Scope:")
        self.scope_frame = SearchScopeFrame(self, settings["recursive"])

        self.import_button = Button(
            self, "Import", command=self.import_folder, state="disabled")

        self.title_label.grid(row=0, column=0, padx=10, pady=10, columnspan=3)
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.select_folder_button.grid(row=1, column=2, padx=5, pady=5)
        self.file_types_label.grid(
            row=2, column=0, padx=5, pady=5, sticky="ne")
        self.file_types_input.grid(row=2, column=1, columnspan=2, sticky="nw")
        self.scope_label.grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.scope_frame.grid(row=3, column=1, columnspan=2, sticky="nw")
        self.import_button.grid(
            row=4, column=0, columnspan=3, padx=10, pady=10)
    
    def select_folder(self) -> None:
        """Allows the user to select the import folder."""
        folder = filedialog.askdirectory(mustexist=True)
        if not folder:
            # Cancelled
            return
        self.folder_entry.variable.set(folder)
        self.update_button_state()
    
    def import_folder(self) -> None:
        """Validates input and subsequently performs folder input."""
        folder = pathlib.Path(self.folder_entry.value)
        extensions = self.file_types_input.selected
        is_recursive = self.scope_frame.recursive
        try:
            files = self.get_files(folder, set(extensions), is_recursive)
            if not files:
                messagebox.showerror(
                    "Nothing",
                        "No audio files found with the given criteria.")
                return
        except RuntimeError:
            messagebox.showerror(
                "Error",
                    f"Maximum paths scanned: {MAX_PATHS_TO_SCAN}. "
                    "Please reduce the search scope.")
            return
        existing_files = set(self.master.files)
        new = [file for file in files if file not in existing_files]
        if not new:
            messagebox.showerror(
                "Nothing",
                    "No new audio files found with the given criteria.")
            return
        new_file_count = len(existing_files) + len(new)
        if new_file_count > MAX_PLAYLIST_LENGTH:
            messagebox.showerror(
                "Error",
                    "This import will bring the number of files to "
                    f"{new_file_count}, which exceeds the maximum allowed "
                    f"number of files: {MAX_PLAYLIST_LENGTH}")
            return
        already_added_count = len(files) - len(new)
        if already_added_count and not messagebox.askyesnocancel(
            "Duplicates",
                f"{already_added_count} file"
                f"{'s' if already_added_count > 1 else ''} "
                f"{'have' if already_added_count > 1 else 'has'} already been "
                "added, and will not be added again. Proceed?"
        ):
            return
        self.master.files.extend(new)
        self.master.listbox.extend(new)
        self.master.update_file_count_label()
        settings = {"extensions": extensions, "recursive": is_recursive}
        update_import_folder_settings(settings)
        self.close()
    
    def get_files(
        self, folder: pathlib.Path, extensions: set[str], is_recursive: bool
    ) -> list[pathlib.Path]:
        """
        Returns a list of all audio files with the given extensions
        in the path, not case-sensitve.
        """
        generator = folder.iterdir() if not is_recursive else folder.rglob("*")
        files = []
        count = 0
        for path in generator:
            count += 1
            if count > MAX_PATHS_TO_SCAN:
                raise RuntimeError
            if path.is_file() and path.suffix.lower() in extensions:
                files.append(path)
        return files

    def update_button_state(self) -> None:
        """Changes the state of the import button based on basic validation."""
        # Folder selected and at least one audio type selected.
        valid = (
            self.folder_entry.value != NOT_SET
            and self.file_types_input.selected)
        self.import_button.config(state=bool_to_state(valid))
    
    def close(self) -> None:
        """Closes the window."""
        self.destroy()
        self.master.opened_import_window = False


class FileTypesFrame(tk.Frame):
    """Handles the selection of file types to include in the file import."""

    def __init__(
        self, master: ImportFolderToplevel, initial_extensions: list[str]
    ) -> None:
        super().__init__(master)
        # Stores enabled/disabled for each file extension.
        self.states = {
            extension: tk.BooleanVar(value=extension in initial_extensions)
            for extension in ALLOWED_EXTENSIONS
        }
        for i, (extension, variable) in enumerate(self.states.items()):
            checkbutton = Checkbutton(
                self, extension, variable, command=master.update_button_state)
            checkbutton.grid(
                row=i//2, column=i%2, padx=5, pady=5, sticky="w")

    @property
    def selected(self) -> list[str]:
        """Returns the selected extensions."""
        return [
            extension
            for extension, state in self.states.items() if state.get()]


class SearchScopeFrame(tk.Frame):
    """
    Allows the user to make a folder import either
    recursively or non-recursively.
    """

    def __init__(self, master: ImportFolderToplevel, initial: bool) -> None:
        super().__init__(master)
        self.recursive_variable = tk.BooleanVar(value=initial)
        for text, value in (
            ("Recursive (include all sub-folders)", True),
            ("Non-recursive (top-level folder only)", False)
        ):
            radiobutton = Radiobutton(
                self, text, self.recursive_variable, value)
            radiobutton.pack(padx=5, pady=5, anchor="w")
    
    @property
    def recursive(self) -> bool:
        return self.recursive_variable.get()


class FileHandlingFrame(tk.Frame):
    """
    Functionality to allow the user to delete an audio file
    in the playlist or move it up or down.
    """

    def __init__(self, master: CreatePlaylistAudioFrame) -> None:
        super().__init__(master)
        self.delete_button = Button(
            self, "Delete", inter(12), command=self.delete)
        self.move_up_button = Button(
            self, "Move Up", inter(12), command=lambda: self.swap(-1))
        self.move_down_button = Button(
            self, "Move Down", inter(12), command=lambda: self.swap(+1))
        self.update_state()

        self.delete_button.pack(padx=10, pady=5)
        self.move_up_button.pack(padx=10, pady=5)
        self.move_down_button.pack(padx=10, pady=5)
    
    def delete(self) -> None:
        """Removes the currently selected file from the playlist."""
        index = self.master.listbox.current_index
        self.master.files.pop(index)
        self.master.listbox.pop(index)
        if index < self.master.listbox.size:
            self.master.listbox.listbox.selection_set(index)
        self.master.update_file_count_label()
        self.update_state()
    
    def swap(self, index_difference: int) -> None:
        """For swapping two values - used in move up and move down."""
        index = self.master.listbox.current_index
        files = self.master.files
        files[index], files[index + index_difference] = (
            files[index + index_difference], files[index])
        self.master.listbox.swap(index, index + index_difference)
        self.update_state()

    def update_state(self) -> None:
        """Updates button states based on currently selected index."""
        index = self.master.listbox.current_index
        if index is None:
            # Nothing selected.
            self.delete_button.config(state="disabled")
            self.move_up_button.config(state="disabled")
            self.move_down_button.config(state="disabled")
            return
        # Can always delete the currently selected item.
        self.delete_button.config(state="normal")
        # Can move up if index > 0 i.e. index != 0.
        self.move_up_button.config(state=bool_to_state(index))
        # Can move down if element is not the last.
        size = self.master.listbox.size
        self.move_down_button.config(state=bool_to_state(index < size - 1))


class CreatePlaylistButtons(tk.Frame):
    """Bottom buttons for the create playlist."""

    def __init__(self, master: CreatePlaylist) -> None:
        super().__init__(master)
        self.cancel_button = Button(
            self, "Back", inter(20), command=master.back)
        self.create_button = Button(
            self, "Create", inter(20), command=master.create)
        
        self.cancel_button.pack(side="left", padx=5)
        self.create_button.pack(side="right", padx=5)





class ViewPlaylists(tk.Frame):
    """
    Window to view and sort playlists by name, length, ID, and
    date/time created, and allows the user to play/edit/delete these
    playlists.
    """

    def __init__(self, master: "main.AudioPlayer") -> None:
        super().__init__(master)
        master.root.title(f"{main.DEFAULT_TITLE} - Playlists")

        self.title = tk.Label(self, font=inter(30, True), text="Playlists")

        self.table = PlaylistsTable(self)
        playlist_records = load_playlists_overview()
        self.table.extend(playlist_records)

        self.create_playlist_button = Button(
            self, "Create Playlist", command=self.create_playlist)

        self.title.pack(padx=10, pady=5)
        self.table.pack(padx=10, pady=5)
        self.create_playlist_button.pack(padx=10, pady=5)
    
    def create_playlist(self) -> None:
        """Navigates to the create playlist tool of the app."""
        self.master.update_state(CreatePlaylist)


class PlaylistsTable(Table):
    """
    Contains the Treeview serving as the table of playlists.
    Can be sorted by name, length, ID and date/time created.
    Click into a given playlist to expand.
    """

    def __init__(self, master: ViewPlaylists) -> None:
        super().__init__(master, TABLE_COLUMNS)
