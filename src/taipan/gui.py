from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
import sys
import os
import platform


def ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv or [""])
    return app


def select_file(caption="Select a file", directory="", filter_str="All Files (*.*)") -> str:
    ensure_app()
    file_path, _ = QFileDialog.getOpenFileName(
        None, caption, directory, filter_str
    )
    return file_path or ""


def show_info(title: str, message: str) -> None:
    ensure_app()
    box = QMessageBox()
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()


def show_error(title: str, message: str) -> None:
    ensure_app()
    QMessageBox.critical(
        None,
        title,
        message,
        QMessageBox.StandardButton.Ok
    )


def open_file_crossplatform(path: str) -> None:
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
        print(f"Failed to open file '{path}': {e}")