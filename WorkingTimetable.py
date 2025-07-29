import xml.etree.ElementTree as ET
import os
import sys
import pandas as pd
import xlsxwriter
import time
import shutil

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import traceback
import logging




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
OpenWorkbook = True
# --------------------------------------------------------------------------------------------------- #











weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}

### Conversion between rsx weekdaykey and what this translate to in shorthand english
weekdaykey_dict2 = {'120':'M-Th','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}


### Used for conversion between the name of each location and its abbreviated version
stationmaster = {
    'Fortitude Valley':'BRC',
    'Electric Train South': 'ETS',
    'Elec Train S': 'ETS',
    'Campbell St': 'CAM',
    'Exhibition': 'EXH',
    'Exhibition ': 'EXH',
    'Normanby': 'NBY',
    'Roma Street': 'RS',
    'Central': 'BNC',
    'Brunswick Street': 'BRC',
    'Bowen Hills': 'BHI',
    'Mayne': 'MNE',
    'Albion': 'AIN',
    'Wooloowin': 'WWI',
    'Eagle Junction': 'EGJ',
    'Toombul': 'TBU',
    'Nundah': 'NND',
    'Northgate': 'NTG',
    'Bindha': 'BHA',
    'Banyo': 'BQY',
    'Nudgee': 'NUD',
    'Boondall': 'BZL',
    'North Boondall': 'NBD',
    'Deagon': 'DEG',
    'Sandgate': 'SGE',
    'Shorncliffe': 'SHC',
    'Caboolture East Yard': 'CAE',
    'Caboolture': 'CAB',
    'Caboolture North': 'CEN',
    'Elimbah Stabling Yard': 'EMHS',
    'Kippa-Ring Stabling Yard': 'KPRS',
    'Kippa-Ring Stable':'KPRS',
    'Kippa-Ring': 'KPR',
    'Airport Junction': 'AJN',
    'Virginia': 'VGI',
    'Sunshine': 'SSN',
    'Geebung': 'GEB',
    'Zillmere': 'ZLL',
    'Carseldine': 'CDE',
    'Bald Hills': 'BDS',
    'Strathpine': 'SPN',
    'Bray Park': 'BPR',
    'Lawnton': 'LWO',
    'Petrie': 'PET',
    'Dakabin': 'DKB',
    'Narangba': 'NRB',
    'Burpengary': 'BPY',
    'Morayfield': 'MYE',
    'Mayne North Yard': 'YN',
    'Mayne North':'YN', #!!!
    'Mayne Yard Arrival': 'YNA',
    'Roma St West Junction': 'RSWJ',
    'South Brisbane': 'SBE',
    'South Bank': 'SBA',
    'Park Road': 'PKR',
    'Dutton Park': 'DUP',
    'Fairfield': 'FFI',
    'Yeronga': 'YRG',
    'Yeerongpilly': 'YLY',
    'Moorooka': 'MQK',
    'Rocklea': 'RKE',
    'Salisbury': 'SLY',
    'Coopers Plains': 'CEP',
    'Banoon': 'BQO',
    'Sunnybank': 'SYK',
    'Altandi': 'ATI',
    'Runcorn': 'RUC',
    'Fruitgrove': 'FTG',
    'Kuraby': 'KRY',
    'Trinder Park': 'TDP',
    'Woodridge': 'WOI',
    'Kingston': 'KGT',
    'Loganlea': 'LGL',
    'Bethania': 'BTI',
    'Edens Landing': 'EDL',
    'Eden\'s Landing': 'EDL',
    'Eden’s Landing': 'EDL',
    'Holmview': 'HVW',
    'Beenleigh': 'BNH',
    'Beenleigh Turnback': 'BNT',
    'Electric Train Flyover': 'ETF',
    'Elec Train Flyover':'ETF',
    'Electric Depot Junction': 'EDJ',
    'Ipswich Stabling':'IPSS',
    'Ipswich Stabling Yard': 'IPSS',
    'Ipswich Stable':'IPSS',
    'Ipswich': 'IPS',
    'Milton': 'MTZ',
    'Auchenflower': 'AHF',
    'Toowong': 'TWG',
    'Taringa': 'TIQ',
    'Indooroopilly': 'IDP',
    'Chelmer': 'CMZ',
    'Graceville': 'GVQ',
    'Sherwood': 'SHW',
    'Corinda': 'CQD',
    'Oxley': 'OXL',
    'Darra': 'DAR',
    'Wacol': 'WAC',
    'Gailes': 'GAI',
    'Goodna': 'GDQ',
    'Redbank': 'RDK',
    'Riverview': 'RVV',
    'Dinmore': 'DIR',
    'Ebbw Vale': 'EBV',
    'Bundamba': 'BDX',
    'Booval': 'BOV',
    'East Ipswich': 'EIP',
    'Rothwell': 'RWL',
    'Mango Hill East': 'MGE',
    'Mango Hill': 'MGH',
    'Murrumba Downs': 'MRD',
    'Kallangur': 'KGR',
    'Richlands': 'RHD',
    'Springfield': 'SFD',
    'Springfield Central': 'SFC',
    'Thomas Street': 'THS',
    'Wulkuraka': 'WUL',
    'Karrabin': 'KRA',
    'Walloon': 'WOQ',
    'Thagoona': 'TAO',
    'Yarrowlea': 'YLE',
    'Rosewood': 'RSW',
    'Buranda': 'BRD',
    'Coorparoo': 'CRO',
    'Norman Park': 'NPR',
    'Morningside': 'MGS',
    'Cannon Hill': 'CNQ',
    'Murarrie': 'MJE',
    'Hemmant': 'HMM',
    'Lindum': 'LDM',
    'Lytton Junction': 'LJN',
    'Wynnum North': 'WYH',
    'Wynnum': 'WNM',
    'Wynnum Central': 'WNC',
    'Manly': 'MNY',
    'Lota': 'LOT',
    'Thorneside': 'TNS',
    'Birkdale': 'BDE',
    'Wellington Point': 'WPT',
    'Ormiston': 'ORO',
    'Cleveland': 'CVN',
    'Elimbah': 'EMH',
    'Beerburrum': 'BEB',
    'Glasshouse Mountains': 'GSS',
    'Beerwah': 'BWH',
    'Landsborough': 'LSH',
    'Mooloolah': 'MOH',
    'Eudlo': 'EUD',
    'Palmwoods': 'PAL',
    'Woombye': 'WOB',
    'Nambour': 'NBR',
    'Mayne Junction': 'MYJ',
    'Windsor': 'WID',
    'Wilston': 'WLQ',
    'Newmarket': 'NWM',
    'Alderley': 'ADY',
    'Enoggera': 'EGG',
    'Gaythorne': 'GAO',
    'Mitchelton': 'MHQ',
    'Oxford Park': 'OXP',
    'Grovely': 'GOQ',
    'Keperra': 'KEP',
    'Ferny Grove': 'FYG',
    'Robina Stabling Yard': 'ROBS',
    'Robina': 'ROB',
    'Varsity Lakes': 'VYS',
    'Caboolture West Yard': 'CAW',
    'International Airport': 'BIT',
    'Domestic Airport': 'BDT',
    'Ormeau': 'ORM',
    'Coomera': 'CXM',
    'Helensvale': 'HLN',
    'Nerang': 'NRG',
    'Beenleigh Stabling Yard': 'BNHS',
    'Beenleigh Stable': 'BNHS',
    'Banyo Stabling Yard': 'BQYS',
    'Wulkuraka Service Centre East': 'WFE',
    'WSC East Entrance': 'FEE',
    'Redbank Stabling Yard': 'RDKS',
    'Redbank Stabling':'RDKS',
    'Roma St Fork': 'RSF',
    'Clayfield': 'CYF',
    'Hendra': 'HDR',
    'Ascot': 'ACO',
    'Doomben': 'DBN',
    'Clapham Yard': 'CPM',
    'Varsity Lakes Turnback': 'VYST',
    'Varsity Lakes TB': 'VYST',
    'Woombye Stabling Yard': 'WOBS',
    'Gympie North': 'GYN',
    'Glanmire': 'GMR',
    'Woondum': 'WOO',
    'Traveston': 'TRA',
    'Cooran': 'COZ',
    'Pomona': 'PMQ',
    'Cooroy': 'COO',
    'Sunrise': 'SSE',
    'Eumundi': 'EUM',
    'North Arm': 'NHR',
    'Yandina': 'YAN',
    'Wulkuraka Service Centre West': 'WFW',
    'WSC West Entrance': 'FWE',
    'Tennyson': 'TNY',
    'Moolabin': 'MBN',
    'Rocklea sidings': 'RKET',
    'Rocklea Sidings': 'RKET',
    'Electric Train Balloon': 'ETB',
    'Elec Train Balloon': 'ETB',
    'Petrie Stabling Yard': 'PETS',
    'Petrie Eastern Sdgs': 'PETS',
    'Mayne East Stabling Yard':'MES',
    'Mayne North Stabling':'MNS',
    'Mayne 2':'MNE2',
    'Ormeau Stabling':'ORMS',
    'Pimpama':'PIA',
    'Hope Island':'HID',
    'Merrimac':'MRC',
    'Boggo Road':'BOG',
    'Boggo Road station':'BOG',
    'Albert Street':'ALB',
    'Woolloongabba':'WLG',
    
    'Mayne North Stabling':'MNS',
    'Mayne East':'MES',
    'Mayne East Stabling':'MES',
    'Clapham Yard':'CPM',
    
    'Beerwah Junction': 'BWJ', 
    'Beewah East Junction': 'BEJ', 
    'Aura': 'AUR', 
    'Caloundra Road': 'CRD', 
    'Mayne North Yard Entrance': 'MNYE', 
    'Bowen Hills North Jn': 'BHNJ', 
    'Signal 10 Departure': 'SIG10D', 
    'Kippa-Ring Stable': 'KPRS', 
    'Ormeau Junction': 'ORMJ', 
    'Salisbury Junction': 'SLYJ', 
    'Yeerongpilly Junction': 'YLYJ', 
    'Southern Tunnel Portal': 'STP', 
    'Northern Tunnel Portal': 'NTP', 
    'Land Bridge': 'LBR', 
    'Tunnel Jn': 'ZZZTJN', 
    'Mayne East Junction': 'MEJ', 
    'Clapham Yard Junction': 'CYJ', 
    'Signal 9 Arrival': 'SIG9A', 
    'Mayne East Yard': 'MES', 
    'Fork Timing Point': 'FRK', 
    'Tennyson Branch Junction': 'TNYBCHJ', 
    
    'Comes From': 'CF',
    'Continues To': 'CT',
    'Central arrive':'BNCarr',
    'Central depart':'BNCdep',
    'Bowen Hills arrive':'BHIarr',
    'Bowen Hills depart':'BHIdep',
    'Roma Street arrive':'RSarr',
    'Roma Street depart':'RSdep',
    'Fortitude Valley arrive':'BRCarr',
    'Fortitude Valley depart':'BRCdep',
    'Ipswich arrive':'IPSarr',
    'Ipswich depart':'IPSdep'
  }
























def TTS_WTT(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None
    
    try:

        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        if __name__ == "__main__":
            print(filename,'\n')
    
        tree = ET.parse(filename)
        root = tree.getroot()
        
        
        
        filename = filename[:-4]
        weekdayfilename_xlsx  = f'WorkingTimetable-{filename}-Weekday.xlsx'
        weekendfilename_xlsx  = f'WorkingTimetable-{filename}-Weekend.xlsx'
        monthufilename_xlsx   = f'WorkingTimetable-{filename}-Mon-Thu.xlsx'
        fridayfilename_xlsx   = f'WorkingTimetable-{filename}-Fri.xlsx'
        saturdayfilename_xlsx = f'WorkingTimetable-{filename}-Saturday.xlsx'
        sundayfilename_xlsx   = f'WorkingTimetable-{filename}-Sunday.xlsx'
        
        weekdayworkbook  = xlsxwriter.Workbook(weekdayfilename_xlsx)
        weekendworkbook  = xlsxwriter.Workbook(weekendfilename_xlsx)
        monthuworkbook   = xlsxwriter.Workbook(monthufilename_xlsx)
        fridayworkbook   = xlsxwriter.Workbook(fridayfilename_xlsx)
        saturdayworkbook = xlsxwriter.Workbook(saturdayfilename_xlsx)
        sundayworkbook   = xlsxwriter.Workbook(sundayfilename_xlsx)
        
    
    
    
    
    
        
        ### If in future, the MTP team may only require let's say a weekend timetable and a weekday timetable to be created,
        ###  this code will allow easy toggling of how many reports get generated for the user
        ### In the meantime, all useful combinations of reports will be created if the day_of_operation exists in the rsx.
        ###  That is, no blank timetable workbooks will be created
        Weekday  = Weekend = MonThu = Friday = Saturday = Sunday = False
        Weekday  = True
        Weekend  = True
        MonThu   = True
        Friday   = True
        Saturday = True
        Sunday   = True
        
        
        
        
        Weekday  = 124 if Weekday  else False
        Weekend  = 130 if Weekend  else False
        MonThu   = 60  if MonThu   else False
        Friday   = 64  if Friday   else False
        Saturday = 128 if Saturday else False
        Sunday   = 2   if Sunday   else False
        
        workbooks_dict = {
            Weekday:  weekdayworkbook,
            Weekend:  weekendworkbook,
            MonThu:   monthuworkbook,
            Friday:   fridayworkbook,
            Saturday: saturdayworkbook,
            Sunday:   sundayworkbook,
            }
        
        workbooks = []
        for day in [Weekday, Weekend, MonThu, Friday, Saturday, Sunday]:
            daysheet = workbooks_dict.get(day)
            if day:
                workbooks.append(daysheet)
                
                
                
                
                
                
                
                
                
                
                
        ### Check for duplicate train numbers before executing the script
        ### Print warning for user if duplicates exist
        ### Print out all duplicates
        tn_list = []
        tn_doubles = []
        for train in root.iter('train'):
            tn  = train.attrib['number']; day = train[0][0][0].attrib['weekdayKey']
            if (tn,day) in tn_list: tn_doubles.append((tn,day))
            tn_list.append((tn,day))
                
        if tn_doubles:
            print('           Error: Duplicate train numbers')
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit()    
                
        start_time = time.time()        
                
                
                
    
        
        
    
            
        
        
        
        
        
        ### uniquestations_dict and network_vrt_dict are used to determine what Line that trip belongs to
        ### Virtual run time (vrt) dictionaries for each line are used to order trips chronologically 
        ###  due to some trips not running through the city making sorting trips by Central arrival unavailable
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
            'CAB':     (15, 3218), 
            'CAE':     (14, 3400), 
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
            'RS':      (0,   0),
            'BNC':     (-1, -127),
            'BRC':     (-2, -244),
            'BHI':     (-3, -341),
            'AIN':     (-4, -532),
            'WWI':     (-5, -614),
            'EGJ':     (-6, -696),
            'AJN':     (-7, -747),
            'BIT':     (-8, -1092),
            'BDT':     (-9, -1248)
            }
        
        
        vrt_2InnerCity = {
            'YN':      (6,   1024 ),
            'YNA':     (5,   649 ),
            'MNE':     (4,   544 ),
            'BHI':     (3,   324 ),
            'BRC':     (2,   264 ),
            'BNC':     (1,   140 ),
            'RS':      (0,   0 ),
            'SBE':     (-1, -226 ),
            'SBA':     (-2, -316 ),
            'PKR':     (-3, -447 ),
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
            'BQYS':    (12, 1740), #1710
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
            'Beenleigh':                vrt_2Beenleigh,
            'Caboolture-Gympie North':  vrt_2GympieNth,
            'Cleveland':                vrt_2Cleveland,
            'Doomben':                  vrt_2Doomben,
            'Ferny Grove':              vrt_2FernyGrove,
            'Varsity Lakes - Airport':  vrt_2VarsityLs,               
            'Ipswich-Rosewood':         vrt_2Rosewood,
            'Inner City':               vrt_2InnerCity,  
            'Redcliffe':                vrt_2KippaRing,
            'Shorncliffe':              vrt_2Shorncliffe,
            'Springfield':              vrt_2Springfield
            }
            
        
        uniquestations_dict = {
            'Beenleigh':                ('BNHS','BNT','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKET','RKE','MQK','CPM','MBN','TNY','YLY','YRG','FFI','DUP'),
            'Caboolture-Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN','AUR','CRD'),
            'Cleveland':                ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                  ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':              ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Varsity Lakes - Airport':  ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT'),
            'Ipswich':                  ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
            'Rosewood':                 ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Ipswich-Rosewood':         ('MBN','TNY','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Inner City':               ('BHI','BRC','BNC','RS'),
            'Redcliffe':                ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':              ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Springfield':              ('RHD','SFD','SFC')
            }
        
    
    
    
    
    
    
        
        ### In each line worksheet, we want to bold key stations and their broadsheet times
        ### If this location has multiple rows (for say arrival time, platform, departure time), bold all these associated lines as well
        bnh_boldlist = ['BNH', 'LGL', 'KRY', 'CEP', 'YLY', 'YRG', 'PKR', 'BNC']
        
        cab_boldlist = ['BNC', 'EGJ', 'NTG', 'PET', 'CAB', 'GYN']
        
        cvn_boldlist = ['CVN', 'BDE', 'MNY', 'MGS', 'PKR', 'BNC']
        
        dbn_boldlist = ['BNC', 'EGJ', 'DBN']
        
        fyg_boldlist = ['BNC', 'BHI', 'MHQ', 'FYG']
        
        vys_boldlist = ['ROB', 'BNH', 'BNC', 'EGJ', 'BDT']
        
        inc_boldlist = ['BNC']
        
        ips_boldlist = ['RSW', 'IPS', 'DAR', 'IDP', 'BNC']
        
        rdp_boldlist = ['BNC', 'EGJ', 'NTG', 'PET']
        
        shc_boldlist = ['BNC', 'EGJ', 'NTG', 'BZL', 'SGE']
        
        sfc_boldlist = ['BNC', 'IDP', 'DAR']
        
        
        ### d_list      tracks the days present in the rsx
        ### forms_dict  keeps track of the next train in the run
        ###              could be changed to use the run ID instead of the connection attribute in the case of missing connections
        ### newstations tracks if new locations have been added to the geography that haven't yet been added to stationmaster
        ###              will allow the code to continue without erroring, stationmaster should then be amended 
        d_list = []
        forms_dict = {}
        newstations = []
        for train in root.iter('train'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
            
            entries = [x for x in train.iter('entry')]
            origin = entries[0].attrib
            destin = entries[-1].attrib
    
            oID = origin['stationID']
            dID = destin['stationID']
            
            odep = origin['departure']
            ddep = destin['departure']
            
            
            connection = [x.attrib['trainNumber'] for x in train.iter('connection')]
            if connection:
                connection = connection[0]
                forms_dict[ (connection,WeekdayKey) ] = (tn,odep,oID)
                
            for entry in entries:
                stID = entry.attrib['stationID']
                name = entry.attrib['stationName']
                
                if name not in stationmaster:
                    newstations.append(name)
                    stationmaster[name] = stID
                 
                    
                 
                    
                 
    
        
        
        
        
        
        
        
        if newstations:
            print('Locations not recorded in station dictionary')
            print('--------------------------------------------')
            for x in newstations:
                print(x)
            print('--------------------------------------------')
            
            
            
            
            
            
        
        
        
        def zip_stations(stationNames):
            """ Creates a list of tuples with the station station names and their abreviations """
            
            y = []
            for x in stationNames:
                # print(x)
                if stationmaster.get(x):
                    y.append(stationmaster.get(x))
                elif 'arrive' in x:
                    y.append(stationmaster.get(x[:-7])+'arr')
                elif 'depart' in x:
                    y.append(stationmaster.get(x[:-7])+'dep')
                elif 'platform' in x:
                    y.append(stationmaster.get(x[:-9])+'pfm')
                else:
                    y.append(None); print(f'Undocumented station: {x}')
            return list(zip(stationNames,y))
                
        
         
            
        ### These will be the row headers appearing in the worksheets - can be customised
        ### zip_stations will pair each location name up with a unique abbreviated station ID
        ###  these list of tuples will be fed into the write_workbook function to print the data for each station for each trip
        bnh_D = zip_stations(['Beenleigh Turnback','Beenleigh Stable','Beenleigh arrive','Beenleigh platform','Beenleigh depart','Holmview','Eden’s Landing','Bethania arrive','Bethania platform','Bethania depart','Loganlea','Kingston platform','Kingston','Woodridge','Trinder Park','Kuraby platform','Kuraby','Fruitgrove','Runcorn','Altandi','Sunnybank','Banoon','Coopers Plains platform','Coopers Plains','Salisbury platform','Salisbury','Rocklea Sidings','Rocklea','Moorooka','Moolabin','Tennyson','Yeerongpilly','Yeronga','Fairfield','Dutton Park','Park Road platform','Park Road','South Bank','South Brisbane','Roma St West Junction','Roma St Fork','Normanby','Exhibition','Campbell St','Elec Train S','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Mayne Yard Arrival','Mayne North','Elec Train Balloon','Electric Depot Junction','Elec Train Flyover'])
        bnh_U = zip_stations(['Elec Train Flyover','Electric Depot Junction','Mayne','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Elec Train S','Campbell St','Exhibition','Normanby','Roma St Fork','Roma St West Junction','South Brisbane','South Bank','Park Road platform','Park Road','Dutton Park','Fairfield','Yeronga','Yeerongpilly','Tennyson','Moolabin','Moorooka','Rocklea','Rocklea Sidings','Salisbury platform','Salisbury','Coopers Plains platform','Coopers Plains','Banoon','Sunnybank','Altandi','Runcorn','Fruitgrove','Kuraby platform','Kuraby','Trinder Park','Woodridge','Kingston platform','Kingston','Loganlea','Bethania arrive','Bethania platform','Bethania depart','Eden’s Landing','Holmview','Beenleigh arrive','Beenleigh platform','Beenleigh depart','Beenleigh Stable','Beenleigh Turnback'])
        
        cab_D = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne Junction','Elec Train S','Exhibition','Campbell St','Normanby','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Eagle Junction','Northgate platform','Northgate','Petrie Eastern Sdgs','Petrie arrive','Petrie platform','Petrie depart','Dakabin','Narangba','Burpengary','Morayfield','Caboolture arrive','Caboolture platform','Caboolture depart','Caboolture West Yard','Caboolture East Yard','Caboolture North','Elimbah Stabling Yard','Elimbah arrive','Elimbah depart','Beerburrum arrive','Beerburrum depart','Glasshouse Mountains arrive','Glasshouse Mountains depart','Beerwah arrive','Beerwah depart','Landsborough arrive','Landsborough depart','Mooloolah arrive','Mooloolah depart','Eudlo arrive','Eudlo depart','Palmwoods arrive','Palmwoods depart','Woombye Stabling Yard','Woombye arrive','Woombye depart','Nambour arrive','Nambour depart','Yandina arrive','Yandina depart','North Arm','Eumundi arrive','Eumundi depart','Sunrise','Cooroy arrive','Cooroy depart','Pomona arrive','Pomona depart','Cooran arrive','Cooran depart','Traveston arrive','Traveston depart','Woondum','Glanmire','Gympie North arrive'])
        cab_U = zip_stations(['Gympie North depart','Glanmire','Woondum','Traveston arrive','Traveston depart','Cooran arrive','Cooran depart','Pomona arrive','Pomona depart','Cooroy arrive','Cooroy depart','Sunrise','Eumundi arrive','Eumundi depart','North Arm','Yandina arrive','Yandina depart','Nambour arrive','Nambour depart','Woombye arrive','Woombye depart','Woombye Stabling Yard','Palmwoods arrive','Palmwoods depart','Eudlo arrive','Eudlo depart','Mooloolah arrive','Mooloolah depart','Landsborough arrive','Landsborough depart','Beerwah arrive','Beerwah depart','Glasshouse Mountains arrive','Glasshouse Mountains depart','Beerburrum arrive','Beerburrum depart','Elimbah arrive','Elimbah depart','Elimbah Stabling Yard','Caboolture North','Caboolture West Yard','Caboolture arrive','Caboolture East Yard','Caboolture platform','Caboolture depart','Morayfield','Burpengary','Narangba','Dakabin','Petrie arrive','Petrie platform','Petrie depart','Petrie Eastern Sdgs','Lawnton','Northgate platform','Northgate','Eagle Junction','Mayne','Mayne Junction','Mayne Yard Arrival','Mayne North','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Roma St West Junction','Normanby','Exhibition','Campbell St','Elec Train S'])
        
        cvn_D = zip_stations(['Cleveland','Ormiston','Wellington Point arrive','Wellington Point depart','Birkdale','Thorneside arrive','Thorneside depart','Lota arrive','Lota depart','Manly arrive','Manly platform','Manly depart','Wynnum Central','Wynnum','Wynnum North','Lytton Junction','Lindum','Hemmant','Murarrie','Cannon Hill platform','Cannon Hill','Morningside','Norman Park','Coorparoo','Buranda','Park Road','South Bank','South Brisbane','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Mayne Yard Arrival','Mayne North','Electric Depot Junction','Elec Train Flyover'])
        cvn_U = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne','Elec Train Flyover','Electric Depot Junction','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Roma St West Junction','South Brisbane','South Bank','Park Road','Buranda','Coorparoo','Norman Park','Morningside','Cannon Hill platform','Cannon Hill','Murarrie','Hemmant','Lindum','Lytton Junction','Wynnum North','Wynnum','Wynnum Central','Manly arrive','Manly platform','Manly depart','Lota arrive','Lota depart','Thorneside arrive','Thorneside depart','Birkdale','Wellington Point arrive','Wellington Point depart','Ormiston','Cleveland'])
        
        dbn_D = zip_stations(['Park Road','South Bank','South Brisbane','Roma St West Junction','Elec Train S','Exhibition','Campbell St','Normanby','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Albion','Wooloowin','Eagle Junction arrive','Eagle Junction platform','Eagle Junction depart','Clayfield','Hendra','Ascot','Doomben platform','Doomben'])
        dbn_U = zip_stations(['Doomben platform','Doomben','Ascot','Hendra','Clayfield','Eagle Junction arrive','Eagle Junction platform','Eagle Junction depart','Wooloowin','Albion','Mayne Yard Arrival','Mayne North','Mayne Junction','Mayne','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Normanby','Exhibition','Campbell St','Elec Train S','Roma St West Junction','South Brisbane','South Bank','Park Road'])
        
        fyg_D = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne','Mayne Junction','Elec Train S','Campbell St','Exhibition','Normanby','Park Road','South Bank','South Brisbane','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Electric Depot Junction','Windsor','Wilston','Newmarket','Alderley','Enoggera','Gaythorne','Mitchelton','Oxford Park','Grovely','Keperra','Ferny Grove platform','Ferny Grove'])
        fyg_U = zip_stations(['Ferny Grove platform','Ferny Grove','Keperra','Grovely','Oxford Park','Mitchelton','Gaythorne','Enoggera','Alderley','Newmarket','Wilston','Windsor','Electric Depot Junction','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Normanby','Exhibition','Campbell St','Mayne Junction','Mayne','Mayne Yard Arrival','Mayne North','Elec Train S','Roma St West Junction','South Brisbane','South Bank','Park Road'])
        
        vys_D = zip_stations(['Varsity Lakes TB','Varsity Lakes platform','Varsity Lakes','Robina platform','Robina','Robina Stabling Yard','Nerang','Helensvale arrive','Helensvale depart','Coomera arrive','Coomera depart','Pimpama','Ormeau','Beenleigh arrive','Beenleigh platform','Beenleigh depart','Loganlea','Altandi','Tennyson','Moolabin','Park Road platform','Park Road','South Bank','South Brisbane','Roma St West Junction','Roma St Fork','Mayne North','Mayne Yard Arrival','Mayne Junction','Elec Train S','Campbell St','Exhibition','Normanby','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Albion','Wooloowin','Eagle Junction platform','Eagle Junction','Airport Junction','International Airport','Domestic Airport'])
        vys_U = zip_stations(['Domestic Airport','International Airport','Airport Junction','Eagle Junction platform','Eagle Junction','Wooloowin','Albion','Mayne','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Normanby','Roma St Fork','Exhibition','Campbell St','Elec Train S','Roma St West Junction','Moolabin','Tennyson','South Brisbane','South Bank','Park Road platform','Park Road','Altandi','Loganlea','Beenleigh arrive','Beenleigh platform','Beenleigh depart','Ormeau','Pimpama','Coomera arrive','Coomera depart','Helensvale arrive','Helensvale depart','Nerang','Robina Stabling Yard','Robina platform','Robina','Varsity Lakes platform','Varsity Lakes','Varsity Lakes TB'])
        
        inc_D = zip_stations(['Park Road','South Bank','South Brisbane','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Mayne Yard Arrival','Mayne North'])
        inc_U = zip_stations(['Mayne North','Mayne Yard Arrival','Elec Train Balloon','Mayne','Elec Train Flyover','Electric Depot Junction','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Normanby','Exhibition','Campbell St','Elec Train S','Roma St West Junction','South Brisbane','South Bank','Park Road'])
        
        ips_D = zip_stations(['Rosewood platform','Rosewood','Yarrowlea','Thagoona','Walloon','WSC West Entrance','Wulkuraka Service Centre West','Karrabin','Wulkuraka','Wulkuraka Service Centre East','WSC East Entrance','Thomas Street','Ipswich Stable','Ipswich arrive','Ipswich platform','Ipswich depart','East Ipswich','Booval','Bundamba','Ebbw Vale','Dinmore','Riverview','Redbank Stabling','Redbank','Goodna','Gailes','Wacol','Darra arrive','Darra platform','Darra depart','Oxley platform','Oxley','Tennyson','Moolabin','Corinda platform','Corinda','Sherwood platform','Sherwood','Graceville','Chelmer','Indooroopilly','Taringa','Toowong','Auchenflower','Milton','Roma St West Junction','Roma St Fork','Normanby','Exhibition','Campbell St','Elec Train S','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Electric Depot Junction','Elec Train Flyover','Mayne','Elec Train Balloon','Mayne Yard Arrival','Mayne North'])
        ips_U = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne','Electric Depot Junction','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Elec Train S','Campbell St','Exhibition','Normanby','Roma St Fork','Roma St West Junction','Milton','Auchenflower','Toowong','Taringa','Indooroopilly','Chelmer','Graceville','Sherwood platform','Sherwood','Corinda platform','Corinda','Moolabin','Tennyson','Oxley platform','Oxley','Darra arrive','Darra platform','Darra depart','Wacol','Gailes','Goodna','Redbank','Redbank Stabling','Riverview','Dinmore','Ebbw Vale','Bundamba','Booval','East Ipswich','Ipswich arrive','Ipswich platform','Ipswich depart','Ipswich Stable','Thomas Street','WSC East Entrance','Wulkuraka Service Centre East','Wulkuraka','Karrabin','Walloon','Thagoona','Yarrowlea','Rosewood platform','Rosewood'])
        
        rdp_D = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne Junction','Elec Train S','Campbell St','Exhibition','Normanby','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Albion','Wooloowin','Eagle Junction','Airport Junction','Toombul','Nundah','Northgate platform','Northgate','Virginia','Sunshine','Geebung','Zillmere','Carseldine','Bald Hills','Strathpine','Bray Park','Lawnton','Petrie arrive','Petrie platform','Petrie depart','Petrie Eastern Sdgs','Narangba','Kallangur','Murrumba Downs','Mango Hill','Mango Hill East','Rothwell','Kippa-Ring Stabling Yard','Kippa-Ring platform','Kippa-Ring'])
        rdp_U = zip_stations(['Kippa-Ring platform','Kippa-Ring','Kippa-Ring Stabling Yard','Rothwell','Mango Hill East','Mango Hill','Murrumba Downs','Kallangur','Petrie arrive','Petrie platform','Petrie depart','Lawnton','Bray Park','Strathpine','Bald Hills','Carseldine','Zillmere','Geebung','Sunshine','Virginia','Northgate platform','Northgate','Nundah','Toombul','Eagle Junction','Wooloowin','Albion','Mayne Junction','Mayne Yard Arrival','Mayne North','Mayne','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Roma St West Junction','Normanby','Exhibition','Campbell St','Elec Train S'])
        
        shc_D = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne Junction','Elec Train S','Campbell St','Exhibition','Normanby','Park Road','South Bank','South Brisbane','Roma St West Junction','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Albion','Wooloowin','Eagle Junction platform','Eagle Junction','Airport Junction','Toombul','Nundah','Northgate platform','Northgate','Bindha','Banyo Stabling Yard','Banyo','Nudgee','Boondall','North Boondall','Deagon','Sandgate','Shorncliffe'])
        shc_U = zip_stations(['Shorncliffe','Sandgate','Deagon','North Boondall','Boondall','Nudgee','Banyo','Banyo Stabling Yard','Bindha','Northgate platform','Northgate','Nundah','Toombul','Airport Junction','Eagle Junction platform','Eagle Junction','Wooloowin','Albion','Mayne','Mayne Junction','Mayne Yard Arrival','Mayne North','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Roma St West Junction','South Brisbane','South Bank','Park Road','Normanby','Exhibition','Campbell St','Elec Train S'])
        
        sfc_D = zip_stations(['Springfield Central platform','Springfield Central','Springfield','Richlands','Darra','Oxley platform','Oxley','Corinda platform','Corinda','Sherwood platform','Sherwood','Graceville','Chelmer','Indooroopilly','Taringa','Toowong','Auchenflower','Milton','Roma St West Junction','Roma St Fork','Normanby','Exhibition','Campbell St','Elec Train S','Roma Street arrive','Roma Street platform','Roma Street depart','Central arrive','Central platform','Central depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Mayne','Mayne Yard Arrival','Mayne North'])
        sfc_U = zip_stations(['Mayne North','Mayne Yard Arrival','Mayne','Mayne Junction','Bowen Hills arrive','Bowen Hills platform','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley platform','Fortitude Valley depart','Central arrive','Central platform','Central depart','Roma Street arrive','Roma Street platform','Roma Street depart','Elec Train S','Campbell St','Exhibition','Normanby','Roma St Fork','Roma St West Junction','Milton','Auchenflower','Toowong','Taringa','Indooroopilly','Chelmer','Graceville','Sherwood platform','Sherwood','Park Road','Tennyson','Moolabin','Corinda platform','Corinda','Oxley platform','Oxley','Darra','Richlands','Springfield','Springfield Central platform','Springfield Central'])
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        def write_workbook(daycode, weekdaykeys):
            """ 
            The use of a master function to write a workbook with all other functions nested within
            Run twice, one for school days and one for weekends
            """
            
            def flatten(H):
                """ Takes a list of lists and returns every individual element in one list """
                
                while type(H[0]) == str:
                    H = [H]
                return [item for sublist in H for item in sublist]
        
            def stoptime_info(entry_index): 
                """ Returns the arrival and departure times for the nth stop in a trip """
                
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
                """ Format converter from hh:mm:ss to [h]:mm """
                
                if type(timestring) == list:
                    timestring = timestring[0]
                ##################################################
                
                if timestring is None or timestring.isalpha() or ':' not in timestring:
                    pass
                
                elif '(' in timestring and ')' in timestring:
                    timestring = timestring[1:-1]
                    if timestring[0] == '0':
                        timestring = timestring[1:-3]
                    else: timestring = timestring[:-3]
                    return express(timestring)
                    
                
                elif timestring[0] == '0':
                    timestring = timestring[1:-3]
                else: timestring = timestring[:-3]
                return timestring
            
            
            
            
            def express(departure):
                """ Puts the departure times in parentheses if it runs express through that station """
                
                return departure.join(['(',')'])
        
        
            def build_triplist(triplist,line,Outbound=False):
                """ 
                Fills an empty list with trips that match conditions for each line
                Info for each trip, including DoO and departure times, are contained in a dictionary - tripdict
                """
                
                tripdict = {}
                vrt = network_vrt_dict.get(line)
                line_stops = uniquestations_dict.get(line)
                entries = [x for x in train.iter('entry')]
                stations = {x.attrib['stationID'] for x in entries}
                
                lineID = train.attrib['lineID']
                run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
                
                origin = entries[0].attrib
                destin = entries[-1].attrib
                stationIDs = [x.attrib['stationID'] for x in entries]
                oID = origin['stationID']
                dID = destin['stationID']
                
                
                condition = stations.intersection(line_stops) 
                ### Trains are sorted into lines using the 'condition' variable,
                ### If condition is true after all the checks, a dictionary will be created with all relevant information about the trip
                ### The condition works by checking the train route for the existence of a station unique to that particular line
                ### In some cases, additional edge-cases must be accounted for            
                if line == 'Beenleigh':
                    condition = condition and stations.isdisjoint(uniquestations_dict.get('Varsity Lakes - Airport'))
        
                elif line == 'Shorncliffe':
                    condition = condition or ('NTG' in [oID,dID] and any([vrt.get(x) for x in stationIDs if x != 'NTG']))
                    
                elif line == 'Inner City':
                    city_end1 = ['PKR','RS','ETS']
                    city_end2 = ['BHI','YN','ETB','ETF']
                    if Outbound:
                        condition = oID in city_end1 and dID in city_end2
                    else:
                        condition = oID in city_end2 and dID in city_end1  
                
                elif line == 'Redcliffe':
                    shared_line_rdp_stations = ['LWO', 'BPR', 'SPN', 'BDS', 'CDE', 'ZLL', 'GEB', 'SSN', 'VGI']
                    if Outbound:
                        condition = condition or dID in shared_line_rdp_stations
                    else:
                        condition = condition or oID in shared_line_rdp_stations
        
        
                
                ### Lines are sorted as outbound or inbounded based on the order of the station indexes, 
                ### Roma Street being zero and increasing by one at every station until the line terminus
                ### If the station indexes decrease as the train travels along its path, its an inbound train; the converse means it's outbound
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
                
                    if Outbound:
                        condition = condition and increasing
                    else:
                        condition = condition and decreasing 
                
                
                
                ### Once a trip has been checked, all information needed for the working timetable is bundled into a dictionary,
                ### which is then appended to the relevant triplist
                if condition:
                     
                    tripdict['Train ID'] = tn           
                    tripdict['DoO'] = weekdaykey_dict2.get(WeekdayKey)
                    tripdict['Run ID'] = run
                    traintype = origin['trainTypeId']
                    if 'IMU' in traintype:
                        tripdict['Unit'] = traintype[-6:]
                    elif 'DEPT' in traintype:
                        tripdict['Unit'] = 'DEPT'
                    else:
                        tripdict['Unit'] = traintype[-3:]
                    
                    connection = [x for x in train.iter('connection')]
                    if connection:
                        connection = connection[0]
                        tripdict['Formed By'] = connection.get('trainNumber')
                        tripdict['Formed At'] = connection.get('trainDeparture')
                    else: 
                        tripdict['Formed By'] = 'STRT'
                        tripdict['Formed At'] = origin['departure']
                    
                    tripdict['Formed/Origin Location'] = oID
                    
                    for entry in entries:
                        
                        if entry.attrib['stationID'] in vrt:
                            firstinline       = entry.attrib['stationID']
                            firstdeparture    = entry.attrib['departure']
                            firstinline_vrt   = vrt.get(firstinline)[-1]
                            
                            if Outbound:
                                vcbd = str(pd.Timedelta(firstdeparture) - pd.Timedelta(seconds=firstinline_vrt))
                            else:
                                vcbd = str(pd.Timedelta(firstdeparture) + pd.Timedelta(seconds=firstinline_vrt))
                            
                            
                            
                            
                            if vcbd[:6] == '1 days':
                                vcbd = str(24 + int(vcbd[7:9])) + str(vcbd[9:])
                            else: vcbd = vcbd[7:]
                            tripdict['VirtualCBD'] = vcbd
                            break
                    
                    tripdict['Forms'], tripdict['Forms At'], tripdict['Forms/Destination Location'] = forms_dict.get( (tn,WeekdayKey), ('FNSH',ddep,dID) )
                    
                    for n,x in enumerate(entries):
                        stationID   = x.attrib['stationID']
                        stopType = x.attrib['type']
                        platform    = '#' + x.attrib['trackID'][-1]
                        (arrival, departure) = stoptime_info(n)
                          
                        
                            
                            
                        tripdict[stationID] = express(departure) if stopType == 'pass' else departure
                        tripdict[stationID+'arr'] = express(arrival) if stopType == 'pass' else arrival
                        tripdict[stationID+'dep'] = express(departure) if stopType == 'pass' else departure
                        tripdict[stationID+'pfm'] = platform
                        
                    triplist.append(tripdict)
                    
            def refine_triplist(triplist):
                """ 
                Given a list for a line in a particular direction,
                Sort the list chronologically and merge trips that run on multiple days
                """
                
                SORT_ORDER = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'M-Th':4, 'Fri':5, 'Sat':6, 'Sun':7}
                triplist.sort(key=lambda x: SORT_ORDER[x['DoO']])
                triplist.sort(key=lambda x: x['VirtualCBD'])
                refinedtriplist = []
                for tripdict in triplist:
                    
                    if tripdict == triplist[0]:
                        refinedtriplist = [tripdict]
                        
                    else:
                        
                        ### Initialise bool variable to keep track of whether the current train is a duplicate
                        same_train = False
        
                        ### Check n previous trips
                        n = 3
                        
                        end_idx = len(refinedtriplist) - 1
                        
                        for i,rtd in enumerate(refinedtriplist):
                            if end_idx - i <= n:
                                same_train_list = []
                                tripdict_relevant_keys = [k for k in tripdict if k not in ['DoO','VirtualCBD'] and 'pfm' not in k]
                                for key in tripdict_relevant_keys:
                                    same_value = timetrim(tripdict.get(key)) == timetrim(rtd.get(key))
                                    same_train_list.append(same_value) 
    
                                    same_train_list.append(rtd.get('DoO') in ['M-Th','Sun','Sat','Fri'])
                                    same_train_list.append(tripdict.get('DoO') in ['M-Th','Sun','Sat','Fri'])
                                same_train = all(same_train_list)
                                if same_train:
                                    idx = i
                                    break
                            
                        if same_train:
                            refinedtriplist[idx]['DoO'] = 'M-F' if book == weekdayworkbook else 'WE'
                        else:
                            refinedtriplist.append(tripdict)
        
                return refinedtriplist
            
            
            def write_timetable(sheet):   
                """ Write the data to the worksheet, including train ID, DoO and departure times for each station """
                
                (triplist,stations,mainstations,title) = workinglineinfo_dict.get(sheet)
                stations_long = list(zip(*stations))[0]
                stations_abr  = list(zip(*stations))[1]
                triplist = refine_triplist(triplist)
                
                # sheet.freeze_panes(8,1)
                for i in range(1,len(stations)+13):
                    sheet.set_row(i,14.5)
        
        
                headers = ['Train ID','DoO','Run ID','Unit','Formed By','Formed At','Formed/Origin Location']
                footers = ['Forms', 'Forms At', 'Forms/Destination Location']
        
                startrow   = len(headers) + 2
                formsindex = len(stations) + startrow + 1
                sheet.write(2,0,'Days of Operation',boldleft)
                sheet.write_column(1,         0,headers,boldleft)
                sheet.write_column(formsindex,0,footers,boldleft)
                      
                for i,x in enumerate(triplist,1):
                    
                    sheet.write(0,i,'',title)
                    sheet.set_column(i,i,6)    #!!!
                    # sheet.set_column(i,i,10) #!!!
                    
                    vals = []
                    laststationdep, firststationarr = False, False
                    for idx,sID in enumerate(stations_abr):
                        
                        timevalue = x.get(sID)
                        
                        if timevalue:
                            if firststationarr or 'arr' not in sID:
                                vals.append(timetrim(timevalue))
                            else:
                                vals.append(None)
                            firststationarr = True
                        else:
                            vals.append(None)
                            
                        if timevalue:
                            if 'dep' in sID:
                                laststationdep = True
                                laststationidx = idx
                            else:
                                laststationdep = False
                                
                    if laststationdep:
                        vals[laststationidx] = None
                    
                    prev_vals = None
                    temp_vals = None
                    
                    for j,v in enumerate(vals):
                        
                        s = stations_abr[j]
                        for suffix in ['arr','dep','pfm']:
                            if suffix in s:
                                s = s[:-3]
                                
                        if i == 1:
                            if s in mainstations:
                                sheet.write(j+startrow,0,stations_long[j],boldleft)
                            else:
                                sheet.write(j+startrow,0,stations_long[j],left)
        
                        if s in mainstations:
                            sheet.write(j+startrow,i,v,bold)
                        else:
                            sheet.write(j+startrow,i,v)
                                
                                
                        if v and ':' in v:
                            uvals = v[1:-1] if '(' in v else v
                            temp_vals = '0' + (uvals) if len(uvals) == 4 else uvals
                            
                            if j == 0:
                                prev_vals = temp_vals
                            if temp_vals and prev_vals:
                                if temp_vals < prev_vals:
                                    if s in mainstations:
                                        sheet.write(j+startrow,i,v,boldredborder)
                                    else:
                                        sheet.write(j+startrow,i,v,redborder)
                                
                            
                            prev_vals = temp_vals
                    
                    
                    
                    sheet.freeze_panes(9,1)
                    # sheet.write(8,i,timetrim(x.get('VirtualCBD')),yellow) #!!!
                    # sheet.write(8,i,x.get('VirtualCBD'),yellow) #!!!
        
                    # Write the train info
                    for row,key in enumerate(headers,1):
                        sheet.write(row,i,timetrim(x.get(key)),default)
                    
                    # Write tbe info of the train this trip forms
                    for row,key in enumerate(footers,formsindex):
                        sheet.write(row,i,timetrim(x.get(key)))
                        
                        
                
                        
                    
                    
                        
                            
                    
                    
            ### Initialise two lists for each line - one inbound, one outbound
            ### Loop through the rsx and build a trip lists for each line
            ### Write the broadsheets for each line
            list1  = []
            list2  = []
            list3  = []
            list4  = []
            list5  = []
            list6  = []
            list7  = []
            list8  = []
            list9  = []
            list10 = []
            list11 = []
            list12 = []
            list13 = []
            list14 = []
            list15 = []
            list16 = []
            list17 = []
            list18 = []
            list19 = []
            list20 = []
            list21 = []
            list22 = []
            
            workinglineinfo_dict = {
                BNH_down:       (list1, bnh_D,bnh_boldlist,redtitle),
                BNH_up:         (list2, bnh_U,bnh_boldlist,redtitle),
                CAB_GYN_down:   (list3, cab_D,cab_boldlist,greentitle),
                CAB_GYN_up:     (list4, cab_U,cab_boldlist,greentitle),
                CVN_down:       (list5, cvn_D,cvn_boldlist,darkbluetitle),
                CVN_up:         (list6, cvn_U,cvn_boldlist,darkbluetitle),
                DBN_down:       (list7, dbn_D,dbn_boldlist,purpletitle),
                DBN_up:         (list8, dbn_U,dbn_boldlist,purpletitle),
                FYG_down:       (list9, fyg_D,fyg_boldlist,redtitle),
                FYG_up:         (list10,fyg_U,fyg_boldlist,redtitle),
                VYS_down:       (list11,vys_D,vys_boldlist,yellowtitle),
                VYS_up:         (list12,vys_U,vys_boldlist,yellowtitle),
                INC_down:       (list13,inc_D,inc_boldlist,greytitle),
                INC_up:         (list14,inc_U,inc_boldlist,greytitle),
                IPS_RSW_down:   (list15,ips_D,ips_boldlist,greentitle),
                IPS_RSW_up:     (list16,ips_U,ips_boldlist,greentitle),
                RDP_down:       (list17,rdp_D,rdp_boldlist,bluetitle),
                RDP_up:         (list18,rdp_U,rdp_boldlist,bluetitle),
                SHC_down:       (list19,shc_D,shc_boldlist,darkbluetitle),
                SHC_up:         (list20,shc_U,shc_boldlist,darkbluetitle),
                SFC_down:       (list21,sfc_D,sfc_boldlist,bluetitle),
                SFC_up:         (list22,sfc_U,sfc_boldlist,bluetitle)
                }
            
            gen = (x for x in root.iter('train') if x[0][0][0].attrib['weekdayKey'] in weekdaykeys)
            for train in gen:
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                entries = [x for x in train.iter('entry')]
                destin = entries[-1].attrib
                ddep = destin['departure']
                tn  = train.attrib['number']
                
                build_triplist(list1,  'Beenleigh'                               )    
                build_triplist(list2,  'Beenleigh',                 Outbound=True) 
                
                build_triplist(list3,  'Caboolture-Gympie North',   Outbound=True) 
                build_triplist(list4,  'Caboolture-Gympie North'                 ) 
        
                build_triplist(list5,  'Cleveland'                               )                  
                build_triplist(list6,  'Cleveland',                 Outbound=True)                  
                
                build_triplist(list7,  'Doomben',                   Outbound=True)                          
                build_triplist(list8,  'Doomben'                                 )                          
                
                build_triplist(list9,  'Ferny Grove',               Outbound=True)                        
                build_triplist(list10, 'Ferny Grove'                             )                        
                
                build_triplist(list11, 'Varsity Lakes - Airport'                 )        
                build_triplist(list12, 'Varsity Lakes - Airport',   Outbound=True)
                
                build_triplist(list13, 'Inner City',                Outbound=True) 
                build_triplist(list14, 'Inner City'                              ) 
        
                build_triplist(list15, 'Ipswich-Rosewood'                        ) 
                build_triplist(list16, 'Ipswich-Rosewood',          Outbound=True) 
        
                build_triplist(list17, 'Redcliffe',                 Outbound=True)                        
                build_triplist(list18, 'Redcliffe'                               )                        
        
                build_triplist(list19, 'Shorncliffe',               Outbound=True)   
                build_triplist(list20, 'Shorncliffe'                             )   
                
                build_triplist(list21, 'Springfield'                             )                        
                build_triplist(list22, 'Springfield',               Outbound=True)                        
        
            
            write_timetable(BNH_down)
            write_timetable(BNH_up)
            
            write_timetable(CAB_GYN_down)
            write_timetable(CAB_GYN_up)
            
            write_timetable(CVN_down)
            write_timetable(CVN_up)
            
            write_timetable(DBN_down)
            write_timetable(DBN_up)
        
            write_timetable(FYG_down)
            write_timetable(FYG_up)
            
            write_timetable(VYS_down)
            write_timetable(VYS_up)
            
            write_timetable(INC_down)
            write_timetable(INC_up)
            
            write_timetable(IPS_RSW_down)
            write_timetable(IPS_RSW_up)
            
            write_timetable(RDP_down)
            write_timetable(RDP_up)
            
            write_timetable(SHC_down)
            write_timetable(SHC_up)
            
            write_timetable(SFC_down)
            write_timetable(SFC_up)
            
            titles(daycode)
            
            # SFC_up.activate()
            # CAB_GYN_up.activate()
            # IPS_RSW_up.activate()
            # RDP_down.activate()
            # INC_up.activate()
            # SHC_up.activate()
            BNH_down.activate()
            # VYS_up.activate()
            # CVN_up.activate()
            # FYG_down.activate()
            # DBN_down.activate()
            
            
            printout = ''
            for d in weekdaykeys:
                if d == weekdaykeys[0]:
                    printout += d
                elif d == weekdaykeys[-1]:
                    printout += ' or ' + d
                else:
                    printout += ', ' + d
            print(f'\nAll trains with weekdayKey {printout} have been processed')
            
            dayofop_dict = {
                weekdayworkbook:  (weekdayfilename_xlsx, 'weekday'),
                weekendworkbook:  (weekendfilename_xlsx, 'weekend'),
                monthuworkbook:   (monthufilename_xlsx,  'Mon-Thurs'),
                fridayworkbook:   (fridayfilename_xlsx,  'Friday'),
                saturdayworkbook: (saturdayfilename_xlsx,'Saturday'),
                sundayworkbook:   (sundayfilename_xlsx,  'Sunday')
                }
            
            filename_xlsx, dayname = dayofop_dict.get(book)
            
            if CreateWorkbook:
                book.close() 
                if copyfile:
                    shutil.copy(filename_xlsx, mypath) 
                else:
                    if OpenWorkbook:
                        os.startfile(rf'{filename_xlsx}')
                        print(f'Opening {dayname} workbook')
                
            # ###########################################################   
            # dayofop_dict = {
            #     weekdayworkbook:  (weekdayfilename_xlsx, 'weekday'),
            #     weekendworkbook:  (weekendfilename_xlsx, 'weekend'),
            #     monthuworkbook:   (monthufilename_xlsx,  'Mon-Thurs'),
            #     fridayworkbook:   (fridayfilename_xlsx,  'Friday'),
            #     saturdayworkbook: (saturdayfilename_xlsx,'Saturday'),
            #     sundayworkbook:   (sundayfilename_xlsx,  'Sunday')
            #     }
            
            # filename_xlsx, dayname = dayofop_dict.get(book)
            
            # if OpenWorkbook and __name__ == "__main__":
            #     os.startfile(rf'{filename_xlsx}')
            #     print(f'Opening {dayname} workbook')
            # else:
            #     if copyfile:
            #         shutil.copy(filename_xlsx, mypath) 
            # ###########################################################
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
                    
        ### Create the worksheets
        ### Format the broadsheet
        ### Print the data
        ### Generate and open the workbook
        for book in workbooks:
            timetableinfo = book.add_worksheet('TimetableInfo')
            BNH_down      = book.add_worksheet('BNH-Down')
            BNH_up        = book.add_worksheet('BNH-Up')
            CAB_GYN_down  = book.add_worksheet('CAB+GYN-Down')
            CAB_GYN_up    = book.add_worksheet('CAB+GYN-Up')
            CVN_down      = book.add_worksheet('CVN-Down')
            CVN_up        = book.add_worksheet('CVN_Up')
            DBN_down      = book.add_worksheet('DBN-Down')
            DBN_up        = book.add_worksheet('DBN-Up')
            FYG_down      = book.add_worksheet('FYG-Down')
            FYG_up        = book.add_worksheet('FYG-Up')
            VYS_down      = book.add_worksheet('VYS+BDT-Down')
            VYS_up        = book.add_worksheet('VYS+BDT-Up')
            INC_down      = book.add_worksheet('INC-Down')
            INC_up        = book.add_worksheet('INC-Up')
            IPS_RSW_down  = book.add_worksheet('IPS+RSW-Down')
            IPS_RSW_up    = book.add_worksheet('IPS+RSW-Up')
            RDP_down      = book.add_worksheet('RDP-Down')
            RDP_up        = book.add_worksheet('RDP-Up')
            SHC_down      = book.add_worksheet('SHC-Down')
            SHC_up        = book.add_worksheet('SHC-Up')
            SFC_down      = book.add_worksheet('SFC-Down')
            SFC_up        = book.add_worksheet('SFC-Up')
            
            book.formats[0].set_align('center')
            book.formats[0].set_font_size(9)
            
            #Workbook formats
            default         = book.add_format({'align':'center','font_size':9  })
            left            = book.add_format({'align':'left',  'font_size':9  })
            bold            = book.add_format({'align':'center','font_size':9,'bold':True})
            boldleft        = book.add_format({'align':'left',  'font_size':9,'bold':True})
            
            boldredborder   = book.add_format({'align':'center','font_size':9, 'border':1, 'border_color':'#CC194C', 'bold':True})
            redborder       = book.add_format({'align':'center','font_size':9, 'border':1, 'border_color':'#CC194C'  })
            yellow          = book.add_format({'align':'center','font_size':9, 'bg_color':'yellow'  })
            
            #Worksheet title formats
            redtitle        = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#D10019'})
            greentitle      = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#007D45'})
            darkbluetitle   = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#004170'})
            purpletitle     = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#705098'})
            yellowtitle     = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#FEC938'})
            greytitle       = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#797A7C'})
            bluetitle       = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#0075B7'})
            
            
            
            
            
            linefont_dict = {
                BNH_down:       redtitle,
                BNH_up:         redtitle,
                CAB_GYN_down:   greentitle,
                CAB_GYN_up:     greentitle,
                CVN_down:       darkbluetitle,
                CVN_up:         darkbluetitle,
                DBN_down:       purpletitle,
                DBN_up:         purpletitle,
                FYG_down:       redtitle,
                FYG_up:         redtitle,
                VYS_down:       yellowtitle,
                VYS_up:         yellowtitle,
                INC_down:       greytitle,
                INC_up:         greytitle,
                IPS_RSW_down:   greentitle,
                IPS_RSW_up:     greentitle,
                RDP_down:       bluetitle,
                RDP_up:         bluetitle,
                SHC_down:       darkbluetitle,
                SHC_up:         darkbluetitle,
                SFC_down:       bluetitle,
                SFC_up:         bluetitle
                }
            
            def titles(daysofoperation):
                daysofoperation = ' - ' + daysofoperation
                def title(sheet,text):
                    font = linefont_dict.get(sheet)
                    text = text + daysofoperation
                    sheet.set_column(0,0,len(text)*1.43)
                    sheet.write('A1',text,font)
                title(BNH_down,         'Beenleigh - Down - Inbound')
                title(BNH_up,           'Beenleigh - Up - Outbound')
                title(CAB_GYN_down,     'Caboolture/Nambour/Gympie North - Down - Outbound')
                title(CAB_GYN_up,       'Caboolture/Nambour/Gympie North - Up - Inbound')
                title(CVN_down,         'Cleveland - Down - Inbound')
                title(CVN_up,           'Cleveland - Up - Outbound')
                title(DBN_down,         'Doomben - Down - Outbound')
                title(DBN_up,           'Doomben - Up - Inbound')
                title(FYG_down,         'Ferny Grove - Down - Outbound')
                title(FYG_up,           'Ferny Grove - Up - Inbound')
                title(VYS_down,         'Varsity Lakes/Airport - Down - Inbound')
                title(VYS_up,           'Varsity Lakes/Airport - Up - Outbound')
                title(INC_down,         'Inner City - Down - Outbound')
                title(INC_up,           'Inner City - Up - Inbound')
                title(IPS_RSW_down,     'Ipswich/Rosewood - Down - Inbound')
                title(IPS_RSW_up,       'Ipswich/Rosewood - Up - Outbound')
                title(RDP_down,         'Redcliffe Peninsula - Down - Outbound')
                title(RDP_up,           'Redcliffe Peninsula - Up - Inbound')
                title(SHC_down,         'Shorncliffe - Down - Outbound')
                title(SHC_up,           'Shorncliffe - Up - Inbound')
                title(SFC_down,         'Springfield - Down - Inbound')
                title(SFC_up,           'Springfield - Up - Outbound')
        
            if book == weekdayworkbook:
                if '120' in d_list and '4' in d_list:
                    write_workbook('Mon to Fri', ['120','64','32','16','8','4'])
        
            elif book == weekendworkbook:
                if '1' in d_list and '2' in d_list:
                    write_workbook('Sat to Sun', ['1','2'])
        
            elif book == monthuworkbook:
                if '120' in d_list:
                    write_workbook('Mon to Thu', ['120','64','32','16','8'])
        
            elif book == fridayworkbook:
                if '4' in d_list:
                    write_workbook('Friday', ['4'])
        
            elif book == saturdayworkbook:
                if '2' in d_list:
                    write_workbook('Saturday', ['2'])
        
            elif book == sundayworkbook:
                if '1' in d_list:
                    write_workbook('Sunday', ['1'])
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('Working Timetable','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_WTT(path)
        