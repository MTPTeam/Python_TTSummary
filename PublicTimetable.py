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
weekdaykey_dict2 = {'120':'M-Th', '4':'Fri', '2':'Sat', '1':'Sun'}


### Used for conversion between the name of each location and its abbreviated version
stationmaster = {
    'Fortitude Valley':'BRC',
    'Electric Train South': 'ETS',
    'Elec Train S': 'ETS',
    'Campbell St': 'CAM',
    'Exhibition ':'EXH',
    'Exhibition': 'EXH',
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

    'Comes From': 'CF',
    'Continues To': 'CT',
  }




### Used for 'Comes From' or 'Continues To' rows to avoid having stabling locations in the public timetable
### First or last station reassigned if a non-revenue location
### Code can be changed to iterate 'entries' over only revenue locations and skip this step but this method works fine too
city = 'RS'
stablingmaster = {
    'CAW':'CAB',
    'BNT':'BNH',
    'BNHS':'BNH',
    'IPSS':'IPS',
    'VYST':'VYS',
    'RKET':'RKE',
    'KPRS':'KPR',
    'ROBS':'ROB',
    'BQYS':'BQY',
    'EMHS':'EMH',
    'RDKS':'RDK',
    'WOBS':'WOB',
    'PETS':'PET',
    'MNS':city,
    'MES':city,
    'MWS':city,
    'YN':city,
    'YNA':city,
    'MNE':city,
    'ETF':city,
    'ETS':city,
    'ETB':city,
    'NBY':city,
    'MES':city,
    'CAM':city,
    'EXH':city,
    'BHI':city,
    'RS':city
    }







































def TTS_PTT(path, mypath = None):

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
        
        weekdayfilename_xlsx =  f'PublicTimetable-{filename}-Weekday.xlsx'
        weekendfilename_xlsx =  f'PublicTimetable-{filename}-Weekend.xlsx'
        monthufilename_xlsx =   f'PublicTimetable-{filename}-Mon-Thu.xlsx'
        fridayfilename_xlsx =   f'PublicTimetable-{filename}-Fri.xlsx'
        saturdayfilename_xlsx = f'PublicTimetable-{filename}-Saturday.xlsx'
        sundayfilename_xlsx =   f'PublicTimetable-{filename}-Sunday.xlsx'
        
        weekdayworkbook =  xlsxwriter.Workbook(weekdayfilename_xlsx)
        weekendworkbook =  xlsxwriter.Workbook(weekendfilename_xlsx)
        monthuworkbook =   xlsxwriter.Workbook(monthufilename_xlsx)
        fridayworkbook =   xlsxwriter.Workbook(fridayfilename_xlsx)
        saturdayworkbook = xlsxwriter.Workbook(saturdayfilename_xlsx)
        sundayworkbook =   xlsxwriter.Workbook(sundayfilename_xlsx)
        
        
        
        
        
        ### If in future, the MTP team may only require let's say a weekend timetable and a weekday timetable to be created,
        ###  this code will allow easy toggling of how many reports get generated for the user
        ### In the meantime, all useful combinations of reports will be created if the day_of_operation exists in the rsx.
        ###  That is, no blank timetable workbooks will be created
        Weekday = Weekend = MonThu = Friday = Saturday = Sunday = False
        Weekday = True
        Weekend = True
        MonThu = True
        Friday = True
        Saturday = True
        Sunday = True
        
        
        
        workbooks = []
        
        Weekday =  124 if Weekday  else False
        Weekend =  130 if Weekend  else False
        MonThu =   60  if MonThu   else False
        Friday =   64  if Friday   else False
        Saturday = 128 if Saturday else False
        Sunday =   2   if Sunday   else False
        
        workbooks_dict = {
            Weekday:  weekdayworkbook,
            Weekend:  weekendworkbook,
            MonThu:   monthuworkbook,
            Friday:   fridayworkbook,
            Saturday: saturdayworkbook,
            Sunday:   sundayworkbook,
            }
        
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
            'BNH':     (25, 2879),
            'HVW':     (24, 2745),
            'EDL':     (23, 2624),
            'BTI':     (22, 2518),
            'LGL':     (21, 2353),
            'KGT':     (20, 2208),
            'WOI':     (19, 2027),
            'TDP':     (18, 1951),
            'KRY':     (17, 2070), 
            'FTG':     (16, 1636),
            'RUC':     (15, 1556),
            'ATI':     (14, 1463),
            'SYK':     (13, 1368),
            'BQO':     (12, 1279),
            'CEP':     (11, 1600),
            'SLY':     (10, 1039),
            'RKE':     (9, 949),
            'MQK':     (8, 869),
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
            'GYN':     (35, 10613),
            'GMR':     (34, 9187),
            'WOO':     (33, 8811),
            'TRA':     (32, 8393),
            'COZ':     (31, 8163),
            'PMQ':     (30, 7673),
            'COO':     (29, 7223),
            'SSE':     (28, 6978),
            'EUM':     (27, 6893),
            'NHR':     (26, 4300),
            'YAN':     (25, 6503),
            'NBR':     (24, 7000), 
            'WOB':     (23, 5693),
            'PAL':     (22, 5483),
            'EUD':     (21, 5153),
            'MOH':     (20, 4763),
            'LSH':     (19, 4433),
            'BWH':     (18, 4163),
            'GSS':     (17, 3893),
            'BEB':     (16, 3413),
            'EMH':     (15, 3143),
            'CAB':     (14, 3218), 
            'MYE':     (13, 2636),
            'BPY':     (12, 2414),
            'NRB':     (11, 2653),
            'DKB':     (10, 1880),
            'PET':     (9,  1853),
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
            'CVN':     (21, 2875),
            'ORO':     (20, 2743),
            'WPT':     (19, 2592),
            'BDE':     (18, 2436),
            'TNS':     (17, 2285),
            'LOT':     (16, 2156),
            'MNY':     (15, 1814),
            'WNC':     (14, 1863),
            'WNM':     (13, 1781),
            'WYH':     (12, 1691),
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
            'VYS':     (12,  3996),
            'ROB':     (11,  3822),
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
            'BIT':     (-7, -1092),
            'BDT':     (-8, -1248)
            }
        
        
        vrt_2InnerCity = {
            'NTG':     (9,   1350), 
            'NND':     (8,   903),
            'TBU':     (7,   834),
            'EGJ':     (6,   714), 
            'WWI':     (5,   631),
            'AIN':     (4,   551),
            'BHI':     (3,   324 ),
            'BRC':     (2,   264 ),
            'BNC':     (1,   140 ),
            'RS':      (0,   0 ),
            'SBE':     (-1, -226 ),
            'SBA':     (-2, -316 ),
            'PKR':     (-3, -447 ),
            }
        
        
        vrt_2InnerNorth = {
            'NTG':     (9, 1350), 
            'NND':     (8, 903),
            'TBU':     (7, 834),
            'EGJ':     (6, 714), 
            'WWI':     (5, 631),
            'AIN':     (4, 551),
            'BHI':     (3, 324 ),
            'BRC':     (2, 264 ),
            'BNC':     (1, 140 ),
            'RS':      (0, 0 ),
            }
        
        
        vrt_2Rosewood = {
            'RSW':     (29, 4025),
            'YLE':     (28, 3422),
            'TAO':     (27, 3367),
            'WOQ':     (26, 3138),
            'KRA':     (25, 3380),
            'WUL':     (24, 2762),
            'THS':     (23, 2682),
            'IPS':     (22, 2940), 
            'EIP':     (21, 2436),
            'BOV':     (20, 2343),
            'BDX':     (19, 2244), 
            'EBV':     (18, 2117),
            'DIR':     (17, 2024),
            'RVV':     (16, 1918),
            'RDK':     (15, 1960),
            'GDQ':     (14, 1588),
            'GAI':     (13, 1464),
            'WAC':     (12, 1366),
            'DAR':     (11, 1475),
            'OXL':     (10, 993),
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
            'KPR':     (21, 2850),
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
            'SHC':     (17, 2290),
            'SGE':     (16, 2025),
            'DEG':     (15, 1586),
            'NBD':     (14, 1499),
            'BZL':     (13, 1422),
            'NUD':     (12, 1261),
            'BQY':     (11, 1182),
            'BHA':     (10, 1106),
            'NTG':     (9,  1350), 
            'NND':     (8,  903),
            'TBU':     (7,  834),
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
            'Caboolture - Gympie North':  vrt_2GympieNth,
            'Cleveland':                  vrt_2Cleveland,
            'Doomben':                    vrt_2Doomben,
            'Ferny Grove':                vrt_2FernyGrove,
            'Varsity Lakes - Airport':    vrt_2VarsityLs,               
            'Inner North':                vrt_2InnerNorth,
            'Inner City':                 vrt_2InnerCity,  
            'Ipswich - Rosewood':         vrt_2Rosewood,
            'Redcliffe':                  vrt_2KippaRing,
            'Shorncliffe':                vrt_2Shorncliffe,
            'Springfield':                vrt_2Springfield
            }
        
        
        uniquestations_dict = {
            'Beenleigh':                  ('BNHS','BNT','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKET','RKE','MQK','CPM','MBN','TNY','YLY','YRG','FFI','DUP'),
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN'),
            'Cleveland':                  ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                    ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':                ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Varsity Lakes - Airport':    ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT'),
            'Ipswich':                    ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
            'Rosewood':                   ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Ipswich - Rosewood':         ('MBN','TNY','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Inner City':                 ('BHI','BRC','BNC','RS'),
            'Inner North':                ('BHI','BRC','BNC','RS'), 
            'Redcliffe':                  ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Springfield':                ('RHD','SFD','SFC')
            }
        
        
        
        
        
        
        ### d_list      tracks the days present in the rsx
        ### newstations tracks if new locations have been added to the geography that haven't yet been added to stationmaster
        ###              will allow the code to continue without erroring, stationmaster should then be amended 
        d_list = []
        newstations = []
        revtrains = [x for x in root.iter('train') if 'Empty' not in x[1][0].attrib['trainTypeId']]
        for train in revtrains:
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
                
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
                if stationmaster.get(x):
                    y.append(stationmaster.get(x))
                elif 'arrive' in x:
                    y.append(stationmaster.get(x[:-7])+'arr')
                elif 'depart' in x:
                    y.append(stationmaster.get(x[:-7])+'dep')
                # elif 'platform' in x:
                #     y.append(stationmaster.get(x[:-9])+'pfm')
                else:
                    print(f'Undocumented station: {x}')
                    y.append(None)
            return list(zip(stationNames,y))
        
        
        
        
        
        
        
        
        
        ### These will be the row headers appearing in the worksheets - can be customised
        ### zip_stations will pair each location name up with a unique abbreviated station ID
        ###  these list of tuples will be fed into the write_workbook function to print the data for each station for each trip
        bnh_in  = zip_stations(['Beenleigh','Holmview','Eden\'s Landing','Bethania','Loganlea','Kingston','Woodridge','Trinder Park','Kuraby','Fruitgrove','Runcorn','Altandi','Sunnybank','Banoon','Coopers Plains','Salisbury','Rocklea','Moorooka','Yeerongpilly','Yeronga','Fairfield','Dutton Park','Park Road','South Bank','South Brisbane','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Continues To'])
        bnh_out = zip_stations(['Comes From','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','South Brisbane','South Bank','Park Road','Dutton Park','Fairfield','Yeronga','Yeerongpilly','Moorooka','Rocklea','Salisbury','Coopers Plains','Banoon','Sunnybank','Altandi','Runcorn','Fruitgrove','Kuraby','Trinder Park','Woodridge','Kingston','Loganlea','Bethania','Eden\'s Landing','Holmview','Beenleigh'])
        
        cab_in  = zip_stations(['Gympie North','Traveston','Cooran','Pomona','Cooroy','Eumundi','Yandina','Nambour','Woombye','Palmwoods','Eudlo','Mooloolah','Landsborough','Beerwah','Glasshouse Mountains','Beerburrum','Elimbah','Caboolture','Morayfield','Burpengary','Narangba','Dakabin','Petrie','Northgate','Eagle Junction','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','Continues To'])
        cab_out = zip_stations(['Comes From','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Eagle Junction','Northgate','Petrie','Dakabin','Narangba','Burpengary','Morayfield','Caboolture','Elimbah','Beerburrum','Glasshouse Mountains','Beerwah','Landsborough','Mooloolah','Eudlo','Palmwoods','Woombye','Nambour','Yandina','Eumundi','Cooroy','Pomona','Cooran','Traveston','Gympie North'])
        cab_out_wknd = zip_stations(['Comes From','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Albion','Wooloowin','Eagle Junction','Toombul','Nundah','Northgate','Virginia','Sunshine','Geebung','Zillmere','Carseldine','Bald Hills','Strathpine','Bray Park','Lawnton','Petrie','Dakabin','Narangba','Burpengary','Morayfield','Caboolture','Elimbah','Beerburrum','Glasshouse Mountains','Beerwah','Landsborough','Mooloolah','Eudlo','Palmwoods','Woombye','Nambour','Yandina','Eumundi','Cooroy','Pomona','Cooran','Traveston','Gympie North']) 
        
        cvn_in  = zip_stations(['Cleveland','Ormiston','Wellington Point','Birkdale','Thorneside','Lota','Manly','Wynnum Central','Wynnum','Wynnum North','Lindum','Hemmant','Murarrie','Cannon Hill','Morningside','Norman Park','Coorparoo','Buranda','Park Road','South Bank','South Brisbane','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Continues To'])
        cvn_out = zip_stations(['Comes From','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','South Brisbane','South Bank','Park Road','Buranda','Coorparoo','Norman Park','Morningside','Cannon Hill','Murarrie','Hemmant','Lindum','Wynnum North','Wynnum','Wynnum Central','Manly','Lota','Thorneside','Birkdale','Wellington Point','Ormiston','Cleveland'])
        
        dbn_in  = zip_stations(['Doomben','Ascot','Hendra','Clayfield','Eagle Junction','Wooloowin','Albion','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','South Brisbane','South Bank','Park Road','Continues To'])
        dbn_out = zip_stations(['Comes From','Park Road','South Bank','South Brisbane','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Albion','Wooloowin','Eagle Junction','Clayfield','Hendra','Ascot','Doomben'])
        
        fyg_in  = zip_stations(['Ferny Grove','Keperra','Grovely','Oxford Park','Mitchelton','Gaythorne','Enoggera','Alderley','Newmarket','Wilston','Windsor','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','South Brisbane','South Bank','Park Road','Continues To'])
        fyg_out = zip_stations(['Comes From','Park Road','South Bank','South Brisbane','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Windsor','Wilston','Newmarket','Alderley','Enoggera','Gaythorne','Mitchelton','Oxford Park','Grovely','Keperra','Ferny Grove'])
        
        vys_in  = zip_stations(['Varsity Lakes','Robina','Nerang','Helensvale','Coomera','Pimpama','Ormeau','Beenleigh','Loganlea','Altandi','Park Road','South Bank','South Brisbane','Roma Street arrive','Roma Street depart','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Albion','Wooloowin','Eagle Junction','International Airport','Domestic Airport','Continues To'])
        vys_out = zip_stations(['Domestic Airport','International Airport','Eagle Junction','Wooloowin','Albion','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street arrive','Roma Street depart','South Brisbane','South Bank','Park Road','Altandi','Loganlea','Beenleigh','Ormeau','Pimpama','Coomera','Helensvale','Nerang','Robina','Varsity Lakes'])
        
        ips_in  = zip_stations(['Rosewood','Thagoona','Walloon','Karrabin','Wulkuraka','Thomas Street','Ipswich arrive','Ipswich depart','East Ipswich','Booval','Bundamba','Ebbw Vale','Dinmore','Riverview','Redbank','Goodna','Gailes','Wacol','Darra','Oxley','Corinda','Sherwood','Graceville','Chelmer','Indooroopilly','Taringa','Toowong','Auchenflower','Milton','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Continues To']) 
        ips_out = zip_stations(['Comes From','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','Milton','Auchenflower','Toowong','Taringa','Indooroopilly','Chelmer','Graceville','Sherwood','Corinda','Oxley','Darra','Wacol','Gailes','Goodna','Redbank','Riverview','Dinmore','Ebbw Vale','Bundamba','Booval','East Ipswich','Ipswich arrive','Ipswich depart','Thomas Street','Wulkuraka','Karrabin','Walloon','Thagoona','Rosewood'])
        
        inn_in  = zip_stations(['Comes From','Northgate','Nundah','Toombul','Eagle Junction','Wooloowin','Albion','Bowen Hills arrive','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley depart','Central arrive','Central depart','Roma Street arrive','Continues To'])
        inn_out = zip_stations(['Comes From','Roma Street depart','Central arrive','Central depart','Fortitude Valley arrive','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills depart','Albion','Wooloowin','Eagle Junction','Toombul','Nundah','Northgate','Continues To'])
        
        inc_in  = zip_stations(['Comes From','Northgate','Nundah','Toombul','Eagle Junction','Wooloowin','Albion','Bowen Hills arrive','Bowen Hills depart','Fortitude Valley arrive','Fortitude Valley depart','Central arrive','Central depart','Roma Street arrive','Roma Street depart','South Brisbane','South Bank','Park Road','Continues To'])
        inc_out = zip_stations(['Comes From','Park Road','South Bank','South Brisbane','Roma Street arrive','Roma Street depart','Central arrive','Central depart','Fortitude Valley arrive','Fortitude Valley depart','Bowen Hills arrive','Bowen Hills depart','Albion','Wooloowin','Eagle Junction','Toombul','Nundah','Northgate','Continues To'])
        
        rdp_in  = zip_stations(['Kippa-Ring','Rothwell','Mango Hill East','Mango Hill','Murrumba Downs','Kallangur','Petrie','Lawnton','Bray Park','Strathpine','Bald Hills','Carseldine','Zillmere','Geebung','Sunshine','Virginia','Northgate','Eagle Junction','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','Milton','Continues To'])
        rdp_out = zip_stations(['Comes From','Milton','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Eagle Junction','Northgate','Virginia','Sunshine','Geebung','Zillmere','Carseldine','Bald Hills','Strathpine','Bray Park','Lawnton','Petrie','Kallangur','Murrumba Downs','Mango Hill','Mango Hill East','Rothwell','Kippa-Ring'])
        
        shc_in  = zip_stations(['Shorncliffe','Sandgate','Deagon','North Boondall','Boondall','Nudgee','Banyo','Bindha','Northgate','Nundah','Toombul','Eagle Junction','Wooloowin','Albion','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','South Brisbane','South Bank','Park Road','Continues To'])
        shc_out = zip_stations(['Comes From','Park Road','South Bank','South Brisbane','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Albion','Wooloowin','Eagle Junction','Toombul','Nundah','Northgate','Bindha','Banyo','Nudgee','Boondall','North Boondall','Deagon','Sandgate','Shorncliffe'])
        
        sfc_in  = zip_stations(['Springfield Central','Springfield','Richlands','Darra','Oxley','Corinda','Sherwood','Graceville','Chelmer','Indooroopilly','Taringa','Toowong','Auchenflower','Milton','Roma Street','Central arrive','Central depart','Fortitude Valley','Bowen Hills','Continues To'])
        sfc_out = zip_stations(['Comes From','Bowen Hills','Fortitude Valley','Central arrive','Central depart','Roma Street','Milton','Auchenflower','Toowong','Taringa','Indooroopilly','Chelmer','Graceville','Sherwood','Corinda','Oxley','Darra','Richlands','Springfield','Springfield Central'])
        
        
        zipped_stations_dict = {
            'Beenleigh':                  (bnh_in, bnh_out),
            'Caboolture - Gympie North':  (cab_in, cab_out),
            'Cleveland':                  (cvn_in, cvn_out),
            'Doomben':                    (dbn_in, dbn_out),
            'Ferny Grove':                (fyg_in, fyg_out),
            'Varsity Lakes - Airport':    (vys_in, vys_out),               
            'Inner North':                (inn_in, inn_out),
            'Inner City':                 (inc_in, inc_out),  
            'Ipswich - Rosewood':         (ips_in, ips_out),
            'Redcliffe':                  (rdp_in, rdp_out),
            'Shorncliffe':                (shc_in, shc_out),
            'Springfield':                (sfc_in, sfc_out)
            }
        
        
        
        
        def write_workbook(daycode, weekdaykeys):
            """ 
            The use of a master function to write a workbook with all other functions nested within
            Run twice, one for school days and one for weekends
            """
        
            def stoptime_info(entry_index): 
                """ Returns the arrival and departure times for the nth stop in a trip """
                
                x = entry_index
                departure = train[1][x].attrib['departure'] 
                
                stoptime = int(train[1][x].attrib.get('stopTime',0))
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
                    
                if timestring is None or timestring.isalpha() or ':' not in timestring:
                    pass
                elif timestring[0] == '0':
                    timestring = timestring[1:-3]
                else: timestring = timestring[:-3]
                return timestring
            
            def build_triplist(triplist, line, Outbound=False):
                """ 
                Fills an empty list with trips that match conditions for each line
                Info for each trip, including DoO and departure times, are contained in a dictionary - tripdict
                """
                seqcbd = 'BNC'
                cbd = 'IPS' if line == 'Ipswich - Rosewood' else seqcbd
                
                vrt = network_vrt_dict.get(line)
                line_stops = uniquestations_dict.get(line)
                stationlist  = zipped_stations_dict.get(line)[1 if Outbound else 0]
                last_listed_station = stationlist[-1][-1]
                
                entries = train[1].findall('entry')
                stationIDs = [x.attrib['stationID'] for x in entries]
                stops = {x.attrib['stationID'] for x in entries if x.attrib['type']=='stop'}
                
                condition = stops.intersection(line_stops) 
                
                if line == 'Inner North':
                    condition = condition and stops.intersection(['NTG','EGJ'])
                    
                elif line == 'Shorncliffe':
                    condition = condition or ('NTG' in [oID,dID] and any([vrt.get(x) for x in stationIDs if x != 'NTG']))
        
                
                
                if condition:
                    
                    for n,entry in enumerate(train[1].iter('entry')):
                        
                        if entry.attrib['stationID'] in vrt:
                            firstonline = entry.attrib['stationID']                  
                            first_sIDinVRT = n
                            break
                    
                    for n,entry in enumerate(train[1].iter('entry')):
                        if n <= first_sIDinVRT:
                            secondonline = firstonline
                        else:
                            if entry.attrib['stationID'] in vrt:
                                secondonline = entry.attrib['stationID']
                                break
                        
                    a = int(vrt.get(firstonline)[0])    
                    b = int(vrt.get(secondonline)[0])
                    increasing = b > a
                    decreasing = b < a
                    decreasing = decreasing or b == a
                
                    if Outbound:
                        condition = condition and increasing
                    else:
                        condition = condition and decreasing 
                
                
                if condition: 
                    tripdict = {}
                    
                    tripdict['Train ID'] = tn
                    
                    #!!! vrt introduce rs/rst sorting
                    if cbd not in stationIDs:
                        # print(f'{tn} does not run to either IPS or {seqcbd}, sort trip in the schedule using virtual run times to Central')
                        for entry in train[1].iter('entry'):
                            
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
                        
                    
                    for n,x in enumerate(entries):
                        
                        stationName = x.attrib['stationName']
                        stationID   = x.attrib['stationID']
                        stationType = x.attrib['type']
                        dwell       = int(x.attrib['stopTime']) if x.get('stopTime') else 0
                        
                        (arrival, departure) = stoptime_info(n)
                        
                        
                        
                        if stationType == 'pass':
                            tripdict[stationID] = 'exp'
                        elif stationID == last_listed_station:
                            tripdict[stationID] = arrival
                        elif stationID in ['MOH','EUD','WOB','PAL'] and dwell >= 360:
                            tripdict[stationID] = arrival
                        else:
                            tripdict[stationID] = departure
        
                        if stationName == 'Central':
                            tripdict['BNCarr'] = arrival
                            tripdict['BNCdep'] = departure
                            if cbd == 'BNC':
                                tripdict['VirtualCBD'] = departure
                            
                        if stationName == 'Roma Street':
                            tripdict['RSarr'] = arrival
                            tripdict['RSdep'] = departure
        
                            
                        if stationName == 'Brunswick Street':
                            tripdict['BRCarr'] = arrival
                            tripdict['BRCdep'] = departure
                            
                        if stationName == 'Ipswich':
                            tripdict['IPSarr'] = arrival
                            tripdict['IPSdep'] = departure
                            if cbd == 'IPS':
                                tripdict['VirtualCBD'] = departure
                            
                        if stationName == 'Bowen Hills':
                            tripdict['BHIarr'] = arrival
                            tripdict['BHIdep'] = departure
                            
                    tripdict['AM/PM'] = 'am' if origin['departure'] < '12:00:00' or origin['departure'] > '24:00:00' else 'pm'
                    tripdict['DoO'] = weekdaykey_dict2.get(WeekdayKey)
                        
                    
                    # tripdict['DoO'] = 'M-Th' if WeekdayKey=='120' else 'Fri'
                    tripdict['Comes From'] = stablingmaster.get(oID,oID)
                    tripdict['Continues2'] = stablingmaster.get(dID,dID)
                    
                    
        
                    triplist.append(tripdict)
                
        
            def refine_triplist(triplist, stations):
                """ 
                Given a list for a line in a particular direction,
                Sort the list chronologically and merge trips that run on multiple days
                """
        
                SORT_ORDER = {'M-Th': 0, 'Fri': 1, 'Sat': 2, 'Sun':3}
                triplist.sort(key=lambda x: SORT_ORDER[x['DoO']])
                triplist.sort(key=lambda x: x['VirtualCBD'])
        
                DELIMITER = '|'
                refinedtriplist = []
                
                for tripdict in triplist:
                    
    
                    if tripdict == triplist[0]:
                        refinedtriplist.append(tripdict)
                        
                    else:    
                        
                        ### Initialise bool variable to keep track of whether the current train is a duplicate
                        same_train = False
                        
                        ### Check n previous trips
                        n = 3
                        
                        end_idx = len(refinedtriplist) - 1
                        
                        for i,rtd in enumerate(refinedtriplist):
                            
                            if end_idx - i <= n:
                                same_train_list = []
                                for s in stations:
                                    same_station = timetrim(tripdict.get(s)) == timetrim(rtd.get(s))
                                    same_train_list.append(same_station)
                                same_train_list.append( tripdict.get('Comes From') == rtd.get('Comes From') )
                                same_train_list.append( tripdict.get('Continues2') == rtd.get('Continues2') )
                                
                                same_train = all(same_train_list)
                                if same_train and rtd['DoO'] != tripdict['DoO']:
                                    idx = i
                                    break
                            
                            
                        if same_train:
                            refinedtriplist[idx]['DoO'] = 'M-F' if book == weekdayworkbook else 'WE'
                            if refinedtriplist[idx]['Train ID'] != tripdict['Train ID']:
                                refinedtriplist[idx]['Train ID'] = DELIMITER.join( [refinedtriplist[idx]['Train ID'], tripdict['Train ID']] )
                        else:
                            refinedtriplist.append(tripdict)
                
                return refinedtriplist
        
        
        
            def write_timetable(sheet, triplist, stations, line):
                """ Write the data to the worksheet, including train ID, DoO and departure times for each station """
                
                (title, font1, boldfont1, font2, boldfont2, mainstations) = lineinfo_dict.get(line)
                stations_long = list(zip(*stations))[0]
                stations_abr  = list(zip(*stations))[1]
                triplist = refine_triplist(triplist, stations_abr)
                
                sheet.write_column('A2', ['Days of Operation','Train ID','Station'], boldleft)
                sheet.freeze_panes(5, 1)
                for i in range(1,len(stations)+5):
                    sheet.set_row(i,14.5)
        
                
                # Write the station names and bold key stations
                sheet.write_column('A6',stations_long,left)
                for s in mainstations:
                    ind = stations_abr.index(s)
                    row = 5 + ind
                    col = 0
                    st  = stations_long[ind]
                    sheet.write(row,col,st,boldleft)
        
                for (i,x) in enumerate(triplist,1):
                     
                    vals = []
                    laststationdep, firststationarr = False, False
                    # firststationarr = False
                    for idx,sID in enumerate(stations_abr):
                        # sID = station[-1]
                        
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
                        
                    if len(weekdaykeys) == 1:
                        font  = default
                        bfont = bold
                    else:
                        if x.get('DoO') in ('M-Th','Sun'):
                            font  = font2
                            bfont = boldfont2
                            
                        elif x.get('DoO') in ('Fri','Sat'):
                            font  = font1
                            bfont = boldfont1
                            
                        else:
                            font  = default
                            bfont = bold
                        
                    smallfont = smallfontdict.get(font)
                    DoO = x.get('DoO')
                    tID = x.get('Train ID')
                    ToD = x.get('AM/PM')
                    
                    sheet.write(0,i,'',title)
                    sheet.write(1,i,DoO,font)
                    if len(weekdaykeys) == 1:
                        sheet.write(2,i,tID,font)
                        sheet.write(3,i,ToD,font)
                    else:
                        sheet.write(2,i,tID,smallfont)
                        sheet.write(3,i,ToD,smallfont)
                    sheet.write(4,i,'',font)
                    
                    startrow = 5
                    for ii,v in enumerate(vals):
                         
                        if stations_abr[ii] in mainstations:
                            if v == 'exp':
                                sheet.write(ii+startrow,i,v,expressbold)
                            else:
                                sheet.write(ii+startrow,i,v,bfont)
                                
                        elif v != 'exp':
                            sheet.write(ii+startrow,i,v,font)
                            
                        else:
                            sheet.write(ii+startrow,i,v,express)       
                    
                    getCF = x.get('Comes From')
                    getCT = x.get('Continues2')
                    # vline = network_vrt_dict.get(line)
                    start  = getCF if getCF not in stations_abr else None
                    finish = getCT if getCT not in stations_abr else None
                    if 'Comes From' in stations_long:
                         cf = stations_long.index('Comes From') + 5
                         sheet.write(cf,i,start,font)               
                    if 'Continues To' in stations_long:
                         ct = stations_long.index('Continues To') + 5
                         sheet.write(ct,i,finish,font)
                         
                    sheet.set_column(i,i,6.3)
                        
            
            
            
            
            
            
            
            ### Initialise two lists for each line - one inbound, one outbound
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
            list23 = []
            list24 = []
            
            # Generate a iterable of all revenue services 
            revenue = (x for x in root.iter('train') if x[0][0][0].attrib['weekdayKey'] in weekdaykeys and 'Empty' not in x[1][0].attrib['trainTypeId'])
            for train in revenue:
                tn = train.attrib['number']
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                entries = [x for x in train.iter('entry')]
                origin = entries[0].attrib
                destin = entries[-1].attrib
                oID = origin['stationID']
                dID = destin['stationID']
                
                
                
                build_triplist( list1,  'Beenleigh'                                )
                build_triplist( list2,  'Beenleigh',                 Outbound=True )
                
                build_triplist( list3,  'Caboolture - Gympie North'                ) 
                build_triplist( list4,  'Caboolture - Gympie North', Outbound=True )
                
                build_triplist( list5,  'Cleveland'                                )
                build_triplist( list6,  'Cleveland',                 Outbound=True )
                
                build_triplist( list7,  'Doomben'                                  )
                build_triplist( list8,  'Doomben',                   Outbound=True )
                
                build_triplist( list9,  'Ferny Grove'                              )
                build_triplist( list10, 'Ferny Grove',               Outbound=True )
                
                build_triplist( list11, 'Varsity Lakes - Airport'                  )
                build_triplist( list12, 'Varsity Lakes - Airport',   Outbound=True )
                
                build_triplist( list15, 'Inner North'                              )
                build_triplist( list16, 'Inner North',               Outbound=True )
                
                build_triplist( list17, 'Inner City'                               )
                build_triplist( list18, 'Inner City',                Outbound=True )
                
                build_triplist( list13, 'Ipswich - Rosewood'                       )
                build_triplist( list14, 'Ipswich - Rosewood',        Outbound=True )
                
                build_triplist( list19, 'Redcliffe'                                )
                build_triplist( list20, 'Redcliffe',                 Outbound=True )
                
                build_triplist( list21, 'Shorncliffe'                              )
                build_triplist( list22, 'Shorncliffe',               Outbound=True )
                
                build_triplist( list23, 'Springfield'                              )
                build_triplist( list24, 'Springfield',               Outbound=True )
        
            
            write_timetable( BNH_in,      list1,  bnh_in,   'Beenleigh' )  
            write_timetable( BNH_out,     list2,  bnh_out,  'Beenleigh' )     
            
            cab_stops = cab_out if book == weekdayworkbook else cab_out_wknd
            write_timetable( CAB_GYN_in,  list3,  cab_in,   'Caboolture - Gympie North' ) 
            write_timetable( CAB_GYN_out, list4,  cab_stops,'Caboolture - Gympie North' )
        
            write_timetable( CVN_in,      list5,  cvn_in,   'Cleveland' )   
            write_timetable( CVN_out,     list6,  cvn_out,  'Cleveland' ) 
         
            write_timetable( DBN_in,      list7,  dbn_in,   'Doomben' )   
            write_timetable( DBN_out,     list8,  dbn_out,  'Doomben' )
        
            write_timetable( FYG_in,      list9,  fyg_in,   'Ferny Grove' )   
            write_timetable( FYG_out,     list10, fyg_out,  'Ferny Grove' ) 
        
            write_timetable( VYS_in,      list11, vys_in,   'Varsity Lakes - Airport' )   
            write_timetable( VYS_out,     list12, vys_out,  'Varsity Lakes - Airport' )
            
            write_timetable( INN_in,      list15, inn_in,   'Inner North' )   
            write_timetable( INN_out,     list16, inn_out,  'Inner North' ) 
        
            write_timetable( INC_in,      list17, inc_in,   'Inner City' )   
            write_timetable( INC_out,     list18, inc_out,  'Inner City' ) 
            
            write_timetable( IPS_RSW_in,  list13, ips_in,   'Ipswich - Rosewood' )   
            write_timetable( IPS_RSW_out, list14, ips_out,  'Ipswich - Rosewood' )       
        
            write_timetable( RDP_in,      list19, rdp_in,   'Redcliffe' )   
            write_timetable( RDP_out,     list20, rdp_out,  'Redcliffe' ) 
        
            write_timetable( SHC_in,      list21, shc_in,   'Shorncliffe' )   
            write_timetable( SHC_out,     list22, shc_out,  'Shorncliffe' ) 
        
            write_timetable( SFC_in,      list23, sfc_in,   'Springfield' )   
            write_timetable( SFC_out,     list24, sfc_out,  'Springfield' ) 
            
            titles(daycode)
            
            # IPS_RSW_in.activate()
            # CAB_GYN_in.activate()
            # SHC_in.activate()
            # INC_in.activate()
            BNH_in.activate() 
            
            print(f'\nAll trains with weekdayKey {" or ".join(weekdaykeys)} have been processed')
            
            dayofop_dict = {
                weekdayworkbook:  (weekdayfilename_xlsx, 'weekday'),
                weekendworkbook:  (weekendfilename_xlsx, 'weekend'),
                monthuworkbook:   (monthufilename_xlsx,  'Mon-Thurs'),
                fridayworkbook:   (fridayfilename_xlsx,  'Friday'),
                saturdayworkbook: (saturdayfilename_xlsx,'Saturday'),
                sundayworkbook:   (sundayfilename_xlsx,  'Sunday')
                }
            
            filename_xlsx,dayname = dayofop_dict.get(book)
            
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
            
            # filename_xlsx,dayname = dayofop_dict.get(book)
            
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
            BNH_in        = book.add_worksheet('BNH-In')
            BNH_out       = book.add_worksheet('BNH-Out')
            CAB_GYN_in    = book.add_worksheet('CAB+GYN-In')
            CAB_GYN_out   = book.add_worksheet('CAB+GYN-Out')
            CVN_in        = book.add_worksheet('CVN-In')
            CVN_out       = book.add_worksheet('CVN_out')
            DBN_in        = book.add_worksheet('DBN-In')
            DBN_out       = book.add_worksheet('DBN-Out')
            FYG_in        = book.add_worksheet('FYG-In')
            FYG_out       = book.add_worksheet('FYG-Out')
            VYS_in        = book.add_worksheet('VYS+BDT-In')
            VYS_out       = book.add_worksheet('VYS+BDT-Out')
            INN_in        = book.add_worksheet('INN-In')
            INN_out       = book.add_worksheet('INN-Out')
            INC_in        = book.add_worksheet('INC-In')
            INC_out       = book.add_worksheet('INC-Out')
            IPS_RSW_in    = book.add_worksheet('IPS+RSW-In')
            IPS_RSW_out   = book.add_worksheet('IPS+RSW-Out')
            RDP_in        = book.add_worksheet('RDP-In')
            RDP_out       = book.add_worksheet('RDP-Out')
            SHC_in        = book.add_worksheet('SHC-In')
            SHC_out       = book.add_worksheet('SHC-Out')
            SFC_in        = book.add_worksheet('SFC-In')
            SFC_out       = book.add_worksheet('SFC-Out')
            
            book.formats[0].set_align('center')
            book.formats[0].set_font_size(9)
            
            
            
            #Workbook formats
            default             = book.add_format({'align':'center','font_size':9})
            left                = book.add_format({'align':'left','font_size':9})
            bold                = book.add_format({'align':'center','font_size':9,'bold':True})
            boldleft            = book.add_format({'align':'left','font_size':9,'bold':True})
            six                 = book.add_format({'align':'center','font_size':6})
            express             = book.add_format({'align':'center','font_size':9,             'bg_color':'#FFEBBE'})
            expressbold         = book.add_format({'align':'center','font_size':9,'bold':True, 'bg_color':'#FFEBBE'})
            
            
            
            #Worksheet title formats
            redtitle            = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#D10019'})
            greentitle          = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#007D45'})
            darkbluetitle       = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#004170'})
            purpletitle         = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#705098'})
            yellowtitle         = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#FEC938'})
            greytitle           = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#797A7C'})
            bluetitle           = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#0075B7'})
            
        
            thursdayred         = book.add_format({'align':'center','font_size':9, 'bg_color':'#FFCCD2'}) 
            thursdayredsmall    = book.add_format({'align':'center','font_size':6, 'bg_color':'#FFCCD2'}) 
            thursdayredbold     = book.add_format({'align':'center','font_size':9, 'bg_color':'#FFCCD2','bold':True}) 
            fridayred           = book.add_format({'align':'center','font_size':9, 'bg_color':'#FF7F8E'}) 
            fridayredsmall      = book.add_format({'align':'center','font_size':6, 'bg_color':'#FF7F8E'}) 
            fridayredbold       = book.add_format({'align':'center','font_size':9, 'bg_color':'#FF7F8E','bold':True}) 
        
            thursdaygreen       = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCFFE8'})
            thursdaygreensmall  = book.add_format({'align':'center','font_size':6, 'bg_color':'#CCFFE8'})
            thursdaygreenbold   = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCFFE8','bold':True})
            fridaygreen         = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FFFC5'})
            fridaygreensmall    = book.add_format({'align':'center','font_size':6, 'bg_color':'#7FFFC5'})
            fridaygreenbold     = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FFFC5','bold':True})
            
            thursdayblue        = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCE9FF'})
            thursdaybluesmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#CCE9FF'})
            thursdaybluebold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCE9FF','bold':True})
            fridayblue          = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FC9FF'})
            fridaybluesmall     = book.add_format({'align':'center','font_size':6, 'bg_color':'#7FC9FF'})
            fridaybluebold      = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FC9FF','bold':True})
            
            thursdaypurple      = book.add_format({'align':'center','font_size':9, 'bg_color':'#E4DDED'})
            thursdaypurplesmall = book.add_format({'align':'center','font_size':6, 'bg_color':'#E4DDED'})
            thursdaypurplebold  = book.add_format({'align':'center','font_size':9, 'bg_color':'#E4DDED','bold':True})
            fridaypurple        = book.add_format({'align':'center','font_size':9, 'bg_color':'#BDABD3'})
            fridaypurplesmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#BDABD3'})
            fridaypurplebold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#BDABD3','bold':True})
            
            thursdayyellow      = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEDC80'})
            thursdayyellowsmall = book.add_format({'align':'center','font_size':6, 'bg_color':'#FEDC80'})
            thursdayyellowbold  = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEDC80','bold':True})
            fridayyellow        = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEEDBE'})
            fridayyellowsmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#FEEDBE'})
            fridayyellowbold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEEDBE','bold':True})
            
            thursdaygrey        = book.add_format({'align':'center','font_size':9, 'bg_color':'#E5E5E5'})
            thursdaygreysmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#E5E5E5'})
            thursdaygreybold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#E5E5E5','bold':True})
            fridaygrey          = book.add_format({'align':'center','font_size':9, 'bg_color':'#BEBEC0'})
            fridaygreysmall     = book.add_format({'align':'center','font_size':6, 'bg_color':'#BEBEC0'})
            fridaygreybold      = book.add_format({'align':'center','font_size':9, 'bg_color':'#BEBEC0','bold':True})
            
            smallfontdict = {
                default         :six,
                thursdayred     :thursdayredsmall,
                fridayred       :fridayredsmall,
                thursdayblue    :thursdaybluesmall,
                fridayblue      :fridaybluesmall,
                thursdaygreen   :thursdaygreensmall,
                fridaygreen     :fridaygreensmall,   
                thursdaypurple  :thursdaypurplesmall,
                fridaypurple    :fridaypurplesmall,
                thursdayyellow  :thursdayyellowsmall,
                fridayyellow    :fridayyellowsmall,   
                thursdaygrey    :thursdaygreysmall,
                fridaygrey      :fridaygreysmall,   
                }
        
            bnh_capitalstops = ['BNH','PKR','BNCarr','BNCdep']  
            cab_capitalstops = ['GYN','NBR','CAB','PET', 'NTG', 'EGJ','BNCarr','BNCdep']  
            cvn_capitalstops = ['MNY','PKR','BNCarr','BNCdep']
            dbn_capitalstops = ['EGJ','BNCarr','BNCdep','PKR']
            fyg_capitalstops = ['PKR','BNCarr','BNCdep']
            vys_capitalstops = ['BNH','PKR','BNCarr','BNCdep','EGJ']
            ips_capitalstops = ['BNCarr','BNCdep','MTZ','IDP','DAR','IPSarr','IPSdep'] 
            inn_capitalstops = ['NTG','BNCarr','BNCdep']
            inc_capitalstops = ['NTG','BNCarr','BNCdep']
            rdp_capitalstops = ['PET','NTG','BNCarr','BNCdep']
            shc_capitalstops = ['PKR','BNCarr','BNCdep','NTG']
            sfc_capitalstops = ['DAR','BNCarr','BNCdep']
            
            lineinfo_dict = {
                'Beenleigh':                  (redtitle,      thursdayred, thursdayredbold, fridayred, fridayredbold,             bnh_capitalstops),
                'Caboolture - Gympie North':  (greentitle,    thursdaygreen, thursdaygreenbold, fridaygreen, fridaygreenbold,     cab_capitalstops),
                'Cleveland':                  (darkbluetitle, thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         cvn_capitalstops),
                'Doomben':                    (purpletitle,   thursdaypurple, thursdaypurplebold, fridaypurple, fridaypurplebold, dbn_capitalstops),
                'Ferny Grove':                (redtitle,      thursdayred, thursdayredbold, fridayred, fridayredbold,             fyg_capitalstops),
                'Varsity Lakes - Airport':    (yellowtitle,   thursdayyellow, thursdayyellowbold, fridayyellow, fridayyellowbold, vys_capitalstops),
                'Inner North':                (greytitle,     thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold,         inn_capitalstops),
                'Inner City':                 (greytitle,     thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold,         inc_capitalstops),
                'Ipswich - Rosewood':         (greentitle,    thursdaygreen, thursdaygreenbold, fridaygreen, fridaygreenbold,     ips_capitalstops),
                'Redcliffe':                  (bluetitle,     thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         rdp_capitalstops),
                'Shorncliffe':                (darkbluetitle, thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         shc_capitalstops),
                'Springfield':                (bluetitle,     thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         sfc_capitalstops)
                    }
            
            linefont_dict = {
                BNH_in:       redtitle,
                BNH_out:      redtitle,
                CAB_GYN_in:   greentitle,
                CAB_GYN_out:  greentitle,
                CVN_in:       darkbluetitle,
                CVN_out:      darkbluetitle,
                DBN_in:       purpletitle,
                DBN_out:      purpletitle,
                FYG_in:       redtitle,
                FYG_out:      redtitle,
                VYS_in:       yellowtitle,
                VYS_out:      yellowtitle,
                INN_in:       greytitle,
                INN_out:      greytitle,
                INC_in:       greytitle,
                INC_out:      greytitle,
                IPS_RSW_in:   greentitle,
                IPS_RSW_out:  greentitle,
                RDP_in:       bluetitle,
                RDP_out:      bluetitle,
                SHC_in:       darkbluetitle,
                SHC_out:      darkbluetitle,
                SFC_in:       bluetitle,
                SFC_out:      bluetitle,
                }
                
            def titles(daysofoperation):
                daysofoperation = ' - ' + daysofoperation
                def title(sheet,text):
                    font = linefont_dict.get(sheet)
                    text = text + daysofoperation
                    sheet.set_column(0,0,len(text)*1.43)
                    sheet.write('A1',text,font)
                title(BNH_in,       'Beenleigh to City - Inbound')
                title(BNH_out,      'City to Beenleigh - Outbound')
                title(CAB_GYN_in,   'Caboolture/Nambour/Gympie North to City - Inbound')
                title(CAB_GYN_out,  'City to Caboolture/Nambour/Gympie North - Outbound')
                title(CVN_in,       'Cleveland to City - Inbound')
                title(CVN_out,      'City to Cleveland - Outbound')
                title(DBN_in,       'Doomben to City - Inbound')
                title(DBN_out,      'City to Doomben - Outbound')
                title(FYG_in,       'Ferny Grove to City - Inbound')
                title(FYG_out,      'City to Ferny Grove - Outbound')
                title(VYS_in,       'Varsity Lakes/Airport to City - Inbound')
                title(VYS_out,      'City to Varsity Lakes/Airport - Outbound')
                title(INN_in,       'Inner North to City - Inbound')
                title(INN_out,      'City to Inner North - Outbound')
                title(INC_in,       'Inner City to City - Inbound')
                title(INC_out,      'City to Inner City - Outbound')
                title(IPS_RSW_in,   'Ipswich/Rosewood to City - Inbound')
                title(IPS_RSW_out,  'City to Ipswich/Rosewood - Outbound')
                title(RDP_in,       'Redcliffe Peninsula to City - Inbound')
                title(RDP_out,      'City to Redcliffe Peninsula - Outbound')
                title(SHC_in,       'Shorncliffe to City - Inbound')
                title(SHC_out,      'City to Shorncliffe - Outbound')
                title(SFC_in,       'Springfield to City - Inbound')
                title(SFC_out,      'City to Springfield - Outbound')
        
            if book == weekdayworkbook:
                if '120' in d_list and '4' in d_list:
                    write_workbook('Mon to Fri', ['120','4']) 
                    
            elif book == weekendworkbook:
                if '1' in d_list and '2' in d_list:
                    write_workbook('Sat to Sun', ['1','2']) 
                    
            elif book == monthuworkbook:
                if '120' in d_list:
                    write_workbook('Mon to Thu', ['120'])
                    
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
            messagebox.showinfo('Public Timetable','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_PTT(path)