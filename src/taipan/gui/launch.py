import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QGridLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QCursor, QColor, QIcon
from taipan.gui.base import select_file, select_multi_rsx_files, select_folder
from taipan.gui.ui_constants.stylesheet import STYLESHEET, img_path
import os
from taipan.gui.ui_constants.names import SCRIPTS, COLUMN_ORDER
from taipan.gui.base import register_main_window, select_checkboxes 
from taipan.gui.ui_constants.background import BlurredBackground


snake_emoji = "\U0001F40D"

import importlib
def _lazy(module, attr):
 
    # these imports are hefty which affects the startup time - lazy load them (so the user sees the UI right away although imports are still loading in the background)
   _cache = {}
   def _loader(*args, **kwargs):
       if module not in _cache:
           _cache[module] = getattr(importlib.import_module(module), attr)
       return _cache[module](*args, **kwargs)
   return _loader


# update this with functions as required 
TTS_ERR         = _lazy("taipan.reports.ErrorChecker",           "TTS_ERR")
TTS_PTT         = _lazy("taipan.timetables.PublicTimetable",     "TTS_PTT")
TTS_SB          = _lazy("taipan.stabling.StablingBalance",       "TTS_SB")
TTS_SC          = _lazy("taipan.stabling.StablingCount",         "TTS_SC")
TTS_GRAPH       = _lazy("taipan.stabling.StablingCountStepGraph","TTS_Graph")
assign_line_ids = _lazy("taipan.rsx.run_renamer_new",   "assign_line_ids")
sectorise       = _lazy("taipan.rsx.SectoriseRSX",               "sectorise")
rename_trains   = _lazy("taipan.rsx.train_renamer",              "main")
TTS_TM          = _lazy("taipan.reports.TrainMovements",         "TTS_TM")
run_km          = _lazy("taipan.reports.kilometrage",            "main")
TTS_TC          = _lazy("taipan.reports.TripCount",              "TTS_TC")
TTS_RI          = _lazy("taipan.reports.RunInfo",                "TTS_RI")
TTS_FL          = _lazy("taipan.first_last.FirstLast",           "TTS_FL")
TTS_SFL         = _lazy("taipan.first_last.SimpleFirstLast",     "TTS_SFL")
TTS_FLG         = _lazy("taipan.first_last.first_last_graph",    "TTS_FLG")
TTS_WTT         = _lazy("taipan.timetables.WorkingTimetable",    "TTS_WTT")
TTS_TDSWTT      = _lazy("taipan.timetables.WorkingTimetable (TDS)",    "TTS_TDSWTT")
TTS_TDSPTT      = _lazy("taipan.timetables.PublicTimetable (TDS)",    "TTS_TDSPTT")
slice_rsxfile   = _lazy("taipan.rsx.slice_rsx",                  "main")
run_geo_convert = _lazy("taipan.converters.ITOPSGeoConvert",     "run_geo_convert")
run_itops_tt    = _lazy("taipan.converters.ITOPS_TTConvert",     "main")
TTS_H           = _lazy("taipan.converters.HASTUS_Converter",    "TTS_H")
TTS_TDS         = _lazy("taipan.converters.TDS_Converter",       "TTS_TDS")
TTS_HTT         = _lazy("taipan.converters.HASTUS_ttrefnum",     "TTS_HTT")
run_ngr_dpp     = _lazy("taipan.plans.NGRDailyPlan",             "run_ngr_dpp")
run_ngr_wpp     = _lazy("taipan.plans.NGRWeeklyPlan",            "run_ngr_wpp")
TTS_VAS         = _lazy("taipan.reports.VASExtract",             "TTS_VAS")
TTS_RSX_UTC     = _lazy("taipan.converters.convert_RSX_UTC",     "convert_RSX_UTC")


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
icon_path = os.path.join(BASE_DIR, "images", "taipan-icon.jpg").replace("\\", "/")


class _Worker(QThread):
   done  = pyqtSignal(object)
   error = pyqtSignal(str)
   def __init__(self, func):
       super().__init__()
       self.func = func
   def run(self):
       try:
           result = self.func()
           self.done.emit(result)
       except Exception as e:
           self.error.emit(f"{type(e).__name__}: {e}")


class ScriptCard(QWidget):

    def __init__(self, title, data, dispatcher, parent=None):

        super().__init__(parent)

        is_orange = data.get("style") == "orange"
        self.setObjectName("card_orange" if is_orange else "card_normal")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        ### card shadows
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)

        # Create color and apply alpha separately
        shadow_color = QColor("#1a1917")
        shadow_color.setAlpha(200)  # 128 is roughly 50% opacity
        shadow.setColor(shadow_color)

        self.setGraphicsEffect(shadow)
                
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(6)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("card_title_orange" if is_orange else "card_title_normal")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        div = QFrame()
        div.setObjectName("div_orange" if is_orange else "div_normal")
        div.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(div)
        layout.addSpacing(6)

        for group_name, items in data["groups"].items():
            if group_name:
                layout.addSpacing(8)
                sub = QLabel(group_name)
                sub.setObjectName("subcat_orange" if is_orange else "subcat_normal")
                sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(sub)
                layout.addSpacing(6)

            for label, func_name, tooltip in items:
                btn = QPushButton(label)
                btn.setObjectName("btn_orange" if is_orange else "btn_normal")


                
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(10)
                shadow.setOffset(2, 3)
                shadow.setColor(QColor(0, 0, 0, 70))
                btn.setGraphicsEffect(shadow)
                
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn.setToolTip(tooltip)
                btn.setMinimumHeight(36)
                btn.clicked.connect(lambda checked, f=func_name, b=btn: dispatcher(f, b))
                layout.addWidget(btn)
                layout.addSpacing(2)

        if data.get("note"):
            layout.addSpacing(4)
            note = QLabel(data["note"])
            note.setObjectName("card_note")
            note.setWordWrap(True)
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(note)
        layout.addStretch()


class TaipanLauncher(QMainWindow):

    def __init__(self):

        super().__init__()
        register_main_window(self)
        self.setWindowIcon(QIcon(icon_path))
        self.last_file = None
        self.setWindowTitle("TAIPAN Timetable Tools")
        self.setMinimumSize(1000, 640)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)
        self.setAcceptDrops(True)


        QFont("Segoe UI", 12)
        self._build_ui()

        from threading import Thread
        Thread(target=self._warmup, daemon=True).start()

    def _warmup(self):
        # put frequently used modules here to be pre imported to avoid first click delay 
        import taipan.stabling.StablingCount
        import taipan.timetables.PublicTimetable
        import taipan.reports.TrainMovements
        import taipan.reports.ErrorChecker
        import taipan.reports.TripCount

    @pyqtSlot(object)            
    def _invoke_slot(self, func):
        func()

    
    def get_file(self, *, force_new=False, filter_str="All Files (*.*)", multi_rsx=False):

        def is_rsx(path):
            if isinstance(path, list):
                return all(str(p).lower().endswith(".rsx") for p in path)
            return str(path).lower().endswith(".rsx")

        #  sanity check: never allow non-RSX to live in memory
        if self.last_file and not is_rsx(self.last_file):
            self.last_file = None

        if force_new:
            path = select_multi_rsx_files() if multi_rsx else select_file(filter_str=filter_str)

            if path:
                #  ONLY save + update UI for RSX and NOT multi files 
                if is_rsx(path) and not isinstance(path, list):

                    self.last_file = path

                    if isinstance(path, list):
                        self.file_lbl.setText(f"{len(path)} files")
                    else:
                        self.file_lbl.setText(os.path.basename(path))
                        self.file_lbl.setToolTip(path)

                    self.clear_btn.setVisible(True)

            return path

        #  reuse ONLY if it's RSX (single OR multi — doesn't matter)
        if self.last_file:
            return self.last_file

        # otherwise pick file
        path = select_multi_rsx_files() if multi_rsx else select_file(filter_str=filter_str)

        if path:
            #  ONLY save RSX
            if is_rsx(path):
                self.last_file = path

            # UI update
            if isinstance(path, list):
                self.file_lbl.setText(f"{len(path)} files")
            else:
                self.file_lbl.setText(os.path.basename(path))
                self.file_lbl.setToolTip(path)

            self.clear_btn.setVisible(True)

        return path
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()


    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        #  get first file
        file_path = urls[0].toLocalFile()

        if file_path:
            self.last_file = file_path
            import os
            self.last_file = file_path
            self.file_lbl.setText(os.path.basename(file_path))
            self.clear_btn.setVisible(True)


    def _clear_file(self):
        self.last_file = None
        self.file_lbl.setText("Drag and drop RSX here...")          # remove filename (right side)
        self.clear_btn.setVisible(False)   # hide the ✕ button
        self._set_status(f"{snake_emoji} FILE CLEARED")


    def run_task(self, func, start_msg, done_msg): 
        self._set_status(start_msg)
        self._worker = _Worker(func)
        self._worker.done.connect(lambda: self._set_status(done_msg))
        self._worker.error.connect(lambda e: self._set_status(f"{snake_emoji} ERROR — {e}"))
        self._worker.start()
        

    def _build_ui(self):

        central = BlurredBackground(img_path, blur_radius=5, darken=150)
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(88)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 14, 20, 14)
        h_layout.setSpacing(16)
        
        badge = QLabel("MTP")
        badge.setObjectName("mtp_badge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(60, 60)
        h_layout.addWidget(badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        t1 = QLabel("TAIPAN")
        t1.setObjectName("app_title")
        title_col.addWidget(t1)

        t2 = QLabel("Timetable Tools")
        t2.setObjectName("app_subtitle")
        title_col.addWidget(t2)
        h_layout.addLayout(title_col)
        h_layout.addStretch()
        root.addWidget(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)   # <-- add this
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


       
        content = QWidget()
        content.setObjectName("scroll_content")

        grid = QGridLayout(content)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        for col_idx, col_cards in enumerate(COLUMN_ORDER):

            col_w = QWidget()
            col_v = QVBoxLayout(col_w)
            col_v.setContentsMargins(0, 0, 0, 0)
            col_v.setSpacing(12)
            col_v.setAlignment(Qt.AlignmentFlag.AlignTop)

            for card_name in col_cards:
                card = ScriptCard(title=card_name,data=SCRIPTS[card_name],dispatcher=self._dispatch,)
                col_v.addWidget(card)

            grid.addWidget(col_w, 0, col_idx)

        for i in range(4):
            grid.setColumnStretch(i, 1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Status bar

        status = QWidget()
        status.setObjectName("status_bar")
        status.setFixedHeight(34)
        s_layout = QHBoxLayout(status)
        s_layout.setContentsMargins(20, 0, 20, 0)
        self.status_lbl = QLabel(f"{snake_emoji} READY")
        self.status_lbl.setObjectName("status_text")

        self.file_lbl = QLabel("Drag and drop RSX here...")                    #  file name (right)
        self.file_lbl.setObjectName("status_file")

        self.clear_btn = QPushButton("✕")             #  clear button
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.setToolTip("Clear selected file")
        self.clear_btn.clicked.connect(self._clear_file)
        self.clear_btn.setVisible(False)              # hidden until file exists

        #  layout order
        s_layout.addWidget(self.status_lbl)
        s_layout.addStretch()
        s_layout.addWidget(self.file_lbl)
        s_layout.addWidget(self.clear_btn)

        root.addWidget(status)

    def _dispatch(self, func_name, button=None):

        handler = getattr(self, func_name, None)

        if handler:
            handler(button)
        else:
            name = func_name.replace("_run_", "").replace("_", " ").upper()
            self._set_status(f"{snake_emoji} NOT YET IMPLEMENTED — {name}")


    def _set_status(self, text):
        self.status_lbl.setText(text)

    def _run_ptt(self, button=None):

        
        path = self.get_file(
                filter_str="RSX Files (*.rsx)"
            )

        if not path:
            return

        self.run_task(
            lambda: TTS_PTT(path),
            f"{snake_emoji} RUNNING — PUBLIC TIMETABLE...",
            f"{snake_emoji} DONE — PUBLIC TIMETABLE"
        )



    def _run_wtt(self, button=None):
        path = self.get_file(
                filter_str="RSX Files (*.rsx)"
            )

        if not path:
            return

        self.run_task(
            lambda: TTS_WTT(path),
            f"{snake_emoji} RUNNING — WORKING TIMETABLE...",
            f"{snake_emoji} DONE — WORKING TIMETABLE"
        )

    def _run_runinfo(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_RI(path),f"{snake_emoji} RUNNING — RUN INFO...",f"{snake_emoji} DONE — RUN INFO")

    def _run_movements(self, button=None):
        path = self.get_file(
                filter_str="RSX Files (*.rsx)"
            )

        if not path:
            return

        self.run_task(
            lambda: TTS_TM(path),
            f"{snake_emoji} RUNNING — TRAIN MOVEMENTS...",
            f"{snake_emoji} DONE — TRAIN MOVEMENTS"
        )
    def _run_tripcount(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_TC(path),f"{snake_emoji} RUNNING — TRIP COUNT...",f"{snake_emoji} DONE — TRIP COUNT")



    
    def _run_runtime(self, button=None):
        # run this as subprocess since dash doesn't exit 
        
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        import subprocess
        import sys

        
        subprocess.Popen([
            sys.executable,
            "-m",
            "taipan.reports.RuntimeDashboard",
            path
        ])



    def _run_km(self, button=None):

        
        path = self.get_file(
            force_new=True,
            filter_str="Excel Files (*.xlsx *.xls)"
        )

        if path:
            self.run_task(
                lambda: run_km(path),  
                f"{snake_emoji} RUNNING — KM CALC...",
                f"{snake_emoji} DONE — KM CALC"
                )
        else:
            return


    def _run_first_last(self, button=None):
        
        paths = self.get_file(multi_rsx=True, force_new=True, filter_str="RSX Files (*.rsx)")

        if len(paths) != 2:
            self._set_status(f"{snake_emoji} ERROR — Please select exactly two RSX files.")
        else:
            self.run_task(lambda: TTS_FL(paths),  f"{snake_emoji} RUNNING — FIRST LAST...",f"{snake_emoji} DONE — FIRST LAST")

    

    def _run_simple_first_last(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_SFL(path),f"{snake_emoji} RUNNING — SIMPLE FIRST LAST...",f"{snake_emoji} DONE — SIMPLE FIRST LAST")

    def _run_first_last_graph(self, button=None):
        paths = self.get_file(multi_rsx=True, force_new=True, filter_str="RSX Files (*.rsx)")

        if not paths:
            return
    
        
        self.run_task(lambda: TTS_FLG(paths), f"{snake_emoji} RUNNING — FIRSTLAST GRAPH...", f"{snake_emoji} DONE — FIRSTLAST GRAPH")


    def _run_slicer(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: slice_rsxfile(path),f"{snake_emoji} RUNNING — SLICER...",f"{snake_emoji} DONE — SLICER")

    def _run_stabling_balance(self, button=None):
        
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_SB(path),f"{snake_emoji} RUNNING — STABLING BALANCE...",f"{snake_emoji} DONE — STABLING BALANCE")


    def _run_stabling_count(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_SC(path),f"{snake_emoji} RUNNING — STABLING COUNT...",f"{snake_emoji} DONE — STABLING COUNT")

    def _run_stabling_graph(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_GRAPH(path),f"{snake_emoji} RUNNING — STABLING GRAPH...",f"{snake_emoji} DONE — STABLING GRAPH")

    def _run_assign_lineids(self, button=None):
        
        path = self.get_file(filter_str="RSX Files (*.rsx);;All Files (*.*)")

        if not path:
            return

        self.run_task(
            lambda: assign_line_ids(path),
            f"{snake_emoji} RUNNING — ASSIGN LINEIDS...",
            f"{snake_emoji} DONE — ASSIGN LINEIDS"
        )


    def _run_train_renamer(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx);;All Files (*.*)")

        if not path:
            return
        
        choices = select_checkboxes(
        title="Train Number Characters",
        message="Select which characters to update:",
        options=[
            ("1st - Train type (EMU, NGR, etc.)", "1"),
            ("2nd - Destination / corridor",       "2"),
            ("3rd - Stopping pattern / peak",      "3"),
            ("4th - Direction (Up/Down)",          "4"),
        ],
        default_values=["1", "2", "3", "4"],)


        self.run_task(
            lambda: rename_trains(path, set(choices)),
            f"{snake_emoji} RUNNING — TRAIN RENAMER...",
            f"{snake_emoji} DONE — TRAIN RENAMER"
        )
    def _run_sectorise(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx);;All Files (*.*)")

        if not path:
            return

        self.run_task(
            lambda: sectorise(path),
            f"{snake_emoji} RUNNING — SECTORISE RSX...",
            f"{snake_emoji} DONE — SECTORISE RSX"
        )

    def _run_itops_tt(self, button=None):
        
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(
            lambda: run_itops_tt(path),
            f"{snake_emoji} RUNNING — ITOPS FILE PREP...",
            f"{snake_emoji} DONE — ITOPS FILE PREP"
        )


    def _run_itops_geo(self, button=None):
        
        paths = self.get_file(multi_rsx=True, force_new=True, filter_str="RSX Files (*.rsx)")

        if not paths:
            return

        self.run_task(
            lambda: run_geo_convert(paths),
            f"{snake_emoji} RUNNING — ITOPS GEO CONVERSION...",
            f"{snake_emoji} DONE — ITOPS GEO CONVERSION"
        )


    def _run_hastus(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return


        self.run_task(lambda: TTS_H(path),f"{snake_emoji} RUNNING — HASTUS...",f"{snake_emoji} DONE — HASTUS")


    def _run_hastus_ttrefnum(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_HTT(path),f"{snake_emoji} RUNNING — HASTUS (TTREFNUM)...",f"{snake_emoji} DONE — HASTUS (TTREFNUM)")

    def _run_ngr_weekly(self, button=None):
        path = self.get_file(
                filter_str="RSX Files (*.rsx)",
                force_new=True   # ALWAYS open picker
            )

        if not path:
            return

        self.run_task(
            lambda: run_ngr_wpp(path),
            f"{snake_emoji} RUNNING — NGR WPP...",
            f"{snake_emoji} DONE — NGR WPP"
        )

    def _run_ngr_daily(self, button=None):
        

        
        path = self.get_file(
                filter_str="RSX Files (*.rsx)",
                force_new=True   # ALWAYS open picker
            )

        if not path:
            return

        self.run_task(
            lambda: run_ngr_dpp(path),
            f"{snake_emoji} RUNNING — NGR DPP...",
            f"{snake_emoji} DONE — NGR DPP"
        )


    def _run_vas(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_VAS(path),f"{snake_emoji} RUNNING — VAS EXTRACTOR...",f"{snake_emoji} DONE — VAS EXTRACTOR")

    

   
    def _run_tds_jp(self, button=None):

        ### tds converter goes here 
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_TDS(path),f"{snake_emoji} RUNNING — TDS CONVERTER...",f"{snake_emoji} DONE — TDS CONVERTER")

    def _run_tds_wtt(self, button=None):
        # FILTER TO TXT FILES
        path = self.get_file(force_new=True,filter_str="TXT Files (*.txt)")

        if not path:
            return

        ## working timetable (tds) goes here
        self.run_task(
            lambda: TTS_TDSWTT(path),
            f"{snake_emoji} RUNNING — TDS → WORKINGTT...",
            f"{snake_emoji} DONE — TDS → WORKINGTT"
        )

    def _run_tds_ptt(self, button=None):

        path = self.get_file(force_new=True,filter_str="TXT Files (*.txt)")

        if not path:
            return


        ## public timetable (tds) goes here
        self.run_task(
            lambda: TTS_TDSPTT(path),
            f"{snake_emoji} RUNNING — TDS → PUBLICTT...",
            f"{snake_emoji} DONE — TDS → PUBLICTT"
        )

    def _run_qa(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_ERR(path),f"{snake_emoji} RUNNING — QA / ERROR CHECKER...",f"{snake_emoji} DONE — QA / ERROR CHECKER")

    
    def _run_rsx_utc(self, button=None):
        rsx_path = self.get_file(filter_str="RSX Files (*.rsx)") 
        freight_folder = select_folder(
            caption="Select freight TXT folder (cancel to skip)",
            directory=os.path.dirname(rsx_path) if rsx_path else "",
        ) or None


        ### test 


        if not rsx_path:
            return

        self.run_task(lambda: TTS_RSX_UTC(rsx_path = rsx_path, freight_folder=freight_folder),f"{snake_emoji} RUNNING — RSX → UTC CONVERTER...",f"{snake_emoji} DONE — RSX → UTC CONVERTER")

    
  




def main():
    app = QApplication(sys.argv)

    # Use Windows style so stylesheets fully apply
    #app.setStyle("Windows")
    app.setStyleSheet(STYLESHEET) 
    window = TaipanLauncher()
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
 