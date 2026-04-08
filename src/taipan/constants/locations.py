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
    'BNH':  {'name': 'Beenleigh',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'HVW':  {'name': 'Holmview',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'EDL':  {'name': "Eden's Landing",     'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BTI':  {'name': 'Bethania',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'LGL':  {'name': 'Loganlea',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'KGT':  {'name': 'Kingston',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'WOI':  {'name': 'Woodridge',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'TDP':  {'name': 'Trinder Park',       'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'KRY':  {'name': 'Kuraby',             'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'FTG':  {'name': 'Fruitgrove',         'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'RUC':  {'name': 'Runcorn',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'ATI':  {'name': 'Altandi',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'SYK':  {'name': 'Sunnybank',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BQO':  {'name': 'Banoon',             'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'CEP':  {'name': 'Coopers Plains',     'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'SLY':  {'name': 'Salisbury',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'RKE':  {'name': 'Rocklea',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'MQK':  {'name': 'Moorooka',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MBN':  {'name': 'Meeandah',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'TNY':  {'name': 'Tennyson',           'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'YLY':  {'name': 'Yeerongpilly',       'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'YRG':  {'name': 'Yeronga',            'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'FFI':  {'name': 'Fairfield',          'line': 'Beenleigh', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'DUP':  {'name': 'Dutton Park',        'line': 'Beenleigh', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},

    # --- Caboolture - Gympie North line -----------------------------------
    'GYN':  {'name': 'Gympie North',            'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'GMR':  {'name': 'Glanmire',                'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'WOO':  {'name': 'Woondum',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'TRA':  {'name': 'Traveston',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'COZ':  {'name': 'Cooran',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'PMQ':  {'name': 'Pomona',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'COO':  {'name': 'Cooroy',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'SSE':  {'name': 'Sunrise',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'EUM':  {'name': 'Eumundi',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'NHR':  {'name': 'North Arm',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'YAN':  {'name': 'Yandina',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'NBR':  {'name': 'Nambour',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'WOB':  {'name': 'Woombye',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'PAL':  {'name': 'Palmwoods',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'EUD':  {'name': 'Eudlo',                   'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MOH':  {'name': 'Mooloolah',               'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'LSH':  {'name': 'Landsborough',            'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BWH':  {'name': 'Beerwah',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'GSS':  {'name': 'Glasshouse Mountains',    'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BEB':  {'name': 'Beerburrum',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'EMH':  {'name': 'Elimbah',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'CEN':  {'name': 'Caboolture East Junction','line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'CAW':  {'name': 'Caboolture West',         'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    # 'CAE': {'name': 'Caboolture East',        'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': True,  'byline_terminus': False},
    'CAB':  {'name': 'Caboolture',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'MYE':  {'name': 'Morayfield',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BPY':  {'name': 'Burpengary',              'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'NRB':  {'name': 'Narangba',                'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'DKB':  {'name': 'Dakabin',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'PET':  {'name': 'Petrie',                  'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'LWO':  {'name': 'Lawnton',                 'line': 'Caboolture - Gympie North', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},

    # --- Cleveland line ---------------------------------------------------
    'CVN':  {'name': 'Cleveland',        'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': True},
    'ORO':  {'name': 'Ormiston',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WPT':  {'name': 'Wellington Point', 'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'BDE':  {'name': 'Birkdale',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'TNS':  {'name': 'Thorneside',       'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'LOT':  {'name': 'Lota',             'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'MNY':  {'name': 'Manly',            'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WNC':  {'name': 'Wynnum Central',   'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WNM':  {'name': 'Wynnum',           'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WYH':  {'name': 'Wynnum North',     'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'LJN':  {'name': 'Lindum Junction',  'line': 'Cleveland', 'sector': 3, 'non_revenue': True,  'byline_terminus': False},
    'LDM':  {'name': 'Lindum',           'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'HMM':  {'name': 'Hemmant',          'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'MJE':  {'name': 'Murarrie',         'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'CNQ':  {'name': 'Cannon Hill',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'MGS':  {'name': 'Morningside',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'NPR':  {'name': 'Norman Park',      'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'CRO':  {'name': 'Coorparoo',        'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'BRD':  {'name': 'Buranda',          'line': 'Cleveland', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},

    # --- Doomben line -----------------------------------------------------
    'DBN':  {'name': 'Doomben',  'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'ACO':  {'name': 'Ascot',    'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'HDR':  {'name': 'Hendra',   'line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'CYF':  {'name': 'Clayfield','line': 'Doomben', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},

    # --- Ferny Grove line -------------------------------------------------
    'FYG':  {'name': 'Ferny Grove',  'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': True},
    'KEP':  {'name': 'Keperra',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'GOQ':  {'name': 'Grovely',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'OXP':  {'name': 'Oxford Park',  'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'MHQ':  {'name': 'Mitchelton',   'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'GAO':  {'name': 'Gaythorne',    'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'EGG':  {'name': 'Enoggera',     'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'ADY':  {'name': 'Alderley',     'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'NWM':  {'name': 'Newmarket',    'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WLQ':  {'name': 'Wilston',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'WID':  {'name': 'Windsor',      'line': 'Ferny Grove', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'EDJ':  {'name': 'Electric Depot Junction ', 'line': 'Ferny Grove', 'sector': 3, 'non_revenue': True, 'byline_terminus': False},

    # --- Varsity Lakes / Airport line -------------------------------------
    'VYS':  {'name': 'Varsity Lakes',       'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'ROB':  {'name': 'Robina',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MRC':  {'name': 'Merrimac',            'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'NRG':  {'name': 'Nerang',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'HLN':  {'name': 'Helensvale',          'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'HID':  {'name': 'Hope Island',         'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'CXM':  {'name': 'Coomera',             'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'PPA':  {'name': 'Pimpama',             'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'ORM':  {'name': 'Ormeau',              'line': 'Varsity Lakes - Airport', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'AJN':  {'name': 'Airport Junction',    'line': 'Varsity Lakes - Airport', 'sector': 2, 'non_revenue': True,  'byline_terminus': False},
    'BIT':  {'name': 'International Airport','line': 'Varsity Lakes - Airport','sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BDT':  {'name': 'Domestic Airport',    'line': 'Varsity Lakes - Airport', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},

    # --- Ipswich - Rosewood line ------------------------------------------
    'RSW':  {'name': 'Rosewood',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'TAO':  {'name': 'Thagoona',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'WOQ':  {'name': 'Walloon',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'KRA':  {'name': 'Karrabin',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'THS':  {'name': 'Thomas Street','line': 'Ipswich - Rosewood','sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'IPS':  {'name': 'Ipswich',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'EIP':  {'name': 'East Ipswich','line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BOV':  {'name': 'Booval',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BDX':  {'name': 'Bundamba',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'EBV':  {'name': 'Ebbw Vale',   'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'DIR':  {'name': 'Dinmore',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'RVV':  {'name': 'Riverview',   'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'RDK':  {'name': 'Redbank',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'GDQ':  {'name': 'Goodna',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'GAI':  {'name': 'Gailes',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'WAC':  {'name': 'Wacol',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'DAR':  {'name': 'Darra',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'OXL':  {'name': 'Oxley',       'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'CQD':  {'name': 'Corinda',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'SHW':  {'name': 'Sherwood',    'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'GVQ':  {'name': 'Graceville',  'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'CMZ':  {'name': 'Chelmer',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'IDP':  {'name': 'Indooroopilly','line': 'Ipswich - Rosewood','sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'TIQ':  {'name': 'Taringa',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'TWG':  {'name': 'Toowong',     'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'AHF':  {'name': 'Auchenflower','line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'MTZ':  {'name': 'Milton',      'line': 'Ipswich - Rosewood', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},

    # --- Springfield branch -----------------------------------------------
    'SFC':  {'name': 'Springfield Central', 'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'SFD':  {'name': 'Springfield',         'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'RHD':  {'name': 'Richlands',           'line': 'Springfield', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},

    # --- Redcliffe line ---------------------------------------------------
    'KPR':  {'name': 'Kippa-Ring',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': True},
    'RWL':  {'name': 'Rothwell',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MGE':  {'name': 'Mango Hill East', 'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MGH':  {'name': 'Mango Hill',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'MRD':  {'name': 'Murrumba Downs',  'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'KGR':  {'name': 'Kallangur',       'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BPR':  {'name': 'Bray Park',       'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'SPN':  {'name': 'Strathpine',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BDS':  {'name': 'Bald Hills',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'CDE':  {'name': 'Carseldine',      'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'ZLL':  {'name': 'Zillmere',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'GEB':  {'name': 'Geebung',         'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'SSN':  {'name': 'Sunshine',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'VGI':  {'name': 'Virginia',        'line': 'Redcliffe', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},

    # --- Shorncliffe line -------------------------------------------------
    'SHC':  {'name': 'Shorncliffe',    'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},
    'SGE':  {'name': 'Sandgate',       'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'DEG':  {'name': 'Deagon',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'NBD':  {'name': 'North Boondall', 'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BZL':  {'name': 'Boondall',       'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'NUD':  {'name': 'Nudgee',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BQY':  {'name': 'Banyo',          'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'BHA':  {'name': 'Bindha',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'NTG':  {'name': 'Northgate',      'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'NND':  {'name': 'Nundah',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'TBU':  {'name': 'Toombul',        'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'EGJ':  {'name': 'Eagle Junction', 'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'WWI':  {'name': 'Wooloowin',      'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': False},
    'AIN':  {'name': 'Albion',         'line': 'Shorncliffe', 'sector': 2, 'non_revenue': False, 'byline_terminus': True},

    # --- Inner City / City loop -------------------------------------------
    'RS':   {'name': 'Roma Street',     'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': True},
    'BHI':  {'name': 'Bowen Hills',     'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False},
    'BRC':  {'name': 'Fortitude Valley','line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False},
    'BNC':  {'name': 'Central',         'line': 'Inner City', 'sector': None, 'shared_sectors': [2,3], 'non_revenue': False, 'byline_terminus': False},
    'PKR':  {'name': 'Park Road',       'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': True},
    'SBA':  {'name': 'South Bank',      'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},
    'SBE':  {'name': 'South Brisbane',  'line': 'Inner City', 'sector': 3, 'non_revenue': False, 'byline_terminus': False},

    # --- Normanby / Exhibition --------------------------------------------
    'ETS':  {'name': 'Exhibition Terminal South', 'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False},
    'CAM':  {'name': 'Camera',                    'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False},
    'EXH':  {'name': 'Exhibition',                'line': 'Normanby', 'sector': 1, 'non_revenue': False, 'byline_terminus': False},
    'BOG':  {'name': 'Boggo Rd',                'line': 'Normanby', 'sector': 1, 'non_revenue': False, 'byline_terminus': False, 'vrt': None},

    'NBY':  {'name': 'Normanby',                  'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False},
    'RSF':  {'name': 'Roma Street Fork',          'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False},
    'RSWJ': {'name': 'Roma Street West Junction', 'line': 'Normanby', 'sector': None, 'non_revenue': True,  'byline_terminus': False},
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
   'Wulkuraka':     {'capacity': 8,   'ngr_only': True,  'yards': ['WFE', 'WFW', 'FEE'], 'sector': 2}, # NGR only yard
   'Ipswich':       {'capacity': 6.5, 'qr_only': True,   'yards': ['IPSS', 'IPS'],        'sector': 2}, # QR only yard 
   'Redbank':       {'capacity': 6,   'qr_only': True,   'yards': ['RDKS'],               'sector': 2},
   'Robina':        {'capacity': 11,  'ngr_only': True,  'yards': ['ROBS'],               'sector': 1},
   'Manly':         {'capacity': 3,   'qr_only': True,   'yards': ['MNY'],                'sector': 3},
   'Beenleigh':     {'capacity': 8,   'qr_only': True,   'yards': ['BNHS'],               'sector': 1},
   'Mayne West':    {'capacity': 29,  'yards': ['ETB', 'ETF', 'ETS', 'MWS', 'RS', 'BHI']},  # mixed yard, one total capacity no fleet restriction 
   'Mayne North':   {'capacity': 18,  'yards': ['YN', 'MNS'],         'sector': 2},
   'Mayne East':    {'capacity': 17,  'yards': ['MES'],                'sector': 1},
   'Petrie':        {'capacity': 1,   'qr_only': True,   'yards': ['PETS'],               'sector': 1},
   'Kippa-Ring':    {'capacity': 10,  'ngr_only': True,  'yards': ['KPRS'],               'sector': 1},
   'Caboolture':    {'capacity': 10,  'qr_only': True,   'yards': ['CAE', 'CAW', 'CAB'],  'sector': 1},
   'Elimbah':       {'capacity': 8,   'ngr_only': True,  'yards': ['EMHS'],               'sector': 1},
   'Woombye':       {'capacity': 4,   'ngr_only': True,  'yards': ['WOBS'],               'sector': 1},
   'Nambour':       {'capacity': 3,   'qr_only': True,   'yards': ['NBR'],                'sector': 1},
   'Gympie North':  {'capacity': 1,   'qr_only': True,   'yards': ['GYN'],                'sector': 1},
   'Banyo':         {'capacity': 4,   'ngr_only': True,  'yards': ['BQYS'],               'sector': 2},
   'Clapham':       {'capacity': 15,  'yards': ['CPM'],                'sector': 1},
   'Ormeau':        {'capacity': 20,  'yards': ['ORMS'],               'sector': 1},
   'Beerwah South': {'capacity': 8,   'ngr_only': True,  'yards': ['BWHS'],               'sector': 1},
   # Not yet online
   'Birtinya':      {'capacity': None, 'yards': ['BIRS'], 'sector': 1},
}


# other locations that are not stations and not yards

MISC_LOCATIONS = {
    # turnbacks and other places 
    'VYST': { 'name': 'Varsity Lakes Turnback', 'sector': 1 },
    'BNT':  { 'name': 'Beenleigh Turnback',     'sector': 1 }, 
}


# update internal list of non stable yards 
NON_STABLE_LOCATIONS = ['IPS','MNY','CAB','NBR','GYN','RS','BHI']