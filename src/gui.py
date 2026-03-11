# qt_helpers.py
import sys
import os
import platform
from typing import Optional

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox


def ensure_app() -> "QApplication":
    """
    Ensure a QApplication exists and return it.
    """
    app = QApplication.instance()
    if app is None:
        # Create without showing any window.
        app = QApplication(sys.argv or [""])
    return app



def select_file(caption="Select a file", directory="", filter_str="All Files (*.*)") -> str:
    app = ensure_app()

    # ---- CRITICAL FIX ----
    # Process events so the dialog actually shows on Windows
    app.processEvents()

    dialog = QFileDialog()
    dialog.setWindowTitle(caption)
    dialog.setDirectory(directory)
    dialog.setNameFilter(filter_str)

    if dialog.exec_():  # User clicked OK
        selected = dialog.selectedFiles()[0]
        return selected
    return ""



def show_info(title: str, message: str) -> None:
    """
    Show an informational message box.
    """
    ensure_app()
    QMessageBox.information(None, title, message, QMessageBox.Ok)


def show_error(title: str, message: str) -> None:
    """
    Show an error message box.
    """
    ensure_app()
    QMessageBox.critical(None, title, message, QMessageBox.Ok)


def open_file_crossplatform(path: str) -> None:
    """
    Open a file or URL with the default associated application across platforms.
    Replaces Windows-only os.startfile.
    """
    if not path:
        return

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system == "Darwin":
            os.spawnlp(os.P_NOWAIT, "open", "open", path)
        else:
            os.spawnlp(os.P_NOWAIT, "xdg-open", "xdg-open", path)
    except Exception as e:
        # Non-fatal: log to stdout as a fallback
        print(f"Failed to open file '{path}': {e}")