
###### DAYS 

WEEKDAY_KEYS_MASTER = {
    '120': {'short': 'Mon-Thu', 'long': 'Monday-Thursday', 'alias': 'M-Th'},
    '64':  {'short': 'Mon',     'long': 'Monday',          'alias': 'M'},
    '32':  {'short': 'Tue',     'long': 'Tuesday',         'alias': 'T'},
    '16':  {'short': 'Wed',     'long': 'Wednesday',       'alias': 'W'},
    '8':   {'short': 'Thu',     'long': 'Thursday',        'alias': 'R'},
    '4':   {'short': 'Fri',     'long': 'Friday',          'alias': 'F'},
    '2':   {'short': 'Sat',     'long': 'Saturday',        'alias': 'S'},
    '1':   {'short': 'Sun',     'long': 'Sunday',          'alias': 'U'},
}

DAY_PRIORITY = ['64','32','16','8','4','2','1','120']
SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1']
#SORT_ORDER_UNIT = ['REP','NGR','NGRE','IMU100','EMU','SMU','HYBRID','ICE','DEPT']
ID_TO_SHORT = {k: v['short'] for k, v in WEEKDAY_KEYS_MASTER.items()}
ID_TO_LONG  = {k: v['long'] for k, v in WEEKDAY_KEYS_MASTER.items()}
ID_TO_ALIAS = {k: v['alias'] for k, v in WEEKDAY_KEYS_MASTER.items()}

MON_THU_MASK = 64 | 32 | 16 | 8   # = 120


# Universal Reverse Map (maps name/alias back to the ID)
NAME_TO_ID = {}
for uid, info in WEEKDAY_KEYS_MASTER.items():
    for val in info.values():
        NAME_TO_ID[val.lower()] = uid


SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1'] 


##### UNITS / TRAINTYPES 
SORT_ORDER_UNIT = ['QMU', 'REP','NGR','NGRE','IMU100','EMU','SMU','HYBRID', 'DEPT']

### LOCATIONS (YARDS/STATIONS)
# if new location found, update locations, flag it 
# print new location in excel file for easy debugging 
# update stabling yard locations, capacity, and sectors here 
# DO NOT!!! ADD a sector variable for yards that share sectors - this is handled automatically. only add a sector if yards in list are single sector
YARDS = {
    'Wulkuraka':    {'capacity': 11,  'yards': ['WFE', 'WFW', 'FEE'], 'sector': 2,},
    'Ipswich':      {'capacity': 7,   'yards': ['IPSS', 'IPS'], 'sector': 2 },
    'Redbank':      {'capacity': 6,   'yards': ['RDKS'], 'sector': 2},
    'Robina':       {'capacity': 11,  'yards': ['ROBS'], 'sector': 1},
    'Manly':        {'capacity': 3,   'yards': ['MNY'], 'sector': 3},
    'Beenleigh':    {'capacity': 8,   'yards': ['BNHS'], 'sector': 1 },
    'Mayne West':   {'capacity': '/',  'yards': ['ETB', 'ETF', 'ETS', 'MWS', 'RS', 'BHI'],},
    'Mayne North':  {'capacity': '/',  'yards': ['YN', 'MNS'], 'sector': 2},
    'Mayne East':   {'capacity': '/',  'yards': ['MES'], 'sector': 1,},
    'Petrie':       {'capacity': 1,   'yards': ['PETS'], 'sector': 1},
    'Kippa-Ring':   {'capacity': 10,  'yards': ['KPRS'], 'sector': 1,},
    'Caboolture':   {'capacity': 9,   'yards': ['CAE', 'CAW', 'CAB'], 'sector': 1 },
    'Elimbah':      {'capacity': 8,   'yards': ['EMHS'], 'sector': 1},
    'Woombye':      {'capacity': 4,   'yards': ['WOBS'], 'sector': 1,},
    'Nambour':      {'capacity': 3,   'yards': ['NBR'], 'sector': 1 },
    'Gympie North': {'capacity': 1,   'yards': ['GYN'], 'sector': 1},
    'Banyo':        {'capacity': 4,   'yards': ['BQYS'], 'sector': 2},
    'Clapham':      {'capacity': '/',  'yards': ['CPM'], 'sector': 1,},
    'Ormeau':       {'capacity': '/',  'yards': ['ORMS'], 'sector': 1,},
    'Beerwah South':{'capacity': 8,   'yards': ['BWHS'], 'sector': 1},
    'Birtinya':     {'capacity': '/', 'yards': ['BIRS'], 'sector': 1}
}


# update internal list of non stable yards 
NON_STABLE_LOCATIONS = ['IPS','MNY','CAB','NBR','GYN','RS','BHI']


### STYLING (colours)

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



# Explicit override
TRAIN_TYPE_MASK = {
    'empty_6-rep': 'Empty_6-QMU',
    '6-rep': '6-QMU',
    '6-qmu_(aw0)_surface': 'Empty_6-QMU',
    '6-qmu_(aw3)_surface': '6-QMU',
    '6-ngr_(aw0)_surface': 'Empty_6-NGR',
    '6-ngr_(aw3)_surface': '6-NGR',
    'qmu_s': '6-QMU',
    'empty_qmu_s': 'Empty_6-QMU',
    '6-ngr_s': '6-NGR',
    'empty_6-ngr_s': 'Empty_6-NGR',
    'ngr_s': '6-NGR',
}


##### comments

STEPS_COL = [
            '1. Determine the location where each Run starts and finishes.',
            '2. By Unit type by Day, count the number of Runs that start or finish at each location.',
            '3. Find where start and finish counts do not match over the day.',
            '4. Find where start and finish counts do not match over the week.'
            ]