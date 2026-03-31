#### All the cosmetic/formatting constants live here 



ALERT = "#CC194C"
GREY  = "#CCCCCC"
REP   = "#FFB7B7"
NGR   = "#E4DFEC"
NGRE  = "#FFFF93"
IMU   = "#FDE9D9"
EMU   = "#DAEEF3"
SMU   = "#F2DCDB"
DEPT  = "#EBF1DE"
QMU = "#B7FFDB"


UNBALANCED_YELLOW = "#CCB233"
WHITE = "#FFFFFF"

# Map used by the builder to generate families
FAMILY_BG = {
    "REP":    REP,
    "NGR":    NGR,
    "NGRE":   NGRE,
    "IMU100": IMU,
    "EMU":    EMU,
    "HYBRID": EMU,   # shared EMU palette
    "SMU":    SMU,
    "DEPT":   DEPT,
    "QMU":    QMU
}


STYLE_VARIANTS = {
    "normal": {},

    "bold": {
        "bold": True,
        "bottom": 1,
    },

    "boldred": {
        "bold": True,
        "font_color": ALERT,
    },

    "big": {
        "font_size": 16,
        "valign": "vcenter",
    },

    "bigred": {
        "font_size": 16,
        "valign": "vcenter",
        "font_color": ALERT,
    },

    "border": {
        "left": 1,
        "right": 1,
    },
}







GENERIC_STYLES = {
    "title": {
        "bold": True,
        "align": "center",
    },

    "header": {
        "bold": True,
        "align": "center",
        "bg_color": GREY,
    },

    "size16": {
        "font_size": 16,
    },

    "size14": {
        "font_size": 14,
    },

    "centered": {
        "align": "center",
    },

    "boldleft": {
        "bold": True,
        "align": "left",
    },

    "boldright": {
        "bold": True,
        "align": "right",
    },

    "redcentered": {
        "align": "center",
        "font_color": ALERT,
    },

    "redleft": {
        "align": "left",
        "font_color": ALERT,
    },

    "redboldleft": {
        "bold": True,
        "align": "left",
        "font_color": ALERT,
    },
}


_UNIT_COLOURS = [
    '#2563EB',  # blue
    '#F97316',  # orange
    '#16A34A',  # green
    '#DC2626',  # red
    '#9333EA',  # purple
    '#0891B2',  # cyan
    '#DB2777',  # pink
    '#CA8A04',  # amber
]

_TOTAL_COLOUR  = '#0F172A'   # near-black
_CAPACITY_COLOUR = '#EF4444' # soft red
_GRID_COLOUR   = '#F1F5F9'   # very light blue-grey — barely visible
_AXIS_COLOUR   = '#64748B'   # slate



BORDER_STYLES = {
    "top": {"top": 1},
    "bottom": {"bottom": 1},
    "left": {"left": 1},
    "right": {"right": 1},
    "border": {"border": 1, "border_color": "#000000"},
    "border_alert": {"border": 1, "border_color": ALERT},
}



SEMANTIC_STYLES = {
    "unbalanced": {
        "bg_color": UNBALANCED_YELLOW,
    },

    "unbalanced_red": {
        "bg_color": ALERT,
        "font_color": WHITE,
    },

    "interpeak_flag": {
        "bold": True,
        "border": 1,
        "border_color": "#000000",
        "font_color": "#FF0000",
        "bg_color": UNBALANCED_YELLOW,
        "align": "center",
    },
}


STEPS_COL = [
            '1. Determine the location where each Run starts and finishes.',
            '2. By Unit type by Day, count the number of Runs that start or finish at each location.',
            '3. Find where start and finish counts do not match over the day.',
            '4. Find where start and finish counts do not match over the week.'
            ]


# for first last graph
CHART_W, CHART_H = 500, 380
SLICER_LEFT      = 10
CHART_LEFT       = 170   # leave room for slicers on the left

SLICER_CONFIGS = [
    ("StationName",   "Station",   10,  CHART_LEFT + CHART_W*2 + 40, 150, 200),
    ("Day",       "Day",       220, CHART_LEFT + CHART_W*2 + 40, 150, 160),
    ("Timetable", "Timetable", 390, CHART_LEFT + CHART_W*2 + 40, 150, 120),
    ]