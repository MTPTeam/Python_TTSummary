
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

# Universal Reverse Map (maps name/alias back to the ID)
NAME_TO_ID = {}
for uid, info in WEEKDAY_KEYS_MASTER.items():
    for val in info.values():
        NAME_TO_ID[val.lower()] = uid


SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1'] 


##### UNITS / TRAINTYPES 
SORT_ORDER_UNIT = ['QMU', 'REP','NGR','NGRE','IMU100','EMU','SMU','HYBRID', 'DEPT']

### LOCATIONS (YARDS/STATIONS)
# if new location found, update locations , flag it 
# print new location in excel file for easy debugging 
# update stabling yard locations here 
YARDS = {
    'Wulkuraka':    {'capacity': 11,  'yards': ['WFE', 'WFW', 'FEE']},
    'Ipswich':      {'capacity': 7,   'yards': ['IPSS', 'IPS']},
    'Redbank':      {'capacity': 6,   'yards': ['RDKS']},
    'Robina':       {'capacity': 11,  'yards': ['ROBS']},
    'Manly':        {'capacity': 3,   'yards': ['MNY']},
    'Beenleigh':    {'capacity': 8,   'yards': ['BNHS']},
    'Mayne West':   {'capacity': '/',  'yards': ['ETB', 'ETF', 'ETS', 'MWS', 'RS', 'BHI']},
    'Mayne North':  {'capacity': '/',  'yards': ['YN', 'MNS']},
    'Mayne East':   {'capacity': '/',  'yards': ['MES']},
    'Petrie':       {'capacity': 1,   'yards': ['PETS']},
    'Kippa-Ring':   {'capacity': 10,  'yards': ['KPRS']},
    'Caboolture':   {'capacity': 9,   'yards': ['CAE', 'CAW', 'CAB']},
    'Elimbah':      {'capacity': 8,   'yards': ['EMHS']},
    'Woombye':      {'capacity': 4,   'yards': ['WOBS']},
    'Nambour':      {'capacity': 3,   'yards': ['NBR']},
    'Gympie North': {'capacity': 1,   'yards': ['GYN']},
    'Banyo':        {'capacity': 4,   'yards': ['BQYS']},
    'Clapham':      {'capacity': '/',  'yards': ['CPM']},
    'Ormeau':       {'capacity': '/',  'yards': ['ORMS']},
    'Beerwah South':{'capacity': 8,   'yards': ['BWHS']},
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
QMU = "#A7B48D"


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