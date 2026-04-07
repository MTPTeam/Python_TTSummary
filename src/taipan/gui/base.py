from PyQt6.QtWidgets import QApplication, QHBoxLayout, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget, QComboBox, QGridLayout, QListWidgetItem, QWidget, QScrollArea, QTextEdit

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt6.QtCore import Qt
from taipan.constants.days import ID_TO_SHORT

import sys
import os
import platform
import math 

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


def select_multi_rsx_files(caption: str = "Select RSX files",directory: str = "") -> list[str]:
    ensure_app()

    files, _ = QFileDialog.getOpenFileNames(None,caption,directory,"RSX Files (*.rsx);;All Files (*.*)")
    return files or []


def show_info_scroll(title: str, message: str) -> None:
    ensure_app()

    
    msg = QMessageBox()
    msg.setWindowTitle(title)

    text = QTextEdit()
    text.setPlainText(message)
    text.setReadOnly(True)
    text.setMinimumWidth(700)      # ✅ control width
    text.setMinimumHeight(300)     # ✅ prevent tiny box
    text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    msg.layout().addWidget(text, 0, 0, 1, msg.layout().columnCount())

    msg.exec()


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

