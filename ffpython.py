"""Run this script to start the app up."""
import pathlib
import sys


if hasattr(sys, "_MEIPASS"):
    SRC_FOLDER = pathlib.Path(sys._MEIPASS) / "src"
else:
    SRC_FOLDER = pathlib.Path(__file__).parent / "src"
sys.path.append(str(SRC_FOLDER))


from src import main


if __name__ == "__main__":
    main.main()
