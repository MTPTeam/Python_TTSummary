import xlsxwriter
import re
import os
import sys
import time
import shutil
from datetime import datetime
import xml.etree.ElementTree as ET

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import traceback
import logging


OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True




weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
WEEK_ORDER = {
    'MTWT___':0,
    'M______':1,
    '_T_____':2,
    '__W____':3,
    '___T___':4,
    '____F__':5,
    '_____S_':6,
    '______S':7
    }


stations_dict = {
    'VYS':['ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST'], # I think this should be edited to contain the new GC stations if/when all TT's contain them
    'BDT':['BIT','BDT'], 
    'DBN':['DBN'],
    'KPR':['KGR','MRD','MGH','MGE','RWL','KPR','KPRS'], 
    'SFC':['RHD','SFD','SFC'], 
    'CAB':['CAB','CAW','CAE'], 
    'IPS':['WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'], 
    'NBR':['NBR'], 
    'RSW':['THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'], 
    'FYG':['WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'], 
    'BNH':['BNH','BNHS','BNT','TNY','MBN','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKE','MQK','CPM','TLY','YRG','FFI','DUP'], 
    'SHC':['BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'], 
    'CVN':['BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'], 
    'INC':'InnerCity',
    'INN':'InnerNorth',
    'INS':'InnerSouth',
    'INW':'InnerWest',
    'GYN': ['GYN']
        }















































def TTS_RI(path, mypath = None):
 
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
        filename_xlsx = f'RunInfo-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        
        
        
        
        
           
        
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
        
        
        def format_run(run):
            if '-' in run:
                return run

            newrun = ''
            # ETCS case for E12A, E12B runs to become E12-A, E12-B runs - and for regular E12 runs
            if run.startswith("E") and run[1].isnumeric():
                digits = ''.join(x for x in run[1:] if x.isnumeric())
                letters = ''.join(x for x in run[1:] if x.isalpha())
                newrun = f"E{digits}-{letters}" if run.endswith(('A','B')) else f"E{digits}"
            
            # ETCS case for 34EA, 34EB runs to become 34E-A, 34E-B runs - and for regular 34E runs
            elif len(run) >= 3 and run[0].isnumeric() and run[2] == "E":
                digits = ''.join(x for x in run if x.isnumeric())
                letters = ''.join(x for x in run[3:] if x.isalpha())
                newrun = f"{digits}E-{letters}" if run.endswith(('A','B')) else f"{digits}E"
            
            # Case for 12A, 12B runs to become 12-A, 12-B runs
            elif run[0].isnumeric() and run.endswith(('A','B')):
                digits = ''.join(x for x in run if x.isnumeric())
                letters = ''.join(x for x in run if x.isalpha())
                newrun = f"{digits}-{letters}"
            
            # Case for AB1, AB2 runs to become AB-1, AB-2 runs
            elif run[0].isalpha() and run.endswith(('1','2')):
                letters = ''.join(x for x in run if x.isalpha())
                digits = ''.join(x for x in run if x.isnumeric())
                newrun = f"{letters}-{digits}"

            return newrun if newrun else run
        
        
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
            'VYST':    (17,  4086),
            'VYS':     (16,  3996),
            'ROB':     (15,  3822),
            'ROBS':    (14,  4542),
            'MRC':     (13,  3686),
            'NRG':     (12,  3524),
            'HLN':     (11,  3242),
            'HID':     (10,  3094),
            'CXM':     (9,   2962),
            'PPA':     (8,   2846),
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
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN','AUR','CRD'),
            'Cleveland':                  ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                    ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':                ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Varsity Lakes - Airport':    ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT','PPA','MRC','HID'),
            'Ipswich':                    ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
            'Rosewood':                   ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Ipswich - Rosewood':         ('MBN','TNY','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
            'Redcliffe':                  ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Springfield':                ('RHD','SFD','SFC'),
            'Inner City':                 ('BHI','BRC','BNC','PKR'), #RS
            'Normanby':                   ('ETS','CAM','EXH','NBY','RSF','RSWJ','MTZ')
            }
        
        u_list = []
        d_list = []
        run_dict = {}
        nurseryruns = []
        unassigned = []
        for train in root.iter('train'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            origin = entries[0].attrib
            destin = entries[-1].attrib
            unit   = origin['trainTypeId'].split('-',1)[1]
            lineID = train.attrib['lineID']
            run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
            run = format_run(run)
            origin = entries[0].attrib
            destin = entries[-1].attrib
            
            sIDs = {x.attrib['stationID'] for x in entries}
            
            if unit not in u_list:
                u_list.append(unit)
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
            
                
            oID = origin['stationID']
            dID = destin['stationID']
            odep = origin['departure']
            ddep = destin['departure']
            LoID = origin['stationName']
            LdID = destin['stationName']
            # unit = origin['trainTypeId'].split('-',1)[1] 
            traintype = origin['trainTypeId']
            cars = int(re.findall(r'\d+', traintype)[0])
            status = 'Non-revenue' if 'Empty' in traintype else 'Revenue'
            empty = 1 if status == 'Non-revenue' else 0 
            revnu = 1 if status == 'Revenue' else 0
            
            
            count = 0
            
            
            
            
            for line,vrt in network_vrt_dict.items():
    
                line_stops = uniquestations_dict.get(line)
                
    
                condition = sIDs.intersection(line_stops)
                
                if line == 'Beenleigh':
                    condition = condition and sIDs.isdisjoint(uniquestations_dict.get('Varsity Lakes - Airport'))
                
                elif line == 'Shorncliffe':
                    condition = condition or ('NTG' in [oID,dID] and any([vrt.get(x) for x in sIDs if x != 'NTG']))
                
                elif line == 'Redcliffe':
                    shared_line_rdp_stations = ['LWO', 'BPR', 'SPN', 'BDS', 'CDE', 'ZLL', 'GEB', 'SSN', 'VGI']
                    condition = condition or dID in shared_line_rdp_stations or oID in shared_line_rdp_stations
    
                
                
                
                # print('conditoin',condition)
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
                    
                    
                    
                    break
            
                else:
                    count += 1
    
            no_line = count == len(network_vrt_dict)
            
            
            if no_line:
                unassigned.append([tn,oID,dID])
                            
            elif line in ['Beenleigh','Cleveland','Varsity Lakes - Airport','Ipswich - Rosewood','Springfield']:
                direction = 'Down' if decreasing else 'Up'
            elif line in ['Caboolture - Gympie North','Doomben','Ferny Grove','Inner City','Redcliffe','Shorncliffe','Normanby']:
                direction = 'Up' if decreasing else 'Down'
            
            
            # Create a list of all runs to be printed to the nursery runs worksheet
            if WeekdayKey in ['64','120']:
                nurseryruns.append( [run,tn,'M______',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['32','120']:
                nurseryruns.append( [run,tn,'_T_____',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['16','120']:
                nurseryruns.append( [run,tn,'__W____',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['8','120']:
                nurseryruns.append( [run,tn,'___T___',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['4']:
                nurseryruns.append( [run,tn,'____F__',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['2']:
                nurseryruns.append( [run,tn,'_____S_',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            if WeekdayKey in ['1']:
                nurseryruns.append( [run,tn,'______S',odep,LoID,LdID,ddep,unit,direction,status,cars] )
            
            # Create a dictionary for every run for each day
            if not run_dict.get((run,WeekdayKey)):
                run_dict[(run,WeekdayKey)] = [unit,cars,[tn],empty,revnu,odep,oID,dID,ddep]
                for s in stations_dict:
                    run_dict[(run,WeekdayKey)].append(0)
            else:
                run_dict[(run,WeekdayKey)][2].append(tn)  
                run_dict[(run,WeekdayKey)][3] += empty
                run_dict[(run,WeekdayKey)][4] += revnu
                run_dict[(run,WeekdayKey)][7] = dID
                run_dict[(run,WeekdayKey)][8] = ddep
            
            # Keeps a tally of times a revenue trip has started or ended on each particular line
            for i,(k,v) in enumerate(stations_dict.items(),9):
                if revnu and (oID in v or dID in v):
                    run_dict[(run,WeekdayKey)][i] += 1
        
        
        # Turn the dictionary to a list so the runs can be ordered by start time 
        runs_list = []
        for k,v in run_dict.items():
            runs_list.append([k[1]]+[k[0]]+v)
        runs_list.sort(key=lambda val: val[7])   
            
        
        
        # Sort the day and unit lists
        # Remove mon-thu (120) if individual mon,tue,wed,thu days exist within the rsx
        SORT_ORDER_UNIT = ['REP','EMU', 'NGR', 'NGRE', 'IMU100','SMU','HYBRID', 'ICE', 'DEPT']
        SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1'] 
        # print('rsx_days: ',d_list)   
    
        
        if '120' in d_list:
            d_list.remove('120')
            
            for single_weekday in ['64','32','16','8']:
                if single_weekday not in d_list:
                    d_list.append(single_weekday)
            
    
        
        u_list.sort(key=SORT_ORDER_UNIT.index)
        d_list.sort(key=SORT_ORDER_WEEK.index)    
            
    
        # print('xls_days: ',d_list)
        # print('units:    ',u_list)
        
        
        
        # Add worksheets for days that exist with the rsx
        
        # Info = workbook.add_worksheet('Info')
        
        worksheets = []
        if '64' in d_list:
            Mon = workbook.add_worksheet('Mon')
            worksheets.append(Mon)
            
        if '32' in d_list:
            Tue = workbook.add_worksheet('Tue')
            worksheets.append(Tue)
            
        if '16' in d_list:
            Wed = workbook.add_worksheet('Wed')
            worksheets.append(Wed)
            
        if '8' in d_list:
            Thu = workbook.add_worksheet('Thu')
            worksheets.append(Thu)
            
        if '4' in d_list:
            Fri = workbook.add_worksheet('Fri')
            worksheets.append(Fri)
            
        if '2' in d_list:
            Sat = workbook.add_worksheet('Sat')
            worksheets.append(Sat)
            
        if '1' in d_list:
            Sun = workbook.add_worksheet('Sun')
            worksheets.append(Sun)
            
            
        Nursery = workbook.add_worksheet('Nursery Runs')
        
        
        # Formatting
        #########################################################################################
        #########################################################################################
        title           = workbook.add_format({'bold':True,'align':'center'})
        header          = workbook.add_format({'bold':True,'align':'center','bg_color':'#CCCCCC'})
        size14          = workbook.add_format({'font_size':14})
        boldleft        = workbook.add_format({'bold':True,'align':'left'})
        boldcenter      = workbook.add_format({'bold':True,'align':'center'})
        boldright       = workbook.add_format({'bold':True,'align':'right'})
        greyedouttext   = workbook.add_format({'align':'center','font_color':'#666666'})
        centered        = workbook.add_format({'align':'center'})
        
        
        yellow          = workbook.add_format({'align':'center','bg_color':'#FEC938' })
        purple          = workbook.add_format({'align':'center','bg_color':'#705098','font_color':'#FFFFFF'})
        blue            = workbook.add_format({'align':'center','bg_color':'#0075B7','font_color':'#FFFFFF'})
        green           = workbook.add_format({'align':'center','bg_color':'#007D45','font_color':'#FFFFFF'})
        red             = workbook.add_format({'align':'center','bg_color':'#D10019','font_color':'#FFFFFF'})
        dblue           = workbook.add_format({'align':'center','bg_color':'#004170','font_color':'#FFFFFF'})
        grey            = workbook.add_format({'align':'center','bg_color':'#797A7C','font_color':'#FFFFFF'})
        
        yellow_header   = workbook.add_format({'align':'center','bg_color':'#FEC938','bottom':2 })
        purple_header   = workbook.add_format({'align':'center','bg_color':'#705098','bottom':2,'font_color':'#FFFFFF'})
        blue_header     = workbook.add_format({'align':'center','bg_color':'#0075B7','bottom':2,'font_color':'#FFFFFF'})
        green_header    = workbook.add_format({'align':'center','bg_color':'#007D45','bottom':2,'font_color':'#FFFFFF'})
        red_header      = workbook.add_format({'align':'center','bg_color':'#D10019','bottom':2,'font_color':'#FFFFFF'})
        dblue_header    = workbook.add_format({'align':'center','bg_color':'#004170','bottom':2,'font_color':'#FFFFFF'})
        grey_header     = workbook.add_format({'align':'center','bg_color':'#797A7C','bottom':2,'font_color':'#FFFFFF'})
        
        greyt           = workbook.add_format({'bold': True, 'align':'center','border':2, 'bg_color':'#C0C0C0'})
        greyt_tb        = workbook.add_format({'bold': True, 'align':'center','top':2, 'bottom':2, 'right':1,'left':1, 'bg_color':'#C0C0C0'})
        greyt_tbr       = workbook.add_format({'bold': True, 'align':'center','top':2, 'bottom':2, 'right':2,'left':1, 'bg_color':'#C0C0C0'})
        greyt_tbl       = workbook.add_format({'bold': True, 'align':'center','top':2, 'bottom':2, 'left':2,'right':1, 'bg_color':'#C0C0C0'})
        
        
        # Create a list of cell formats so cells will be coloured depending on their column index, aligning with the designated line colours
        font_list        = []
        header_font_list = []
        for x in stations_dict:
            
            if x in ['VYS','BDT']:
                font_list.append(yellow)
                header_font_list.append(yellow_header)
            
            elif x in ['DBN']:
                font_list.append(purple)
                header_font_list.append(purple_header)
                
            elif x in ['SFC','KPR']:
                font_list.append(blue)
                header_font_list.append(blue_header)
                
            elif x in ['CAB','IPS','NBR','RSW','GYN']:
                font_list.append(green)
                header_font_list.append(green_header)
                
            elif x in ['FYG','BNH']:
                font_list.append(red)
                header_font_list.append(red_header)
                
            elif x in ['SHC','CVN']:
                font_list.append(dblue)
                header_font_list.append(dblue_header)
                
            elif x in ['INC','INN','INS','INW']:
                font_list.append(grey)
                header_font_list.append(grey_header)
                
                
        
        # RunInfo Sheets
        #########################################################################################
        #########################################################################################
        for sheet in worksheets:
            sheet.merge_range('A1:F1','Run',greyt)
            sheet.merge_range('G1:H1','Out',greyt)
            sheet.merge_range('I1:J1','In',greyt)
            sheet.merge_range(0,10,0,10+len(stations_dict)-1,'# Service End Points Per Line Section (1 count per revenue train)',greyt)
            
            sheet.write('A2','Run',greyt_tbl)
            sheet.write('B2','Unit',greyt_tb)
            sheet.write('C2','Cars',greyt_tb)
            sheet.write('D2','Services',greyt_tb)
            sheet.write('E2','#Empties',greyt_tb)
            sheet.write('F2','#Revenue',greyt_tbr)
            sheet.write('G2','Out Time',greyt_tbl)
            sheet.write('H2','Org',greyt_tbr)
            sheet.write('I2','Dest',greyt_tbl)
            sheet.write('J2','In Time',greyt_tbr)
            
            for j,station in enumerate(stations_dict): 
                sheet.write(1,10+j,station,header_font_list[j])  
        
        
        for i,day in enumerate(d_list):
            
            services_col_len = 0   
            
            if day in ['64','32','16','8']:
                day = [day,'120']
            else:
                day = [day]
                
            # For each day, write the runlist information up until the tallies
            day_runs = [x[1:] for x in runs_list if x[0] in day]
            for row,entry in enumerate(day_runs,2):
                if entry[0].isnumeric():
                    entry[0] = int(entry[0])
                elif entry[0][0] == '0':
                    entry[0] = entry[0][1:]
                
                
                
                entry[6] = timetrim(entry[6])
                entry[3] = ','.join(entry[3])
                entry[9] = timetrim(entry[9])
                worksheets[i].write_row(row,0,entry[:10],centered)
                
                # Write the tallies separately to make use of the font_list to conditionally format the cells by what line they belong to
                for ii,tally in enumerate(entry[10:]):
                        if tally:
                            worksheets[i].write(row,10+ii,tally,font_list[ii])    
                
                # Update the variable to keep track how wide the 'services' column needs to be
                services_col_len = max(services_col_len,len(entry[3]))
            
            worksheets[i].set_column(3,3,services_col_len)
            worksheets[i].autofilter(1,0,700,9+len(stations_dict))
        
         
        # Nurery Runs
        #########################################################################################
        #########################################################################################  
        # Sort nursery runs on day then run
        nurseryruns.sort(key=lambda x: x[0])
        nurseryruns.sort(key=lambda x: WEEK_ORDER[x[2]])
        
        # Write to sheet
        for row,x in enumerate(nurseryruns,2):
            x[3] = timetrim(x[3])
            x[6] = timetrim(x[6])
            Nursery.write_row(row,0,x,centered)
            
            
        Nursery.autofilter('A2:K30000')
        Nursery.merge_range('A1:C1','Service',greyt)
        Nursery.merge_range('D1:E1','Origin',greyt)
        Nursery.merge_range('F1:G1','Destination',greyt)
        Nursery.merge_range('H1:K1','Detail',greyt)
        Nursery.write('A2','Run',greyt_tbl)
        Nursery.write('B2','TID',greyt_tb)
        Nursery.write('C2','Day',greyt_tbr)
        Nursery.write('D2','Start',greyt_tbl)
        Nursery.write('E2','Org',greyt_tbr)
        Nursery.write('F2','Dest',greyt_tbl)
        Nursery.write('G2','Finish',greyt_tbr)
        Nursery.write('H2','Unit',greyt_tbl)
        Nursery.write('I2','Direction',greyt_tb)
        Nursery.write('J2','Revenue Status',greyt_tb)
        Nursery.write('K2','Cars',greyt_tbr)
        Nursery.set_column(0,0,9)
        Nursery.set_column(1,1,9)
        Nursery.set_column(2,2,9)
        Nursery.set_column(3,3,25)
        Nursery.set_column(4,4,25)
        Nursery.set_column(5,5,25)
        Nursery.set_column(6,6,25)
        Nursery.set_column(7,7,14)
        Nursery.set_column(8,8,14)
        Nursery.set_column(9,9,14)
        Nursery.set_column(10,10,14)
        
        
        # Info
        #########################################################################################
        #########################################################################################
        # date = datetime.now().strftime("%d-%b-%Y %H:%M")
        # info_col  = ['TTID:','Timetable Name:','Date Imported:','Report Created:']
        # info_col2 = ['',filename,'',date]
        # Info.write_column('A1',info_col,boldright)
        # Info.write_column('B1',info_col2)
        # Info.set_column(0,0,15)
        # Info.set_column(1,1,75)
        
        wrapped = workbook.add_format({'align':'left','right':2,'valign':'top','text_wrap':True})
        bwrapped = workbook.add_format({'align':'left','left':2,'valign':'top','text_wrap':True,'bold':True})
        center = workbook.add_format({'align':'center'})
        left = workbook.add_format({'align':'left'})
        borderright = workbook.add_format({'align':'center','right':2})
        
        unbalanced = workbook.add_format({'bg_color':'#FF7C80','align':'center'})
        unbalancedborderright = workbook.add_format({'bg_color':'#FF7C80','align':'center','right':2})
        lgunmatched = workbook.add_format({'bg_color':'#F2F2F2','font_color':'#FF0000','align':'center'})
        yunmatched = workbook.add_format({'bg_color':'#FFFFCC','font_color':'#FF0000','align':'center'})
        
        leftright = workbook.add_format({'align':'center','right':2,'left':2,'bold':True})
        topbottom = workbook.add_format({'align':'center','top':2,'bottom':2,'bold':True})
        
        emu = workbook.add_format({'bg_color':'#F2DCDB','align':'center','bold':True})
        imu = workbook.add_format({'bg_color':'#EBF1DE','align':'center','bold':True})
        ngr = workbook.add_format({'bg_color':'#E4DFEC','align':'center','bold':True})
        
        dg = workbook.add_format({'bg_color':'#808080'})
        dgtopleft = workbook.add_format({'bg_color':'#808080','top':2,'left':2})
        dgleft = workbook.add_format({'bg_color':'#808080','left':2})
        dgbottomleft = workbook.add_format({'bg_color':'#808080','bottom':2,'left':2})
        dgbottom = workbook.add_format({'bg_color':'#808080','bottom':2})
        dgbottomright = workbook.add_format({'bg_color':'#808080','bottom':2,'right':2})
        dgright = workbook.add_format({'bg_color':'#808080','right':2})
        dgtopright = workbook.add_format({'bg_color':'#808080','top':2,'right':2})
        dgtop = workbook.add_format({'bg_color':'#808080','top':2,'font_color':'white'})
        dgtopbottom = workbook.add_format({'bg_color':'#808080','top':2,'bottom':2,'font_color':'white'})
        dgleftright = workbook.add_format({'bg_color':'#808080','left':2,'right':2})
        
        
        lg = workbook.add_format({'bg_color':'#F2F2F2','align':'center'})
        lgleft = workbook.add_format({'bg_color':'#F2F2F2','left':2,'align':'center'})
        lgright = workbook.add_format({'bg_color':'#F2F2F2','right':2,'align':'center'})
        lgtopbottom = workbook.add_format({'bg_color':'#F2F2F2','align':'center','top':2,'bottom':2})
        lg3left = workbook.add_format({'bg_color':'#F2F2F2','align':'center','top':2,'bottom':2,'left':2})
        lg3right = workbook.add_format({'bg_color':'#F2F2F2','align':'center','top':2,'bottom':2,'right':2})
        lg3top = workbook.add_format({'bg_color':'#F2F2F2','align':'center','top':2,'left':2,'right':2})
        lg3bottom = workbook.add_format({'bg_color':'#F2F2F2','align':'center','bottom':2,'left':2,'right':2})
        
        yellow = workbook.add_format({'bg_color':'#FFFFCC','align':'center'})
        yellowleft = workbook.add_format({'bg_color':'#FFFFCC','align':'center','left':2})
        yellowright = workbook.add_format({'bg_color':'#FFFFCC','align':'center','right':2})
        yellowleftright = workbook.add_format({'bg_color':'#FFFFCC','align':'left','right':2,'left':2})
        yellowtop = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2})
        yellowbottom = workbook.add_format({'bg_color':'#FFFFCC','align':'center','bottom':2})
        yellowtopleft = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'left':2})
        yellowtopright = workbook.add_format({'bg_color':'#FFFFCC','align':'center','right':2,'top':2})
        yellowtopbottom = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'bottom':2})
        y3top = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'left':2,'right':2})
        y3bottom = workbook.add_format({'bg_color':'#FFFFCC','align':'center','bottom':2,'left':2,'right':2})
        # y3left = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'left':2,'bottom':2})
        # y3right = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'bottom':2,'right':2})
        
        
        
        # y3toperror = workbook.add_format({'bg_color':'#FFFFCC','align':'center','top':2,'left':2,'right':2,'font_color':'#FF0000'})
        # yellowleftrighterror = workbook.add_format({'bg_color':'#FFFFCC','align':'left','right':2,'left':2,'font_color':'#FF0000'})
        
        
        
        lgoutside = workbook.add_format({'bg_color':'#F2F2F2','border':2,'align':'center','bold':True})
        youtside = workbook.add_format({'bg_color':'#FFFFCC','border':2,'align':'center','bold':True})
        outside = workbook.add_format({'border':2,'align':'center','bold':True})
        
        w3bottom = workbook.add_format({'align':'center','bottom':2,'left':2,'right':2})
        w3left = workbook.add_format({'align':'center','bottom':2,'left':2,'top':2,'bold':True})
        w3right = workbook.add_format({'align':'center','bottom':2,'top':2,'right':2,'bold':True})
        
        lgoutsideleft = workbook.add_format({'bg_color':'#F2F2F2','border':2,'align':'left','bold':True})
        youtsideleft = workbook.add_format({'bg_color':'#FFFFCC','border':2,'align':'left','bold':True})
        
        # workbook.formats[0].set_align('center') 
        
        def dgbox(startrow,startcol,height,width):
            LSC.write_column( startrow+1,        startcol,         (height-2)*[''], dgleft)
            LSC.write_column( startrow+1,        startcol+width-1, (height-2)*[''], dgright)
            LSC.write_row(    startrow,          startcol+1,       (width-2)*[''],  dgtop)
            LSC.write_row(    startrow+height-1, startcol+1,       (width-2)*[''],  dgtopbottom)
            LSC.write(        startrow,          startcol,         '',              dgtopleft)
            LSC.write(        startrow+height-1, startcol,         '',              dgbottomleft)
            LSC.write(        startrow+height-1, startcol+width-1, '',              dgbottomright)
            LSC.write(        startrow,          startcol+width-1, '',              dgtopright)     
        
        
        
        
        
        
        workbook.add_format({'align':'center','bg_color':'#FEC938' })
        # Live Stabling Count
        #########################################################################################
        #########################################################################################
        n = 20
        LSC  = workbook.add_worksheet('Live Stabling Count')
        
        
        
        # LSC.write_column(2,1,(n+3)*[''],dgleft)
        # LSC.write_column(2,16,(n+3)*[''],dgright)
        # LSC.write_row(1,2,14*[''],dgtop)
        # LSC.write_row(n+5,2,14*[''],dgbottom)
        # LSC.write(1,1,'',dgtopleft)
        # LSC.write(n+5,1,'',dgbottomleft)
        # LSC.write(n+5,16,'',dgbottomright)
        # LSC.write(1,16,'',dgtopright)
        dgbox(1,1,n+4,16)
        LSC.write('C2','INPUTS',dgtop)
        
        
        # LSC.write('F3','Out Bef.')
        # LSC.write('G3','9:00:00 AM')
        # LSC.write('K3','In After.')
        # LSC.write('L3','4:00:00 PM')
        
        LSC.write('C3','',dgbottomright)
        LSC.write('C4','Change',outside)
        LSC.write('D4','Day',youtside)
        LSC.write('E4','Run',youtside)
        LSC.write('F4','Unit',lg3left)
        LSC.write('G4','Out Type',lgtopbottom)
        LSC.write('H4','Out Time',lgtopbottom)
        LSC.write('I4','Org',lgtopbottom)
        LSC.write('J4','Dest',lgtopbottom)
        LSC.write('K4','In Time',lgtopbottom)
        LSC.write('L4','In Type',lg3right)
        LSC.write('M4','Altered Unit',yellowtopbottom)
        LSC.write('N4','Altered Org',yellowtopbottom)
        LSC.write('O4','Altered Dest',yellowtopbottom)
        LSC.write('P4','Notes (Free Text)',youtside)
        LSC.merge_range(2,3,2,4,'INPUTS',youtside)
        LSC.merge_range(2,5,2,11,'OUTPUTS',lgoutside)
        LSC.merge_range(2,12,2,15,'INPUTS',youtside)
        
        stables = ['BNHS','BQYS','CAB','CAE','CAW','EMHS','ETF','ETS','GYN','IPSS','KPRS','MNY','NBR','PETS','RDKS','ROBS','WFE','WFW','WOBS','YN']
        LSC.write_column('C5',list(range(1,n+1)),leftright)
        LSC.write_column('D5',n*[''],center)
        LSC.write_column('M5',n*[''],center)
        LSC.write_column('N5',n*[''],center)
        LSC.write_column('O5',n*[''],center)
        LSC.write_column('E5',n*[''],yellowright)
        LSC.write_column('P5',n*[''],yellowleftright)
        LSC.data_validation(4,3,n+3,3, {'validate': 'list', 'source': ['Mon', 'Tue', 'Wed','Thu','Fri','Sat','Sun']})
        LSC.data_validation(4,12,n+3,12, {'validate': 'list', 'source': ['EMU', 'IMU100', 'NGR']})
        LSC.data_validation(4,13,n+3,13, {'validate': 'list', 'source': stables})
        LSC.data_validation(4,14,n+3,14, {'validate': 'list', 'source': stables})
        # LSC.write(4,3,'test')
        
        LSC.conditional_format(4,3,4,3,{'type':'no_errors','format':   y3top})
        LSC.conditional_format(5,3,n+2,3,{'type':'no_errors','format':   yellowleftright})
        LSC.conditional_format(n+3,3,n+3,3,{'type':'no_errors','format':   y3bottom})
        # LSC.conditional_format(4,4,4,4,{'type':'no_errors','format':   yellowtopright})
        # LSC.conditional_format(5,4,n+3,4,{'type':'no_errors','format':   yellowleftright})
        # LSC.conditional_format(4,12,n+3,12,{'type':'no_errors','format':   yellowleft}) 
        LSC.conditional_format(4,12,n+3,12,{'type':'no_errors','format':   yellow})
        LSC.conditional_format(4,13,n+3,13,{'type':'no_errors','format':   yellow})
        LSC.conditional_format(4,14,n+3,14,{'type':'no_errors','format':   yellow})
        # LSC.conditional_format(4,15,n+3,15,{'type':'no_errors','format':   yellowright})
        
        
        
        LSC.conditional_format(4,5,n+3,5,{'type':'cell','criteria': '!=', 'value':'$M5','format':   lgunmatched})
        LSC.conditional_format(4,8,n+3,8,{'type':'cell','criteria': '!=', 'value':'$N5','format':   lgunmatched})
        LSC.conditional_format(4,9,n+3,9,{'type':'cell','criteria': '!=', 'value':'$O5','format':   lgunmatched})
        LSC.conditional_format(4,12,n+3,12,{'type':'cell','criteria': '!=', 'value':'$F5','format':   yunmatched})
        LSC.conditional_format(4,13,n+3,13,{'type':'cell','criteria': '!=', 'value':'$I5','format':   yunmatched})
        LSC.conditional_format(4,14,n+3,14,{'type':'cell','criteria': '!=', 'value':'$J5','format':   yunmatched})
        
        # LSC.conditional_format(4,3,4,3,{'type':'cell','criteria': '!=', 'value':'$F5','format':   yunmatched})
        # LSC.conditional_format(5,3,n+2,3,{'type':'cell','criteria': '!=', 'value':'$F5','format':   yunmatched})
        
        
        # LSC.conditional_format('B3:K12', {'type':     'cell',
        #                                 'criteria': '>=',
        #                                 'value':    50,
        #                                 'format':   format1})
        
        
        unitcol = [f'=IF(E{row}<>"",VLOOKUP($E{row},INDIRECT("\'"&$D{row}&"\'!A:J"),2,FALSE),"")' for row in list(range(5,n+5))]
        outypecol = [f'=IF(E{row}<>0,IF(H{row}+0<="09:00:00","AM Out","PM Out"),"")' for row in list(range(5,n+5))]
        outtimecol = [f'=IF(E{row}<>"",VLOOKUP($E{row},INDIRECT("\'"&$D{row}&"\'!A:J"),7,FALSE),"")' for row in list(range(5,n+5))]
        orgcol = [f'=IF(E{row}<>"",VLOOKUP($E{row},INDIRECT("\'"&$D{row}&"\'!A:J"),8,FALSE),"")' for row in list(range(5,n+5))]
        destcol = [f'=IF(E{row}<>"",VLOOKUP($E{row},INDIRECT("\'"&$D{row}&"\'!A:J"),9,FALSE),"")' for row in list(range(5,n+5))]
        intimecol = [f'=IF(E{row}<>"",VLOOKUP($E{row},INDIRECT("\'"&$D{row}&"\'!A:J"),10,FALSE),"")' for row in list(range(5,n+5))]
        intypecol = [f'=IF(E{row}<>0,IF(K{row}+0<="16:00:00","AM In","PM In"),"")' for row in list(range(5,n+5))]
        
        LSC.write_column(4,5,unitcol,lgleft)
        LSC.write_column(4,6,outypecol,lg)
        LSC.write_column(4,7,outtimecol,lg)
        LSC.write_column(4,8,orgcol,lg)
        LSC.write_column(4,9,destcol,lg)
        LSC.write_column(4,10,intimecol,lg)
        LSC.write_column(4,11,intypecol,lgright)
        
        

        
        # LSC.write('C24','20')
        yards = ['ETF/ETS','YN','BNHS','BQYS','CAB/CAE','CAW','EMHS','GYN','IPSS','KPRS','MNY','NBR','PETS','RDKS','ROBS','WFE/WFE','WOBS',]
        
        
        unitfontdict = {
            'EMU':emu,
            'IMU100':imu,
            'NGR':ngr
            }
        
        dgbox(1,len(yards)+1,21,34)
        LSC.write('T2','LIVE STABLING COUNTS',dgtop)
        
        for i,unit in enumerate(['EMU','IMU100','NGR']):
            unitfont = unitfontdict.get(unit)
            startcol = 19 + i*11
            LSC.write_row(1,startcol+1,4*[''],dgtopbottom)
            LSC.write_row(2,startcol+1,4*[unit],unitfont)
            
            LSC.write(3,startcol,'Yard',outside)
            LSC.write(3,startcol+1,'AM Out',w3left)
            LSC.write(3,startcol+2,'AM In',topbottom)
            LSC.write(3,startcol+3,'PM Out',topbottom)
            LSC.write(3,startcol+4,'PM In',w3right)
            
            LSC.merge_range(3,startcol+5,3,startcol+9,'Partial Yards',outside)
            LSC.write(4,startcol+5,'ETF',lg3top)
            LSC.write(5,startcol+5,'ETS',lg3bottom)
            
            LSC.write(8,startcol+5,'CAB',lg3top)
            LSC.write(9,startcol+5,'CAE',lg3bottom)
            
            LSC.write(19,startcol+5,'WFE',lg3top)
            LSC.write(20,startcol+5,'WFW',lg3bottom)
            
            
            
            
            LSC.write(2,startcol,'',dgbottomright)
            for rowidx in [2,6,7,10,11,12,13,14,15,16,17,18]:
                if rowidx in [6,10]:
                    LSC.write_row(rowidx,startcol+6,4*[''],dgtop)
                elif rowidx in [7,18]:
                    LSC.write_row(rowidx,startcol+6,4*[''],dgbottom)
                else:
                    LSC.write_row(rowidx,startcol+6,4*[''],dg)
                
                LSC.write(rowidx,startcol+5,'',dgleft)
                
            if i < 2:
                LSC.write_column(2,startcol+10,19*[''],dg)
                LSC.write(21,startcol+10,'',dgbottom)
            
            
            for rowidx in [4,5,8,9,19,20]:
                LSC.write(rowidx,startcol+10,'',dgleftright)
            
            LSC.write_column(4,startcol,yards,leftright)
            LSC.write(4+len(yards)-1,startcol,yards[-1],w3bottom)
            
            
            
            
            
            
            
            #!!!
            # fph = 4*[0]
            # for ii,y in enumerate(yards,4):
            #     LSC.write_row(ii,startcol+1,fph,lg)
            # LSC.write_row(4,startcol+6,fph,lg)
            # LSC.write_row(5,startcol+6,fph,lg)
            # LSC.write_row(8,startcol+6,fph,lg)
            # LSC.write_row(9,startcol+6,fph,lg)
            # LSC.write_row(19,startcol+6,fph,lg)
            # LSC.write_row(20,startcol+6,fph,lg)
            for row in range(5,22):
                ii = row-1
                
                scenario1dict = {'EMU':'T','IMU100':'AE','NGR':'AP'}
                scenario2dict = {'EMU':'Y','IMU100':'AJ','NGR':'AU'}
                col = scenario1dict.get(unit) if row not in [5,9,20] else scenario2dict.get(unit)
                
                
                unitcoldict = {'EMU':['U','V','W','X'],'IMU100':['AF','AG','AH','AI'],'NGR':['AQ','AR','AS','AT']}
                
                u1,u2,u3,u4 = unitcoldict.get(unit)
                    
                partialyardcoldict = {'EMU':['Z','AA','AB','AC'],'IMU100':['AK','AL','AM','AN'],'NGR':['AV','AW','AX','AY']}
                pycol = partialyardcoldict.get(unit)
                    
                    
                
                form1 = f'=-COUNTIFS($F$5:$F$24,{u1}$3,$I$5:$I$24,${col}{row},$G$5:$G$24,{u1}$4)+COUNTIFS($M$5:$M$24,{u1}$3,$N$5:$N$24,${col}{row},$G$5:$G$24,{u1}$4)'
                form2 = f'=-COUNTIFS($F$5:$F$24,{u2}$3,$J$5:$J$24,${col}{row},$L$5:$L$24,{u2}$4)+COUNTIFS($M$5:$M$24,{u2}$3,$O$5:$O$24,${col}{row},$L$5:$L$24,{u2}$4)'
                form3 = f'=-COUNTIFS($F$5:$F$24,{u3}$3,$I$5:$I$24,${col}{row},$G$5:$G$24,{u3}$4)+COUNTIFS($M$5:$M$24,{u3}$3,$N$5:$N$24,${col}{row},$G$5:$G$24,{u3}$4)'
                form4 = f'=-COUNTIFS($F$5:$F$24,{u4}$3,$J$5:$J$24,${col}{row},$L$5:$L$24,{u4}$4)+COUNTIFS($M$5:$M$24,{u4}$3,$O$5:$O$24,${col}{row},$L$5:$L$24,{u4}$4)'
                
                form5 = f'=-COUNTIFS($F$5:$F$24,{u1}$3,$I$5:$I$24,${col}{row+1},$G$5:$G$24,{u1}$4)+COUNTIFS($M$5:$M$24,{u1}$3,$N$5:$N$24,${col}{row+1},$G$5:$G$24,{u1}$4)'
                form6 = f'=-COUNTIFS($F$5:$F$24,{u2}$3,$J$5:$J$24,${col}{row+1},$L$5:$L$24,{u2}$4)+COUNTIFS($M$5:$M$24,{u2}$3,$O$5:$O$24,${col}{row+1},$L$5:$L$24,{u2}$4)'
                form7 = f'=-COUNTIFS($F$5:$F$24,{u3}$3,$I$5:$I$24,${col}{row+1},$G$5:$G$24,{u3}$4)+COUNTIFS($M$5:$M$24,{u3}$3,$N$5:$N$24,${col}{row+1},$G$5:$G$24,{u3}$4)'
                form8 = f'=-COUNTIFS($F$5:$F$24,{u4}$3,$J$5:$J$24,${col}{row+1},$L$5:$L$24,{u4}$4)+COUNTIFS($M$5:$M$24,{u4}$3,$O$5:$O$24,${col}{row+1},$L$5:$L$24,{u4}$4)'
                
                form9  = f'={pycol[0]}{row}+{pycol[0]}{row+1}'
                form10 = f'={pycol[1]}{row}+{pycol[1]}{row+1}'
                form11 = f'={pycol[2]}{row}+{pycol[2]}{row+1}'
                form12 = f'={pycol[3]}{row}+{pycol[3]}{row+1}'
                
                if row not in [5,9,20]:
                    LSC.write(ii,startcol+1,form1,center)
                    LSC.write(ii,startcol+2,form2,center)
                    LSC.write(ii,startcol+3,form3,center)
                    LSC.write(ii,startcol+4,form4,borderright)
                else:
                    LSC.write(ii,startcol+1,form9,center)
                    LSC.write(ii,startcol+2,form10,center)
                    LSC.write(ii,startcol+3,form11,center)
                    LSC.write(ii,startcol+4,form12,center)
                    
                    LSC.write(ii,startcol+6,form1,center)
                    LSC.write(ii,startcol+7,form2,center)
                    LSC.write(ii,startcol+8,form3,center)
                    LSC.write(ii,startcol+9,form4,center)
                    LSC.write(ii+1,startcol+6,form5,center)
                    LSC.write(ii+1,startcol+7,form6,center)
                    LSC.write(ii+1,startcol+8,form7,center)
                    LSC.write(ii+1,startcol+9,form8,center)
                    
            LSC.conditional_format(4,startcol+1,20,startcol+3, {'type':'cell', 'criteria': '!=', 'value':0, 'format':   unbalanced})
            LSC.conditional_format(4,startcol+4,20,startcol+4, {'type':'cell', 'criteria': '!=', 'value':0, 'format':   unbalancedborderright})
                    
                
            LSC.conditional_format(4,startcol+6,20,startcol+9, {'type':'cell', 'criteria': '!=', 'value':0, 'format':   unbalanced})
            
            
            
            
        #### ABOUT
        dgbox(n+7,1,6,16)
        LSC.write(n+7,2,'ABOUT',dgtop)
        
        
        text1 = 'The purpose of this tool is to predict the impacts of stabling and rollingstock changes at a spreadsheet level. This tool helps validate the proposed stabling changes before making them in Railsys.'
        text2 = 'Stabling changes are complex. This tool solves the issue of making bulk stabling changes in Railsys, running the stabling count report, finding out that yards are out of balance and not knowing which run caused the imbalance. Here, any runs can be changed and the impacts seen instantly to find a solution without having to make the changes in Railsys.'
        text3 = 'This tool assumes the starting point is a balanced timetable. This tool works best working on an existing timetable where the stabling count is already balanced and further stabling changes are required. It cannot be used to balance an unbalanced timetable (yet).'
        
        # LSC.merge_range(n+8,2,n+8,3,'Tool')
        LSC.merge_range(n+8,2,n+8,15,'Live Stabling Count',lgoutside)
        LSC.merge_range(n+9,2,n+9,3,'Purpose',bwrapped)
        LSC.merge_range(n+10,2,n+10,3,'Solution to the issue',bwrapped)
        LSC.merge_range(n+11,2,n+11,3,'When to use this tool',bwrapped)
        LSC.merge_range(n+9,4,n+9,15, text1,wrapped)
        LSC.merge_range(n+10,4,n+10,15, text2,wrapped)
        LSC.merge_range(n+11,4,n+11,15, text3,wrapped)
        
        
        
        
        
        
        #### INSTRUCTIONS
        dgbox(n+14,1,8,16)
        LSC.write(n+14,2,'INSTRUCTIONS',dgtop)
        
        
        LSC.merge_range(n+15,2,n+15,15,'How to Use This Tool',lgoutside)
        text4 = 'Yellow cells are INPUTS and can be changed by using the drop down bars or manual input.'
        text5 = 'Light Grey cells are OUTPUTS and should not be changed. These cells contain formulas.'
        text6 = 'Yellow Cells LHS - Columns D,E are where you input your reference train runs.\n Assign the Day reference (Column D) to tell the tool which tab to look at.\n Enter in the Run ID you wish to alter (Column E) to tell the tool which run to prefill the existing details from.\n (You will now see the details of this run appear in Columns F-L)'
        text7 = 'Yellow Cells RHS - Columns M,N,O are where you input your alterations.\n Assign the altered unit type,  origin, and/or  destination to the run.\n If there is no change, simply select the existing unit type, origin and destination from the drop down list.\n (You will now see the stabling balances update in the LIVE STABLING COUNT)'
        text8 = 'Repeat steps 1-2 until all desired alterations have been included.\n The LIVE STABLING COUNT will display cells in RED when there is an imbalance in stabling.\n "-1" indicates the yard is missing a unit.\n "1" indicates the yard has an additional unit.'
        
        LSC.merge_range(n+16,2,n+16,3,'Yellow Cells',youtsideleft)
        LSC.merge_range(n+17,2,n+17,3,'Light Grey Cells',lgoutsideleft)
        LSC.merge_range(n+18,2,n+18,3,'Step 1',bwrapped)
        LSC.merge_range(n+19,2,n+19,3,'Step 2',bwrapped)
        LSC.merge_range(n+20,2,n+20,3,'Repeat',bwrapped)
        
        
        
        LSC.merge_range(n+16,4,n+16,15,text4)
        LSC.merge_range(n+17,4,n+17,15,text5,wrapped)
        LSC.merge_range(n+18,4,n+18,15,text6,wrapped)
        LSC.merge_range(n+19,4,n+19,15,text7,wrapped)
        LSC.merge_range(n+20,4,n+20,15,text8,wrapped)
        
        
        LSC.set_column(1,1,2.29)
        LSC.set_column(11,11,9.86)
        LSC.set_column(12,14,12.14)
        LSC.set_column(15,15,35)
        LSC.set_column(16,16,2.29)
        LSC.set_column(18,18,2.29)
        LSC.set_column(19,19,9.14)
        LSC.set_column(30,30,9.14)
        LSC.set_column(41,41,9.14)
        LSC.set_column(51,51,2.29)
        
        LSC.set_column(24,28,None,None, {"hidden": True})
        LSC.set_column(35,39,None,None, {"hidden": True})
        LSC.set_column(46,50,None,None, {"hidden": True})

        LSC.set_row(n+9,36)
        LSC.set_row(n+10,64.5)
        LSC.set_row(n+11,51)
        LSC.set_row(n+16,25.5)
        LSC.set_row(n+17,25.5)
        LSC.set_row(n+18,83.25)
        LSC.set_row(n+19,90)
        LSC.set_row(n+20,90)
        
        
    
        
        
        
        Nursery.activate()
        # LSC.activate()
        
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
            messagebox.showinfo('Run Information Report','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_RI(path)