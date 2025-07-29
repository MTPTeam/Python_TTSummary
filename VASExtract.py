import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import xlsxwriter
import time
import os
import sys
import shutil

from tkinter import Tk  
from tkinter.filedialog import askopenfilename
 
import traceback
import logging


OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True




weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
vas_daycode_dict = {'4':'M-F', '2':'SAT', '1':'SUN'}


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

    
    ]



RSCode_dict = {
    ('All Stations','Roma Street','Bowen Hills'):'1014',
    ('All Stations','Roma Street','Shorncliffe'):'1050',
    ('All Stations','Roma Street','Doomben'):'1055',
    ('All Stations','Roma Street','Caboolture'):'1060',
    ('NTG-PET','Roma Street','Caboolture'):'1061',
    ('All Stations','Roma Street','Northgate'):'1064',
    ('All Stations','Roma Street','Ferny Grove'):'1080',
    ('All Stations','Roma Street','Domestic'):'1090',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Roma Street','Caboolture'):'1161',
    ('All Stations','Roma Street','Petrie'):'1166',
    ('BHI-EGJ,EGJ-NTG','Roma Street','Kippa-Ring'):'1167',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Roma Street','Nambour'):'1173',
    ('BHI-NTG,NTG-PET,PET-CAB','Roma Street','Nambour'):'1174',
    ('BHI-NTG,NTG-PET,PET-CAB','Roma Street','Gympie North'):'1176',
    ('All Stations','Bowen Hills','Roma Street'):'1410',
    ('All Stations','Bowen Hills','Beenleigh'):'1420',
    ('All Stations','Bowen Hills','Kuraby'):'1422',
    ('PKR-ATI,ATI-LGL,LGL-BNH','Bowen Hills','Varsity Lakes'):'1428',
    ('All Stations','Bowen Hills','Ipswich'):'1430',
    ('All Stations','Bowen Hills','Springfield Central'):'1435',
    ('All Stations','Bowen Hills','Rosewood'):'1436',
    ('MTZ-IDP,IDP-DAR','Bowen Hills','Ipswich'):'1437',
    ('All Stations','Bowen Hills','Cleveland'):'1440',
    ('MGS-MNY','Bowen Hills','Cleveland'):'1442',
    ('PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Bowen Hills','Varsity Lakes'):'1526',
    ('MTZ-IDP,IDP-DAR','Bowen Hills','Rosewood'):'1536',
    ('All Stations','Bowen Hills','Park Road'):'1542',
    ('All Stations','Beenleigh','Bowen Hills'):'2014',
    ('All Stations','Beenleigh','Ferny Grove'):'2080',
    ('KRY-SLY','Beenleigh','Ferny Grove'):'2082',
    ('All Stations','Kuraby','Bowen Hills'):'2214',
    ('All Stations','Kuraby','Ferny Grove'):'2280',
    ('All Stations','Coopers Plains','Bowen Hills'):'2314',
    ('All Stations','Coopers Plains','Ferny Grove'):'2380',
    ('BNH-LGL,LGL-ATI,ATI-PKR','Varsity Lakes','Bowen Hills'):'2517',
    ('BNH-LGL,LGL-ATI,ATI-PKR','Varsity Lakes','Doomben'):'2556',
    ('All Stations','Rocklea','Domestic'):'2590',
    ('BNH-LGL,LGL-ATI,ATI-PKR','Varsity Lakes','Domestic'):'2598',
    ('BNH-LGL,LGL-WOI,WOI-ATI,ATI-CEP,CEP-YRG,YRG-PKR','Varsity Lakes','Bowen Hills'):'2615',
    ('BNH-LGL,LGL-WOI,WOI-ATI,ATI-CEP,CEP-YRG,YRG-PKR','Varsity Lakes','Doomben'):'2650',
    ('BNH-LGL,LGL-WOI,WOI-ATI,ATI-CEP,CEP-YRG,YRG-PKR,BHI-EGJ,EGJ-NTG','Varsity Lakes','Northgate'):'2664',
    ('BNH-LGL,LGL-WOI,WOI-ATI,ATI-CEP,CEP-YRG,YRG-PKR','Varsity Lakes','Domestic'):'2692',
    ('All Stations','Ipswich','Bowen Hills'):'3014',
    ('All Stations','Ipswich','Rosewood'):'3036',
    ('All Stations','Ipswich','Shorncliffe'):'3050',
    ('NTG-PET','Ipswich','Caboolture'):'3063',
    ('DAR-IDP,IDP-MTZ','Rosewood','Domestic'):'3065',
    ('BHI-EGJ,EGJ-NTG','Wacol','Kippa-Ring'):'3156',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Ipswich','Caboolture'):'3160',
    ('DAR-IDP,IDP-MTZ,BHI-EGJ,EGJ-NTG,NTG-PET','Ipswich','Caboolture'):'3161',
    ('BHI-EGJ,EGJ-NTG','Ipswich','Kippa-Ring'):'3167',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Ipswich','Nambour'):'3170',
    ('DAR-IDP,IDP-MTZ,BHI-EGJ,EGJ-NTG,NTG-PET','Ipswich','Nambour'):'3171',
    ('All Stations','Ipswich','Ferny Grove'):'3214',
    ('DAR-IDP,IDP-MTZ,BHI-EGJ,EGJ-NTG','Ipswich','Kippa-Ring'):'3461',
    ('All Stations','Springfield Central','Bowen Hills'):'3514',
    ('NTG-PET','Springfield Central','Nambour'):'3561',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Springfield Central','Caboolture'):'3562',
    ('NTG-PET','Springfield Central','Caboolture'):'3563',
    ('DAR-IDP,IDP-MTZ','Ipswich','Doomben'):'3565',
    ('BHI-EGJ,EGJ-NTG','Springfield Central','Kippa-Ring'):'3567',
    ('NTG-PET','Ipswich','Nambour'):'3572',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Springfield Central','Nambour'):'3573',
    ('All Stations','Rosewood','Bowen Hills'):'3614',
    ('DAR-IDP,IDP-MTZ','Rosewood','Bowen Hills'):'3615',
    ('All Stations','Rosewood','Ipswich'):'3630',
    ('All Stations','Springfield Central','Doomben'):'3660',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Rosewood','Caboolture'):'3663',
    ('BHI-EGJ,EGJ-NTG','Rosewood','Kippa-Ring'):'3667',
    ('BHI-EGJ,EGJ-NTG,NTG-PET','Rosewood','Nambour'):'3671',
    ('DAR-IDP,IDP-MTZ','Ipswich','Bowen Hills'):'3714',
    ('All Stations','Cleveland','Bowen Hills'):'4014',
    ('MNY-MGS','Cleveland','Bowen Hills'):'4017',
    ('All Stations','Cleveland','Shorncliffe'):'4050',
    ('All Stations','Cleveland','Northgate'):'4064',
    ('All Stations','Cleveland','Ferny Grove'):'4080',
    ('MNY-MGS','Cleveland','Doomben'):'4155',
    ('All Stations','Park Road','Bowen Hills'):'4214',
    ('All Stations','Park Road','Shorncliffe'):'4250',
    ('All Stations','Park Road','Doomben'):'4255',
    ('All Stations','Park Road','Northgate'):'4264',
    ('All Stations','Park Road','Ferny Grove'):'4280',
    ('All Stations','Park Road','Domestic'):'4290',
    ('All Stations','Manly','Shorncliffe'):'4550',
    ('All Stations','Manly','Doomben'):'4555',
    ('All Stations','Cannon Hill','Bowen Hills'):'4614',
    ('All Stations','Cannon Hill','Shorncliffe'):'4650',
    ('All Stations','Cannon Hill','Northgate'):'4664',
    ('BHI-EGJ,EGJ-NTG','Cannon Hill','Kippa-Ring'):'4980',
    ('All Stations','Shorncliffe','Roma Street'):'5010',
    ('PKR-ATI,ATI-LGL,LGL-BNH','Doomben','Varsity Lakes'):'5025',
    ('All Stations','Shorncliffe','Springfield Central'):'5031',
    ('All Stations','Shorncliffe','Cleveland'):'5040',
    ('All Stations','Shorncliffe','Park Road'):'5041',
    ('All Stations','Shorncliffe','Manly'):'5045',
    ('All Stations','Shorncliffe','Cannon Hill'):'5046',
    ('PKR-CNQ','Shorncliffe','Cannon Hill'):'5047',
    ('PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Doomben','Varsity Lakes'):'5126',
    ('All Stations','Doomben','Roma Street'):'5510',
    ('All Stations','Doomben','Kuraby'):'5522',
    ('All Stations','Doomben','Cleveland'):'5540',
    ('MGS-MNY','Doomben','Cleveland'):'5541',
    ('All Stations','Doomben','Park Road'):'5542',
    ('All Stations','Caboolture','Ipswich'):'6030',
    ('All Stations','Kippa-Ring','Cleveland'):'6040',
    ('PET-NTG','Caboolture','Roma Street'):'6011',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Roma Street'):'6111',
    ('MTZ-IDP,IDP-DAR','Caboolture','Ipswich'):'6131',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Springfield Central'):'6135',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Rosewood'):'6136',
    ('PET-NTG','Caboolture','Ipswich'):'6230',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Ipswich'):'6231',
    ('PET-NTG,NTG-EGJ,EGJ-BHI,MTZ-IDP,IDP-DAR','Caboolture','Ipswich'):'6232',
    ('PET-NTG','Caboolture','Springfield Central'):'6235',
    ('All Stations','Northgate','Roma Street'):'6410',
    ('NTG-EGJ,EGJ-BHI,PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Northgate','Varsity Lakes'):'6426',
    ('All Stations','Northgate','Cleveland'):'6440',
    ('All Stations','Northgate','Park Road'):'6442',
    ('All Stations','Northgate','Manly'):'6445',
    ('All Stations','Northgate','Cannon Hill'):'6446',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Cleveland'):'6510',
    ('All Stations','Petrie','Roma Street'):'6611',
    ('All Stations','Kippa-Ring','Roma Street'):'6710',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Roma Street'):'6711',
    ('All Stations','Kippa-Ring','Beenleigh'):'6720',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Ipswich'):'6731',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Springfield Central'):'6735',
    ('CAB-PET,PET-NTG,NTG-BHI','Nambour','Roma Street'):'7110',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Roma Street'):'7113',
    ('PET-NTG','Nambour','Ipswich'):'7130',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Ipswich'):'7131',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Springfield Central'):'7135',
    ('CAB-PET,PET-NTG,NTG-BHI','Gympie North','Roma Street'):'7612',
    ('All Stations','Ferny Grove','Roma Street'):'8010',
    ('All Stations','Ferny Grove','Beenleigh'):'8020',
    ('All Stations','Ferny Grove','Kuraby'):'8022',
    ('All Stations','Ferny Grove','Coopers Plains'):'8023',
    ('All Stations','Ferny Grove','Cleveland'):'8040',
    ('All Stations','Ferny Grove','Park Road'):'8042',
    ('All Stations','Domestic','Roma Street'):'9010',
    ('All Stations','Domestic','Rocklea'):'9025',
    ('All Stations','Domestic','Park Road'):'9042',
    ('MTZ-IDP,IDP-DAR','Domestic','Rosewood'):'9125',
    ('PKR-ATI,ATI-LGL,LGL-BNH','Domestic','Varsity Lakes'):'9128',
    ('PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Domestic','Varsity Lakes'):'9226',
    ('EDI = SPECIAL','',''):'10146',
    ('EDI = EKKA Loop','',''):'10200',
    }


















def TTS_VAS(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

    try:

        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        if __name__ == "__main__":
            print(filename,'\n')
        
        
        tree = ET.parse(filename)
        root = tree.getroot()
        
        
        filename      = filename[:-4]
        filename_xlsx = f'VASExtract-{filename}.xlsx'
        workbook      = xlsxwriter.Workbook(filename_xlsx)
        sheet         = workbook.add_worksheet('VAS')
        greyboldleft  = workbook.add_format({'bold':True,'bg_color':'#C0C0C0'})
        headers       = ['TrainId','Day','Pattern','Origin','Destination','RSCode']
        sheet.write_row('A1', headers, greyboldleft)
        sheet.autofilter('A1:F30000')
        
        ### Check for duplicate train numbers before executing the script
        ### Print warning for user if duplicates exist
        ### Print out all duplicates
        tn_list = []
        tn_doubles = []
        originpass = []
        destinpass = []
        for train in root.iter('train'):
            tn  = train.attrib['number']; day = train[0][0][0].attrib['weekdayKey']
            if (tn,day) in tn_list: tn_doubles.append((tn,day))
            tn_list.append((tn,day))
            
            traintype = [x.attrib['trainTypeId'] for x in train.iter('entry')][0]
            if 'Empty' not in traintype:
                stoptypes = [x.attrib['type'] for x in train.iter('entry') if x.attrib['stationID'] not in non_revenue_stations]
                
                origintype,destintype = stoptypes[0],stoptypes[-1]
                if origintype == 'pass':
                    originpass.append((tn,day))
                if destintype == 'pass':
                    destinpass.append((tn,day))
                
        if tn_doubles:
            print('           Error: Duplicate train numbers')
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit()  
        
        if originpass or destinpass:
            print('           Error: First station pass or last station pass through a revenue location')
            for tn,day in originpass: print(f' - First pass: {tn} on {weekdaykey_dict.get(day)} - ')
            for tn,day in destinpass: print(f' - Last pass:  {tn} on {weekdaykey_dict.get(day)} - ')
            time.sleep(15)
            sys.exit() 
        
        
        
        start_time = time.time()
        
        
    
        
        
    
        
        
    
        
        
        
        
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
        
        vrt_2InnerCity = {
            'YN':      (6,   1024 ),
            'YNA':     (5,   649 ),
            'MNE':     (4,   544 ),
            'BHI':     (3,   324 ),
            'BRC':     (2,   264 ),
            'BNC':     (1,   140 ),
            
            'RS':      (0,   0 ),
            'RSWJ':    (-1,  -60),
            'SBE':     (-1, -226 ),
            'SBA':     (-2, -316 ),
            'PKR':     (-3, -447 ),
            }
        
        vrt_2Milton = {
            'ETS':      (6,800),
            'CAM':      (5,680),
            'EXH':      (4,560),
            'NBY':      (3,410),
            'RSF':      (2,170),
            'RSWJ':     (1,140),
            'MTZ':      (0,0)
            }
        
        network_vrt_dict = {
            'Beenleigh':                  vrt_2Beenleigh,
            'Caboolture - Gympie North':  vrt_2GympieNth,
            'Cleveland':                  vrt_2Cleveland,
            'Doomben':                    vrt_2Doomben,
            'Ferny Grove':                vrt_2FernyGrove,
            'Varsity Lakes - Airport':    vrt_2VarsityLs,               
            'Ipswich - Rosewood':         vrt_2Rosewood,
            'Redcliffe':                  vrt_2KippaRing,
            'Shorncliffe':                vrt_2Shorncliffe,
            'Springfield':                vrt_2Springfield,
            'Inner City':                 vrt_2InnerCity,  
            'Normanby':                   vrt_2Milton
            }
        
        uniquestations_dict = {
            'Beenleigh':                  ('BNHS','BNT','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKET','RKE','MQK','CPM'), # 'TNY', 'MBN','YLY','YRG','FFI','DUP'
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN'),
            'Cleveland':                  ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                    ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':                ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Varsity Lakes - Airport':    ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT'),
            'Ipswich':                    ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
            'Rosewood':                   ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Ipswich - Rosewood':         ('MBN','TNY','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Redcliffe':                  ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Springfield':                ('RHD','SFD','SFC'),
            'Inner City':                 ('BHI','BRC','BNC','PKR'), #RS
            'Normanby':                   ('ETS','CAM','EXH','NBY','RSF','RSWJ','MTZ')
            }
        
        pattern_len = 0
        origin_len = 0
        destin_len = 0
        
        rsx_info = {}
        test = {}
        
        
        oIDdID_dict = {}
        tn3_tn_dict = {}
        unassigned = []
        sp_list = []
        rscode_list = []
        fridayonwards = [x for x in root.iter('train') if x[0][0][0].attrib['weekdayKey'] in ['4','2','1']]
        for train in fridayonwards:
            tn  = train.attrib['number']
            tn3 = tn[1:]
            tn1st = tn[0]
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry') if x.attrib['stationID'] not in non_revenue_stations]
            newentries = [x for x in train.iter('entry')]
            origin = entries[0].attrib
            destin = entries[-1].attrib
            
            oID = origin['stationName']
            dID = destin['stationName']
            
            oID = 'Domestic' if oID == 'Domestic Airport' else oID
            dID = 'Domestic' if dID == 'Domestic Airport' else dID
            
            
            
            if 'Empty' in origin['trainTypeId']:
                service = 'empty'
                pattern = 'EDI = SPECIAL'
                
            else:
                service = 'revnu'
                
                stoplist = [(x.attrib['stationID'],x.attrib['type']) for x in entries]
                stations = [x.attrib['stationID'] for x in entries]
    
                counter = []
                express = []
        
    
                if True:
        
                    for i,x in enumerate(entries):
                        if x.attrib['type'] == 'pass' and x.attrib['stationID'] not in non_revenue_stations:
                            counter.append(i)
        
                    if counter:
                        counter_grouped = [[]]
                        group = 0
        
                        
                        for idx,i in enumerate(counter):
                            if idx == 0:
                                counter_grouped[0] = [i]
                            
                            elif int(i) - int(counter[idx-1])  == 1:
                                counter_grouped[group].append(i)
                                
                            else:
                                group += 1
                                counter_grouped.append([i])
                        
                        x = [(stations[i[0]-1], stations[i[-1]+1]) for i in counter_grouped]
                        pattern = ','.join(['-'.join(p) for p in x])
                        
        
                    else:
                        pattern = 'All Stations'
    
            if pattern not in sp_list:
                sp_list.append(pattern)
                    
            rscodekey = (pattern,oID, dID) if service == 'revnu' else (pattern, '','')
                
            if rscodekey not in rscode_list:
                rscode_list.append(rscodekey)
                
                
    # # =============================================================================
    # #             
    # # =============================================================================
    #         if tn in ['JM09','1M09']:
    #             # if newentries[0].attrib['stationName'] != oID or newentries[-1].attrib['stationName'] != dID:
    #             print(tn)
    #             # print(entries[0].attrib['stationName'],'→',entries[-1].attrib['stationName'])
    #             # print(newentries[0].attrib['stationName'],'→',newentries[-1].attrib['stationName'])
    #             print(oID,'→',dID,pattern)
    #             print()
    # # =============================================================================
    # #             
    # # =============================================================================
        
                
            
            pattern_len = len(pattern) if len(pattern) > pattern_len else pattern_len
            origin_len  = len(oID) if len(oID) > origin_len else origin_len
            destin_len  = len(dID) if len(dID) > destin_len else destin_len
            # sIDs = {x.attrib['stationID'] for x in train[1].findall('entry')}    
            # count = 0
            # for line,vrt in network_vrt_dict.items():
        
            #     line_stops = uniquestations_dict.get(line)
                
        
            #     condition = sIDs.intersection(line_stops)
                
            #     if line == 'Beenleigh':
            #         condition = condition and sIDs.isdisjoint(uniquestations_dict.get('Varsity Lakes - Airport'))
                
            #     elif line == 'Shorncliffe':
            #         condition = condition or ('NTG' in [oID,dID] and any([vrt.get(x) for x in sIDs if x != 'NTG']))
                
            #     elif line == 'Redcliffe':
            #         shared_line_rdp_stations = ['LWO', 'BPR', 'SPN', 'BDS', 'CDE', 'ZLL', 'GEB', 'SSN', 'VGI']
            #         condition = condition or dID in shared_line_rdp_stations or oID in shared_line_rdp_stations
        
        
            #     if condition:
                    
            #         for n,entry in enumerate(train[1].iter('entry')):
                        
            #             if entry.attrib['stationID'] in vrt:
            #                 firstonline = entry.attrib['stationID']                  
            #                 first_sIDinVRT = n
            #                 break
                    
            #         for n,entry in enumerate(train[1].iter('entry')):
            #             if n <= first_sIDinVRT:
            #                 secondonline = firstonline
            #             else:
            #                 if entry.attrib['stationID'] in vrt:
            #                     secondonline = entry.attrib['stationID']
            #                     break
                        
            #         a = int(vrt.get(firstonline)[0])    
            #         b = int(vrt.get(secondonline)[0])
            #         increasing = b > a
            #         decreasing = b <= a
                    
                    
                    
            #         break
            
            #     else:
            #         count += 1
        
            # no_line = count == len(network_vrt_dict)
            
            
            # if no_line:
            #     unassigned.append([tn,oID,dID])
                            
            # elif line in ['Beenleigh','Cleveland','Varsity Lakes - Airport','Ipswich - Rosewood','Springfield']:
            #     direction = 'Down' if decreasing else 'Up'
            # elif line in ['Caboolture - Gympie North','Doomben','Ferny Grove','Inner City','Redcliffe','Shorncliffe','Normanby']:
            #     direction = 'Up' if decreasing else 'Down'
                
                
            
            
            keyinfo = (tn3,WeekdayKey,service)
            valinfo = (oID,dID,pattern)
            
            if keyinfo not in rsx_info:
                rsx_info[keyinfo] = [valinfo]
                test[keyinfo] = [tn]
            else:
                if valinfo != rsx_info[keyinfo][-1]:
                    rsx_info[keyinfo].append(valinfo)
                    test[keyinfo].append(tn)
    
            
            
            
            
            
            
            tn3_pair = (tn3,WeekdayKey,service)
            
            if tn3_pair not in oIDdID_dict:
                oIDdID_dict[tn3_pair] = [(oID,dID,pattern)]
                tn3_tn_dict[tn3_pair] = [tn]
            else:
                ###
                oIDdID_dict[tn3_pair].append((oID,dID,pattern))
                tn3_tn_dict[tn3_pair].append(tn)
        
        errortrains = []
        
        
        duplicatetn3s = []
        for k,v in oIDdID_dict.items():
            if len(v) >= 2:
                duplicatetn3s.append([k[1],tn3_tn_dict.get(k)])
                
                
        duptest = []
        for k,v in rsx_info.items():
            if len(v) >= 2:
                dupblock = []
                for i,val in enumerate(v):
                    dupblock.append([k[1],test.get(k)[i],k[2],val])
                    print(test.get(k)[i],f'{val[0]} → {val[1]} ({val[2]})')
                duptest.append(dupblock)
                print()
                
         
    
        
        # print('\nUnassigned Service Patterns')
        # for x in rscode_list:
        #     if not RSCode_dict.get(x):
        #         print(f'{x[1]} to {x[2]} ({x[0]})')
        
        print('\n\n')
        
        if duptest:
            print('!---------------------------------------ERROR---------------------------------------!')
            print('Multiple trains on the same day using the same last 3 characters but different routes')
            print('_____________________________________________________________________________________\n')
            filename_txt = f'UsesSameId-{filename}.txt'
            o = open(filename_txt, 'w')
            wl = o.writelines
            l =  '|'
            nl = '\n'
            for x in duptest:
                day = x[0][0]
                duptrains = ', '.join([y[1] for y in x])
                wl([day,l,duptrains,nl])
                for y in x:
                    y[0] = weekdaykey_dict.get(y[0])
                    y[3] = f'{y[3][0]} → {y[3][1]}'
                    
                    print(f'{y[0]}_{y[1]} ({y[2]}) - {y[3]}')
                print()
            o.close()
            # os.startfile(rf'{filename_txt}')
                
                    
        else:
    
        
            
            # sheet.autofilter('A2:F50000')
            # sheet.autofilter('A2:F100000')
            
            
            i = 1
            for k,v in oIDdID_dict.items():
                
                threechar = k[0]
                DoO = vas_daycode_dict.get(k[1])
                service = k[2]
                oID = v[0][0]
                dID = v[0][1]
                pattern = v[0][2]
                tn = tn3_tn_dict.get(k)[0]
                tn1st = tn[0]
                
                
                
                empty_tIDs = ['A','B','2','C','E']
                revnu_tIDs = ['T','U','1','J','D']
                
        
                
                if tn1st in empty_tIDs:
                    RSCode = '10146'
        
                    for t in empty_tIDs:
                        sheet.write(i,0, t+threechar)
                        sheet.write(i,1, DoO)
                        sheet.write(i,2, pattern)
                        sheet.write(i,3, oID)
                        sheet.write(i,4, dID)
                        sheet.write(i,5, RSCode)
                        i += 1
                elif tn1st in revnu_tIDs:
                    # RSCode = '     '
                    RSCode = RSCode_dict.get((pattern,oID,dID))
                    # if not RSCode:
                        # print(tn, (pattern,oID,dID))
                    
                    for t in revnu_tIDs:
                        sheet.write(i,0, t+threechar)
                        sheet.write(i,1, DoO)
                        sheet.write(i,2, pattern)
                        sheet.write(i,3, oID)
                        sheet.write(i,4, dID)
                        sheet.write(i,5, RSCode)
                        i += 1
                else:
                    pass
                
                
            sheet.set_column(2,2,pattern_len)
            sheet.set_column(3,3,origin_len)
            sheet.set_column(4,4,destin_len)
            
            
            if CreateWorkbook:
                workbook.close()
                print('Creating workbook')  
                if copyfile:
                    shutil.copy(filename_xlsx, mypath) 
                else:
                    if OpenWorkbook:
                        os.startfile(rf'{filename_xlsx}')
                        print('\nOpening workbook')  
                        
            # if CreateWorkbook:
            #     workbook.close()
            #     print('\n------------------')
            #     print('------------------\n')
            #     print('Creating workbook')  
            #     if OpenWorkbook and __name__ == "__main__":
            #         os.startfile(rf'{filename_xlsx}')
            #         print('\nOpening workbook') 
            #     else:
            #         if copyfile:
            #             shutil.copy(filename_xlsx, mypath) 
            
    
            
    
        
        
        
        
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('VAS Extract','Process Done')
        
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_VAS(path)