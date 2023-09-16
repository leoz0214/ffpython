"""Handles file IO, save data of the app etc."""
import json
import pathlib
from typing import Callable, Any

from utils import APP_FOLDER, ALLOWED_EXTENSIONS


DATA_FOLDER = APP_FOLDER / "data"
# Last used import folder settings.
IMPORT_FOLDER_SETTINGS = DATA_FOLDER / "import_folder_settings.json"


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
