import os


BG         = "#f1e7cf"   
CARD_BG    = "#e8cc90"
CARD_OBG   = "#d06018"
BORDER     = "#b08040"

BTN_BG    = "#fff4de"
BTN_HOVER = "#eeddb7"
BTN_PRESS = "#cfa960"

ORANGE     = "#c8601a"
ORANGE2    = "#ef7740"
TAN        = "#cb962e"
TEXT       = "#2c1a06"
TEXT_LIGHT = "#6b4a1a"
WHITE      = "#ffffff"
STATUS_BG  = "#8a5c1a"


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
img_path = os.path.join(BASE_DIR, "images", "taipan_img.jpg").replace("\\", "/")
print(img_path)
STYLESHEET = f"""

QPushButton {{
    border: none;
}}

* {{

    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;

}}



QWidget#central {{
    border-image: url("{img_path}") 0 0 0 0 stretch stretch;
}}



QLabel#status_file {{
    color: #f5e8c8;
    font-size: 11px;
}}




QWidget#header {{

    background-color: {ORANGE};
    border-bottom: 3px solid #a04a10;

}}

QLabel#mtp_badge {{

    background-color: {ORANGE2};
    color: {WHITE};
    font-size: 22px;
    font-weight: 900;
    border: 3px solid {WHITE};
    border-radius: 6px;

}}

QLabel#app_title {{

    color: {WHITE};
    font-size: 30px;
    font-weight: 800;

}}

QLabel#app_subtitle {{

    color: #fad281;
    font-size: 22px;
    font-weight: 400;

}}

QScrollArea {{

    border: none;
    background-color: {BG};

}}


QWidget#scroll_content {{
    border-image: url("{img_path}") 0 0 0 0 stretch stretch;
}}


QScrollBar:vertical {{

    background: #d4b878;
    width: 8px;
    border-radius: 4px;

}}

QScrollBar::handle:vertical {{

    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;

}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QWidget#card_normal {{
    background-color: rgba(255, 255, 255, 0.65);
    border: 2px solid #b08040;
    border-radius: 12px;
}}

QWidget#card_orange {{
    background-color: rgba(255, 255, 255, 0.65);
    border: 2px solid #a04008;
    border-radius: 12px;
}}


QLabel#card_title_normal {{

    color: {TEXT};
    font-size: 15px;
    font-weight: 700;
    background-color: transparent;
    padding: 2px 0px 4px 0px;

}}

QLabel#card_title_orange {{

    color: {WHITE};
    font-size: 15px;
    font-weight: 700;
    background-color: transparent;
    padding: 2px 0px 4px 0px;

}}

QFrame#div_normal {{

    background-color: {BORDER};
    max-height: 1px;
    border: none;

}}

QFrame#div_orange {{

    background-color: #e8906a;
    max-height: 1px;
    border: none;

}}


QLabel#subcat_normal {{
    color: {TEXT};
    font-size: 14px;
    font-weight: bold;
    font-style: normal;   /* remove italic */
    padding: 6px 0px 2px 0px;
}}


QLabel#subcat_orange {{

    color: #fad281;
    font-size: 11px;
    font-style: italic;
    background-color: transparent;
    padding: 6px 0px 2px 0px;

}}

QLabel#card_note {{

    color: {TEXT};
    font-size: 11px;
    font-style: italic;
    background-color: transparent;
    padding: 4px 2px;

}}

QPushButton#btn_normal {{

    
    background-color: {BTN_BG};
    color: {TEXT};

    border: 2px solid {BORDER};
    border-bottom: 4px solid #8a6020;   /* darker bottom = depth */

    border-radius: 6px;
    padding: 8px 14px;

    font-size: 14px;
    font-weight: 600;


}}

QPushButton#btn_normal:hover {{

    background-color: {BTN_HOVER};
    border: 2px solid {TAN};
    border-bottom: 4px solid #7a5010;
    color: {TEXT};

}}

QPushButton#btn_normal:pressed {{

    background-color: {BTN_PRESS};
    border: 2px solid {BORDER};
    border-top: 4px solid #8a6020;
    border-bottom: 2px solid {BORDER};
    padding-top: 10px;
    padding-bottom: 6px;

}}

QPushButton#btn_orange {{

    background-color: {BTN_BG};
    color: {TEXT};
    border: 2px solid #d07040;
    border-bottom: 4px solid #7a3008;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: 600;
    text-align: center;

}}

QPushButton#btn_orange:hover {{

    background-color: {BTN_HOVER};
    border: 2px solid {ORANGE2};
    border-bottom: 4px solid #903010;
    color: {TEXT};

}}

QPushButton#btn_orange:pressed {{

    background-color: {BTN_PRESS};
    border: 2px solid #7a3008;
    border-top: 4px solid #7a3008;
    border-bottom: 2px solid #7a3008;
    padding-top: 10px;
    padding-bottom: 6px;

}}



QWidget#status_bar {{

    background-color: {STATUS_BG};
    border-top: 2px solid #6a3c0a;

}}

QLabel#status_text {{

    color: #f5e8c8;
    font-size: 14px;
    letter-spacing: 2px;
    font-weight: 500;

}}

QToolTip {{

    background-color: #2c1a06;
       color: #f1dfb6;
       border: 1px solid #cb962e;
       padding: 6px 10px;
       border-radius: 4px;
       font-size: 13px;

}}

"""