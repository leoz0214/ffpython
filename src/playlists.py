"""Handles playlist creation, playing, viewing, editing and deleting."""
import enum
import pathlib
import random
import tkinter as tk
from contextlib import suppress
from tkinter import filedialog
from tkinter import messagebox
from typing import Callable

import main
from colours import FG
from fileh import (
    get_import_folder_settings, update_import_folder_settings,
    create_playlist, update_playlist, delete_playlist, playlist_exists,
    load_playlists_overview, get_playlist, PlaylistNotFound
)
from utils import (
    inter, open_audio_file, bool_to_state, limit_length,
    ALLOWED_EXTENSIONS, MAX_PLAYLIST_NAME_DISPLAY_LENGTH
)
from widgets import (
    Button, StringEntry, Textbox, Listbox, HorizontalLine, Radiobutton,
    Checkbutton, Table, TableColumn, LoopingFrame
)


MAX_PLAYLIST_NAME_LENGTH = 100
MAX_PLAYLIST_DESCRIPTION_LENGTH = 2000
MIN_PLAYLIST_LENGTH = 2
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
# For the Playlist titles, sets a suitable playlist name font size.
PLAYLIST_NAME_SIZE = {
    50: 20,
    20: 25,
    0: 30
}
# Description when empty.
DEFAULT_DESCRIPTION = "No description provided."
# Common error message whenever a playlist no longer exists.
MISSING_PLAYLIST_ERROR = {
    "title": "Missing Playlist",
    "message": "The target playlist was not found in the database.\n"
               "Perhaps it has been deleted."
}
# Maximum finite number of playlist repeats.
MAX_PLAYLIST_LOOPS = 9


class SortBy(enum.Enum):
    """Possible ways of sorting the playlist table."""
    id = "ID"
    name = "Name"
    length = "Length"
    date_time_created = "Created"


class PlaylistPlayback:
    """
    Stores required playlist information during the playback,
    and also tracks the number of loops and current file being played.
    """

    def __init__(
        self, name: str, files: list[str], loops: None | int | float
    ) -> None:
        self.name = limit_length(name, MAX_PLAYLIST_NAME_DISPLAY_LENGTH)
        self.files = files
        self.loops = loops
        self.position = 0
    
    @property
    def current(self) -> str:
        """Current file."""
        return self.files[self.position]

    @property
    def at_end(self) -> bool:
        """Returns True if on last file or beyond., else False."""
        return self.position >= len(self.files) - 1


class PlaylistForm(tk.Frame):
    """
    Allows the user to create/edit a playlist.
    The technical database term for create or update is: UPSERT.
    Pass in the playlist ID for edit mode, or else create a new playlist.
    """

    def __init__(
        self, master: "main.AudioPlayer", playlist_id: int | None = None,
        from_view_playlists: bool = False
    ) -> None:
        super().__init__(master)
        # Convenient Boolean to indicate whether or not this is create mode.
        self.new = playlist_id is None
        self.playlist_id = playlist_id
        self.from_view_playlists = from_view_playlists
        # 'create' or 'edit' used for string embedding.
        self.keyword = "create" if self.new else "edit"
        if not self.new:
            try:
                initial_data = get_playlist(self.playlist_id)
            except PlaylistNotFound:
                # Playlist no longer exists,
                # likely deleted from another process.
                self.change(confirm=False)
                messagebox.showerror(**MISSING_PLAYLIST_ERROR)
                return
        # Return to view playlists if called from there, makes most sense.
        if self.new:
            master.root.title(f"{main.DEFAULT_TITLE} - Playlist - Create")
        else:
            # Add playlist ID in title to avoid ambiguity.
            master.root.title(
                f"{main.DEFAULT_TITLE} - Playlist - Edit ({playlist_id})")

        self.title = tk.Label(
            self, font=inter(30, True),
            text=f"{self.keyword.title()} Playlist")
        if self.new:
            self.metadata_frame = PlaylistFormMetadataFrame(self)
            self.audio_frame = PlaylistFormAudioFrame(self)
        else:
            # Fill in fields with current data.
            self.metadata_frame = PlaylistFormMetadataFrame(
                self, initial_data.name, initial_data.description)
            self.audio_frame = PlaylistFormAudioFrame(self, initial_data.files)
        self.separator = HorizontalLine(self, width=750)
        self.separator2 = HorizontalLine(self, width=750)
        self.buttons = PlaylistFormButtons(self)
        self.menu = PlaylistFormMenu(self)

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
    
    def upsert(self) -> None:
        """Creates or updates the playlist upon confirmation."""
        name = self.metadata_frame.name
        if not name:
            messagebox.showerror("Empty Name", "Please enter a playlist name.")
            return
        description = self.metadata_frame.description
        # pathlib.Path -> str. Ready to be inserted into DB if needed.
        files = [str(file) for file in self.audio_frame.files]
        # Only makes sense for a playlist to have at least 2 files.
        if len(files) < MIN_PLAYLIST_LENGTH:
            messagebox.showerror(
                "Insufficient Files",
                    "Please ensure the playlist "
                    f"has at least {MIN_PLAYLIST_LENGTH} files.")
            return
        if not self.new and not playlist_exists(self.playlist_id, "id"):
            self.change(confirm=False)
            messagebox.showerror(**MISSING_PLAYLIST_ERROR)
            return
        if playlist_exists(name) and (
            self.new or get_playlist(self.playlist_id).name != name
        ):
            messagebox.showerror(
                "Existing Playlist",
                    "A playlist with the same name (different ID) "
                    "already exists.")
            return
        if not messagebox.askyesnocancel(
            f"Confirm Playlist {self.keyword.title()}",
                f"Are you sure you would like to {self.keyword} this playlist?"
        ):
            return
        # Check one last time playlist exists.
        if not self.new and not playlist_exists(self.playlist_id, "id"):
            self.change(confirm=False)
            messagebox.showerror(**MISSING_PLAYLIST_ERROR)
            return
        # Attempts playlist create/update, shows error message if failed.
        try:
            if self.new:
                create_playlist(name, description, files)
            else:
                update_playlist(self.playlist_id, name, description, files)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to {self.keyword} the playlist: {e}")
            return
        messagebox.showinfo(
            "Success",
                f"Playlist successfully {self.keyword.removesuffix('e')}ed.")
        self.change(confirm=False)
    
    def change(self, command: Callable = None, confirm: bool = True) -> None:
        """Moves back or to another part of the program."""
        # Safeguards in case user accidentally goes back unintentionally.
        if confirm and not messagebox.askyesnocancel(
            "Confirm Back",
                "Are you sure you would no longer like to "
                f"{self.keyword} this playlist? All unsaved data will be lost."
        ):
            return
        for binding in ("Control-o", "control-i"):
            self.master.root.unbind(f"<{binding}>")
        if command is None:
            # By default, return to the main audio player.
            if self.from_view_playlists:
                self.master.view_playlists()
            else:
                self.master.update_state()
        else:
            command()
    

class PlaylistFormMenu(tk.Menu):
    """Toplevel menu for the playlist form of the program.."""

    def __init__(self, master: PlaylistForm) -> None:
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
            label="Back", font=inter(12), command=master.change)
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12),
            command=lambda: main.quit_app(master.master.root))
        self.add_cascade(label="File", menu=self.file_menu)

        self.playlists_menu = tk.Menu(self, tearoff=False)
        self.playlists_menu.add_command(
            label="View", font=inter(12),
            command=lambda: master.change(master.master.view_playlists))
        self.add_cascade(label="Playlists", menu=self.playlists_menu)


class PlaylistFormMetadataFrame(tk.Frame):
    """Handles the name and description of a playlist."""

    def __init__(
        self, master: PlaylistForm, name: str = "", description: str = ""
    ) -> None:
        super().__init__(master)
        self.name_label = tk.Label(
            self, font=inter(15), text="Name of playlist:")
        if not name:
            n = 1
            # Finds the first Playlist {n} name not in use.
            while playlist_exists(f"Playlist {n}"):
                n += 1
            name = f"Playlist {n}"
        self.name_entry = StringEntry(
            self, width=44, max_length=MAX_PLAYLIST_NAME_LENGTH,
            initial_value=name)
        
        self.description_label = tk.Label(
            self, font=inter(15), text="Description (optional):")
        self.description_entry = Textbox(
            self, height=5, max_length=MAX_PLAYLIST_DESCRIPTION_LENGTH)
        self.description_entry.textbox.insert("1.0", description)
    
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


class PlaylistFormAudioFrame(tk.Frame):
    """Handles the input of the audio files to include in the playlist."""

    def __init__(self, master: PlaylistForm, files: list[str] = None) -> None:
        super().__init__(master)
        self.listbox = Listbox(self, height=10, horizontal_scrollbar=True)
        self.add_file_button = Button(self, "Add File", command=self.add_file)
        self.import_folder_button = Button(
            self, "Import Folder", command=self.import_folder)
        self.file_handling_frame = FileHandlingFrame(self)
        self.files = list(map(pathlib.Path, files or []))
        self.file_count_label = tk.Label(
            self, font=inter(20), text=f"Files: {len(self.files)}")
        self.listbox.extend(self.files)
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
        def wrapper(self: "PlaylistFormAudioFrame") -> None:
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

    def __init__(self, master: PlaylistFormAudioFrame) -> None:
        super().__init__(master)
        self.title(f"{master.master.master.master.title()} - Import Folder")
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
        
        self.menu = ImportFolderToplevelMenu(self)

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
        self.config(menu=self.menu)
    
    def select_folder(self) -> None:
        """Allows the user to select the import folder."""
        folder = filedialog.askdirectory(mustexist=True, parent=self)
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
                        "No audio files found with the given criteria.",
                        parent=self)
                return
        except RuntimeError:
            messagebox.showerror(
                "Error",
                    f"Maximum paths scanned: {MAX_PATHS_TO_SCAN}. "
                    "Please reduce the search scope.", parent=self)
            return
        existing_files = set(self.master.files)
        new = [file for file in files if file not in existing_files]
        if not new:
            messagebox.showerror(
                "Nothing",
                    "No new audio files found with the given criteria.",
                    parent=self)
            return
        new_file_count = len(existing_files) + len(new)
        if new_file_count > MAX_PLAYLIST_LENGTH:
            messagebox.showerror(
                "Error",
                    "This import will bring the number of files to "
                    f"{new_file_count}, which exceeds the maximum allowed "
                    f"number of files: {MAX_PLAYLIST_LENGTH}", parent=self)
            return
        already_added_count = len(files) - len(new)
        if already_added_count and not messagebox.askyesnocancel(
            "Duplicates",
                f"{already_added_count} file"
                f"{'s' if already_added_count > 1 else ''} "
                f"{'have' if already_added_count > 1 else 'has'} already been "
                "added, and will not be added again. Proceed?", parent=self
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


class ImportFolderToplevelMenu(tk.Menu):
    """Menu for the import folder toplevel."""

    def __init__(self, master: ImportFolderToplevel) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Select (Ctrl+O)", font=inter(12),
            command=master.select_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Cancel (Alt+F4)", font=inter(12), command=master.close)
        self.add_cascade(label="File", menu=self.file_menu)


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

    def __init__(self, master: PlaylistFormAudioFrame) -> None:
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


class PlaylistFormButtons(tk.Frame):
    """Bottom buttons for the playlist form."""

    def __init__(self, master: PlaylistForm) -> None:
        super().__init__(master)
        self.cancel_button = Button(
            self, "Back", inter(20), command=master.change)
        self.upsert_button = Button(
            self, master.keyword.title(), inter(20), command=master.upsert)
        
        self.cancel_button.pack(side="left", padx=5)
        self.upsert_button.pack(side="right", padx=5)





class ViewPlaylists(tk.Frame):
    """
    Window to view and sort playlists by name, length, ID, and
    date/time created, and allows the user to play/edit/delete these
    playlists.
    """

    def __init__(self, master: "main.AudioPlayer") -> None:
        # Modifies the table columns to match the current table.
        for column in TABLE_COLUMNS:
            column.command = self.get_sort_filter(column)
        super().__init__(master)
        master.root.title(f"{main.DEFAULT_TITLE} - Playlists")
        self.playlist_records = load_playlists_overview()

        self.title = tk.Label(self, font=inter(30, True), text="Playlists")

        if self.playlist_records:
            self.sort_by = None
            self.ascending = True
            self.table = PlaylistsTable(self)
            self.sort(SortBy.name, initial=True)

            # A playlist toplevel is active.
            self.playlist_open = False

            self.info_frame = ViewPlaylistsInfo(self)
            self.separator1 = HorizontalLine(self, 750)

            self.separator2 = HorizontalLine(self, 750)
        else:
            # No playlists.
            self.no_playlists_label = tk.Label(
                self, font=inter(25),
                text="No playlists found.\nCreate a playlist to get started!")
        self.navigation_frame = ViewPlaylistsButtons(self)

        self.menu = ViewPlaylistsMenu(self)

        self.title.pack(padx=10, pady=3)
        if self.playlist_records:
            self.info_frame.pack(padx=10, pady=3)
            self.separator1.pack(padx=10, pady=3)
            self.table.pack(padx=10, pady=3)
            self.separator2.pack(padx=10, pady=3)
        else:
            self.no_playlists_label.pack(padx=10, pady=25)
        self.navigation_frame.pack(padx=10, pady=3)
        master.root.config(menu=self.menu)
    
    def create_playlist(self) -> None:
        """Navigates to the create playlist tool of the app."""
        self.master.update_state(
            lambda master: PlaylistForm(master, from_view_playlists=True))
    
    def get_sort_filter(self, column: TableColumn) -> Callable:
        """Returns the sort filter for a given column."""
        return lambda: self.sort(getattr(SortBy, column.id))
    
    def sort(
        self, sort_by: SortBy, initial: bool = False, update: bool = False
    ) -> None:
        """
        Sorts the playlist records as required.
        The initial flag indicates if the method is called from __init__.
        The update flag indicates if the method is called by the program
        at a later point such as after deleting a playlist.
        """
        self.table.clear()
        sort_functions = {
            SortBy.id: lambda playlist: playlist[0],
            SortBy.name: lambda playlist: playlist[1].lower(),
            SortBy.length: lambda playlist: playlist[2],
            SortBy.date_time_created: lambda playlist: playlist[3]
        }
        if sort_by == self.sort_by:
            if not update:
                # Same filter reversed, only if not from the program.
                self.ascending = not self.ascending
        else:
            # Changed filter - ascending by default.
            self.ascending = True
        if initial:
            # Sorts the playlist records in place.
            self.playlist_records.sort(
                key=sort_functions[sort_by], reverse=not self.ascending)
        else:
            # Also updates the playlist records in the process.
            self.playlist_records = sorted(
                load_playlists_overview(), key=sort_functions[sort_by],
                reverse=not self.ascending)
            if not self.playlist_records:
                # Refresh and display the no playlists screen.
                self.master.view_playlists()
                return
        self.table.extend(self.playlist_records)
        self.sort_by = sort_by
        # Only need to update the sort by display if already existent.
        if not initial:
            self.info_frame.update_total_playlists()
            self.info_frame.update_sort_by()
    
    def home(self) -> None:
        """Returns back to the main app."""
        self.master.update_state()
    
    def open_playlist(self) -> None:
        """Opens the toplevel for a given playlist."""
        if self.playlist_open:
            # Toplevel already open, do not allow another.
            return
        with suppress(IndexError):
            playlist_id = int(self.table.get()[0])
            PlaylistToplevel(self, playlist_id)
            self.playlist_open = True


class ViewPlaylistsMenu(tk.Menu):
    """Toplevel menu for the view playlists part of the program."""

    def __init__(self, master: ViewPlaylists) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Home", font=inter(12), command=master.home)
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12), command=main.quit_app)
        self.add_cascade(label="File", menu=self.file_menu)

        self.playlists_menu = tk.Menu(self, tearoff=False)
        self.playlists_menu.add_command(
            label="Create", font=inter(12),
            command=master.master.create_playlist)
        self.add_cascade(label="Playlists", menu=self.playlists_menu)


class PlaylistsTable(Table):
    """
    Contains the Treeview serving as the table of playlists.
    Can be sorted by name, length, ID and date/time created.
    Click into a given playlist to expand.
    """

    def __init__(self, master: ViewPlaylists) -> None:
        super().__init__(master, TABLE_COLUMNS)
        self.treeview.bind(
            "<<TreeviewSelect>>", lambda *_: master.open_playlist())


class ViewPlaylistsInfo(tk.Frame):
    """Provides information about the playlists and current sort by."""

    def __init__(self, master: ViewPlaylists) -> None:
        super().__init__(master)
        self.count_label = tk.Label(
            self, font=inter(15), width=30,
            text=f"Total Playlists: {len(master.playlist_records)}")
        self.sort_by_label = tk.Label(self, font=inter(15), width=30)
        self.update_sort_by()
        self.count_label.pack(padx=10, side="left")
        self.sort_by_label.pack(padx=10, side="right")
    
    def update_sort_by(self) -> None:
        """Updates the sort by display."""
        arrow = "↑" if self.master.ascending else "↓"
        self.sort_by_label.config(
            text=f"Sorted By: {self.master.sort_by.value} ({arrow})")
    
    def update_total_playlists(self) -> None:
        """Updates the total number of playlists."""
        self.count_label.config(
            text=f"Total Playlists: {len(self.master.playlist_records)}")


class ViewPlaylistsButtons(tk.Frame):
    """Button navigation of the view playlists section."""

    def __init__(self, master: ViewPlaylists) -> None:
        super().__init__(master)
        self.home_button = Button(self, "Home", command=master.home)
        self.create_playlist_button = Button(
            self, "Create Playlist", command=master.create_playlist)

        self.home_button.pack(padx=10, pady=5, side="left")
        self.create_playlist_button.pack(padx=10, pady=5, side="right")


class PlaylistToplevel(tk.Toplevel):
    """
    Window which displays information about a given playlist in detail,
    allowing the playlist to be edited, deleted, cleaned, and of course,
    played.
    """

    def __init__(self, master: ViewPlaylists, playlist_id: int) -> None:
        try:
            self.data = get_playlist(playlist_id)
        except PlaylistNotFound:
            messagebox.showerror(**MISSING_PLAYLIST_ERROR)
            master.sort(master.sort_by, update=True)
            return
        super().__init__(master)
        self.title(f"{main.DEFAULT_TITLE} - Playlist - {self.data.name}")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close)
        # Sets an appropriate playlist name size based on name length.
        for length, size in PLAYLIST_NAME_SIZE.items():
            if len(self.data.name) >= length:
                break 
        self.name_label = tk.Label(
            self, font=inter(size, True), text=self.data.name, wraplength=1000)
        self.metadata_label = tk.Label(self, font=inter(15))
        self.update_metadata_text()
        self.description_text = Textbox(self, width=100, height=5)
        self.description_text.text = (
            self.data.description or DEFAULT_DESCRIPTION)
        self.description_text.textbox.config(state="disabled")

        self.separator1 = HorizontalLine(self, 750)
        self.files_listbox = Listbox(
            self, width=100, height=10, horizontal_scrollbar=True)
        self.update_files_listbox()
        self.separator2 = HorizontalLine(self, 750)
        self.buttons = PlaylistButtons(self)

        self.name_label.pack(padx=10, pady=3)
        self.metadata_label.pack(padx=10, pady=3)
        self.description_text.pack(padx=10, pady=3)
        self.separator1.pack(padx=10, pady=3)
        self.files_listbox.pack(padx=10, pady=3)
        self.separator2.pack(padx=10, pady=3)
        self.buttons.pack(padx=10, pady=3)
    
    def play(self) -> None:
        """Proceeds to prepare playlist playback."""
        self.master.master.update_state(
            lambda master: PlaylistPlayFrame(master, self.data.id))
    
    def edit(self) -> None:
        """Proceeds to the playlist form to edit this playlist."""
        # Destroys toplevel and closes view playlists.
        self.destroy()
        self.master.master.update_state(
            lambda master: PlaylistForm(master, self.data.id, True))
    
    def delete(self, confirm: bool = True) -> None:
        """Deletes the playlist, perhaps upon user confirmation."""
        if confirm and not messagebox.askyesnocancel(
            "Confirm Delete Playlist",
                "Are you sure you would like to delete this playlist?\n"
                "Once deleted, a playlist CANNOT be restored.",
            icon="warning", parent=self
        ):
            return
        try:
            if not playlist_exists(self.data.id, "id"):
                messagebox.showinfo(
                    "Playlist Already Deleted",
                        "The playlist has already been deleted.", parent=self)
            else:
                delete_playlist(self.data.id)
                messagebox.showinfo(
                    "Success",
                        "Successfully deleted the playlist.", parent=self)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to delete the playlist: {e}", parent=self)
            return
        self.close()
        self.master.sort(self.master.sort_by, update=True)
    
    def clean(self) -> None:
        """
        Removes no longer existing files in a playlist upon confirmation.
        If the playlist length drops below 2, ask user to confirm delete
        the playlist since playlists shorter than length 2 are disallowed.
        """
        if not messagebox.askyesnocancel(
            "Confirm Clean Playlist",
                "Are you sure you would like to remove no longer existing "
                "files from the playlist?", parent=self
        ):
            return
        # Retrieves an up-to-date version of the data in case
        # of changes from another process.
        try:
            self.data = get_playlist(self.data.id)
        except PlaylistNotFound:
            self.close()
            self.master.sort(self.master.sort_by, update=True)
            messagebox.showerror(**MISSING_PLAYLIST_ERROR, parent=self)
        old_length = len(self.data.files)
        # Determines new files.
        files = [
            file for file in self.data.files if pathlib.Path(file).is_file()]
        new_length = len(files)
        if new_length == old_length:
            # No length change, no action needed.
            messagebox.showinfo(
                "No Missing Files",
                    "All files in the playlist still exist.", parent=self)
            return
        if len(files) < MIN_PLAYLIST_LENGTH:
            if not messagebox.askyesnocancel(
                "Confirm Delete Playlist",
                    "Upon cleaning, the playlist length falls to "
                    f"{new_length}, below the minimum length of "
                    f"{MIN_PLAYLIST_LENGTH}.\nTherefore, the playlist can "
                    "only be deleted. Are you sure you would like to proceed?",
                icon="warning", parent=self
            ):
                return
            self.delete(confirm=False)
            return
        # Simply updates data but changes the files.
        update_playlist(
            self.data.id, self.data.name, self.data.description, files)
        # Yet again updates data.
        self.data = get_playlist(self.data.id)
        messagebox.showinfo(
            "Success",
                "The playlist was successfully cleaned and reduced from "
                f"{old_length} to {new_length} files.", parent=self)
        self.update_metadata_text()
        self.update_files_listbox()

    def update_metadata_text(self) -> None:
        """Updates the metadata information label."""
        metadata_text = (
            f"Playlist ID: {self.data.id} | "
            f"Created: {self.data.date_time_created} | "
            f"Length: {len(self.data.files)}")
        self.metadata_label.config(text=metadata_text)
    
    def update_files_listbox(self) -> None:
        """Updates the listbox of playlist files."""
        self.files_listbox.clear()
        # Pad all file numbers to the number of digits of the
        # maximum file number.
        zfill = len(str(len(self.data.files)))
        self.files_listbox.extend(
            f"{str(i).zfill(zfill)} | {file}"
            for i, file in enumerate(self.data.files, 1))
    
    def close(self) -> None:
        """Closes this playlist's toplevel."""
        self.destroy()
        self.master.playlist_open = False


class PlaylistButtons(tk.Frame):
    """
    Buttons which allow a given playlist to be
    edited, deleted, cleaned and played.
    """

    def __init__(self, master: PlaylistToplevel) -> None:
        super().__init__(master)
        self.play_button = Button(self, "Play", inter(25), command=master.play)
        self.edit_button = Button(self, "Edit", inter(12), command=master.edit)
        self.clean_button = Button(
            self, "Clean", inter(12), command=master.clean)
        self.delete_button = Button(
            self, "Delete", inter(12), command=master.delete)

        self.play_button.grid(
            row=0, column=0, rowspan=3, padx=(200, 100), pady=5, sticky="w")
        self.edit_button.grid(row=0, column=1, padx=10, pady=2)
        self.clean_button.grid(row=1, column=1, padx=10, pady=2)
        self.delete_button.grid(row=2, column=1, padx=10, pady=2)


class PlaylistPlayFrame(tk.Frame):
    """
    Allows the user to confirm playlist playback and perhaps
    also set the number of playlist loops.
    The audio files can also be shuffled in case order never mattered.
    """

    def __init__(self, master: "main.AudioPlayer", playlist_id: int) -> None:
        try:
            self.data = get_playlist(playlist_id)
        except PlaylistNotFound:
            master.view_playlists()
            messagebox.showerror(**MISSING_PLAYLIST_ERROR)
            return
        super().__init__(master)
        self.original_order = self.data.files.copy()
        master.root.title(
            f"{main.DEFAULT_TITLE} - Playlist - {self.data.name} - Play")
        for length, size in PLAYLIST_NAME_SIZE.items():
            if len(self.data.name) >= length:
                break
        self.title = tk.Label(
            self, font=inter(size, True), text=self.data.name, wraplength=1000)
        self.length_label = tk.Label(
            self, font=inter(15), text=f"Files: {len(self.data.files)}")
        self.separator1 = HorizontalLine(self, 750)
        self.listbox = Listbox(
            self, width=100, height=12, horizontal_scrollbar=True)
        self.fill_listbox(self.data.files)
        self.settings_frame = PlaylistPlaySettingsFrame(self)
        self.separator2 = HorizontalLine(self, 750)
        self.buttons = PlaylistPlayButtons(self)
        self.menu = PlaylistPlayMenu(self)

        master.root.bind("<Control-r>", lambda *_: self.reset_order())
        master.root.bind("<Control-s>", lambda *_: self.shuffle())

        self.title.pack(padx=5, pady=2)
        self.length_label.pack(padx=5, pady=2)
        self.separator1.pack(padx=5, pady=2)
        self.listbox.pack(padx=5, pady=2)
        self.settings_frame.pack(padx=5, pady=2)
        self.separator2.pack(padx=5, pady=2)
        self.buttons.pack(padx=5, pady=2)
        master.root.config(menu=self.menu)
    
    def fill_listbox(self, files: list[str]) -> None:
        """Fills the listbox with the given files."""
        self.listbox.clear()
        zfill = len(str(len(files)))
        self.listbox.extend(
            f"{str(i).zfill(zfill)} | {file}"
            for i, file in enumerate(files, 1))
    
    def reset_order(self) -> None:
        """Resets the order of the files back to the original."""
        if self.settings_frame.reset_order_button["state"] == "disabled":
            # Button disabled, also cannot access through keybind.
            return
        self.data.files[:] = self.original_order
        self.fill_listbox(self.data.files)
        self.settings_frame.update_reset_order_state()
        self.menu.update_state()
    
    def shuffle(self) -> None:
        """Shuffles the order of the files."""
        random.shuffle(self.data.files)
        self.fill_listbox(self.data.files)
        self.settings_frame.update_reset_order_state()
        self.menu.update_state()
    
    def unbind_keybinds(self) -> None:
        """Unbinds the keybinds."""
        for keybind in ("Control-r", "Control-s"):
            self.master.root.unbind(f"<{keybind}>")
    
    def back(self) -> None:
        """Cancels playback and returns to view playlists."""
        if not messagebox.askyesnocancel(
            "Confirm Back",
                "Are you sure you would no longer like to play this playlist?"
        ):
            return
        self.unbind_keybinds()
        self.master.view_playlists()
    
    def start(self) -> None:
        """Starts the playlist playback."""
        self.unbind_keybinds()
        loops = self.settings_frame.looping_frame.loops
        playlist = PlaylistPlayback(self.data.name, self.data.files, loops)
        self.master.start_playlist(playlist)


class PlaylistPlayMenu(tk.Menu):
    """Toplevel menu for the playlist playback preparation window."""

    def __init__(self, master: PlaylistPlayFrame) -> None:
        super().__init__(master)
        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(
            label="Reset Order (Ctrl+R)", font=inter(12),
            command=master.reset_order)
        self.file_menu.add_command(
            label="Shuffle (Ctrl+S)", font=inter(12), command=master.shuffle)
        self.file_menu.add_command(
            label="Start", font=inter(12), command=master.start)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Back", font=inter(12), command=master.back)
        self.file_menu.add_command(
            label="Close App (Alt+F4)", font=inter(12), command=main.quit_app)
        self.add_cascade(label="File", menu=self.file_menu)
    
    def update_state(self) -> None:
        """Updates the Reset Order option state as per the button state."""
        self.file_menu.entryconfig(
            0, state=self.master.settings_frame.reset_order_button["state"])


class PlaylistPlaySettingsFrame(tk.Frame):
    """
    Options allowing the user to shuffle/reset to default
    the order of a playlist and also set the number of playlist loops.
    """

    def __init__(self, master: PlaylistPlayFrame) -> None:
        super().__init__(master)
        self.reset_order_button = Button(
            self, "Reset Order", state="disabled", command=master.reset_order)
        self.shuffle_button = Button(self, "Shuffle", command=master.shuffle)
        self.looping_frame = LoopingFrame(self, MAX_PLAYLIST_LOOPS)

        self.reset_order_button.pack(padx=5, pady=3, side="left")
        self.shuffle_button.pack(padx=5, pady=3, side="left")
        self.looping_frame.pack(padx=(100, 5), side="right", anchor="e")
    
    def update_reset_order_state(self) -> None:
        """
        Updates the state of the reset order button:
        disabled if already in original order.
        """
        self.reset_order_button.config(
            state=bool_to_state(
                self.master.data.files != self.master.original_order))


class PlaylistPlayButtons(tk.Frame):
    """Either starts the playlist or cancels playback."""

    def __init__(self, master: PlaylistPlayFrame) -> None:
        super().__init__(master)
        self.back_button = Button(
            self, "Back", inter(20), command=master.back)
        self.start_button = Button(
            self, "Start", inter(20), command=master.start)
        self.back_button.pack(padx=5, pady=3, side="left")
        self.start_button.pack(padx=5, pady=3, side="right")
