#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Import the Required Modules #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
import xlsxwriter
import re
import os
import sys
import time
import shutil
import pandas as pd
from datetime import datetime
from datetime import date
import xml.etree.ElementTree as ET

import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

import traceback
import logging


#~~~~~~~~~~~~#
# Initialise #
#~~~~~~~~~~~~#
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
    'VYS':['ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST'],
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


#~~~~~~~~~~~~~~~~~~~~~~~#
# Define a Sub-Function #
#~~~~~~~~~~~~~~~~~~~~~~~#
def is_file_open(file_path):
    try:
        # Try to open the file in exclusive mode ('x' for creation)
        with open(file_path, 'r+'):  # This opens the file for reading and writing
            return False  # File is not open, we can use it
    except IOError:
        return True  # IOError is raised if the file is in use


#~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Define the Main Function #
#~~~~~~~~~~~~~~~~~~~~~~~~~~#
def NGR_DPP(path, path_char, mypath = None):
 
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
        filename_xlsx = f'NGR Deployment Plan-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # Check for Duplicate Train No's #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        tn_list = []
        tn_doubles = []
        for train in root.iter('train'):
            tn  = train.attrib['number']; day = train[0][0][0].attrib['weekdayKey']
            if (tn,day) in tn_list: tn_doubles.append((tn,day))
            tn_list.append((tn,day))
                
        if tn_doubles:
            print('           Error: Duplicate train numbers')
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(10)
            sys.exit() 
        
        
        #~~~~~~~~~~~~~~#
        # Timing Setup #
        #~~~~~~~~~~~~~~#
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
        
        
        #~~~~~~~~~~~~~~~~~~~~~~~#
        # Creating Dictionaries #
        #~~~~~~~~~~~~~~~~~~~~~~~#
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
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN','AUR','CRD'),
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
        
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # Parse RSX to Extract Attributes #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
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
            # cars = int(re.findall(r'\d+', traintype)[0])
            status = 'Non-revenue' if 'Empty' in traintype else 'Revenue'
            empty = 1 if status == 'Non-revenue' else 0 
            revnu = 1 if status == 'Revenue' else 0
            
            
            count = 0
            
            # CONFUSED FROM HERE ##############################################
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
            # TO HERE #########################################################
            
            # Create a list of all runs to be printed to the nursery runs worksheet
            # if WeekdayKey in ['64','120']:
            #     nurseryruns.append( [run,tn,'M______',odep,LoID,LdID,ddep,unit,direction,status] )
            # if WeekdayKey in ['32','120']:
            #     nurseryruns.append( [run,tn,'_T_____',odep,LoID,LdID,ddep,unit,direction,status] )
            # if WeekdayKey in ['16','120']:
            #     nurseryruns.append( [run,tn,'__W____',odep,LoID,LdID,ddep,unit,direction,status] )
            if WeekdayKey in ['8','120']:
                nurseryruns.append( [run,tn,'___T___',odep,LoID,LdID,ddep,unit,direction,status] )
            if WeekdayKey in ['4']:
                nurseryruns.append( [run,tn,'____F__',odep,LoID,LdID,ddep,unit,direction,status] )
            if WeekdayKey in ['2']:
                nurseryruns.append( [run,tn,'_____S_',odep,LoID,LdID,ddep,unit,direction,status] )
            if WeekdayKey in ['1']:
                nurseryruns.append( [run,tn,'______S',odep,LoID,LdID,ddep,unit,direction,status] )
            
            # Create a dictionary for every run for each day
            if not run_dict.get((run,WeekdayKey)):
                run_dict[(run,WeekdayKey)] = [unit,[tn],empty,revnu,odep,oID,dID,ddep]
                for s in stations_dict:
                    run_dict[(run,WeekdayKey)].append(0)
            else:
                run_dict[(run,WeekdayKey)][1].append(tn)  
                run_dict[(run,WeekdayKey)][2] += empty
                run_dict[(run,WeekdayKey)][3] += revnu
                run_dict[(run,WeekdayKey)][6] = dID
                run_dict[(run,WeekdayKey)][7] = ddep
            
                
            # # Keeps a tally of times a revenue trip has started or ended on each particular line
            # for i,(k,v) in enumerate(stations_dict.items(),9):
            #     if revnu and (oID in v or dID in v):
            #         run_dict[(run,WeekdayKey)][i] += 1
        
        
        # Turn the dictionary to a list so the runs can be ordered by start time 
        runs_list = []
        for k,v in run_dict.items():
            runs_list.append([k[1]]+[k[0]]+v)
        runs_list.sort(key=lambda val: val[7])   
        
        # Sort the day and unit lists
        # Remove mon-thu (120) if individual mon,tue,wed,thu days exist within the rsx
        SORT_ORDER_UNIT = ['REP','EMU', 'NGR', 'IMU100','SMU','HYBRID', 'ICE', 'DEPT']
        SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1'] 
        
        if '120' in d_list:
            d_list.remove('120')
            
            for single_weekday in ['64','32','16','8']:
                if single_weekday not in d_list:
                    d_list.append(single_weekday)    
        
        u_list.sort(key=SORT_ORDER_UNIT.index)
        d_list.sort(key=SORT_ORDER_WEEK.index)    

        #~~~~~~~~~~~~~~~~~~#
        # Excel Formatting #
        #~~~~~~~~~~~~~~~~~~#
        blue_title     = workbook.add_format({'font_size':20,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#0070C0','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        blue_title_s   = workbook.add_format({'font_size':16,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#0070C0','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        red_title      = workbook.add_format({'font_size':20,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#C00000','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        red_title_s    = workbook.add_format({'font_size':16,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#C00000','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        green_title    = workbook.add_format({'font_size':20,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#92D050','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        green_title_s  = workbook.add_format({'font_size':16,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#92D050','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        orange_title   = workbook.add_format({'font_size':20,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#F37021','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        orange_title_s = workbook.add_format({'font_size':16,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#F37021','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        summ_title_s   = workbook.add_format({'font_size':16,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#00768C','border':2,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
                     
        blue_header    = workbook.add_format({'font_size':11,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#0070C0','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        blue_subhead   = workbook.add_format({'font_size':11,'bold':False,'align':'center','valign': 'vcenter','bg_color':'#0070C0','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        red_header     = workbook.add_format({'font_size':11,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#C00000','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        red_subhead    = workbook.add_format({'font_size':11,'bold':False,'align':'center','valign': 'vcenter','bg_color':'#C00000','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        green_header   = workbook.add_format({'font_size':11,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#92D050','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        green_subhead  = workbook.add_format({'font_size':11,'bold':False,'align':'center','valign': 'vcenter','bg_color':'#92D050','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        orange_header  = workbook.add_format({'font_size':11,'bold':True,'align':'center','valign': 'vcenter','bg_color':'#F37021','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        orange_subhead = workbook.add_format({'font_size':11,'bold':False,'align':'center','valign': 'vcenter','bg_color':'#F37021','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        
        blue_left      = workbook.add_format({'font_size':11,'bold':False,'align':'left','valign': 'vcenter','bg_color':'#0070C0','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        red_left       = workbook.add_format({'font_size':11,'bold':False,'align':'left','valign': 'vcenter','bg_color':'#C00000','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        green_left     = workbook.add_format({'font_size':11,'bold':False,'align':'left','valign': 'vcenter','bg_color':'#92D050','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
        orange_left    = workbook.add_format({'font_size':11,'bold':False,'align':'left','valign': 'vcenter','bg_color':'#F37021','border':1,'font_color':'#FFFFFF','font_name': 'Atkinson Hyperlegible'})
     
        greyt          = workbook.add_format({'bold': True, 'align':'center','valign': 'vcenter','border':2, 'bg_color':'#C0C0C0','text_wrap': True})
        greyt_u        = workbook.add_format({'bold': True, 'align':'center','valign': 'vcenter','bottom':2, 'bg_color':'#C0C0C0','text_wrap': True})
        greyt_rhs      = workbook.add_format({'bold': True, 'align':'right','border':2, 'bg_color':'#C0C0C0','text_wrap': True})
        centred        = workbook.add_format({'align':'center','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        centred_box    = workbook.add_format({'border':1,'align':'center','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        centred_tr     = workbook.add_format({'align':'center','valign': 'vcenter','top':2,'right':2,'bottom':1,'left':1})
        centred_br     = workbook.add_format({'align':'center','valign': 'vcenter','top':1,'right':2,'bottom':2,'left':1})
        left           = workbook.add_format({'font_size':11,'border':1,'align':'left','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        left_box       = workbook.add_format({'font_size':11,'border':1,'align':'left','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        left_bold      = workbook.add_format({'font_size':11,'border':1,'bold':True, 'align':'left','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        right          = workbook.add_format({'font_size':11,'align':'right','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        right_box      = workbook.add_format({'font_size':11,'border':1,'align':'right','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        right_bold     = workbook.add_format({'font_size':11,'bold':True,'align':'right','valign': 'vcenter','font_name':'Atkinson Hyperlegible'})
        
        thin_border    = workbook.add_format({'border':1})
        thick_border   = workbook.add_format({'border':2})
        thick_top      = workbook.add_format({'top':2, 'left':1, 'right':1, 'bottom':1})
        thick_right    = workbook.add_format({'top':1, 'left':1, 'right':2, 'bottom':1})
        thick_left     = workbook.add_format({'top':1, 'left':2, 'right':1, 'bottom':1})
        thick_bottom   = workbook.add_format({'top':1, 'left':1, 'right':1, 'bottom':2})
        
        top_right      = workbook.add_format({'top':2, 'left':1, 'right':2, 'bottom':1})
        top_left       = workbook.add_format({'top':2, 'left':2, 'right':1, 'bottom':1})
        bottom_right   = workbook.add_format({'top':1, 'left':1, 'right':2, 'bottom':2})
        bottom_left    = workbook.add_format({'top':1, 'left':2, 'right':1, 'bottom':2})
        
        tight_right    = workbook.add_format({'top':2, 'left':1, 'right':2, 'bottom':2})
        tight_left     = workbook.add_format({'top':2, 'left':2, 'right':1, 'bottom':2})
        tight_middle   = workbook.add_format({'top':2, 'left':1, 'right':1, 'bottom':2})
        
        dp_plan = workbook.add_worksheet('Deployment Plan')
        km_run = workbook.add_worksheet('KM Breakdown by Run')
        km_service = workbook.add_worksheet('KM by Service')
        
        ' fill out the top, right, bottom left edge, then top, right, bottom left CORNERS'
        def box_thick(start_row, start_col, end_row, end_col, worksheet):  
            if start_row == end_row and end_col == start_col+1:
                worksheet.conditional_format(start_row, start_col, end_row, end_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': thick_border})
            else:
                worksheet.conditional_format(start_row, end_col, start_row, end_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': top_right})
                worksheet.conditional_format(end_row, end_col, end_row, end_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': bottom_right})
                worksheet.conditional_format(end_row, start_col, end_row, start_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': bottom_left})
                worksheet.conditional_format(start_row, start_col, start_row, start_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': top_left})
                for col in range(start_col, end_col + 1): # top border
                    worksheet.conditional_format(start_row, col, start_row, col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': thick_top})
                    
                for row in range(start_row, end_row + 1): # right border
                    worksheet.conditional_format(row, end_col, row, end_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': thick_right})
                      
                for row in range(start_row, end_row + 1): # left border
                    worksheet.conditional_format(row, start_col, row, start_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': thick_left})
                
                for col in range(start_col, end_col + 1): # bottom border
                    worksheet.conditional_format(end_row, col, end_row, col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': thick_bottom})
            
        ' single row thick box - addresses right and left edges then fills in columns between'
        def short_box_thick(row, start_col, end_col, worksheet):  
            worksheet.conditional_format(row, end_col, row, end_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': tight_right})
            worksheet.conditional_format(row, start_col, row, start_col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': tight_left})
            for col in range(start_col, end_col + 1): # top and bottom border
                worksheet.conditional_format(row, col, row, col, {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': tight_middle})
        ########## COULD CHANGE BOX THICK TO HAVE AN IF STATEMENT, if: start_row == end_row, do short box thick instead of regular##############
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # Train Characteristics Sheet #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        filename_char = path_char.split('/')[-1]
        tchar = pd.read_excel(filename_char) # , engine = 'openpyxl')

        
        columns_to_extract = ["Number", "DoO", "Length of train run [km]"]
        tchar_data = tchar[columns_to_extract]
        km_service.write('A1',columns_to_extract[0],greyt_u)
        km_service.write('B1',"Day Code",greyt_u)
        km_service.write('C1',columns_to_extract[2],greyt_u)
        km_service.write('E1',columns_to_extract[1],greyt_u)
        km_service.write('G2',"Taken from:",greyt_rhs)
        km_service.write('H2',filename, centred_tr)
        km_service.write('G3',"When:",greyt_rhs)
        today = date.today()
        km_service.write('H3', today.strftime("%d/%m/%Y"), centred_br)
        
        for idx, row in tchar_data.iterrows():
            km_service.write(idx+1, 0, row['Number'], centred)  # Column A
            km_service.write_number(idx+1, 2, row['Length of train run [km]'], centred)  # Column C
            km_service.write(idx+1, 4, row['DoO'], centred)  # Column E
            
            # Insert the Day Code formula based on the value of DoO (in column E)
            formula = f'=IF(E{idx+2}="Sa","_____S_",IF(E{idx+2}="Sun","______S",IF(E{idx+2}="Fr","____F__",IF(E{idx+2}="Mo-Thu","MTWT___",IF(E{idx+2}="Mo","M______",IF(E{idx+2}="Tu","_T_____",IF(E{idx+2}="We","__W____",IF(E{idx+2}="Thu","___T___","Nope"))))))))'
            km_service.write_formula(idx+1, 1, formula, centred)  # Column B (Day Code)
        
        km_service.autofilter(0, 0, len(tchar_data), 4)
        km_service.set_column('A:A', 13)  # Set column A width to 13
        km_service.set_column('B:B', 14)  # Set column B width to 14
        km_service.set_column('C:C', 27)  # Set column C width to 27
        km_service.set_column('E:E', 10)  # Set column E width to 10
        km_service.set_column('G:G', 12)  # Set column G width to 12
        km_service.set_column('H:H', 26)  # Set column H width to 26
        
        #~~~~~~~~~~~~~~~~~~~~~~~#
        # Deployment Plan Sheet #
        #~~~~~~~~~~~~~~~~~~~~~~~#
        dp_plan.set_zoom(70)
        dp_plan.set_default_row(15.75)
        
        dp_plan.merge_range('A1:K1','Monday to Thursday',blue_title)
        dp_plan.merge_range('M1:W1','Friday',red_title)
        dp_plan.merge_range('Y1:AI1','Saturday',green_title)
        dp_plan.merge_range('AK1:AU1','Sunday',orange_title)
    
        dp_plan.set_row(0,30)
        dp_plan.set_column('A:XFD',8.88)
        
        headers = ['Run', 'Train', 'Day', 'Start','Origin','Destination','Finish','Type','Direction','Comment','KMs']        
        
        def write_headers(start_row, start_col, headers, style): # Write headers to the specified starting cell
            for col, header in enumerate(headers):
                dp_plan.write(start_row, start_col + col, header, style)
        
        def fill_formula(start_row, end_row, column, formula, sheet): # fill out rows with KM formula
            for row in range(start_row, end_row+1):
                run_formula = formula.replace('ROW_NUM', str(row + 1))
                sheet.write_formula(row, column, run_formula, centred_box)             
            
        
        # Setting column widths using lists of columns
        day_col       = ['C:C','O:O','AA:AA','AM:AM']
        org_dest_col  = ['E:F','Q:R','AC:AD','AO:AP']
        comment_col   = ['J:J','V:V','AH:AH','AT:AT']
        direction_col = ['I:I','U:U','AG:AG','AS:AS']
        for col in day_col:
            dp_plan.set_column(col, 10.5)
        for col in org_dest_col:
            dp_plan.set_column(col, 31)
        for col in comment_col:
            dp_plan.set_column(col, 13.5)
        for col in direction_col:
            dp_plan.set_column(col, 11.5)
        
        
        # Sort nursery runs on run then day (was day then run)
        nurseryruns.sort(key=lambda x: WEEK_ORDER[x[2]])
        nurseryruns.sort(key=lambda x: x[0])
        
        # Filtering out runs which are not numbered
        def valid_run(run):
            return bool(re.match(r'^\d+A?$', run))
        
        nurseryruns = [entry for entry in nurseryruns if valid_run(entry[0])]
        
        # Custom sort function
        def custom_sort(entry):
            run = entry[0]
            run_number = int(run.rstrip('A')) # remove 'A' and change to integer
            return run_number
        
        # Sort the filtered data to put 100 after 99 instead of 10
        nurseryruns = sorted(nurseryruns, key=custom_sort)
        
        # Initilaise row values
        rolling_th = rolling_fr = rolling_sa = rolling_su = rolling_row = 1
        run_row = 4
        
        #~~~~~~~~~~~~~~~~~~~~~~~#
        # Forming Sheet 1 and 2 #
        #~~~~~~~~~~~~~~~~~~~~~~~#
        for row,x in enumerate(nurseryruns,2):
            x[3] = timetrim(x[3])
            x[6] = timetrim(x[6])
            
            # KM formula template
            # formula_th = "=XLOOKUP(1,(ARRAY('KM by Service'!$A$2:$A$10000='Deployment Plan'!BROW_NUM))*(ARRAY('KM by Service'!$B$2:$B$10000='Deployment Plan'!CROW_NUM)),'KM by Service'!$C$2:$C$10000)"
            # formula_fr = "=XLOOKUP(1,(ARRAY('KM by Service'!$A$2:$A$10000='Deployment Plan'!NROW_NUM))*(ARRAY('KM by Service'!$B$2:$B$10000='Deployment Plan'!OROW_NUM)),'KM by Service'!$C$2:$C$10000)"
            # formula_sa = "=XLOOKUP(1,(ARRAY('KM by Service'!$A$2:$A$10000='Deployment Plan'!ZROW_NUM))*(ARRAY('KM by Service'!$B$2:$B$10000='Deployment Plan'!AAROW_NUM)),'KM by Service'!$C$2:$C$10000)"
            # formula_su = "=XLOOKUP(1,(ARRAY('KM by Service'!$A$2:$A$10000='Deployment Plan'!ALROW_NUM))*(ARRAY('KM by Service'!$B$2:$B$10000='Deployment Plan'!AMROW_NUM)),'KM by Service'!$C$2:$C$10000)"
            formula_th = f"""=_xlfn.XLOOKUP(1,('KM by Service'!$A$2:$A$10000='Deployment Plan'!BROW_NUM)*('KM by Service'!$B$2:$B$10000='Deployment Plan'!CROW_NUM),'KM by Service'!$C$2:$C$10000)"""
            formula_fr = f"""=_xlfn.XLOOKUP(1,('KM by Service'!$A$2:$A$10000='Deployment Plan'!NROW_NUM)*('KM by Service'!$B$2:$B$10000='Deployment Plan'!OROW_NUM),'KM by Service'!$C$2:$C$10000)"""
            formula_sa = f"""=_xlfn.XLOOKUP(1,('KM by Service'!$A$2:$A$10000='Deployment Plan'!ZROW_NUM)*('KM by Service'!$B$2:$B$10000='Deployment Plan'!AAROW_NUM),'KM by Service'!$C$2:$C$10000)"""
            formula_su = f"""=_xlfn.XLOOKUP(1,('KM by Service'!$A$2:$A$10000='Deployment Plan'!ALROW_NUM)*('KM by Service'!$B$2:$B$10000='Deployment Plan'!AMROW_NUM),'KM by Service'!$C$2:$C$10000)"""

            # KM Summary templates
            thrun_formula = "=SUMIFS('Deployment Plan'!K:K,'Deployment Plan'!A:A,'KM Breakdown by Run'!ARUN_ROW,'Deployment Plan'!J:J,'KM Breakdown by Run'!ADEUCE_RUN)"
            frrun_formula = "=SUMIFS('Deployment Plan'!W:W,'Deployment Plan'!M:M,'KM Breakdown by Run'!DRUN_ROW,'Deployment Plan'!V:V,'KM Breakdown by Run'!DDEUCE_RUN)"
            sarun_formula = "=SUMIFS('Deployment Plan'!AI:AI,'Deployment Plan'!Y:Y,'KM Breakdown by Run'!GRUN_ROW,'Deployment Plan'!AH:AH,'KM Breakdown by Run'!GDEUCE_RUN)"
            surun_formula = "=SUMIFS('Deployment Plan'!AU:AU,'Deployment Plan'!AK:AK,'KM Breakdown by Run'!JRUN_ROW,'Deployment Plan'!AT:AT,'KM Breakdown by Run'!JDEUCE_RUN)"
            
            # KM Summary function
            def km_summ(starting_row, starting_column, col_name, formula, style):
                
                km_run.write(starting_row, starting_column, nurseryruns[row-3][0], style)
                km_run.write(starting_row+1, starting_column, 'Non-Revenue', left_box)
                km_run.write(starting_row+2, starting_column, 'Revenue', left_box)
                
                run_formula = formula.replace('RUN_ROW', str(run_row + 1))
                nonrev_formula = run_formula.replace('DEUCE_RUN', str(run_row + 2))
                rev_formula = run_formula.replace('DEUCE_RUN', str(run_row + 3))
                km_run.write(starting_row+1, starting_column+1, nonrev_formula, right_box)
                km_run.write(starting_row+2, starting_column+1, rev_formula, right_box)
                km_run.write(starting_row, starting_column+1, f'={col_name}{starting_row+2}+{col_name}{starting_row+3}', right_box)
                
            # KM's and format for the last run of each day (sunday is triggered further below)
            # if row == len(nurseryruns)+1:
            #     if x[0] == thurs_run[0][0]:
            #         fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
            #         box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
            #     if x[0] == fri_run[0][0]:
            #         fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
            #         box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
            #     if x[0] == sat_run[0][0]:
            #         fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
            #         box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
            #     if x[0] == sun_run[0][0]:
            #         fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
            #         box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                
            # KM's and format for each new run of the day (triggered by seeing a previously unseen run number after the first entry)
            if row != 2 and x[0] != nurseryruns[row-3][0]:
                if nurseryruns[row-3][0] == thurs_run[0][0]:
                    if thurs_run[0][0].endswith('A'):
                        fill_formula(rolling_th+1,(rolling_th+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_th,0,(rolling_th+len(thurs_run)),10,dp_plan)
                    else:
                        fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                
                if nurseryruns[row-3][0] == fri_run[0][0]:
                    if fri_run[0][0].endswith('A'):
                        fill_formula(rolling_fr+1,(rolling_fr+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_fr,12,(rolling_fr+len(fri_run)),22,dp_plan)
                    else:
                        fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                        
                if nurseryruns[row-3][0] == sat_run[0][0]:
                    if sat_run[0][0].endswith('A'):
                        fill_formula(rolling_sa+1,(rolling_sa+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_sa,24,(rolling_sa+len(sat_run)),34,dp_plan)
                    else:
                        fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                
                if nurseryruns[row-3][0] == sun_run[0][0]:
                    if sun_run[0][0].endswith('A'):
                        fill_formula(rolling_su+1,(rolling_su+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_su,36,(rolling_su+len(sun_run)),46,dp_plan)
                    else:
                        fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                

                if not nurseryruns[row-3][0].endswith('A'):
                    rolling_th = 2+rolling_row + len(thurs_run)
                    rolling_fr = 2+rolling_row + len(fri_run)
                    rolling_sa = 2+rolling_row + len(sat_run)
                    rolling_su = 2+rolling_row + len(sun_run)
                                         
                if nurseryruns[row-3][0] == thurs_run[0][0] == fri_run[0][0] == sat_run[0][0] == sun_run[0][0]:
                    km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    km_summ(run_row,9,'K',surun_formula,orange_subhead)
                    
                    box_thick(run_row,0,run_row+2,1,km_run)
                    box_thick(run_row,3,run_row+2,4,km_run)
                    box_thick(run_row,6,run_row+2,7,km_run)
                    box_thick(run_row,9,run_row+2,10,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_th < rolling_row or rolling_fr < rolling_row or rolling_sa < rolling_row or rolling_su < rolling_row):
                        rolling_th += 2 + max(len(thurs_run), len(fri_run), len(sat_run), len(sun_run))
                        rolling_fr += 2 + max(len(thurs_run), len(fri_run), len(sat_run), len(sun_run))
                        rolling_sa += 2 + max(len(thurs_run), len(fri_run), len(sat_run), len(sun_run))
                        rolling_su += 2 + max(len(thurs_run), len(fri_run), len(sat_run), len(sun_run))
                        rolling_row = max(rolling_th, rolling_fr, rolling_sa, rolling_su, rolling_row) 
                    else: rolling_row += (2+max(len(thurs_run),len(fri_run),len(sat_run),len(sun_run)))
                    
                elif nurseryruns[row-3][0] == thurs_run[0][0] == fri_run[0][0] == sat_run[0][0]:
                    km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    
                    box_thick(run_row,0,run_row+2,1,km_run)
                    box_thick(run_row,3,run_row+2,4,km_run)
                    box_thick(run_row,6,run_row+2,7,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_th < rolling_row or rolling_fr < rolling_row or rolling_sa < rolling_row):
                        rolling_th += 2 + max(len(thurs_run), len(fri_run), len(sat_run))
                        rolling_fr += 2 + max(len(thurs_run), len(fri_run), len(sat_run))
                        rolling_sa += 2 + max(len(thurs_run), len(fri_run), len(sat_run))
                        rolling_row = max(rolling_th,rolling_fr,rolling_sa,rolling_row)
                    else:
                        rolling_row += 2+max(len(thurs_run),len(fri_run),len(sat_run))                    

                elif nurseryruns[row-3][0] == thurs_run[0][0] == fri_run[0][0] == sun_run[0][0]:
                    km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    km_summ(run_row,9,'K',surun_formula,orange_subhead)
                    
                    box_thick(run_row,0,run_row+2,1,km_run)
                    box_thick(run_row,3,run_row+2,4,km_run)
                    box_thick(run_row,9,run_row+2,10,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_th < rolling_row or rolling_fr < rolling_row or rolling_su < rolling_row):
                        rolling_th += 2 + max(len(thurs_run), len(fri_run), len(sun_run))
                        rolling_fr += 2 + max(len(thurs_run), len(fri_run), len(sun_run))
                        rolling_su += 2 + max(len(thurs_run), len(fri_run), len(sun_run))
                        rolling_row = max(rolling_th,rolling_fr,rolling_su,rolling_row)
                    else:
                        rolling_row += 2+max(len(thurs_run),len(fri_run),len(sun_run))
                        
                elif nurseryruns[row-3][0] == thurs_run[0][0] == fri_run[0][0]:
                    km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    
                    box_thick(run_row,0,run_row+2,1,km_run)
                    box_thick(run_row,3,run_row+2,4,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_th < rolling_row or rolling_fr < rolling_row):
                        rolling_th += 2 + max(len(thurs_run), len(fri_run))
                        rolling_fr += 2 + max(len(thurs_run), len(fri_run))
                        rolling_row = max(rolling_th,rolling_fr,rolling_row)
                    else:
                        rolling_row += 2+max(len(thurs_run),len(fri_run))
                        
                elif nurseryruns[row-3][0] == sat_run[0][0] == sun_run[0][0]:
                    km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    km_summ(run_row,9,'K',surun_formula,orange_subhead)
                    
                    box_thick(run_row,6,run_row+2,7,km_run)
                    box_thick(run_row,9,run_row+2,10,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_sa < rolling_row or rolling_su < rolling_row):
                        rolling_sa += 2 + max(len(sat_run), len(sun_run))
                        rolling_su += 2 + max(len(sat_run), len(sun_run))
                        rolling_row = max(rolling_sa,rolling_su,rolling_row)
                    else:
                        rolling_row += 2+max(len(sat_run),len(sun_run))
                        
                elif nurseryruns[row-3][0] == sun_run[0][0]:
                    km_summ(run_row,9,'K',surun_formula,orange_subhead)
                    
                    box_thick(run_row,9,run_row+2,10,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_su < rolling_row):
                        rolling_su += 2 + len(sun_run)
                        rolling_row = max(rolling_su,rolling_row)
                    else:
                        rolling_row += 2+len(sun_run)
                        
                elif nurseryruns[row-3][0] == sat_run[0][0]:
                    km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    
                    box_thick(run_row,6,run_row+2,7,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_sa < rolling_row):
                        rolling_sa += 2 + len(sat_run)
                        rolling_row = max(rolling_sa,rolling_row)
                    else:
                        rolling_row += 2+len(sat_run)
                        
                elif nurseryruns[row-3][0] == thurs_run[0][0]:
                    km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    
                    box_thick(run_row,0,run_row+2,1,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_th < rolling_row):
                        rolling_th += 2 + len(thurs_run)
                        rolling_row = max(rolling_th,rolling_row)
                    else:
                        rolling_row += 2+len(thurs_run)
                        
                else:
                    km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    
                    box_thick(run_row,3,run_row+2,4,km_run)
                    
                    run_row += 4
                    
                    if nurseryruns[row-3][0].endswith('A') and (rolling_fr < rolling_row):
                        rolling_fr += 2 + len(fri_run)
                        rolling_row = max(rolling_fr,rolling_row)
                    else:
                        rolling_row += 2+len(fri_run)
                
            if x[2] == '___T___':
                
                x[2] = 'MTWT___' # THIS MAY NEED MORE LOGIC TO CHECK OTHER DAYS  ########################

                if row == 2:
                    thurs_run = []
                    thurs_run.append(x)
                    start_row = rolling_row+1
                    write_headers(rolling_row,0,headers,blue_header)
                    dp_plan.write_row(start_row,0,x,centred_box)
                    start_row += 1
                    
                elif x[0] != nurseryruns[row-3][0]:                
                    if not x[0].endswith('A'):
                        start_row = rolling_row+1
                        write_headers(rolling_row,0,headers,blue_header)
                        dp_plan.write_row(start_row,0,x,centred_box)
                    
                    elif x[0] == thurs_run[-1][0]+'A':
                        dp_plan.merge_range(rolling_th-1, 0, rolling_th-1, 10, f'Form Run {x[0]}', greyt) 
                        start_row = rolling_th+1
                        write_headers(rolling_th,0,headers,blue_header)
                        dp_plan.write_row(start_row,0,x,centred_box)
                    thurs_run = []
                    thurs_run.append(x)
                    start_row += 1
                    
                elif x[0] == nurseryruns[row-3][0]:
                    if x[2] != nurseryruns[row-3][2]:
                        if not x[0].endswith('A'):
                            start_row = rolling_row+1
                            write_headers(rolling_row,0,headers,blue_header)
                            dp_plan.write_row(start_row,0,x,centred_box)
                        
                        elif x[0].endswith('A'):
                            dp_plan.merge_range(rolling_th-1, 0, rolling_th-1, 10, f'Form Run {x[0]}', greyt)
                            start_row = rolling_th+1
                            write_headers(rolling_th,0,headers,blue_header)
                            dp_plan.write_row(start_row,0,x,centred_box)
                        thurs_run = []
                        thurs_run.append(x)
                        start_row += 1
                    else:
                        thurs_run.append(x)
                        dp_plan.write_row(start_row,0,x,centred_box)
                        start_row += 1

                if row == len(nurseryruns)+1:
                    # fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                    # box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                    
                    if x[0] == thurs_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                        km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                        box_thick(run_row,0,run_row+2,1,km_run)
                        
                    if x[0] == fri_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                        km_summ(run_row,3,'E',frrun_formula,red_subhead)
                        box_thick(run_row,3,run_row+2,4,km_run)
                        
                    if x[0] == sat_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                        km_summ(run_row,6,'H',sarun_formula,green_subhead)
                        box_thick(run_row,6,run_row+2,7,km_run)
                        
                    if x[0] == sun_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                        km_summ(run_row,9,'K',surun_formula,orange_subhead)
                        box_thick(run_row,9,run_row+2,10,km_run)
                    
                    # km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    
                    # box_thick(run_row,0,run_row+2,1,km_run)
                    
            elif x[2] == '____F__':
                if row == 2:
                    fri_run = []
                    fri_run.append(x)
                    start_row = rolling_row+1
                    write_headers(rolling_row,12,headers,red_header)
                    dp_plan.write_row(start_row,12,x,centred_box)
                    start_row += 1
                    
                elif x[0] != nurseryruns[row-3][0]:
                    if not x[0].endswith('A'):
                        start_row = rolling_row+1
                        write_headers(rolling_row,12,headers,red_header)
                        dp_plan.write_row(start_row,12,x,centred_box)
                        
                    
                    elif x[0] == fri_run[-1][0]+'A':
                        dp_plan.merge_range(rolling_fr-1, 12, rolling_fr-1, 22, f'Form Run {x[0]}', greyt)
                        start_row = rolling_fr+1
                        write_headers(rolling_fr,12,headers,red_header)
                        dp_plan.write_row(start_row,12,x,centred_box)
                    fri_run = []
                    fri_run.append(x)
                    start_row += 1
                    
                elif x[0] == nurseryruns[row-3][0]:
                    if x[2] != nurseryruns[row-3][2]:
                        if not x[0].endswith('A'):
                            start_row = rolling_row+1
                            write_headers(rolling_row,12,headers,red_header)
                            dp_plan.write_row(start_row,12,x,centred_box)
                        
                        elif x[0].endswith('A'):
                            dp_plan.merge_range(rolling_fr-1, 12, rolling_fr-1, 22, f'Form Run {x[0]}', greyt)
                            start_row = rolling_fr+1
                            write_headers(rolling_fr,12,headers,red_header)
                            dp_plan.write_row(start_row,12,x,centred_box)
                        fri_run = []
                        fri_run.append(x)
                        start_row += 1
                    else:
                        fri_run.append(x)
                        dp_plan.write_row(start_row,12,x,centred_box)
                        start_row += 1
                    
                if row == len(nurseryruns)+1:
                    # fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                    # box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                    
                    if x[0] == thurs_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                        km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                        box_thick(run_row,0,run_row+2,1,km_run)
                        
                    if x[0] == fri_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                        km_summ(run_row,3,'E',frrun_formula,red_subhead)
                        box_thick(run_row,3,run_row+2,4,km_run)
                        
                    if x[0] == sat_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                        km_summ(run_row,6,'H',sarun_formula,green_subhead)
                        box_thick(run_row,6,run_row+2,7,km_run)
                        
                    if x[0] == sun_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                        km_summ(run_row,9,'K',surun_formula,orange_subhead)
                        box_thick(run_row,9,run_row+2,10,km_run)
                    
                    # km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    # box_thick(run_row,0,run_row+2,1,km_run)
                    # km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    # box_thick(run_row,3,run_row+2,4,km_run)
                        
            elif x[2] == '_____S_':
                if row == 2:
                    sat_run = []
                    sat_run.append(x)
                    start_row = rolling_row+1
                    write_headers(rolling_row,24,headers,green_header)
                    dp_plan.write_row(start_row,24,x,centred_box)
                    start_row += 1
                    
                elif x[0] != nurseryruns[row-3][0]:
                    if not x[0].endswith('A'):
                        start_row = rolling_row+1
                        write_headers(rolling_row,24,headers,green_header)
                        dp_plan.write_row(start_row,24,x,centred_box)
                        
                    
                    elif x[0] == sat_run[-1][0]+'A':
                        dp_plan.merge_range(rolling_sa-1, 24, rolling_sa-1, 36, f'Form Run {x[0]}', greyt)
                        start_row = rolling_sa+1
                        write_headers(rolling_sa,24,headers,green_header)
                        dp_plan.write_row(start_row,24,x,centred_box)
                    sat_run = []
                    sat_run.append(x)
                    start_row += 1
                    
                elif x[0] == nurseryruns[row-3][0]:
                    if x[2] != nurseryruns[row-3][2]:
                        if not x[0].endswith('A'):
                            start_row = rolling_row+1
                            write_headers(rolling_row,24,headers,green_header)
                            dp_plan.write_row(start_row,24,x,centred_box)
                        
                        elif x[0].endswith('A'):
                            dp_plan.merge_range(rolling_sa-1, 24, rolling_sa-1, 36, f'Form Run {x[0]}', greyt)
                            start_row = rolling_sa+1
                            write_headers(rolling_sa,24,headers,green_header)
                            dp_plan.write_row(start_row,24,x,centred_box)
                        sat_run = []
                        sat_run.append(x)
                        start_row += 1
                    else:
                        sat_run.append(x)
                        dp_plan.write_row(start_row,24,x,centred_box)
                        start_row += 1
                        
                if row == len(nurseryruns)+1:
                    # fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                    # box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                    
                    if x[0] == thurs_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                        km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                        box_thick(run_row,0,run_row+2,1,km_run)
                        
                    if x[0] == fri_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                        km_summ(run_row,3,'E',frrun_formula,red_subhead)
                        box_thick(run_row,3,run_row+2,4,km_run)
                        
                    if x[0] == sat_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                        km_summ(run_row,6,'H',sarun_formula,green_subhead)
                        box_thick(run_row,6,run_row+2,7,km_run)
                        
                    if x[0] == sun_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                        km_summ(run_row,9,'K',surun_formula,orange_subhead)
                        box_thick(run_row,9,run_row+2,10,km_run)
                    
                    # km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    # km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    # km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    
                    # box_thick(run_row,0,run_row+2,1,km_run)
                    # box_thick(run_row,3,run_row+2,4,km_run)
                    # box_thick(run_row,6,run_row+2,7,km_run)
                        
            elif x[2] == '______S': 
                if row == 2:
                    sun_run = []
                    sun_run.append(x)
                    start_row = rolling_row+1
                    write_headers(rolling_row,36,headers,orange_header)
                    dp_plan.write_row(start_row,36,x,centred_box)
                    start_row += 1
                
                
                elif x[0] != nurseryruns[row-3][0]:
                    if not x[0].endswith('A'):
                        start_row = rolling_row+1
                        write_headers(rolling_row,36,headers,orange_header)
                        dp_plan.write_row(start_row,36,x,centred_box)
                        
                    
                    elif x[0] == sun_run[-1][0]+'A':
                        dp_plan.merge_range(rolling_su-1, 36, rolling_su-1, 48, f'Form Run {x[0]}', greyt)
                        start_row = rolling_su+1
                        write_headers(rolling_su,36,headers,orange_header)
                        dp_plan.write_row(start_row,36,x,centred_box)
                    sun_run = []
                    sun_run.append(x)
                    start_row += 1
                    
                elif x[0] == nurseryruns[row-3][0]:
                    if x[2] != nurseryruns[row-3][2]:
                        if not x[0].endswith('A'):
                            start_row = rolling_row+1
                            write_headers(rolling_row,36,headers,orange_header)
                            dp_plan.write_row(start_row,36,x,centred_box)
                        
                        elif x[0].endswith('A'):
                            dp_plan.merge_range(rolling_su-1, 36, rolling_su-1, 48, f'Form Run {x[0]}', greyt)
                            start_row = rolling_su+1
                            write_headers(rolling_su,36,headers,orange_header)
                            dp_plan.write_row(start_row,36,x,centred_box)
                        sun_run = []
                        sun_run.append(x)
                        start_row += 1
                    else:
                        sun_run.append(x)
                        dp_plan.write_row(start_row,36,x,centred_box)
                        start_row += 1
                        
                if row == len(nurseryruns)+1:
                    # fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                    # box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                    
                    if x[0] == thurs_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(thurs_run)),10,formula_th,dp_plan)
                        box_thick(rolling_row,0,(rolling_row+len(thurs_run)),10,dp_plan)
                        km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                        box_thick(run_row,0,run_row+2,1,km_run)
                        
                    if x[0] == fri_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(fri_run)),22,formula_fr,dp_plan)
                        box_thick(rolling_row,12,(rolling_row+len(fri_run)),22,dp_plan)
                        km_summ(run_row,3,'E',frrun_formula,red_subhead)
                        box_thick(run_row,3,run_row+2,4,km_run)
                        
                    if x[0] == sat_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sat_run)),34,formula_sa,dp_plan)
                        box_thick(rolling_row,24,(rolling_row+len(sat_run)),34,dp_plan)
                        km_summ(run_row,6,'H',sarun_formula,green_subhead)
                        box_thick(run_row,6,run_row+2,7,km_run)
                        
                    if x[0] == sun_run[0][0]:
                        fill_formula(rolling_row+1,(rolling_row+len(sun_run)),46,formula_su,dp_plan)
                        box_thick(rolling_row,36,(rolling_row+len(sun_run)),46,dp_plan)
                        km_summ(run_row,9,'K',surun_formula,orange_subhead)
                        box_thick(run_row,9,run_row+2,10,km_run)
                    
                    # km_summ(run_row,0,'B',thrun_formula,blue_subhead)
                    # km_summ(run_row,3,'E',frrun_formula,red_subhead)
                    # km_summ(run_row,6,'H',sarun_formula,green_subhead)
                    # km_summ(run_row,9,'K',surun_formula,orange_subhead)
                    
                    # box_thick(run_row,0,run_row+2,1,km_run)
                    # box_thick(run_row,3,run_row+2,4,km_run)
                    # box_thick(run_row,6,run_row+2,7,km_run)
                    # box_thick(run_row,9,run_row+2,10,km_run)
        
        #~~~~~~~~~~~~~~~~~#
        # KM by RUN Sheet #
        #~~~~~~~~~~~~~~~~~#
        km_run.set_zoom(115)
        km_run.set_default_row(15.75)
                   
        km_run.merge_range('A1:B1','Monday to Thursday',blue_title_s)
        km_run.merge_range('D1:E1','Friday',red_title_s)
        km_run.merge_range('G1:H1','Saturday',green_title_s)
        km_run.merge_range('J1:K1','Sunday',orange_title_s)
        km_run.merge_range('M1:N1','Weekly Totals',summ_title_s)
        km_run.merge_range('M7:N7','Revenue KMs',summ_title_s)
        km_run.merge_range('M13:N13','Non-Revenue KMs',summ_title_s)
        
        box_thick(0,0,0,1, km_run)
        box_thick(0,3,0,4, km_run)
        box_thick(0,6,0,7, km_run)
        box_thick(0,9,0,10, km_run)
        box_thick(0,12,0,13, km_run)
        box_thick(6,12,6,13, km_run)
        box_thick(12,12,12,13, km_run)
        
        km_run.write('A2','Grand Total', blue_subhead)
        box_thick(0,0,1,1,km_run)
        km_run.write('D2','Grand Total', red_subhead)
        box_thick(0,3,1,4,km_run)
        km_run.write('G2','Grand Total', green_subhead)
        box_thick(0,6,1,7,km_run)
        km_run.write('J2','Grand Total', orange_subhead)
        box_thick(0,9,1,10,km_run)
        
        km_run.write('M2','Total', left_bold)
        km_run.write('M3','Revenue', left_bold)
        km_run.write('M4','Non-Revenue', left_bold)
        box_thick(0,12,3,13,km_run)
        
        km_run.write('M8','Monday to Thursday', blue_left)
        km_run.write('M9','Friday', red_left)
        km_run.write('M10','Saturday', green_left)
        km_run.write('M11','Sunday', orange_left)
        box_thick(6,12,10,13,km_run)
        
        km_run.write('M14','Monday to Thursday', blue_left)
        km_run.write('M15','Friday', red_left)
        km_run.write('M16','Saturday', green_left)
        km_run.write('M17','Sunday', orange_left)
        box_thick(12,12,16,13,km_run)
        
        km_run.write('A4','Run',blue_header)
        km_run.write('B4','Sum of Kms',blue_header)
        short_box_thick(3,0,1,km_run)
        km_run.write('D4','Run',red_header)
        km_run.write('E4','Sum of Kms',red_header)
        short_box_thick(3,3,4,km_run)
        km_run.write('G4','Run',green_header)
        km_run.write('H4','Sum of Kms',green_header)
        short_box_thick(3,6,7,km_run)
        km_run.write('J4','Run',orange_header)
        km_run.write('K4','Sum of Kms',orange_header)
        short_box_thick(3,9,10,km_run)
        
        km_run.set_row(0,24)
        km_run.set_row(1,28.5)
        km_run.set_column('M:M', 26.75)
        km_run.set_column('N:N', 15)
        
        # Setting long-standing formulas 
        km_run.write('N2','=N3+N4', right)
        km_run.write('N3','=4*N8+N9+N10+N11', right)
        km_run.write('N4','=4*N14+N15+N16+N17', right)
        km_run.write('N8','=SUMIF($A$6:$A$1000,"Revenue",$B$6:$B$1000)', right_bold)
        km_run.write('N9','=SUMIF($D$6:$D$1000,"Revenue",$E$6:$E$1000)', right_bold)
        km_run.write('N10','=SUMIF($G$6:$G$1000,"Revenue",$H$6:$H$1000)', right_bold)
        km_run.write('N11','=SUMIF($J$6:$J$1000,"Revenue",$K$6:$K$1000)', right_bold)
        km_run.write('N14','=SUMIF($A$6:$A$1000,"Non-revenue",$B$6:$B$1000)', right_bold)
        km_run.write('N15','=SUMIF($D$6:$D$1000,"Non-revenue",$E$6:$E$1000)', right_bold)
        km_run.write('N16','=SUMIF($G$6:$G$1000,"Non-revenue",$H$6:$H$1000)', right_bold)
        km_run.write('N17','=SUMIF($J$6:$J$1000,"Non-revenue",$K$6:$K$1000)', right_bold)
        
        #Grand Totals
        grand_ref = {
            'B':'B2',
            'E':'E2',
            'H':'H2',
            'K':'K2'
        }
        for column_letter, target_cell in grand_ref.items():
            grand_formula = f"=SUMPRODUCT((MOD(ROW({column_letter}5:{column_letter}1000)-5,4)=0)*{column_letter}5:{column_letter}1000)"
            km_run.write_formula(target_cell, grand_formula, right_box)
        
        # Setting column widths using lists of columns
        p1 = ['A:A','D:D', 'G:G', 'J:J']
        p2 = ['B:B','E:E', 'H:H', 'K:K']
        sp = ['C:C','F:F','I:I','L:L']
        for col in p1:
            km_run.set_column(col,15.76)
        for col in p2:
            km_run.set_column(col,17.12)
        for col in sp:
            km_run.set_column(col,6.89)

        #~~~~~~~~~~~~~~~~~~~~~#
        # Process Information #
        #~~~~~~~~~~~~~~~~~~~~~#
        # If the errors are acting strange, comment out this top if statement
        # if is_file_open(filename_xlsx):  # Check if the file is open
        #     messagebox.showerror("Error", "The workbook is already open. Please close it before proceeding.")
        #     return  # Exit the function if the file is open
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            messagebox.showinfo('','Process Done')
        if CreateWorkbook:
            workbook.close()
            print('Creating workbook')  
            if copyfile:
                shutil.copy(filename_xlsx, mypath) 
            else:
                if OpenWorkbook:
                    os.startfile(rf'{filename_xlsx}')
                    print('\nOpening workbook')  
        
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Create Error Log for Exceptions #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    except Exception as e: # without defining exceptions, a "try" command cannot be executed
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            messagebox.showinfo('', 'Please choose valid files. \n \nThis process requires an RSX and Excel output.')
            time.sleep(1)
            
            
#~~~~~~~~~~~~~~~~~~~~~~#
# Calling the Function #
#~~~~~~~~~~~~~~~~~~~~~~#
if __name__ == "__main__":
    rsxselecta = tk.Tk() # creates tkinter window
    rsxselecta.withdraw() # we don't want a full GUI, so keep the root window from appearing
    rsxselecta.lift() # brings to the front
    rsxselecta.attributes('-topmost', 1)
    rsxselecta.update() # updates tkinter process to ensure it is complete before requesting a file
    messagebox.showinfo('', 'Please choose your RSX.')
    path = askopenfilename(title="Select your RSX") # requests the user to select a file
    messagebox.showinfo('', 'Please choose your Train Characteristics file.')
    path_char = askopenfilename(title="Select your Train Characteristics file")
    
    rsxselecta.destroy() # destroys tkinter window and variables within it
    NGR_DPP(path,path_char) # runs the script
