"""Convenient script to convert the app to a standalone EXE."""
import os
import pathlib
import subprocess


FOLDER = pathlib.Path(__file__).parent
ICON = FOLDER / "images" / "icon.ico"
ADD_DATA = (
    FOLDER / "bin",
    FOLDER / "font",
    FOLDER / "images"
)
SRC_FOLDER = FOLDER / "src"
SCRIPT = FOLDER / "ffpython.py"

CONVERSION_FOLDER = FOLDER / "exe_conversion"
CONVERSION_FOLDER.mkdir(exist_ok=True)
os.chdir(CONVERSION_FOLDER)


def main() -> None:
    """Main procedure of the utility script."""
    arguments = ["pyinstaller", "--noconfirm", "--onefile", "--windowed"]
    arguments.extend(("--icon", str(ICON)))
    for folder in ADD_DATA:
        arguments.extend(("--add-data", f"{folder};{folder.name}/"))
    arguments.extend(("--paths", str(SRC_FOLDER)))
    arguments.append(str(SCRIPT))
    subprocess.run(arguments)


if __name__ == "__main__":
    main()
