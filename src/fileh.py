"""Handles file IO, save data and database of the app etc."""
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
                (id integer primary key, name TEXT UNIQUE, description TEXT)
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
            # Non-existent audio files.
            insert_files = [
                file for file in files if
                # Does not exist in the table.
                not cursor.execute(
                    f"""
                    SELECT EXISTS
                    (SELECT * FROM {AUDIO_TABLE} WHERE file_path='{file}') 
                    """).fetchone()[0]
            ]
            cursor.executemany(
                f"""
                INSERT INTO {AUDIO_TABLE} (id, file_path) VALUES (NULL, ?)
                """, ([file] for file in insert_files))
            playlist_id = cursor.execute(
                f"""
                INSERT INTO {PLAYLISTS_TABLE} (id, name, description)
                VALUES (NULL, '{name}', '{description}')
                """
            ).execute(
                f"SELECT id FROM {PLAYLISTS_TABLE} WHERE name='{name}'"
            ).fetchone()[0]
            audio_playlist_records = []
            for position, file in enumerate(files):
                audio_id = cursor.execute(
                    f"SELECT id FROM {AUDIO_TABLE} WHERE file_path='{file}'"
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
                (SELECT * FROM {PLAYLISTS_TABLE} WHERE name='{name}')
                """).fetchone()[0])
    finally:
        connection.close()
