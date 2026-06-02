from PyQt6.QtWidgets import QApplication, QHBoxLayout, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget, QComboBox, QGridLayout, QListWidgetItem, QWidget, QScrollArea, QTextEdit, QSpacerItem, QSizePolicy, QGridLayout

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt6.QtCore import Qt
from taipan.constants.days import ID_TO_SHORT

import sys
import os
import platform
import math 
import threading
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG

# disable native dialog since its too slow on windows
#_FAST_OPTIONS = QFileDialog.Option.DontUseNativeDialog


def ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv or [""])
    return app


def select_file(caption: str = "Select a file",directory: str = "",filter_str: str = "All Files (*.*)") -> str:
    ensure_app()

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        caption,
        directory,
        filter_str,
    )
    return file_path or ""




def select_multi_rsx_files(caption: str = "Select RSX files",directory: str = "",) -> list[str]:
    ensure_app()
    files, _ = QFileDialog.getOpenFileNames(
        None,
        caption,
        directory,
        "RSX Files (*.rsx)",
    )
    return files



def select_option(title: str, message: str, options: list[tuple[str, str]]) -> str | None:
    ensure_app()

    dialog = QDialog()
    dialog.setWindowTitle(title)
    layout = QVBoxLayout()

    label = QLabel(message)
    layout.addWidget(label)

    selected = None

    def on_click(value):
        nonlocal selected
        selected = value
        dialog.accept()

    for display, value in options:
        btn = QPushButton(display)
        btn.clicked.connect(lambda checked, v=value: on_click(v))
        layout.addWidget(btn)

    dialog.setLayout(layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return selected
    else:
        return None


def select_checkboxes(title: str, message: str, options: list[tuple[str, str]], default_values: list[str] | None = None) -> list[str] | None:
    ensure_app()

    dialog = QDialog()
    dialog.setWindowTitle(title)

    dialog.setMinimumWidth(450)  # wider
    # dialog.setMinimumHeight(300) # taller

    layout = QVBoxLayout()
    layout.addWidget(QLabel(message))

    default_values = set(default_values or [])
    checkboxes: list[tuple[QCheckBox, str]] = []
    for display, value in options:
        checkbox = QCheckBox(display)
        if value in default_values:
            checkbox.setChecked(True)
        layout.addWidget(checkbox)
        checkboxes.append((checkbox, value))

    button_box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    dialog.setLayout(layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return [value for checkbox, value in checkboxes if checkbox.isChecked()]
    return None


def show_info_scroll(title: str, message: str) -> None:
    ensure_app()

    
    msg = QMessageBox()
    msg.setWindowTitle(title)

    text = QTextEdit()
    text.setPlainText(message)
    text.setReadOnly(True)
    text.setMinimumWidth(700)      
    text.setMinimumHeight(300)     
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

    # Force a minimum width using a spacer
    spacer = QSpacerItem(400, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    layout = box.layout()
    if isinstance(layout, QGridLayout):
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())

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


_main_window = None

def register_main_window(win):
   global _main_window
   _main_window = win

def call_on_main_thread(func):
   if threading.current_thread() is threading.main_thread():
       return func()
   result = [None]
   def wrapper():
       result[0] = func()
   QMetaObject.invokeMethod(
       _main_window,
       "_invoke_slot",
       Qt.ConnectionType.BlockingQueuedConnection,
       Q_ARG(object, wrapper),
   )
   return result[0]

# wrap existing dialogs
def show_info_safe(title, message):
   call_on_main_thread(lambda: show_info(title, message))
def show_info_scroll_safe(title, message):
   call_on_main_thread(lambda: show_info_scroll(title, message))
def select_option_safe(title, message, options):
   return call_on_main_thread(lambda: select_option(title, message, options))
def show_error_safe(title, message):
   call_on_main_thread(lambda: show_error(title, message))
def select_checkboxes_safe(title, message, options, default_values=None):
   return call_on_main_thread(lambda: select_checkboxes(title, message, options, default_values))
