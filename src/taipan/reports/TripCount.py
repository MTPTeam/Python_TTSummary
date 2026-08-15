import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import xlsxwriter
import time
import os
import sys
import shutil

from taipan.gui.base import select_file, select_option_safe, show_info_safe

import traceback
import logging
from PyQt6.QtWidgets import QApplication

# Testing change for github

### CreateFile toggles whether text files are generated on running the script
### OpenWorkbook will subsequently open the newly created files for the user
### ProcessDoneMessagebox toggles whether a dialogue box is created after script finishes running
###  - adds a 15 second pause if script errors

### "= False" line can be left on permanently to facilitate easy toggling
### "= True" lines must be turned on when uploading files to the taipan script library
# --------------------------------------------------------------------------------------------------- #
OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook   = True
# --------------------------------------------------------------------------------------------------- #


### Used to classify into AM Peak, PM Peak, Off Peak, etc
ampeak_srt = '06:00:00'
ampeak_end = '09:00:00'
pmpeak_srt = '15:30:00'
pmpeak_end = '18:30:00'






### Used to filter out stations where passengers cannot board
### Want to only iterate over revenue locations
non_revenue_stations = [
    'RSWJ',
    'RSF',
    'MNE',
    'LJN',
    'ETF',
    'EDJ',
    'YLE',
    'ETS',
    'CAM',
    'EXH',
    'NBY',
    'YNA',
    'YN',
    'MYJ',
    'AJN',
    'IPSS',
    'VYST',
    'CAW',
    'CAE',
    'CEN',
    'BNHS',
    'BNT',
    'EMHS',
    'RKET',
    'WOBS',
    'PETS',
    'KPRS',
    'RDKS'
    'BQYS',
    'ROBS',
    'WUL',
    'WFE'
    'FEE',
    'WFW',
    
    
    
    
    'NTP',
    'STP',
    'SIG9A',
    'SIG10D',
    'ZZZTJN',
    'TNYBCHJ',
    'YLYJ',
    'BHNJ',
    'MEJ',
    'ORMS',
    'MNYE',
    
    
    
    #F3S
    'MNS',
    'MES',
    'MWS',
    'CPM',
    
    
    'NHR', #North Arm
    'SSE', #Sunrise
    'WOO', #Woondum
    'GMR', #Glanmire
    
    'DUP', #Dutton Park
    'RKE', #Rocklea
    
    'BWJ',    #Beerwah Junction
    'BEJ',    #Beewah East Junction
    'MNYE',   #Mayne North Yard Entrance
    'BHNJ',   #Bowen Hills North Jn
    'SIG10D', #Signal 10 Departure
    'KPRS',   #Kippa-Ring Stable
    'ORMJ',   #Ormeau Junction
    'SLYJ',   #Salisbury Junction
    'YLYJ',   #Yeerongpilly Junction
    'STP',    #Southern Tunnel Portal
    'NTP',    #Northern Tunnel Portal
    'LBR',    #Land Bridge
    'ZZZTJN', #Tunnel Jn
    'MEJ',    #Mayne East Junction
    'CYJ',    #Clapham Yard Junction
    'SIG9A',  #Signal 9 Arrival
    'MES',    #Mayne East Yard
    'FRK',    #Fork Timing Point
    'TNYBCHJ',#Tennyson Branch Junction
    ]


weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}


def TTS_TC(path, mypath = None):
    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir
    
    try:

        station = select_option_safe("Select CBD Reference Station", "Please select a CBD reference station:", [("Roma Street - RS", "Roma Street"), ("Central Station - BNC", "Central Station")])

        if station is None:

            print("No station selected. Exiting.")

            return
        
        print(f"Selected Station: {station}\n")
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        if __name__ == "__main__":
            app = QApplication(sys.argv)
            print(filename,'\n')
        tree = ET.parse(filename)
        root = tree.getroot()
        
        filename = filename[:-4]
        if station == "Roma Street":
            filename_xlsx = f'TripCountROMA-{filename}.xlsx'
        elif station == "Central Station":
            filename_xlsx = f'TripCountCENTRAL-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        
    
        ### Check for duplicate train numbers before executing the script
        ### Print warning for user if duplicates exist
        ### Print out all duplicates
        tn_list = []
        tn_doubles = []
        for train in root.iter('train'):
            tn  = train.attrib['number']
            day = train[0][0][0].attrib['weekdayKey']
            if (tn,day) in tn_list: tn_doubles.append((tn,day))
            tn_list.append((tn,day))
                
        unique_codes = list(set(day for _, day in tn_list))
        daysinfile = [weekdaykey_dict.get(code) for code in unique_codes]
        daysinfile = [weekdaykey_dict.get(code) for code in unique_codes]

        has_full_week = {'Mon-Thu','Fri','Sat','Sun'}.issubset(daysinfile)
        has_fri_sat_only = set(daysinfile) == {'Fri','Sat'}

        if set(daysinfile) == {'Fri', 'Sat'}:

            apply_ratio_method = select_option_safe(
                "Only Fri and Sat trains detected in the RSX file",
                "Apply Current Timetable based Ratio Method for Weekly Trip Count Estimates?",
                [("Yes", True), ("No", False)]
            )

            if apply_ratio_method is None:
                return  # User clicked X, exit script

        else:
            apply_ratio_method = False
            
        if tn_doubles:
            print('           Error: Duplicate train numbers')
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit()  
        
        start_time = time.time()
        
        
        
        
        
        
        
        ThreeSector = False
        revtrains = [x for x in root.iter('train') if 'Empty' not in x[1][0].attrib['trainTypeId']]
        for train in revtrains:
            entries = [x for x in train.iter('entry')]
            if 'RTL' in [x.attrib['stationID'] for x in entries]:
                ThreeSector = True
                break        
        # print(str(3 if ThreeSector else 2), 'Sector timetable\n')
        
        
        
        ### uniquestations_dict and network_vrt_dict are used to determine what Line that trip belongs to
        ### Virtual run time (vrt) dictionaries for each line are used to categorised trips into PMP, AMP, OffPeak etc when trip has no Central timing point
        ###   (Useful for timetables with closures)
        vrt_2Beenleigh = {
            'BNT':     (30, 3910),
            'BNHS':    (29, 3990),
            'BNH':     (28, 2879),
            'HVW':     (27, 2745),
            'EDL':     (26, 2624),
            'BTI':     (25, 2518),
            'LGL':     (24, 2353),
            'KGT':     (23, 2208),
            'WOI':     (22, 2027),
            'TDP':     (21, 1951),
            'KRY':     (20, 2070), 
            'FTG':     (19, 1636),
            'RUC':     (18, 1556),
            'ATI':     (17, 1463),
            'SYK':     (16, 1368),
            'BQO':     (15, 1279),
            'CEP':     (14, 1600),
            'SLY':     (13, 1039),
            'RKET':    (12, 1100),
            'RKE':     (11, 949),
            'MQK':     (10, 869),
            'MBN':     (9,  963),
            'TNY':     (8,  902),
            'YLY':     (7,  779),
            'YRG':     (6,  707),
            'FFI':     (5,  603),
            'DUP':     (4,  519),
            'PKR':     (3,  441),
            'SBA':     (2,  286),
            'SBE':     (1,  205),
            'RS':      (0,  0)
            }
        
        
        vrt_2Caboolture = {
            'CEN':     (17, 2961),
            'CAW':     (16, 3443),
            # 'CAE':     (15, 3400), 
            'CAB':     (14, 3218), 
            'MYE':     (13, 2636),
            'BPY':     (12, 2414),
            'NRB':     (11, 2653),
            'DKB':     (10, 1880),
            'PET':     (9,  1853),
            'PETS':    (8,  1711),
            'LWO':     (7,  1757),
            'VGI':     (6,  1300),
            'NTG':     (5,  1082),
            'EGJ':     (4,  713),
            'BHI':     (3,  500),
            'BRC':     (2,  0),
            'BNC':     (1,  0),
            'RS':      (0,  0)
            }
        
        vrt_2GympieNth = {
            # 'CRD': (),
            # 'AUR': (),
            'GYN':     (40, 10613),
            'GMR':     (39, 9187),
            'WOO':     (38, 8811),
            'TRA':     (37, 8393),
            'COZ':     (36, 8163),
            'PMQ':     (35, 7673),
            'COO':     (34, 7223),
            'SSE':     (33, 6978),
            'EUM':     (32, 6893),
            'NHR':     (31, 4300),
            'YAN':     (30, 6503),
            'NBR':     (29, 7000), 
            'WOB':     (28, 5693),
            'WOBS':    (27, 5363),
            'PAL':     (26, 5483),
            'EUD':     (25, 5153),
            'MOH':     (24, 4763),
            'LSH':     (23, 4433),
            'BWH':     (22, 4163),
            'GSS':     (21, 3893),
            'BEB':     (20, 3413),
            'EMH':     (19, 3143),
            'EMHS':    (18, 3768),
            'CEN':     (17, 2961),
            'CAW':     (16, 3443),
            # 'CAE':     (15, 3400), 
            'CAB':     (14, 3218), 
            'MYE':     (13, 2636),
            'BPY':     (12, 2414),
            'NRB':     (11, 2653),
            'DKB':     (10, 1880),
            'PET':     (9,  1853),
            'PETS':    (8,  1711),
            'LWO':     (7,  1757),
            'VGI':     (6,  1300),
            'NTG':     (5,  1082),
            'EGJ':     (4,  713),
            'BHI':     (3,  500),
            'BRC':     (2,  0),
            'BNC':     (1,  0),
            'RS':      (0,  0)
            }
        
        
        vrt_2Cleveland = {
            'CVN':     (22, 2875),
            'ORO':     (21, 2743),
            'WPT':     (20, 2592),
            'BDE':     (19, 2436),
            'TNS':     (18, 2285),
            'LOT':     (17, 2156),
            'MNY':     (16, 1814),
            'WNC':     (15, 1863),
            'WNM':     (14, 1781),
            'WYH':     (13, 1691),
            'LJN':     (12, 1574),
            'LDM':     (11, 1528),
            'HMM':     (10, 1414),
            'MJE':     (9,  1203),
            'CNQ':     (8,  1053),
            'MGS':     (7,  921),
            'NPR':     (6,  769),
            'CRO':     (5,  680),
            'BRD':     (4,  574),
            'PKR':     (3,  700),
            'SBA':     (2,  316),
            'SBE':     (1,  226),
            'RS':      (0,  0)
            }
        
        
        vrt_2Doomben = {
            'DBN':     (10, 1165),
            'ACO':     (9,  1016),
            'HDR':     (8,  928),
            'CYF':     (7,  867),
            'EGJ':     (6,  759),
            'WWI':     (5,  676),
            'AIN':     (4,  676),
            'BHI':     (3,  398),
            'BRC':     (2,  299),
            'BNC':     (1,  149),
            'RS':      (0,  0)
            }
        
        
        vrt_2FernyGrove = {
            'FYG':     (15, 1445),
            'KEP':     (14, 1260),
            'GOQ':     (13, 1190),
            'OXP':     (12, 1118),
            'MHQ':     (11, 1038),
            'GAO':     (10, 941),
            'EGG':     (9,  873),
            'ADY':     (8,  800),
            'NWM':     (7,  701),
            'WLQ':     (6,  617),
            'WID':     (5,  537),
            'EDJ':     (4,  470),
            'BHI':     (3,  537),
            'BRC':     (2,  257),
            'BNC':     (1,  107),
            'RS':      (0,  0)
            }
        
        
        vrt_2VarsityLs = {
            'VYST':    (14,  4086),
            'VYS':     (13,  3996),
            'ROB':     (12,  3822),
            'ROBS':    (11,  4542),
            'NRG':     (10,  3524),
            'HLN':     (9,   3242),
            'CXM':     (8,   2962),
            'ORM':     (7,   2728),
            'BNH':     (6,   2336),
            'LGL':     (5,   1903),
            'ATI':     (4,   1194),
            'PKR':     (3,   431),
            'SBA':     (2,   278),
            'SBE':     (1,   198),
            'RS':      (0,   0)
            }
        
        vrt_2Airport = {
            'BDT':     (2,1248),
            'BIT':     (1,1092),
            'RS':      (0,0),
            }
        
        vrt_2Ipswich = {
            'IPSS':    (26, 3125),
            'IPS':     (25, 2940), 
            'EIP':     (24, 2436),
            'BOV':     (23, 2343),
            'BDX':     (22, 2244), 
            'EBV':     (21, 2117),
            'DIR':     (20, 2024),
            'RVV':     (19, 1918),
            'RDK':     (18, 1960),
            # 'RDKS':    (17, 1760),
            'GDQ':     (16, 1588),
            'GAI':     (15, 1464),
            'WAC':     (14, 1366),
            'DAR':     (13, 1475),
            'OXL':     (12, 993),
            'TNY':     (11, 600),
            'MBN':     (10, 500),
            'CQD':     (9,  900),
            'SHW':     (8,  780),    
            'GVQ':     (7,  696),
            'CMZ':     (6,  619),
            'IDP':     (5,  526),
            'TIQ':     (4,  417),
            'TWG':     (3,  309),
            'AHF':     (2,  231),
            'MTZ':     (1,  138),
            'RS':      (0,  0)
            }
        
        
        vrt_2Rosewood = {
            'RSW':     (37, 4025),
            'YLE':     (36, 3422),
            'TAO':     (35, 3367),
            'WOQ':     (34, 3138),
            'FWE':     (33, 2933),
            'WFW':     (32, 2962),
            'KRA':     (31, 3380),
            'WUL':     (30, 2762),
            'WFE':     (29, 3642),
            'FEE':     (28, 3012),
            'THS':     (27, 2682),
            'IPSS':    (26, 3125),
            'IPS':     (25, 2940), 
            'EIP':     (24, 2436),
            'BOV':     (23, 2343),
            'BDX':     (22, 2244), 
            'EBV':     (21, 2117),
            'DIR':     (20, 2024),
            'RVV':     (19, 1918),
            'RDK':     (18, 1960),
            # 'RDKS':    (17, 1760),
            'GDQ':     (16, 1588),
            'GAI':     (15, 1464),
            'WAC':     (14, 1366),
            'DAR':     (13, 1475),
            'OXL':     (12, 993),
            'TNY':     (11, 600),
            'MBN':     (10, 500),
            'CQD':     (9,  900),
            'SHW':     (8,  780),    
            'GVQ':     (7,  696),
            'CMZ':     (6,  619),
            'IDP':     (5,  526),
            'TIQ':     (4,  417),
            'TWG':     (3,  309),
            'AHF':     (2,  231),
            'MTZ':     (1,  138),
            'RS':      (0,  0)
            }
        
        
        vrt_2KippaRing = {
            'KPR':     (22, 2850),
            'KPRS':    (21, 3030),
            'RWL':     (20, 2640),
            'MGE':     (19, 2550),
            'MGH':     (18, 2400),
            'MRD':     (17, 2310),
            'KGR':     (16, 2220),
            'PET':     (15, 2070),
            'LWO':     (14, 2400),
            'BPR':     (13, 1830),
            'SPN':     (12, 1740),
            'BDS':     (11, 1590),
            'CDE':     (10, 1380),
            'ZLL':     (9,  1290),
            'GEB':     (8,  1200),
            'SSN':     (7,  1110),
            'VGI':     (6,  1020),
            'NTG':     (5,  870),
            'EGJ':     (4,  660),
            'BHI':     (3,  510),
            'BRC':     (2,  240),
            'BNC':     (1,  120),
            'RS':      (0,  0)
            }
        
        
        vrt_2Shorncliffe = {
            'SHC':     (19, 2290),
            'SGE':     (18, 2025),
            'DEG':     (17, 1586),
            'NBD':     (16, 1499),
            'BZL':     (15, 1422),
            'NUD':     (14, 1261),
            'BQY':     (13, 1182),
            'BQYS':    (12, 1740),
            'BHA':     (11, 1106),
            'NTG':     (10, 1350), 
            'NND':     (9,  903),
            'TBU':     (8,  834),
            'AJN':     (7,  800),
            'EGJ':     (6,  714), 
            'WWI':     (5,  631),
            'AIN':     (4,  551),
            'BHI':     (3,  520),
            'BRC':     (2,  299),
            'BNC':     (1,  149),
            'RS':      (0,  0)
            }
        
        
        vrt_2Springfield = {
            'SFC':     (14, 1920),
            'SFD':     (13, 1770),
            'RHD':     (12, 1440),
            'DAR':     (11, 1230),
            'OXL':     (10, 1080),
            'CQD':     (9,  930),
            'SHW':     (8,  840),
            'GVQ':     (7,  750),
            'CMZ':     (6,  660),
            'IDP':     (5,  570),
            'TIQ':     (4,  480),
            'TWG':     (3,  330),
            'AHF':     (2,  240),
            'MTZ':     (1,  150),
            'RS':      (0,  0)
            }
        
        network_vrt_dict = {
            'Beenleigh':                  vrt_2Beenleigh,
            'Caboolture':                 vrt_2Caboolture,
            'Sunshine Coast':             vrt_2GympieNth,
            'Gympie North':               vrt_2GympieNth,
            'Cleveland':                  vrt_2Cleveland,
            'Doomben':                    vrt_2Doomben,
            'Ferny Grove':                vrt_2FernyGrove,
            'Airport':                    vrt_2Airport,
            'Gold Coast':                 vrt_2VarsityLs,
            'Ipswich':                    vrt_2Ipswich,
            'Rosewood':                   vrt_2Rosewood,
            'Redcliffe Peninsula':        vrt_2KippaRing,
            'Shorncliffe':                vrt_2Shorncliffe,
            'Springfield':                vrt_2Springfield,
            }
        
        uniquestations_dict = {
            'Beenleigh':                  ('BNHS','BNT','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKET','RKE','MQK','CPM','ORMS'), # 'TNY', 'MBN','YLY','YRG','FFI','DUP'
            'Caboolture':                 ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN'),
            'Sunshine Coast':             ('EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN','AUR','CRD'),
            'Gympie North':               ('YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN'),
            'Cleveland':                  ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                    ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':                ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Gold Coast':                 ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST'),
            'Airport':                    ('BIT','BDT'),
            'Ipswich':                    ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
            'Rosewood':                   ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Redcliffe Peninsula':        ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Springfield':                ('RHD','SFD','SFC'),
            }
        
        
        
        
        
        
        ### Initialise a list for each worksheet    
        mth_am  = []
        mth_amc = []
        mth_pm  = []
        mth_pmc = []
        mth_opi = []
        mth_opo = []
        fri_am  = []
        fri_amc = []
        fri_pm  = []
        fri_pmc = []
        fri_opi = []
        fri_opo = []
        sat_in  = []
        sat_out = []
        sun_in  = []
        sun_out = []
        
    
        
        
        
        
        
        
        
    
        def stoptime_info(entry_index): 
            """ Returns the arrvial and departure times for a given location  """
            x = entry_index
            
            departure = entries[x].attrib['departure'] 
            
            stoptime = int(entries[x].attrib.get('stopTime',0))
            if stoptime == 1:
                stoptime = 0
                
            arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))  
            if arrival[:6] == '1 days':
                arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
            else: arrival = arrival[7:]
        
            return (arrival,departure)
        
        def timetrim(timestring):
            """ Format converter from hh:mm:ss to hh:mm """
            
            if type(timestring) == list:
                timestring = timestring[0]
            
            if timestring is None or timestring.isalpha() or ':' not in timestring:
                pass
            else:
                timestring = timestring[:-3]
            
            return timestring
        
        
        
        
        
        
        
        
        
        
                    
                    
        def findtrips(line,termini):
            """ 
            Collates a list of trips for each line, given it stops at one of the set starting/ending locations for that line
            """
            
            
            entry = [tn,line,oID,odep,cbdID, cbdarr, cbddep,dID,darr]
            
            
            if oID in termini:
                if weekdayKey == '1':
                    sun_in.append(entry)
                if weekdayKey == '2':
                    sat_in.append(entry)
                if weekdayKey == '4':
                    if ampeak_srt <= cbdtimingp < ampeak_end   or ampeak_srt <= vcbdarr < ampeak_end: fri_am.append(entry)    
                    elif pmpeak_srt <= cbdtimingp < pmpeak_end or pmpeak_srt <= vcbdarr < pmpeak_end: fri_pmc.append(entry) 
                    else: fri_opi.append(entry)
                if weekdayKey == '120':
                    if ampeak_srt <= cbdtimingp < ampeak_end   or ampeak_srt <= vcbdarr < ampeak_end: mth_am.append(entry)    
                    elif pmpeak_srt <= cbdtimingp < pmpeak_end or pmpeak_srt <= vcbdarr < pmpeak_end: mth_pmc.append(entry) 
                    else: mth_opi.append(entry)
                
                    
            if dID in termini:
                if weekdayKey == '1':   
                    sun_out.append(entry)
                if weekdayKey == '2':
                    sat_out.append(entry)
                if weekdayKey == '4':
                    if ampeak_srt <= cbdtimingp < ampeak_end   or ampeak_srt <= vcbdarr < ampeak_end: fri_amc.append(entry)
                    elif pmpeak_srt <= cbdtimingp < pmpeak_end or pmpeak_srt <= vcbdarr < pmpeak_end: fri_pm.append(entry)
                    else: fri_opo.append(entry) 
                if weekdayKey == '120':
                    if ampeak_srt <= cbdtimingp < ampeak_end   or ampeak_srt <= vcbdarr < ampeak_end: mth_amc.append(entry)
                    elif pmpeak_srt <= cbdtimingp < pmpeak_end or pmpeak_srt <= vcbdarr < pmpeak_end: mth_pm.append(entry)
                    else: mth_opo.append(entry)  
                    
    
        ### Parses the rsx
        ### Starts gathering data about each service
        ### Declares the location for the cbd timing point
        ### Uses the 'virtual run time' method to get virtual cbd arrival and departure times (vcbdarr / vcbddep) in case an actual cbd timing point does not exist
        ### Starts sorting the services into lines and periods using the findtrips function call
        revenue_parse = [x for x in root.iter('train') if 'Empty' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'] ]
        for train in revenue_parse:
            weekdayKey = train[0][0][0].attrib['weekdayKey']
            tn  = train.attrib['number']
            entries = [x for x in train.iter('entry') if x.attrib['stationID'] not in non_revenue_stations]

    
            sIDdict = {x.attrib['stationID'] for x in entries}        
            stations = [x.attrib['stationID'] for x in entries]
            
            
            
            
            origin = entries[0].attrib
            destin = entries[-1].attrib
            oID = origin['stationID']
            dID = destin['stationID']
            oarr, odep = stoptime_info(0)
            darr, ddep = stoptime_info(-1)
            
            
            
            
            
            
            
            
            
            
            vcbdarr = ''
            
            
            if 'RTL' in stations:
                cbdID = 'RTL'
                cbdidx = stations.index(cbdID)
                cbdarr, cbddep = stoptime_info(cbdidx)
            elif 'BNC' in stations and station == "Central Station":
                cbdID = 'BNC'
                cbdidx = stations.index(cbdID)
                cbdarr, cbddep = stoptime_info(cbdidx)
            elif 'RS' in stations and station == "Roma Street":
                cbdID = 'RS'
                cbdidx = stations.index(cbdID)
                cbdarr, cbddep = stoptime_info(cbdidx)
            else:
                if 'IPS' in stations and 'RSW' in stations:
                    cbdID = 'IPS'
                    cbdidx = stations.index(cbdID)
                    cbdarr, cbddep = stoptime_info(cbdidx)
                else:
                    # print(tn,odep,darr)
                    # print(entries)
                    cbdID  = ''
                    cbdarr = ''
                    cbddep = ''
                    
                    
                    count = 0
                    for line,vrt in network_vrt_dict.items():
    
                        line_stops = uniquestations_dict.get(line)
                        
    
                        condition = sIDdict.intersection(line_stops)
                        
                        if line == 'Beenleigh':
                            condition = condition and sIDdict.isdisjoint(uniquestations_dict.get('Gold Coast'))
                        
                        elif line == 'Shorncliffe':
                            condition = condition or ('NTG' in [oID,dID] and any([vrt.get(x) for x in sIDdict if x != 'NTG']))
                        
                        elif line == 'Redcliffe Peninsula':
                            shared_line_rdp_stations = ['LWO', 'BPR', 'SPN', 'BDS', 'CDE', 'ZLL', 'GEB', 'SSN', 'VGI']
                            condition = condition or dID in shared_line_rdp_stations or oID in shared_line_rdp_stations
    
                        if condition:
                            
                            for n,entry in enumerate(entries):
                                
                                if entry.attrib['stationID'] in vrt:
                                    firstonline = entry.attrib['stationID']                  
                                    first_sIDinVRT = n
                                    break
                            
                            for n,entry in enumerate(entries):
                                if n <= first_sIDinVRT:
                                    secondonline = firstonline
                                else:
                                    if entry.attrib['stationID'] in vrt:
                                        secondonline = entry.attrib['stationID']
                                        break
                                
                            a = int(vrt.get(firstonline)[0])    
                            b = int(vrt.get(secondonline)[0])
                            increasing = b > a
                            decreasing = b <= a     
                        
                    
                        
                            
                            for entry in entries:
                                if entry.attrib['stationID'] in vrt:
                                    firstinline       = entry.attrib['stationID']
                                    firstdeparture    = entry.attrib['departure']
                                    firstinline_vrt   = vrt.get(firstinline)[-1]
                                    
                                    if increasing:
                                        vcbdarr = str(pd.Timedelta(firstdeparture) - pd.Timedelta(seconds=firstinline_vrt))
                                    else:
                                        vcbdarr = str(pd.Timedelta(firstdeparture) + pd.Timedelta(seconds=firstinline_vrt))
                                    
                                    
                                    
                                    
                                    if vcbdarr[:6] == '1 days':
                                        vcbdarr = str(24 + int(vcbdarr[7:9])) + str(vcbdarr[9:])
                                    else: vcbdarr = vcbdarr[7:]
                                    break
                            break
                            
                        else:
                            count += 1
                        
    
                    no_line = count == len(network_vrt_dict)
                    
                    
                    if no_line:
                        print('No line') 
                    
            cbdtimingp = cbdarr
            odep = timetrim(odep)
            cbdarr = timetrim(cbdarr)
            cbddep = timetrim(cbddep)
            darr = timetrim(darr)
    
            
            findtrips('Airport',            ['BDT'])
            findtrips('Beenleigh',          ['BNH','BNHS','BNT','CEP','KRY'])
            findtrips('Caboolture',         ['CAB','CAW'])
            findtrips('Cleveland',          ['CVN','MNY','CNQ'])
            findtrips('Springfield',        ['SFC','DAR'])
            findtrips('Doomben',            ['DBN'])
            findtrips('Ferny Grove',        ['FYG'])
            findtrips('Shorncliffe',        ['SHC','NTG'])
            findtrips('Redcliffe Peninsula',['KPR'])
            findtrips('Gold Coast',         ['VYS','VYST'])
            findtrips('Sunshine Coast',     ['NBR','CRD']),
            findtrips('Gympie North',       ['GYN'])
            #findtrips('Rosewood',           ['RSW'])
            findtrips(
                        'Rosewood' if ('RS' in stations or 'RTL' in stations)
                        else 'Rosewood Shuttle',
                        ['RSW']
                    )
            
            if 'RSW' not in stations:
                findtrips('Ipswich',        ['IPS','IPSS'])
            
            
        
    
    
        
        ### Creates the worksheets for each period + the summary sheet
        ### Adds formatting
        info_sheet           = workbook.add_worksheet('Info Sheet')
        Mon_Thu_AM           = workbook.add_worksheet('Mon_Thu_AM')
        Mon_Thu_AM_Contra    = workbook.add_worksheet('Mon_Thu_AM_Contra')
        Mon_Thu_PM           = workbook.add_worksheet('Mon_Thu_PM')
        Mon_Thu_PM_Contra    = workbook.add_worksheet('Mon_Thu_PM_Contra')
        Mon_Thu_OFF_Inbound  = workbook.add_worksheet('Mon_Thu_OFF_Inbound')
        Mon_Thu_OFF_Outbound = workbook.add_worksheet('Mon_Thu_OFF_Outbound')
        Fri_AM               = workbook.add_worksheet('Fri_AM')
        Fri_AM_Contra        = workbook.add_worksheet('Fri_AM_Contra')
        Fri_PM               = workbook.add_worksheet('Fri_PM')
        Fri_PM_Contra        = workbook.add_worksheet('Fri_PM_Contra')
        Fri_OFF_Inbound      = workbook.add_worksheet('Fri_OFF_Inbound')
        Fri_OFF_Outbound     = workbook.add_worksheet('Fri_OFF_Outbound')
        Sat_Inbound          = workbook.add_worksheet('Sat_Inbound')
        Sat_Outbound         = workbook.add_worksheet('Sat_Outbound')
        Sun_Inbound          = workbook.add_worksheet('Sun_Inbound')
        Sun_Outbound         = workbook.add_worksheet('Sun_Outbound')
        total_count          = workbook.add_worksheet('Total Count')    
        
        
        
        
        
        
        
        
        #EXCEL WORKBOOK FORMATTING 
        ######################################################################
        Periods = ['AM','AMC','PM','PMC','OPI','OPO']
        LineList = [
                    'Beenleigh',
                    'Cleveland',
                    'Springfield',
                    'Doomben',
                    'Ferny Grove',
                    'Shorncliffe',
                    'Redcliffe Peninsula',
                    ' ',
                    ' ',
                    'Gold Coast',
                    'Ipswich + Rosewood',
                    'Rosewood',
                    'Caboolture + Sunshine Coast',
                    'Sunshine Coast',
                    'Gympie North',
                    ' ',
                    ' ',
                    'Rosewood Shuttle',
                    'Sunshine Coast Shuttle',
                    'Inner City Shuttle',
                    'CRR Shuttle',
                    ' ',
                    ' ',
                    'Total (Excluding Airtrain)'
                    ]
        LineList2 = list(LineList); LineList2[-1] = 'Airport'
        
        FormulasList_TripSummary = [
            '=COUNTIF(B:B,J2)',
            '=COUNTIF(B:B,J3)',
            '=COUNTIF(B:B,J4)',
            '=COUNTIF(B:B,J5)',
            '=COUNTIF(B:B,J6)',
            '=COUNTIF(B:B,J7)',
            '=COUNTIF(B:B,J8)',
            '=SUM(K2:K8)',
            '',
            '=COUNTIF(B:B,J11)',
            '=COUNTIF(B:B,TRIM(LEFT(J12,FIND("+",J12)-1)))+COUNTIF(B:B,J13)',
            '=COUNTIF(B:B,J13)',
            '=COUNTIF(B:B,TRIM(LEFT(J14,FIND("+",J14)-1)))+COUNTIF(B:B,J15)',
            '=COUNTIF(B:B,J15)',
            '=COUNTIF(B:B,J16)',
            '=SUM(K11,K12,K14,K16)',
            '',
            '=COUNTIF(B:B,J19)',
            '=COUNTIF(B:B,J20)',
            '=COUNTIF(B:B,J21)',
            '=COUNTIF(B:B,J22)',
            '=SUM(K19:K22)',
            '',
            '=COUNTIF(B:B,J25)',
            '=SUM(K25)']
        #_________________________________________________________________________________________________________________________________________________________
        #_________________________________________________________________________________________________________________________________________________________
        bold                        = workbook.add_format({'bold': True, 'align':'center'})
        border                      = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center'})
        bold12                      = workbook.add_format({'bold': True, 'align':'center', 'font_size':12})
        bold13                     = workbook.add_format({'bold': True, 'align':'center','valign':'vcenter', 'font_size':14})
        
        grey                        = workbook.add_format({'bold': True, 'align':'center', 'bg_color':'#C0C0C0'})
        greybottom                  = workbook.add_format({'bold': True, 'align':'center','bottom':2, 'bg_color':'#C0C0C0'})
        greybottomleft              = workbook.add_format({'bold': True, 'align':'center','bottom':2, 'left':2, 'bg_color':'#C0C0C0'})
        greybottomright             = workbook.add_format({'bold': True, 'align':'center','bottom':2, 'right':2, 'bg_color':'#C0C0C0'})
        greyleftright               = workbook.add_format({'bold': True, 'align':'center','left':2, 'right':2, 'bg_color':'#C0C0C0'})
    
        greyt                       = workbook.add_format({'bold': True, 'align':'center','valign':'vcenter','border':2, 'bg_color':'#C0C0C0'})
        greyb                       = workbook.add_format({'bold': True, 'align':'center','border':1, 'bg_color':'#C0C0C0'})
        greyallbottom               = workbook.add_format({'bold': True, 'align':'center','border':1,'bottom':2, 'bg_color':'#C0C0C0'})
        greyallbottomleft           = workbook.add_format({'bold': True, 'align':'center','border':1,'bottom':2, 'left':2, 'bg_color':'#C0C0C0'})
        greyallbottomright          = workbook.add_format({'bold': True, 'align':'center','border':1,'bottom':2, 'right':2, 'bg_color':'#C0C0C0'})
        greyallleftright            = workbook.add_format({'bold': True, 'align':'center','border':1,'left':2, 'right':2, 'bg_color':'#C0C0C0'})
        greyallleft                 = workbook.add_format({'bold': True, 'align':'center','border':1,'left':2, 'bg_color':'#C0C0C0'})
        greyallright                = workbook.add_format({'bold': True, 'align':'center','border':1,'right':2, 'bg_color':'#C0C0C0'})
        greyalln                    = workbook.add_format({'bold': True, 'align':'center','border':1,'left':2, 'right':2,'top':2, 'bg_color':'#C0C0C0'})
        greyallu                    = workbook.add_format({'bold': True, 'align':'center','border':1,'left':2, 'right':2,'bottom':2, 'bg_color':'#C0C0C0'})
        whitecell_tbordertopleft    = workbook.add_format({'align':'center','border':1,'top':2, 'left':2})
        whitecell_tbordertop        = workbook.add_format({ 'align':'center','border':1,'top':2})
        whitecell_tborderleft       = workbook.add_format({ 'align':'center','border':1,'left':2})
        whitecell_tborderbottom     = workbook.add_format({ 'align':'center','border':1,'bottom':2})
        whitecell_tborderbottomleft = workbook.add_format({ 'align':'center','border':1,'bottom':2,'left':2})
        tr                          = workbook.add_format({'align':'center','right':2})
        left                        = workbook.add_format({'align':'left'})
        boldleft                    = workbook.add_format({'align':'left','bold':True})
        boldright                   = workbook.add_format({'align':'right','bold':True})

        grey_note                   = workbook.add_format({'bold': True,'italic': True,'font_color': '#BFBFBF','align': 'center'})
        whiteallu = workbook.add_format({'bold': True,'align': 'center','border': 1,'left': 2,'right': 2,'top': 2,'bottom': 2})
        
        workbook.formats[0].set_align('center') 
        
        #FORMATS
        #_________________________________________________________________________________________________________________________________________________________
        #_________________________________________________________________________________________________________________________________________________________
        #TRIP LIST
        sheetlist = [Mon_Thu_AM, Mon_Thu_AM_Contra, Mon_Thu_PM, Mon_Thu_PM_Contra, Mon_Thu_OFF_Inbound, Mon_Thu_OFF_Outbound,
                      Fri_AM, Fri_AM_Contra, Fri_PM, Fri_PM_Contra, Fri_OFF_Inbound, Fri_OFF_Outbound,
                      Sat_Inbound,Sat_Outbound,Sun_Inbound,Sun_Outbound] 
        for sheet in sheetlist:
            sheet.merge_range('C1:D1','Origin',     greyleftright)
            sheet.merge_range('E1:G1','CBD',        greyleftright)
            sheet.merge_range('H1:I1','Destination',greyleftright)
            
            sheet.write('A2','Train Number',greybottom)
            sheet.write('B2','Corridor',    greybottomright)
            sheet.write('C2','Station',     greybottomleft)
            sheet.write('D2','Depart',      greybottomright)
            sheet.write('E2','Station',     greybottomleft)
            sheet.write('F2','Arrive',      greybottom)
            sheet.write('G2','Depart',      greybottomright)
            sheet.write('H2','Station',     greybottomleft)
            sheet.write('I2','Arrive',      greybottomright)
            sheet.write('A1','',            grey)
            sheet.write('B1','',            grey)
            colswidth = [17.14,17.71,11.14,10.86,11.14,10.29,10.86,11.14,10.29,40]
            for n,width in enumerate(colswidth):
                sheet.set_column(n,n,width)
            sheet.write_column('J2',LineList2)
            sheet.write_column('K2',FormulasList_TripSummary)
            sheet.write_string('J1',str(sheet.get_name())+': '+str(filename),bold)
            sheet.autofilter('A2:I700')
        
        #TOTAL COUNT
        total_count.set_column(1,1,30)
        total_count.set_column(10,10,30)
        
        total_count.set_row(0,15.75)
        total_count.set_row(4,15.75)
        total_count.set_row(5,15.75)
        total_count.set_row(22,15.75)
        total_count.set_row(25,15.75)
        total_count.set_row(26,15.75)
        total_count.set_row(43,15.75)
        
        total_count.merge_range('B1:R1','Trip Count Report',  bold12)
        total_count.merge_range('B3:R3','Reports the number of City Network trips in the timetable. A trip is defined as a part or all of a service separated into an inbound or outbound journey.')
        
        total_count.merge_range('C5:H5','Mon - Thu',  greyt)
        total_count.merge_range('L5:Q5','Fri',        greyt)
        total_count.merge_range('C34:D34','Sat',      greyt)
        total_count.merge_range('G34:H34','Sun',      greyt)
        total_count.merge_range('L34:Q34','AirTrain', greyt)
        
        #MON-THURS
        total_count.write_row('C6',     Periods,    bold)
        total_count.write_column('B8',  LineList,   bold)
        #FRIDAY
        total_count.write_row('L6',     Periods,    bold)
        total_count.write_column('K8',  LineList,   bold)
        #SAT/SUN
        total_count.write('C35','Sat In',bold);   total_count.write('D35','Sat Out',bold)
        total_count.write('G35','Sun In',bold);   total_count.write('H35','Sun Out',bold)
        total_count.write_column('B37',LineList,bold)
        #AIRTRAIN
        total_count.write_row('L35',Periods,bold  )
        total_count.write('K37','Mon - Thu'       );    total_count.write('K38','Fri')
        total_count.write('P40','Inbound',  bold  );    total_count.write('Q40','Outbound',bold)
        total_count.write('O42','Sat'             );    total_count.write('O43','Sun')
        
        
        
        #Sunday
        FormulasList_SunTotal = ['=SUM(G38:H38)','=SUM(G39:H39)','=SUM(G40:H40)','=SUM(G41:H41)','=SUM(G42:H42)','=SUM(G43:H43)','=SUM(G44:H44)',
                                 '','=SUM(G46:H46)','=SUM(G47:H47)','','=SUM(G49:H49)','','=SUM(G51:H51)','=SUM(G52:H52)',
                                 '','=SUM(G54:H54)','=SUM(G55:H55)','=SUM(G56:H56)','=SUM(G57:H57)','=SUM(G58:H58)',
                                 '',]
        
        
        FormulasList_SunIn = ['=Sun_Inbound!K3','=Sun_Inbound!K4','=Sun_Inbound!K5','=Sun_Inbound!K6','=Sun_Inbound!K7','=Sun_Inbound!K8','','',
                              '=Sun_Inbound!K11','=Sun_Inbound!K12','=Sun_Inbound!K13','=Sun_Inbound!K14','=Sun_Inbound!K15','=Sun_Inbound!K16','','',
                              '=Sun_Inbound!K19','=Sun_Inbound!K20','=Sun_Inbound!K21','=Sun_Inbound!K22','','',
                              '=Sun_Inbound!K25']
        
        FormulasList_SunOut = ['=Sun_Outbound!K3','=Sun_Outbound!K4','=Sun_Outbound!K5','=Sun_Outbound!K6','=Sun_Outbound!K7','=Sun_Outbound!K8','','',
                              '=Sun_Outbound!K11','=Sun_Outbound!K12','=Sun_Outbound!K13','=Sun_Outbound!K14','=Sun_Outbound!K15','=Sun_Outbound!K16','','',
                              '=Sun_Outbound!K19','=Sun_Outbound!K20','=Sun_Outbound!K21','=Sun_Outbound!K22','','',
                              '=Sun_Outbound!K25']
        
        total_count.write('G37','=Sun_Inbound!K2',              whitecell_tbordertopleft) #toptop left
        total_count.write('H37','=Sun_Outbound!K2',             whitecell_tbordertop) #toptop midlle
        total_count.write('I37','=SUM(G37:H37)',                greyalln) #toptop right
        
        total_count.write_column('G38',FormulasList_SunIn,      whitecell_tborderleft)
        total_count.write_column('H38',FormulasList_SunOut,     border)
        total_count.write_column('I38',FormulasList_SunTotal,   greyallleftright)

        total_count.merge_range('G36:H36','Suburban',   whiteallu)
        total_count.merge_range('G45:H45','Interurban', whiteallu)
        total_count.merge_range('G53:H53','Shuttles',   whiteallu)

        
        total_count.write('G60','=G44+G52+G58',                 greyallbottomleft) #bottom left
        total_count.write('H60','=H44+H52+H58',                 greyallbottom) #bottom middle
        total_count.write('I60','=I44+I52+I58',                 greyallu) #bottom right
        
        #shuttes total
        total_count.write('G58','=SUM(G54:G57)',                greyallleft) #middle left
        total_count.write('H58','=SUM(H54:H57)',                greyallright) #middle middle

        #interurban total
        total_count.write('G52','=SUM(G46,G47,G49,G51)',        greyallleft) #middle left
        total_count.write('H52','=SUM(H46,H47,H49,H51)',        greyallright) #middle middle
        
        #suburban total
        total_count.write('G44','=SUM(G37:G43)',                greyallleft) #top left
        total_count.write('H44','=SUM(H37:H43)',                greyallright) #top middle
        
        #Saturday
        FormulasList_SatTotal = ['=SUM(C38:D38)','=SUM(C39:D39)','=SUM(C40:D40)','=SUM(C41:D41)','=SUM(C42:D42)','=SUM(C43:D43)','=SUM(C44:D44)',
                                '','=SUM(C46:D46)','=SUM(C47:D47)','','=SUM(C49:D49)','','=SUM(C51:D51)','=SUM(C52:D52)',
                                '','=SUM(C54:D54)','=SUM(C55:D55)','=SUM(C56:D56)','=SUM(C57:D57)','=SUM(C58:D58)',
                                '',]

        FormulasList_SatIn = ['=Sat_Inbound!K3','=Sat_Inbound!K4','=Sat_Inbound!K5','=Sat_Inbound!K6','=Sat_Inbound!K7','=Sat_Inbound!K8','','',
                            '=Sat_Inbound!K11','=Sat_Inbound!K12','=Sat_Inbound!K13','=Sat_Inbound!K14','=Sat_Inbound!K15','=Sat_Inbound!K16','','',
                            '=Sat_Inbound!K19','=Sat_Inbound!K20','=Sat_Inbound!K21','=Sat_Inbound!K22','','',
                            '=Sat_Inbound!K25']

        FormulasList_SatOut = ['=Sat_Outbound!K3','=Sat_Outbound!K4','=Sat_Outbound!K5','=Sat_Outbound!K6','=Sat_Outbound!K7','=Sat_Outbound!K8','','',
                            '=Sat_Outbound!K11','=Sat_Outbound!K12','=Sat_Outbound!K13','=Sat_Outbound!K14','=Sat_Outbound!K15','=Sat_Outbound!K16','','',
                            '=Sat_Outbound!K19','=Sat_Outbound!K20','=Sat_Outbound!K21','=Sat_Outbound!K22','','',
                            '=Sat_Outbound!K25']

        total_count.write('C37','=Sat_Inbound!K2',          whitecell_tbordertopleft)
        total_count.write('D37','=Sat_Outbound!K2',         whitecell_tbordertop)
        total_count.write('E37','=SUM(C37:D37)',            greyalln)

        total_count.write_column('C38',FormulasList_SatIn,  whitecell_tborderleft)
        total_count.write_column('D38',FormulasList_SatOut, border)
        total_count.write_column('E38',FormulasList_SatTotal,greyallleftright)

        total_count.merge_range('C36:D36','Suburban',   whiteallu)
        total_count.merge_range('C45:D45','Interurban', whiteallu)
        total_count.merge_range('C53:D53','Shuttles',   whiteallu)

        total_count.write('C60','=C44+C52+C58',         greyallbottomleft)
        total_count.write('D60','=D44+D52+D58',         greyallbottom)
        total_count.write('E60','=E44+E52+E58',         greyallu)

        # shuttles total
        total_count.write('C58','=SUM(C54:C57)',        greyallleft)
        total_count.write('D58','=SUM(D54:D57)',        greyallright)

        # interurban total
        total_count.write('C52','=SUM(C46,C47,C49,C51)',greyallleft)
        total_count.write('D52','=SUM(D46,D47,D49,D51)',greyallright)

        # suburban total
        total_count.write('C44','=SUM(C37:C43)',        greyallleft)
        total_count.write('D44','=SUM(D37:D43)',        greyallright)

        #Mon - Thurs
        ############################################################################
        FormulasList_MtT1 = ['=Mon_Thu_AM_Contra!K2','=Mon_Thu_PM!K2','=Mon_Thu_PM_Contra!K2','=Mon_Thu_OFF_Inbound!K2','=Mon_Thu_OFF_Outbound!K2'	] #toprow
        FormulasList_MtT2 = ['=Mon_Thu_AM!K3','=Mon_Thu_AM!K4','=Mon_Thu_AM!K5','=Mon_Thu_AM!K6',
                             '=Mon_Thu_AM!K7','=Mon_Thu_AM!K8', '=SUM(C8:C14)','',
                             '=Mon_Thu_AM!K11','=Mon_Thu_AM!K12','=Mon_Thu_AM!K13','=Mon_Thu_AM!K14','=Mon_Thu_AM!K15','=Mon_Thu_AM!K16',
                             '=SUM(C17,C18,C20,C22)','',
                             '=Mon_Thu_AM!K19','=Mon_Thu_AM!K20','=Mon_Thu_AM!K21','=Mon_Thu_AM!K22',
                             '=SUM(C25:C28)',''] #firstcol
        FormulasList_MtT3 = ['=SUM(D8:D14)','=SUM(E8:E14)','=SUM(F8:F14)','=SUM(G8:G14)','=SUM(H8:H14)'] #1st sumrow
        FormulasList_MtT4 = ['=SUM(D17,D18,D20,D22)','=SUM(E17,E18,E20,E22)','=SUM(F17,F18,F20,F22)','=SUM(G17,G18,G20,G22)','=SUM(H17,H18,H20,H22)'] #2nd sumrow
        FormulasList_MtT5 = ['=D15+D23+D29','=E15+E23+E29','=F15+F23+F29','=G15+G23+G29','=H15+H23+H29','=I15+I23+I29',] #3rd sumrow
    
        FormulasList_MtT6 = [
            ('=Mon_Thu_AM_Contra!K3','=Mon_Thu_PM!K3','=Mon_Thu_PM_Contra!K3','=Mon_Thu_OFF_Inbound!K3','=Mon_Thu_OFF_Outbound!K3'),
            ('=Mon_Thu_AM_Contra!K4','=Mon_Thu_PM!K4','=Mon_Thu_PM_Contra!K4','=Mon_Thu_OFF_Inbound!K4','=Mon_Thu_OFF_Outbound!K4'),
            ('=Mon_Thu_AM_Contra!K5','=Mon_Thu_PM!K5','=Mon_Thu_PM_Contra!K5','=Mon_Thu_OFF_Inbound!K5','=Mon_Thu_OFF_Outbound!K5'),
            ('=Mon_Thu_AM_Contra!K6','=Mon_Thu_PM!K6','=Mon_Thu_PM_Contra!K6','=Mon_Thu_OFF_Inbound!K6','=Mon_Thu_OFF_Outbound!K6'),
            ('=Mon_Thu_AM_Contra!K7','=Mon_Thu_PM!K7','=Mon_Thu_PM_Contra!K7','=Mon_Thu_OFF_Inbound!K7','=Mon_Thu_OFF_Outbound!K7'),
            ('=Mon_Thu_AM_Contra!K8','=Mon_Thu_PM!K8','=Mon_Thu_PM_Contra!K8','=Mon_Thu_OFF_Inbound!K8','=Mon_Thu_OFF_Outbound!K8'),
            ('=Mon_Thu_AM_Contra!K9','=Mon_Thu_PM!K9','=Mon_Thu_PM_Contra!K9','=Mon_Thu_OFF_Inbound!K9','=Mon_Thu_OFF_Outbound!K9'),
            ('=Mon_Thu_AM_Contra!K10','=Mon_Thu_PM!K10','=Mon_Thu_PM_Contra!K10','=Mon_Thu_OFF_Inbound!K10','=Mon_Thu_OFF_Outbound!K10'),
            ('=Mon_Thu_AM_Contra!K11','=Mon_Thu_PM!K11','=Mon_Thu_PM_Contra!K11','=Mon_Thu_OFF_Inbound!K11','=Mon_Thu_OFF_Outbound!K11'),
            ('=Mon_Thu_AM_Contra!K12','=Mon_Thu_PM!K12','=Mon_Thu_PM_Contra!K12','=Mon_Thu_OFF_Inbound!K12','=Mon_Thu_OFF_Outbound!K12'),
            ('=Mon_Thu_AM_Contra!K13','=Mon_Thu_PM!K13','=Mon_Thu_PM_Contra!K13','=Mon_Thu_OFF_Inbound!K13','=Mon_Thu_OFF_Outbound!K13'),
            ('=Mon_Thu_AM_Contra!K14','=Mon_Thu_PM!K14','=Mon_Thu_PM_Contra!K14','=Mon_Thu_OFF_Inbound!K14','=Mon_Thu_OFF_Outbound!K14'),
            ('=Mon_Thu_AM_Contra!K15','=Mon_Thu_PM!K15','=Mon_Thu_PM_Contra!K15','=Mon_Thu_OFF_Inbound!K15','=Mon_Thu_OFF_Outbound!K15'),
            ('=Mon_Thu_AM_Contra!K16','=Mon_Thu_PM!K16','=Mon_Thu_PM_Contra!K16','=Mon_Thu_OFF_Inbound!K16','=Mon_Thu_OFF_Outbound!K16'),
            ('=Mon_Thu_AM_Contra!K17','=Mon_Thu_PM!K17','=Mon_Thu_PM_Contra!K17','=Mon_Thu_OFF_Inbound!K17','=Mon_Thu_OFF_Outbound!K17'),
            ('=Mon_Thu_AM_Contra!K18','=Mon_Thu_PM!K18','=Mon_Thu_PM_Contra!K18','=Mon_Thu_OFF_Inbound!K18','=Mon_Thu_OFF_Outbound!K18'),
            ('=Mon_Thu_AM_Contra!K19','=Mon_Thu_PM!K19','=Mon_Thu_PM_Contra!K19','=Mon_Thu_OFF_Inbound!K19','=Mon_Thu_OFF_Outbound!K19'),
            ('=Mon_Thu_AM_Contra!K20','=Mon_Thu_PM!K20','=Mon_Thu_PM_Contra!K20','=Mon_Thu_OFF_Inbound!K20','=Mon_Thu_OFF_Outbound!K20'),
            ('=Mon_Thu_AM_Contra!K21','=Mon_Thu_PM!K21','=Mon_Thu_PM_Contra!K21','=Mon_Thu_OFF_Inbound!K21','=Mon_Thu_OFF_Outbound!K21'),
            ('=Mon_Thu_AM_Contra!K22','=Mon_Thu_PM!K22','=Mon_Thu_PM_Contra!K22','=Mon_Thu_OFF_Inbound!K22','=Mon_Thu_OFF_Outbound!K22'),
            ] 
        
        FormulasList_MtT7 = ['=SUM(C8:H8)','=SUM(C9:H9)','=SUM(C10:H10)','=SUM(C11:H11)','=SUM(C12:H12)',
                             '=SUM(C13:H13)','=SUM(C14:H14)','=SUM(C15:H15)','','=SUM(C17:H17)',
                             '=SUM(C18:H18)','','=SUM(C20:H20)','','=SUM(C22:H22)','=SUM(C23:H23)','',
                             '=SUM(C25:H25)','=SUM(C26:H26)','=SUM(C27:H27)','=SUM(C28:H28)','=SUM(C29:H29)',] #totalcol

        FormulasList_MtT8 = ['=SUM(D25:D28)','=SUM(E25:E28)','=SUM(F25:F28)','=SUM(G25:G28)','=SUM(H25:H28)'] #shuttle sumrow

        total_count.write('C8','=Mon_Thu_AM!K2',            whitecell_tbordertopleft)
        total_count.write_row('D8',FormulasList_MtT1,       whitecell_tbordertop)
        total_count.write('I8','=SUM(C8:H8)',               greyalln)
        total_count.write('I23','=SUM(C23:H23)',            greyallu)
        total_count.write_column('C9',FormulasList_MtT2,    whitecell_tborderleft)
        
        for i,x in enumerate(FormulasList_MtT6):
            total_count.write_row(i+8,3,x,border)#bulk of table
        
        total_count.write('C15','=SUM(C8:C14)',             greyallleft)
        total_count.write_row('D15',FormulasList_MtT3,      greyb)
        total_count.write('C23','=SUM(C17,C18,C20,C22)',    greyallleft)
        total_count.write('C29','=SUM(C25:C28)',            greyallleft)
        total_count.write_row('D23',FormulasList_MtT4,      greyb)
        total_count.write('C31','=C15+C23+C29',             greyallbottomleft)
        total_count.write_row('D31',FormulasList_MtT5,      greyallbottom)
        
        total_count.write_column('I8',FormulasList_MtT7,    greyallleftright)
        total_count.write_row('D29',FormulasList_MtT8,      greyb)

        total_count.merge_range('C7:H7','Suburban',     whiteallu)
        total_count.merge_range('C16:H16','Interurban', whiteallu)
        total_count.merge_range('C24:H24','Shuttles',   whiteallu)

        #Friday
        ############################################################################
        FormulasList_Fri1 = ['=Fri_AM_Contra!K2','=Fri_PM!K2','=Fri_PM_Contra!K2','=Fri_OFF_Inbound!K2','=Fri_OFF_Outbound!K2']
        FormulasList_Fri2 = ['=Fri_AM!K3','=Fri_AM!K4','=Fri_AM!K5','=Fri_AM!K6',
                            '=Fri_AM!K7','=Fri_AM!K8','=SUM(L8:L14)','',
                            '=Fri_AM!K11','=Fri_AM!K12','=Fri_AM!K13','=Fri_AM!K14','=Fri_AM!K15','=Fri_AM!K16',
                            '=SUM(L17,L18,L20,L22)','',
                            '=Fri_AM!K19','=Fri_AM!K20','=Fri_AM!K21','=Fri_AM!K22',
                            '=SUM(L25:L28)','']
        FormulasList_Fri3 = ['=SUM(M8:M14)','=SUM(N8:N14)','=SUM(O8:O14)','=SUM(P8:P14)','=SUM(Q8:Q14)']
        FormulasList_Fri4 = ['=SUM(M17,M18,M20,M22)','=SUM(N17,N18,N20,N22)','=SUM(O17,O18,O20,O22)','=SUM(P17,P18,P20,P22)','=SUM(Q17,Q18,Q20,Q22)']
        FormulasList_Fri5 = ['=M15+M23+M29','=N15+N23+N29','=O15+O23+O29','=P15+P23+P29','=Q15+Q23+Q29','=R15+R23+R29']

        FormulasList_Fri6 = [
            ('=Fri_AM_Contra!K3','=Fri_PM!K3','=Fri_PM_Contra!K3','=Fri_OFF_Inbound!K3','=Fri_OFF_Outbound!K3'),
            ('=Fri_AM_Contra!K4','=Fri_PM!K4','=Fri_PM_Contra!K4','=Fri_OFF_Inbound!K4','=Fri_OFF_Outbound!K4'),
            ('=Fri_AM_Contra!K5','=Fri_PM!K5','=Fri_PM_Contra!K5','=Fri_OFF_Inbound!K5','=Fri_OFF_Outbound!K5'),
            ('=Fri_AM_Contra!K6','=Fri_PM!K6','=Fri_PM_Contra!K6','=Fri_OFF_Inbound!K6','=Fri_OFF_Outbound!K6'),
            ('=Fri_AM_Contra!K7','=Fri_PM!K7','=Fri_PM_Contra!K7','=Fri_OFF_Inbound!K7','=Fri_OFF_Outbound!K7'),
            ('=Fri_AM_Contra!K8','=Fri_PM!K8','=Fri_PM_Contra!K8','=Fri_OFF_Inbound!K8','=Fri_OFF_Outbound!K8'),
            ('=Fri_AM_Contra!K9','=Fri_PM!K9','=Fri_PM_Contra!K9','=Fri_OFF_Inbound!K9','=Fri_OFF_Outbound!K9'),
            ('=Fri_AM_Contra!K10','=Fri_PM!K10','=Fri_PM_Contra!K10','=Fri_OFF_Inbound!K10','=Fri_OFF_Outbound!K10'),
            ('=Fri_AM_Contra!K11','=Fri_PM!K11','=Fri_PM_Contra!K11','=Fri_OFF_Inbound!K11','=Fri_OFF_Outbound!K11'),
            ('=Fri_AM_Contra!K12','=Fri_PM!K12','=Fri_PM_Contra!K12','=Fri_OFF_Inbound!K12','=Fri_OFF_Outbound!K12'),
            ('=Fri_AM_Contra!K13','=Fri_PM!K13','=Fri_PM_Contra!K13','=Fri_OFF_Inbound!K13','=Fri_OFF_Outbound!K13'),
            ('=Fri_AM_Contra!K14','=Fri_PM!K14','=Fri_PM_Contra!K14','=Fri_OFF_Inbound!K14','=Fri_OFF_Outbound!K14'),
            ('=Fri_AM_Contra!K15','=Fri_PM!K15','=Fri_PM_Contra!K15','=Fri_OFF_Inbound!K15','=Fri_OFF_Outbound!K15'),
            ('=Fri_AM_Contra!K16','=Fri_PM!K16','=Fri_PM_Contra!K16','=Fri_OFF_Inbound!K16','=Fri_OFF_Outbound!K16'),
            ('=Fri_AM_Contra!K17','=Fri_PM!K17','=Fri_PM_Contra!K17','=Fri_OFF_Inbound!K17','=Fri_OFF_Outbound!K17'),
            ('=Fri_AM_Contra!K18','=Fri_PM!K18','=Fri_PM_Contra!K18','=Fri_OFF_Inbound!K18','=Fri_OFF_Outbound!K18'),
            ('=Fri_AM_Contra!K19','=Fri_PM!K19','=Fri_PM_Contra!K19','=Fri_OFF_Inbound!K19','=Fri_OFF_Outbound!K19'),
            ('=Fri_AM_Contra!K20','=Fri_PM!K20','=Fri_PM_Contra!K20','=Fri_OFF_Inbound!K20','=Fri_OFF_Outbound!K20'),
            ('=Fri_AM_Contra!K21','=Fri_PM!K21','=Fri_PM_Contra!K21','=Fri_OFF_Inbound!K21','=Fri_OFF_Outbound!K21'),
            ('=Fri_AM_Contra!K22','=Fri_PM!K22','=Fri_PM_Contra!K22','=Fri_OFF_Inbound!K22','=Fri_OFF_Outbound!K22'),
            ]

        FormulasList_Fri7 = ['=SUM(L8:Q8)','=SUM(L9:Q9)','=SUM(L10:Q10)','=SUM(L11:Q11)','=SUM(L12:Q12)',
                            '=SUM(L13:Q13)','=SUM(L14:Q14)','=SUM(L15:Q15)','','=SUM(L17:Q17)',
                            '=SUM(L18:Q18)','','=SUM(L20:Q20)','','=SUM(L22:Q22)','=SUM(L23:Q23)','',
                            '=SUM(L25:Q25)','=SUM(L26:Q26)','=SUM(L27:Q27)','=SUM(L28:Q28)','=SUM(L29:Q29)']

        FormulasList_Fri8 = ['=SUM(M25:M28)','=SUM(N25:N28)','=SUM(O25:O28)','=SUM(P25:P28)','=SUM(Q25:Q28)']

        total_count.write('L8','=Fri_AM!K2',                whitecell_tbordertopleft)
        total_count.write_row('M8',FormulasList_Fri1,       whitecell_tbordertop)
        total_count.write('R8','=SUM(L8:Q8)',               greyalln)
        total_count.write('R23','=SUM(L23:Q23)',            greyallu)
        total_count.write_column('L9',FormulasList_Fri2,    whitecell_tborderleft)

        for i,x in enumerate(FormulasList_Fri6):
            total_count.write_row(i+8,12,x,border)

        total_count.write('L15','=SUM(L8:L14)',             greyallleft)
        total_count.write_row('M15',FormulasList_Fri3,      greyb)
        total_count.write('L23','=SUM(L17,L18,L20,L22)',    greyallleft)
        total_count.write('L29','=SUM(L25:L28)',            greyallleft)
        total_count.write_row('M23',FormulasList_Fri4,      greyb)
        total_count.write('L31','=L15+L23+L29',             greyallbottomleft)
        total_count.write_row('M31',FormulasList_Fri5,      greyallbottom)

        total_count.write_column('R8',FormulasList_Fri7,    greyallleftright)
        total_count.write_row('M29',FormulasList_Fri8,      greyb)

        total_count.merge_range('L7:Q7','Suburban',     whiteallu)
        total_count.merge_range('L16:Q16','Interurban', whiteallu)
        total_count.merge_range('L24:Q24','Shuttles',   whiteallu)

        #Airtrain
        FormulasList_AirMtT = [
                            '=Mon_Thu_AM_Contra!K25',
                            '=Mon_Thu_PM!K25',
                            '=Mon_Thu_PM_Contra!K25',
                            '=Mon_Thu_OFF_Inbound!K25',
                            '=Mon_Thu_OFF_Outbound!K25']

        FormulasList_AirFri = [
                                '=Fri_AM_Contra!K25',
                                '=Fri_PM!K25',
                                '=Fri_PM_Contra!K25',
                                '=Fri_OFF_Inbound!K25',
                                '=Fri_OFF_Outbound!K25']

        total_count.write('L37','=Mon_Thu_AM!K25',whitecell_tbordertopleft)
        total_count.write('L38','=Fri_AM!K25',whitecell_tborderbottomleft)

        total_count.write_row('M37',FormulasList_AirMtT,whitecell_tbordertop)
        total_count.write_row('M38',FormulasList_AirFri,whitecell_tborderbottom)

        total_count.write('R37','=SUM(L37:Q37)',greyalln)
        total_count.write('R38','=SUM(L38:Q38)',greyallu)
        
        
        total_count.write('P42','=Sat_Inbound!K25',whitecell_tbordertopleft)#topleft
        total_count.write('P43','=Sun_Inbound!K25',whitecell_tborderbottomleft)#bottomleft
        total_count.write('Q42','=Sat_Outbound!K25',whitecell_tbordertop)#top middle
        total_count.write('Q43','=Sun_Outbound!K25',whitecell_tborderbottom)#bottom middle

        total_count.write('R42','=SUM(P42:Q42)',greyalln)#top right
        total_count.write('R43','=SUM(P43:Q43)',greyallu)#bottom right
        total_count.merge_range('L36:Q36','Suburban', whiteallu)
        total_count.merge_range('P41:Q41','Suburban', whiteallu)
        
        
        # Total Weekly Trip Count
        total_count.merge_range('Q59:R60','=SUM((4*I31),R31,E60,I60,(4*R37),R38,R42,R43)', greyt)
        total_count.merge_range('L59:P60','Total Weekly Trip Count:', bold13)


        #Formatting for Rosewood, Sunshine Coast in Interurban ranges
        for cell in ['B19:H19','K19:Q19','B21:H21','K21:Q21',
                     'B48:D48','B50:D50','G48:H48','G50:H50']:
            total_count.conditional_format(cell, {
                'type': 'no_blanks',
                'format': grey_note
            })
        
        info_sheet.write('B2','Trip Count Report', boldleft)
        info_sheet.write('B4','Extracted from \'' + filename + '\'', left)
        info_sheet.write('B6','Report created on ' + datetime.now().strftime("%d-%b-%Y %H:%M"), left)
        
        info_sheet.write('B12','Trains not in table:', left)
        info_sheet.write('C13','Mon - Thu:', left)
        info_sheet.write('C14','Fri:', left)
        info_sheet.write('C15','Sat:', left)
        info_sheet.write('C16','Sun:', left)
        
        # info_sheet.write('E13',','.join(Thursinfosheet), left)
        # info_sheet.write('E14',','.join(Friinfosheet), left)
        # info_sheet.write('E15',','.join(Satinfosheet), left)
        # info_sheet.write('E16',','.join(Suninfosheet), left)
        
        
        total_count.set_tab_color('navy')
        total_count.set_zoom(90)
        total_count.activate()
        
    
        ### Sort trip lists by 'Corridor'
        to_sort = [mth_am,mth_amc,mth_pm,mth_pmc,mth_opi,mth_opo,fri_am,fri_amc,fri_pm ,fri_pmc,fri_opi,fri_opo,sat_in,sat_out,sun_in,sun_out]  
        for x in to_sort:
            x.sort(key=lambda a: a[1])
        
        
        def writesheet(data,worksheet):
            for i,x in enumerate(data):
                worksheet.write(i+2,0,x[0])
                worksheet.write(i+2,1,x[1],tr)
                worksheet.write(i+2,2,x[2])
                worksheet.write(i+2,3,x[3],tr)
                worksheet.write(i+2,4,x[4])
                worksheet.write(i+2,5,x[5])
                worksheet.write(i+2,6,x[6],tr)
                worksheet.write(i+2,7,x[7])
                worksheet.write(i+2,8,x[8],tr)
        
        
        writesheet(mth_am, Mon_Thu_AM)
        writesheet(mth_amc, Mon_Thu_AM_Contra)
        writesheet(mth_pm, Mon_Thu_PM)
        writesheet(mth_pmc, Mon_Thu_PM_Contra)
        writesheet(mth_opi, Mon_Thu_OFF_Inbound)
        writesheet(mth_opo, Mon_Thu_OFF_Outbound)
        writesheet(fri_am, Fri_AM)
        writesheet(fri_amc, Fri_AM_Contra)
        writesheet(fri_pm, Fri_PM)
        writesheet(fri_pmc, Fri_PM_Contra)
        writesheet(fri_opi, Fri_OFF_Inbound)
        writesheet(fri_opo, Fri_OFF_Outbound)
        writesheet(sat_in, Sat_Inbound)
        writesheet(sat_out, Sat_Outbound)
        writesheet(sun_in, Sun_Inbound)
        writesheet(sun_out, Sun_Outbound)
        
        
        if CreateWorkbook:
            workbook.close()
            print('Creating workbook')  
            if copyfile:
                destination = os.path.join(mypath, os.path.basename(filename_xlsx))
                if os.path.abspath(filename_xlsx) != os.path.abspath(destination):
                    shutil.copy(filename_xlsx, destination)
                else:
                    print('Skipping copy because source and destination are the same file')
            else:
                if OpenWorkbook:
                    os.startfile(rf'{filename_xlsx}')
                    print('\nOpening workbook')  
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            app = QApplication(sys.argv)
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            show_info_safe('Trip Count Report','Process Done')
    
    
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(5)
            
if __name__ == "__main__":

    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_TC(path)
    