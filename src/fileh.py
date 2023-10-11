"""Handles file IO, save data and database of the app etc."""
import datetime as dt
import json
import pathlib
import sqlite3
from collections import namedtuple
from typing import Callable, Iterable, Any

from utils import (
    APP_FOLDER, ALLOWED_EXTENSIONS, MAX_PLAYLIST_NAME_DISPLAY_LENGTH,
    limit_length
)


DATA_FOLDER = APP_FOLDER / "data"
# Last used import folder settings.
IMPORT_FOLDER_SETTINGS = DATA_FOLDER / "import_folder_settings.json"
# Database of the app, including playlist data.
DATABASE_PATH = DATA_FOLDER / "database.db"
# Audio file paths in the DB.
AUDIO_TABLE = "audio"
# Playlists metdata in the DB.
PLAYLISTS_TABLE = "playlists"
# Audio/playlists table. Removes m2m.
AUDIO_PLAYLISTS_TABLE = "audio_playlists"

# Playlist object.
Playlist = namedtuple(
    "Playlist", ("id", "name", "description", "files", "date_time_created"))


def create_folder(folder: pathlib.Path = DATA_FOLDER) -> None:
    """Decorator to ensure a folder is created if necessary."""
    def inner(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            folder.mkdir(parents=True, exist_ok=True)
            return func(*args, **kwargs)
        return wrapper
    return inner


def get_import_folder_settings() -> dict:
    """Fetches previous import folder settings or default."""
    try:
        with IMPORT_FOLDER_SETTINGS.open("r", encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"extensions": ALLOWED_EXTENSIONS, "recursive": True}
    

@create_folder()
def update_import_folder_settings(settings: dict) -> None:
    """Updates import folder settings upon a new import."""
    with IMPORT_FOLDER_SETTINGS.open("w", encoding="utf8") as f:
        json.dump(settings, f)


@create_folder()
def set_up_database() -> None:
    """Sets up the database to ensure it is ready to be used."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            # Creates required tables if they do not exists.
            # Playlists table: ID, name (unique), description.
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {PLAYLISTS_TABLE}
                (id integer primary key, name TEXT UNIQUE,
                    description TEXT, utc_date_time_created DATETIME)
                """
            )
            # Audio files table: ID, file path.
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {AUDIO_TABLE}(id integer primary key, file_path TEXT)
                """
            )
            # Audio/Playlists table: audio ID, playlist ID, position.
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS
                {AUDIO_PLAYLISTS_TABLE}(audio_id, playlist_id, position)
                """
            )
    finally:
        connection.close()


def insert_new_audio_files(cursor: sqlite3.Cursor, files: list[str]) -> None:
    """Inserts all new audio files to the audio table."""
    insert_files = [
        file for file in files if
        # Query - Does not exist in the table.
        not cursor.execute(
            f"""
            SELECT EXISTS
            (SELECT * FROM {AUDIO_TABLE} WHERE file_path=?) 
            """, (file,)).fetchone()[0]
    ]
    cursor.executemany(
        f"""
        INSERT INTO {AUDIO_TABLE} (id, file_path) VALUES (NULL, ?)
        """, ([file] for file in insert_files))


def insert_playlist_audio_records(
    cursor: sqlite3.Cursor, playlist_id: int, files: list[str]
) -> None:
    """
    Inserts the playlist/audio records with playlist/audio ID and position.
    """
    audio_playlist_records = []
    for position, file in enumerate(files):
        audio_id = cursor.execute(
            f"SELECT id FROM {AUDIO_TABLE} WHERE file_path=?", (file,)
        ).fetchone()[0]
        record = (audio_id, playlist_id, position)
        audio_playlist_records.append(record)
    cursor.executemany(
        f"""
        INSERT INTO {AUDIO_PLAYLISTS_TABLE}
        (audio_id, playlist_id, position) VALUES (?, ?, ?)
        """, audio_playlist_records)


def delete_old_audio_ids(
    cursor: sqlite3.Cursor, audio_ids: Iterable[int]
) -> None:
    """
    Checks audio IDs to see if they are still referenced in the
    Audio/Playlist table, otherwise deletes the corresponding record.
    This function should only be on audio IDs that have been cut
    of from a playlist after playlist update or deletion.
    """
    to_delete = [
        audio_id for audio_id in audio_ids
        if not bool(cursor.execute(
            f"""
            SELECT EXISTS
            (SELECT * FROM {AUDIO_PLAYLISTS_TABLE} WHERE audio_id=?)
            """, (audio_id,)).fetchone()[0])
    ]
    cursor.executemany(
        f"DELETE FROM {AUDIO_TABLE} WHERE id=?",
        ([audio_id] for audio_id in to_delete))


def create_playlist(name: str, description: str, files: list[str]) -> None:
    """Creates a playlist with the given metadata and audio files."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            insert_new_audio_files(cursor, files)
            date_time_created = dt.datetime.utcnow().isoformat()
            playlist_id = cursor.execute(
                f"""
                INSERT INTO {PLAYLISTS_TABLE}
                (id, name, description, utc_date_time_created)
                VALUES (NULL, ?, ?, ?)
                """, (name, description, date_time_created)
            ).execute(
                f"SELECT id FROM {PLAYLISTS_TABLE} WHERE name=?", (name,)
            ).fetchone()[0]
            insert_playlist_audio_records(cursor, playlist_id, files)
    finally:
        connection.close()


def get_audio_ids(cursor: sqlite3.Cursor, playlist_id: int) -> set[int]:
    """Returns a set of audio IDs for a given playlist."""
    return set(
        record[0] for record in cursor.execute(
            f"""
            SELECT audio_id FROM {AUDIO_PLAYLISTS_TABLE}
            WHERE playlist_id=?
            """, (playlist_id,)))


def update_playlist(
    playlist_id: int, name: str, description: str, files: list[str]
) -> None:
    """Updates a given playlist based on ID."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            # Updates the playlist itself.
            cursor.execute(
                f"""
                UPDATE {PLAYLISTS_TABLE} SET
                name=?, description=? WHERE id=?
                """, (name, description, playlist_id))
            insert_new_audio_files(cursor, files)
            # Updates the playlist/audio records.
            # Obtains old audio IDs in playlist.
            old_audio_ids = get_audio_ids(cursor, playlist_id)
            # Deletes old playlist/audio records.
            cursor.execute(
                f"DELETE FROM {AUDIO_PLAYLISTS_TABLE} WHERE playlist_id=?",
                (playlist_id,))
            insert_playlist_audio_records(cursor, playlist_id, files)
            # Obtains new audio IDs in playlist.
            new_audio_ids = get_audio_ids(cursor, playlist_id)
            # Checks any no longer used audio IDs and deletes
            # them if possible, to save space.
            delete_old_audio_ids(cursor, old_audio_ids - new_audio_ids)
    finally:
        connection.close()


def playlist_exists(name: str) -> bool:
    """Returns True if a playlist with a given name exists, else False."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            return bool(cursor.execute(
                f"""
                SELECT EXISTS
                (SELECT * FROM {PLAYLISTS_TABLE} WHERE name=?)
                """, (name,)).fetchone()[0])
    finally:
        connection.close()


def parse_date_time_created(utc_date_time: str) -> dt.datetime:
    """
    Converts a UTC time string to a local time datetime object
    with microseconds stripped, to output as a date time created.
    """
    utc_date_time_created = dt.datetime.fromisoformat(utc_date_time)
    return utc_date_time_created.replace(
        tzinfo=dt.timezone.utc
    ).astimezone(tz=None).replace(microsecond=0, tzinfo=None)


def load_playlists_overview() -> list[tuple]:
    """
    Returns all basic playlist records from the database.
    Fields: ID, name, length, date/time created.
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            playlist_records = cursor.execute(
                f"""
                SELECT id, name, utc_date_time_created FROM {PLAYLISTS_TABLE}
                """).fetchall()
            audio_playlist_ids = cursor.execute(
                f"SELECT playlist_id FROM {AUDIO_PLAYLISTS_TABLE}"
            ).fetchall()
            lengths = {}
            for playlist_id in audio_playlist_ids:
                # Using index 0 to access the value in the 1-tuple.
                lengths[playlist_id[0]] = lengths.get(playlist_id[0], 0) + 1
            playlists = []
            for record in playlist_records:
                playlist_id = record[0]
                name = limit_length(
                    record[1], MAX_PLAYLIST_NAME_DISPLAY_LENGTH)
                length = lengths[playlist_id]
                date_time_created = parse_date_time_created(record[2])
                playlist_overview = (
                    playlist_id, name, length, date_time_created)
                playlists.append(playlist_overview)
            return playlists
    finally:
        connection.close()


def get_playlist(playlist_id: int) -> Playlist:
    """Returns full playlist data, including each file in the playlist."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            record = cursor.execute(
                f"SELECT * FROM {PLAYLISTS_TABLE} WHERE id=?", (playlist_id,)
            ).fetchone()
            playlist_id = record[0]
            name = record[1]
            description = record[2]
            date_time_created = parse_date_time_created(record[3])
            file_records = cursor.execute(
                f"""
                SELECT audio_id, position FROM {AUDIO_PLAYLISTS_TABLE}
                WHERE playlist_id=?
                """, (playlist_id,)).fetchall()
            # Ensures file records are in the correct order/position.
            # They should be, but just to be sure.
            file_records.sort(key=lambda record: record[1])
            # Gets corresponding file paths now.
            files = [
                cursor.execute(
                    f"SELECT file_path FROM {AUDIO_TABLE} WHERE id=?", 
                    (audio_id,)
                ).fetchone()[0] for audio_id, _ in file_records]
            return Playlist(
                playlist_id, name, description, files, date_time_created)
    finally:
        connection.close()
