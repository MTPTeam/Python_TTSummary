from PyQt6.QtWidgets import QApplication, QHBoxLayout, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget, QComboBox, QGridLayout, QListWidgetItem, QWidget, QScrollArea

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt6.QtCore import Qt
from taipan.constants.days import ID_TO_SHORT


class BlockButton(QPushButton):
    def __init__(self, block: str, dialog):
        super().__init__(str(block))
        self.block = block
        self.dialog = dialog

        self.setCheckable(True)
        self.setFixedSize(65, 30)
        self.setFont(QFont("Calibri", 12))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.dialog.handle_range_click(self.block)
        else:
            super().mousePressEvent(event)



class SliceDialog(QDialog):
    def __init__(self, available_blocks: list[str]):
        super().__init__()
        self.setWindowTitle("RSX Slicer")
        
        self.range_start: str | None = None

        
        self.blocks: list[str] = []
        self.days: list[str] = []
        self.block_buttons: dict[str, QPushButton] = {}

        main_layout = QVBoxLayout()

        blocks_label = QLabel("Select Blocks")
        blocks_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(blocks_label)

        # display blocks in a scroll area
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(4)

        cols = 15
        self.setMinimumWidth(cols * 72 + 30) #dynamically adjust based on columns

        for i, block in enumerate(available_blocks):
            btn = BlockButton(block, self)
            btn.toggled.connect(lambda checked, b=block: self._toggle_block(b, checked))
            
            self.block_buttons[block] = btn     
            grid.addWidget(btn, i // cols, i % cols) 


        # init scroll area for bounded gui box
        scroll = QScrollArea()
        scroll.setWidget(grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)

        # days
        days_label = QLabel("Select Days")
        days_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(days_label)

        day_layout = QHBoxLayout()
        self.day_boxes = {k: QCheckBox(ID_TO_SHORT[k]) for k in ['120', '4', '2', '1']}
        for cb in self.day_boxes.values():
            cb.setFont(QFont("Calibri", 14))
            day_layout.addWidget(cb)
        main_layout.addLayout(day_layout)

        # Done
        done_btn = QPushButton("Done")
        done_btn.setFont(QFont("Calibri", 12))
        done_btn.clicked.connect(self._accept)
        main_layout.addWidget(done_btn)

        self.setLayout(main_layout)

    def _toggle_block(self, block: str, checked: bool):
        btn = self.block_buttons[block]

        base = "background-color: #4CAF50; color: white;" if checked else ""
        
        # preserve range-start border if present
        if block == self.range_start:
            base += " border: 2px solid orange;"

        btn.setStyleSheet(base)

    def _accept(self):
        self.blocks = [b for b, btn in self.block_buttons.items() if btn.isChecked()]
        self.days = [key for key, cb in self.day_boxes.items() if cb.isChecked()]
        self.accept()

    def handle_range_click(self, block: str):
        blocks = list(self.block_buttons.keys())

        # First click → store start
        if self.range_start is None:
            self.range_start = block
            # optional visual indicator
            self.block_buttons[block].setStyleSheet("border: 2px solid orange;")
            return

        # Second click → select range
        start_idx = blocks.index(self.range_start)
        end_idx = blocks.index(block)

        lo, hi = sorted([start_idx, end_idx])

        for b in blocks[lo:hi + 1]:
            self.block_buttons[b].setChecked(True)

        # clear highlight
        btn = self.block_buttons[self.range_start]
        btn.setChecked(btn.isChecked())  # forces repaint via toggle logic
        self.range_start = None


def ask_slice_options(available_blocks):
    dialog = SliceDialog(available_blocks)
    ok = dialog.exec()

    if not ok:
        return [], []

    return dialog.blocks, dialog.days
