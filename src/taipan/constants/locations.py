# SINGLE SOURCE OF TRUTH FOR ALL LOCATION BASED CONSTANTS


# =============================================================================
# stations  = every network-relevant location keyed by station code
# yard-only codes (no VRT, no routing role) live in YARDS only
# lines     = lightweight metadata only (no station lists, no VRTs)

# Derive anything on the fly as so;
# all non-revenue:       [c for c,s in network['stations'].items() if s['non_revenue']]
# all stations on line:  [c for c,s in network['stations'].items() if s['line'] == 'Beenleigh']
# byline termini:        [c for c,s in network['stations'].items() if s['byline_terminus']]
# VRT for a station:     network['stations']['BNH']['vrt']
# VRT for a line:        get_vrt_for_line('Beenleigh')

# =============================================================================

STATIONS_MASTER = {
# -------------------------------------------------------------------------
# LINES  - metadata only
# -------------------------------------------------------------------------
'lines': {
    'Beenleigh':                 {'sector': 1,    'terminus': 'BNH'},
    'Caboolture - Gympie North': {'sector': 1,    'terminus': 'GYN'},
    'Cleveland':                 {'sector': 3,    'terminus': 'CVN'},
    'Doomben':                   {'sector': 2,    'terminus': 'DBN'},
    'Ferny Grove':               {'sector': 3,    'terminus': 'FYG'},
    'Varsity Lakes - Airport':   {'sector': 1,    'terminus': 'VYS'},
    'Ipswich - Rosewood':        {'sector': 2,    'terminus': 'IPS'},
    'Redcliffe':                 {'sector': 1,    'terminus': 'KPR'},
    'Shorncliffe':               {'sector': 2,    'terminus': 'SHC'},
    'Springfield':               {'sector': 2,    'terminus': 'SFC'},
    'Inner City':                {'sector': None, 'terminus': 'RS'},
    'Normanby':                  {'sector': None, 'terminus': 'ETS'},
},

# -------------------------------------------------------------------------
# STATIONS - all network-relevant locations (revenue + routing/VRT)
#
#   BNHS, BNT, EMHS, WOBS, RKET, PETS, KPRS, VYST, ROBS, IPSS,
#   BQYS, WFE, WFW, FEE, WUL, YLE, RDKS,
#   MNS, MES, MWS, YN, YNA, CPM, MYJ, STP, NTP, BHNJ, LBR,
#   MEJ, SLYJ, MNYE, YLYJ, TNYBCHJ, ETF, LJN, MNE
#
# Fields:
#   name             human-readable name
#   line             line this location belongs to (None = unassigned)
#   sector           operating sector (1, 2, 3, or None)
#   shared_sector    if this station is shared across sectors shared_sectors will represent all possible sectors, and sectors will be None
#   non_revenue      True = not a passenger stop 
#   byline_terminus  True = displayed as a line terminus
#   vrt              (order, dist) in the line's VRT chain
#                    negative = beyond Roma St toward airport/south (im assuming second part of tuple is some internal form of distance, but will get refactored out soon)
# -------------------------------------------------------------------------
'stations': {

    # --- Beenleigh line ---------------------------------------------------
    'BNH':  {'name': 'Beenleigh',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (28, 2879)},
    'HVW':  {'name': 'Holmview',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (27, 2745)},
    'EDL':  {'name': "Eden's Landing",     'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (26, 2624)},
    'BTI':  {'name': 'Bethania',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (25, 2518)},
    'LGL':  {'name': 'Loganlea',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (24, 2353)},
    'KGT':  {'name': 'Kingston',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (23, 2208)},
    'WOI':  {'name': 'Woodridge',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (22, 2027)},
    'TDP':  {'name': 'Trinder Park',       'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (21, 1951)},
    'KRY':  {'name': 'Kuraby',             'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (20, 2070)},
    'FTG':  {'name': 'Fruitgrove',         'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (19, 1636)},
    'RUC':  {'name': 'Runcorn',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (18, 1556)},
    'ATI':  {'name': 'Altandi',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (17, 1463)},
    'SYK':  {'name': 'Sunnybank',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (16, 1368)},
    'BQO':  {'name': 'Banoon',             'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (15, 1279)},
    'CEP':  {'name': 'Coopers Plains',     'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (14, 1600)},
    'SLY':  {'name': 'Salisbury',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1039)},
    'RKE':  {'name': 'Rocklea',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (11, 949)},
    'MQK':  {'name': 'Moorooka',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 869)},
    'MBN':  {'name': 'Meeandah',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (9,  963)},
    'TNY':  {'name': 'Tennyson',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (8,  902)},
    'YLY':  {'name': 'Yeerongpilly',       'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  779)},
    'YRG':  {'name': 'Yeronga',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  707)},
    'FFI':  {'name': 'Fairfield',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (5,  603)},
    'DUP':  {'name': 'Dutton Park',        'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (4,  519)},

    # --- Caboolture - Gympie North line -----------------------------------
    'GYN':  {'name': 'Gympie North',            'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (40, 10613)},
    'GMR':  {'name': 'Glanmire',                'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (39, 9187)},
    'WOO':  {'name': 'Woondum',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (38, 8811)},
    'TRA':  {'name': 'Traveston',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (37, 8393)},
    'COZ':  {'name': 'Cooran',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (36, 8163)},
    'PMQ':  {'name': 'Pomona',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (35, 7673)},
    'COO':  {'name': 'Cooroy',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (34, 7223)},
    'SSE':  {'name': 'Sunrise',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (33, 6978)},
    'EUM':  {'name': 'Eumundi',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (32, 6893)},
    'NHR':  {'name': 'North Arm',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (31, 4300)},
    'YAN':  {'name': 'Yandina',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (30, 6503)},
    'NBR':  {'name': 'Nambour',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (29, 7000)},
    'WOB':  {'name': 'Woombye',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (28, 5693)},
    'PAL':  {'name': 'Palmwoods',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (26, 5483)},
    'EUD':  {'name': 'Eudlo',                   'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (25, 5153)},
    'MOH':  {'name': 'Mooloolah',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (24, 4763)},
    'LSH':  {'name': 'Landsborough',            'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (23, 4433)},
    'BWH':  {'name': 'Beerwah',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (22, 4163)},
    'GSS':  {'name': 'Glasshouse Mountains',    'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (21, 3893)},
    'BEB':  {'name': 'Beerburrum',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (20, 3413)},
    'EMH':  {'name': 'Elimbah',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (19, 3143)},
    'CEN':  {'name': 'Caboolture East Junction','line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (17, 2961)},
    'CAW':  {'name': 'Caboolture West',         'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (16, 3443)},
    # 'CAE': {'name': 'Caboolture East',        'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False, 'vrt': (15, 3400)},
    'CAB':  {'name': 'Caboolture',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (14, 3218)},
    'MYE':  {'name': 'Morayfield',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 2636)},
    'BPY':  {'name': 'Burpengary',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 2414)},
    'NRB':  {'name': 'Narangba',                'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 2653)},
    'DKB':  {'name': 'Dakabin',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 1880)},
    'PET':  {'name': 'Petrie',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (9,  1853)},
    'LWO':  {'name': 'Lawnton',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  1757)},

    # --- Cleveland line ---------------------------------------------------
    'CVN':  {'name': 'Cleveland',        'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': True,  'vrt': (22, 2875)},
    'ORO':  {'name': 'Ormiston',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (21, 2743)},
    'WPT':  {'name': 'Wellington Point', 'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (20, 2592)},
    'BDE':  {'name': 'Birkdale',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (19, 2436)},
    'TNS':  {'name': 'Thorneside',       'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (18, 2285)},
    'LOT':  {'name': 'Lota',             'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (17, 2156)},
    'MNY':  {'name': 'Manly',            'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (16, 1814)},
    'WNC':  {'name': 'Wynnum Central',   'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (15, 1863)},
    'WNM':  {'name': 'Wynnum',           'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (14, 1781)},
    'WYH':  {'name': 'Wynnum North',     'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1691)},
    'LJN':  {'name': 'Lindum Junction',  'line': 'Cleveland', 'sector': 3, 'non_revenue': True,  'byline_terminus': False, 'vrt': (12, 1574)},
    'LDM':  {'name': 'Lindum',           'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 1528)},
    'HMM':  {'name': 'Hemmant',          'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 1414)},
    'MJE':  {'name': 'Murarrie',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  1203)},
    'CNQ':  {'name': 'Cannon Hill',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  1053)},
    'MGS':  {'name': 'Morningside',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  921)},
    'NPR':  {'name': 'Norman Park',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  769)},
    'CRO':  {'name': 'Coorparoo',        'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (5,  680)},
    'BRD':  {'name': 'Buranda',          'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (4,  574)},

    # --- Doomben line -----------------------------------------------------
    'DBN':  {'name': 'Doomben',  'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (10, 1165)},
    'ACO':  {'name': 'Ascot',    'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  1016)},
    'HDR':  {'name': 'Hendra',   'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  928)},
    'CYF':  {'name': 'Clayfield','line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  867)},

    # --- Ferny Grove line -------------------------------------------------
    'FYG':  {'name': 'Ferny Grove',  'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': True,  'vrt': (15, 1445)},
    'KEP':  {'name': 'Keperra',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (14, 1260)},
    'GOQ':  {'name': 'Grovely',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1190)},
    'OXP':  {'name': 'Oxford Park',  'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 1118)},
    'MHQ':  {'name': 'Mitchelton',   'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 1038)},
    'GAO':  {'name': 'Gaythorne',    'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 941)},
    'EGG':  {'name': 'Enoggera',     'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  873)},
    'ADY':  {'name': 'Alderley',     'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  800)},
    'NWM':  {'name': 'Newmarket',    'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  701)},
    'WLQ':  {'name': 'Wilston',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  617)},
    'WID':  {'name': 'Windsor',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (5,  537)},
    'EDJ':  {'name': 'Electric Depot Junction ', 'line': 'Ferny Grove', 'sector': 3, 'non_revenue': True, 'byline_terminus': False, 'vrt': (4, 470)},

    # --- Varsity Lakes / Airport line -------------------------------------
    'VYS':  {'name': 'Varsity Lakes',       'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (16, 3996)},
    'ROB':  {'name': 'Robina',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (15, 3822)},
    'MRC':  {'name': 'Merrimac',            'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 3686)},
    'NRG':  {'name': 'Nerang',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 3524)},
    'HLN':  {'name': 'Helensvale',          'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 3242)},
    'HID':  {'name': 'Hope Island',         'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 3094)},
    'CXM':  {'name': 'Coomera',             'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  2962)},
    'PPA':  {'name': 'Pimpama',             'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  2846)},
    'ORM':  {'name': 'Ormeau',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  2728)},
    'AJN':  {'name': 'Airport Junction',    'line': 'Varsity Lakes - Airport', 'sector': 2, 'non_revenue': True,  'byline_terminus': False, 'vrt': (-7, -747)},
    'BIT':  {'name': 'International Airport','line': 'Varsity Lakes - Airport','sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (-8, -1092)},
    'BDT':  {'name': 'Domestic Airport',    'line': 'Varsity Lakes - Airport', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (-9, -1248)},

    # --- Ipswich - Rosewood line ------------------------------------------
    'RSW':  {'name': 'Rosewood',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (37, 4025)},
    'TAO':  {'name': 'Thagoona',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (35, 3367)},
    'WOQ':  {'name': 'Walloon',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (34, 3138)},
    'KRA':  {'name': 'Karrabin',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (31, 3380)},
    'THS':  {'name': 'Thomas Street','line': 'Ipswich - Rosewood','sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (27, 2682)},
    'IPS':  {'name': 'Ipswich',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (25, 2940)},
    'EIP':  {'name': 'East Ipswich','line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (24, 2436)},
    'BOV':  {'name': 'Booval',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (23, 2343)},
    'BDX':  {'name': 'Bundamba',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (22, 2244)},
    'EBV':  {'name': 'Ebbw Vale',   'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (21, 2117)},
    'DIR':  {'name': 'Dinmore',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (20, 2024)},
    'RVV':  {'name': 'Riverview',   'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (19, 1918)},
    'RDK':  {'name': 'Redbank',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (18, 1960)},
    'GDQ':  {'name': 'Goodna',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (16, 1588)},
    'GAI':  {'name': 'Gailes',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (15, 1464)},
    'WAC':  {'name': 'Wacol',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (14, 1366)},
    'DAR':  {'name': 'Darra',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (13, 1475)},
    'OXL':  {'name': 'Oxley',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 993)},
    'CQD':  {'name': 'Corinda',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  900)},
    'SHW':  {'name': 'Sherwood',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  780)},
    'GVQ':  {'name': 'Graceville',  'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  696)},
    'CMZ':  {'name': 'Chelmer',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  619)},
    'IDP':  {'name': 'Indooroopilly','line': 'Ipswich - Rosewood','sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (5,  526)},
    'TIQ':  {'name': 'Taringa',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (4,  417)},
    'TWG':  {'name': 'Toowong',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (3,  309)},
    'AHF':  {'name': 'Auchenflower','line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (2,  231)},
    'MTZ':  {'name': 'Milton',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (1,  138)},

    # --- Springfield branch -----------------------------------------------
    'SFC':  {'name': 'Springfield Central', 'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (14, 1920)},
    'SFD':  {'name': 'Springfield',         'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1770)},
    'RHD':  {'name': 'Richlands',           'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 1440)},

    # --- Redcliffe line ---------------------------------------------------
    'KPR':  {'name': 'Kippa-Ring',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': True,  'vrt': (22, 2850)},
    'RWL':  {'name': 'Rothwell',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (20, 2640)},
    'MGE':  {'name': 'Mango Hill East', 'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (19, 2550)},
    'MGH':  {'name': 'Mango Hill',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (18, 2400)},
    'MRD':  {'name': 'Murrumba Downs',  'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (17, 2310)},
    'KGR':  {'name': 'Kallangur',       'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (16, 2220)},
    'BPR':  {'name': 'Bray Park',       'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1830)},
    'SPN':  {'name': 'Strathpine',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (12, 1740)},
    'BDS':  {'name': 'Bald Hills',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 1590)},
    'CDE':  {'name': 'Carseldine',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 1380)},
    'ZLL':  {'name': 'Zillmere',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  1290)},
    'GEB':  {'name': 'Geebung',         'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  1200)},
    'SSN':  {'name': 'Sunshine',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (7,  1110)},
    'VGI':  {'name': 'Virginia',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  1020)},

    # --- Shorncliffe line -------------------------------------------------
    'SHC':  {'name': 'Shorncliffe',    'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (19, 2290)},
    'SGE':  {'name': 'Sandgate',       'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (18, 2025)},
    'DEG':  {'name': 'Deagon',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (17, 1586)},
    'NBD':  {'name': 'North Boondall', 'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (16, 1499)},
    'BZL':  {'name': 'Boondall',       'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (15, 1422)},
    'NUD':  {'name': 'Nudgee',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (14, 1261)},
    'BQY':  {'name': 'Banyo',          'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (13, 1182)},
    'BHA':  {'name': 'Bindha',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (11, 1106)},
    'NTG':  {'name': 'Northgate',      'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (10, 1350)},
    'NND':  {'name': 'Nundah',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (9,  903)},
    'TBU':  {'name': 'Toombul',        'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (8,  834)},
    'EGJ':  {'name': 'Eagle Junction', 'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (6,  714)},
    'WWI':  {'name': 'Wooloowin',      'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False, 'vrt': (5,  631)},
    'AIN':  {'name': 'Albion',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': True,  'vrt': (4,  551)},

    # --- Inner City / City loop -------------------------------------------
    'RS':   {'name': 'Roma Street',     'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': True,  'vrt': (0,   0)},
    'BHI':  {'name': 'Bowen Hills',     'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False, 'vrt': (3,   324)},
    'BRC':  {'name': 'Fortitude Valley','line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False, 'vrt': (2,   264)},
    'BNC':  {'name': 'Central',         'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False, 'vrt': (1,   140)},
    'PKR':  {'name': 'Park Road',       'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': True,  'vrt': (-3, -447)},
    'SBA':  {'name': 'South Bank',      'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (-2, -316)},
    'SBE':  {'name': 'South Brisbane',  'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': False, 'vrt': (-1, -226)},

    # --- Normanby / Exhibition --------------------------------------------
    'ETS':  {'name': 'Exhibition Terminal South', 'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False, 'vrt': (6, 800)},
    'CAM':  {'name': 'Camera',                    'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False, 'vrt': (5, 680)},
    'EXH':  {'name': 'Exhibition',                'line': 'Normanby', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': (4, 560)},
    'BOG':  {'name': 'Boggo Rd',                'line': 'Normanby', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': None},

    'NBY':  {'name': 'Normanby',                  'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False, 'vrt': (3, 410)},
    'RSF':  {'name': 'Roma Street Fork',          'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False, 'vrt': (2, 170)},
    'RSWJ': {'name': 'Roma Street West Junction', 'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False, 'vrt': (1, 140)},
},}

# =============================================================================
# CONVENIENCE HELPERS - derive everything from the single source above
# Using for slow refactor propagation across files 
# =============================================================================

def get_non_revenue():
    # All non-revenue station codes.
    return [c for c, s in STATIONS_MASTER['stations'].items() if s['non_revenue']]

def get_stations_on_line(line_name):
    #All station codes belonging to a given line.
    return [c for c, s in STATIONS_MASTER['stations'].items() if s['line'] == line_name]

def get_byline_termini():
    #All (code, name) pairs that are displayed byline termini
    return [(c, s['name']) for c, s in STATIONS_MASTER['stations'].items() if s['byline_terminus']]

def get_vrt_for_line(line_name):
    #Returns {code: vrt_tuple} ordered by VRT position for a given line.
    entries = {
    c: s['vrt']
    for c, s in STATIONS_MASTER['stations'].items()
    if s['line'] == line_name and s['vrt'] is not None
    }
    return dict(sorted(entries.items(), key=lambda x: x[1][0], reverse=True))

def station_lookup(code):
    #Full data for a single station code.
    return STATIONS_MASTER['stations'].get(code)



#### STABLING YARDS DICTIONARY
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
