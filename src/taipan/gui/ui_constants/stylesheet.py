import os


WHITE      = "#ffffff"
TEXT       = "#2c1a06"
ORANGE2    = "#ef7740"
TAN        = "#cb962e"
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
    /* BlurredBackground paints itself — central + scroll_content must be transparent */
    QWidget#central {{
    background: transparent;
    }}
    QWidget#scroll_content {{
    background: transparent;
    }}
    QScrollArea {{
    border: none;
    background: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
    background: transparent;
    }}
    QAbstractScrollArea::viewport {{
    background: transparent;
    }}
    /* ════════════════════════════════════════════
    SCROLLBAR
    ════════════════════════════════════════════ */
    QScrollBar:vertical {{
    background: rgba(255, 200, 120, 0.12);
    width: 8px;
    border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
    background: rgba(255, 200, 120, 0.40);
    border-radius: 4px;
    min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
    background: rgba(255, 210, 140, 0.65);
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
    height: 0px;
    }}
    /* ════════════════════════════════════════════
    HEADER — frosted amber bar
    ════════════════════════════════════════════ */
    QWidget#header {{
    background: rgba(180, 80, 15, 0.45);
    border-bottom: 1px solid rgba(255, 200, 100, 0.30);
    }}
    QLabel#mtp_badge {{
    background: rgba(239, 119, 64, 0.35);
    color: {WHITE};
    font-size: 22px;
    font-weight: 900;
    border: 1px solid rgba(255, 210, 150, 0.45);
    border-radius: 10px;
    }}
    QLabel#app_title {{
    color: {WHITE};
    font-size: 30px;
    font-weight: 900;
    letter-spacing: 2px;
    }}
    QLabel#app_subtitle {{
    color: rgba(250, 210, 129, 0.90);
    font-size: 22px;
    font-weight: 400;
    }}
    /* ════════════════════════════════════════════
    CARDS — normal (warm liquid glass)
    ════════════════════════════════════════════ */
    QWidget#card_normal {{
    background: rgba(255, 235, 190, 0.18);
    border: 1px solid rgba(255, 220, 150, 0.38);
    border-radius: 14px;
    }}
    QLabel#card_title_normal {{
    color: #fffaf0;
    font-size: 18px;
    font-weight: 800;
    background: transparent;
    padding: 2px 0px 4px 0px;
    letter-spacing: 1.5px;
    }}
    QFrame#div_normal {{
    background: rgba(255, 210, 120, 0.30);
    max-height: 1px;
    border: none;
    }}
    QLabel#subcat_normal {{
    color: #fffaf0;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 6px 0px 2px 0px;
    background: transparent;
    }}
    /* ════════════════════════════════════════════
    CARDS — orange (amber liquid glass)
    ════════════════════════════════════════════ */
    QWidget#card_orange {{
    background: rgba(200, 75, 15, 0.28);
    border: 1px solid rgba(255, 150, 70, 0.42);
    border-radius: 14px;
    }}
    QLabel#card_title_orange {{
    color: #ffe8c8;
    font-size: 16px;
    font-weight: 800;
    background: transparent;
    padding: 2px 0px 4px 0px;
    letter-spacing: 1.5px;
    }}
    QFrame#div_orange {{
    background: rgba(255, 150, 70, 0.35);
    max-height: 1px;
    border: none;
    }}
    QLabel#subcat_orange {{
    color: rgba(255, 215, 155, 0.95);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: transparent;
    padding: 6px 0px 2px 0px;
    }}
    /* ════════════════════════════════════════════
    CARD NOTE
    ════════════════════════════════════════════ */
    QLabel#card_note {{
    color: #fffaf0;
    font-size: 13px;
    font-style: italic;
    background: transparent;
    padding: 4px 2px;
    }}
    /* ════════════════════════════════════════════
    BUTTONS — normal
    ════════════════════════════════════════════ */
    QPushButton#btn_normal {{
    background: rgba(255, 240, 200, 0.20);
    color: #fff8ee;
    border: 1px solid rgba(255, 215, 140, 0.45);
    border-bottom: 2px solid rgba(180, 120, 30, 0.55);
    border-radius: 7px;
    padding: 8px 14px;
    font-size: 15px;
    font-weight: 650;
    text-align: left;
    }}
    QPushButton#btn_normal:hover {{
    background: rgba(255, 245, 215, 0.36);
    border: 1px solid rgba(255, 225, 155, 0.70);
    border-bottom: 2px solid rgba(200, 140, 40, 0.70);
    color: #ffffff;
    }}
    QPushButton#btn_normal:pressed {{
    background: rgba(220, 165, 60, 0.38);
    border: 1px solid rgba(255, 210, 120, 0.60);
    border-top: 2px solid rgba(180, 120, 30, 0.55);
    border-bottom: 1px solid rgba(255, 210, 120, 0.60);
    color: #ffffff;
    padding-top: 10px;
    padding-bottom: 6px;
    }}
    /* ════════════════════════════════════════════
    BUTTONS — orange
    ════════════════════════════════════════════ */
    QPushButton#btn_orange {{
    background: rgba(255, 200, 140, 0.14);
    color: #ffe8c8;
    border: 1px solid rgba(255, 155, 75, 0.45);
    border-bottom: 2px solid rgba(160, 65, 10, 0.55);
    border-radius: 7px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
    }}
    QPushButton#btn_orange:hover {{
    background: rgba(255, 185, 110, 0.28);
    border: 1px solid rgba(255, 175, 95, 0.68);
    border-bottom: 2px solid rgba(190, 80, 15, 0.68);
    color: #ffffff;
    }}
    QPushButton#btn_orange:pressed {{
    background: rgba(210, 90, 20, 0.48);
    border: 1px solid rgba(255, 155, 75, 0.65);
    border-top: 2px solid rgba(160, 65, 10, 0.55);
    border-bottom: 1px solid rgba(255, 155, 75, 0.65);
    color: #ffffff;
    padding-top: 10px;
    padding-bottom: 6px;
    }}
    /* ════════════════════════════════════════════
    STATUS BAR
    ════════════════════════════════════════════ */
    QWidget#status_bar {{
    background: rgba(80, 40, 8, 0.72);
    border-top: 1px solid rgba(255, 180, 80, 0.22);
    }}
    QLabel#status_text {{
    color: #f5e8c8;
    font-size: 14px;
    letter-spacing: 2px;
    font-weight: 400;
    }}
    QLabel#status_file {{
    color: rgba(245, 232, 200, 0.65);
    font-size: 14px;
    font-weight: 400;
    }}
    QPushButton#clear_btn {{
    background: rgba(200, 60, 40, 0.20);
    border: 1px solid rgba(255, 120, 80, 0.40);
    border-radius: 4px;
    color: rgba(255, 190, 170, 0.90);
    font-size: 11px;
    padding: 0;
    }}
    QPushButton#clear_btn:hover {{
    background: rgba(200, 60, 40, 0.45);
    border: 1px solid rgba(255, 120, 80, 0.75);
    color: #ffffff;
    }}
    /* ════════════════════════════════════════════
    TOOLTIPS
    ════════════════════════════════════════════ */
    QToolTip {{
    background: rgba(20, 10, 2, 0.96);
    color: #fde8c0;
    border: 1px solid rgba(239, 119, 64, 0.55);
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.5px;
    }}
"""