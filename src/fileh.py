"""Handles file IO, save data and database of the app etc."""
import datetime as dt
import json
import pathlib
import sqlite3
from typing import Callable, Any

from utils import APP_FOLDER, ALLOWED_EXTENSIONS


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


def create_playlist(name: str, description: str, files: list[str]) -> None:
    """Creates a playlist the given metadata and audio files."""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.cursor()
            # Obtains Non-existent audio files.
            insert_files = [
                file for file in files if
                # Query - Does not exist in the table.
                # Using double quotes inside to handle single quotes in files.
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
                (audio_id, playlist_id, position)
                VALUES (?, ?, ?)
                """, audio_playlist_records)
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
                length = lengths[record[0]]
                # Converts UTC to local time for display.
                # Also truncates microseconds.
                utc_date_time_created = dt.datetime.fromisoformat(record[2])
                date_time_created = utc_date_time_created.replace(
                    tzinfo=dt.timezone.utc
                ).astimezone(tz=None).replace(microsecond=0, tzinfo=None)
                playlist_overview = (
                    record[0], record[1], length, date_time_created)
                playlists.append(playlist_overview)
            return playlists
    finally:
        connection.close()
