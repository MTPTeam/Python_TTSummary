import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import os
import re
import time
import sys

from tkinter import Tk
from tkinter.filedialog import askopenfilename


import traceback
import logging

ProcessDoneMessagebox = False
ProcessDoneMessagebox = True

# Features
#------------------------------------------------
# Runs that start or end at non-stabling locations
# Runs that change platforms either side of a connection
# Runs that have more than one unit type
# Runs that are missing connections
# Trains with non-standardised train numbers
# Trains with train numbers that don\'t line up with their unit types
# Trains with more than 1 unittype
# Trains with duplicate train numbers
# 
# ??? Less than 8min tb
# 
# 
# 
# 
#------------------------------------------------










weekdaykey_dict  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}


train_numbers_dict = {
    '1':'6-EMU',
    '2':'Empty_6-EMU',
    'A':'Empty_6-IMU100',
    'B':'Empty_3-IMU100',
    'C':'Empty_3-EMU',
    'D':'6-NGR',
    'E':'Empty_6-NGR',
    'J':'3-EMU',
    'T':'6-IMU100',
    'U':'3-IMU100',
    'H':'Empty_6-DEPT',
    'F':'6-REP',
    'G':'Empty_6-REP',
    'X':'6-NGRE',
    'W':'Empty_6-NGRE'
    }

stable_locations = ['WFE','WFW','IPSS','IPS','RDKS','ROBS','MNY','ORMS',
                    'BNHS','ETB','ETF','ETS','YN','MNS','MWS','CPM','PETS','KPRS',
                    'CAE','CAW','CAB','EMHS','BWHS','WOBS','NBR','GYN','BQYS','MES','FEE']


















try:
    
    
    
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    
    directory = '\\'.join(path.split('/')[0:-1])
    os.chdir(directory)
    filename = path.split('/')[-1]
    
    
  
    
    
    
    
    print(filename,'\n')
    
    tree = ET.parse(filename)
    root = tree.getroot()
    filename = filename[:-4]
    
    
    start_time = time.time()
    

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
        'RSWJ',
        'YNA',
        'RSF',
        'ZZZTJN',
        'SIG9A',
        'SIG10D',
        'TNYBCHJ',
        'YLYJ',
        'STP',
        'NTP',
        'BHNJ',
        'LBR',
        'MEJ',
        'SLYJ',
        'MNYE'
        
        'NHR', #North Arm
        'SSE', #Sunrise
        'WOO', #Woondum
        'GMR', #Glanmire
        
        'DUP', #Dutton Park
        'RKE', #Rocklea
        ]
    
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
        'Varsity Lakes - Airport':    ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT','MRC','HID','PPA'),
        'Ipswich':                    ('FWE','WFW','FEE','WFE','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS'),
        'Rosewood':                   ('THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
        'Ipswich - Rosewood':         ('MBN','TNY','WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'),
        'Redcliffe':                  ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
        'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
        'Springfield':                ('RHD','SFD','SFC'),
        'Inner City':                 ('BHI','BRC','BNC','PKR'), #RS
        'Normanby':                   ('ETS','CAM','EXH','NBY','RSF','RSWJ','MTZ')
        }
    
    
    
    
    
    
    nolineid = []
    for train in root.iter('train'):
        tn         = train.attrib['number']
        WeekdayKey = train[0][0][0].attrib['weekdayKey']
        
        try:
            run = train.attrib['lineID'].split('~',1)[1][1:] if '~' in train.attrib['lineID'] else train.attrib['lineID']
        except:
            nolineid.append([tn,WeekdayKey])
            # print(tn)
        
        
    if nolineid:
        print('Parsing error')
        for x in nolineid:
            print(f'Train {x[0]} on {weekdaykey_dict.get(x[1])} has no LineID attribute')
        sys.exit()
    
    
    
    
    test_unittype = []
    connections = {}
    oID_dID_dict = {}
    gen = (x for x in root.iter('train'))
    for train in gen:
        tn         = train.attrib['number']
        # print(tn)
        run        = train.attrib['lineID'].split('~',1)[1][1:] if '~' in train.attrib['lineID'] else train.attrib['lineID']
        WeekdayKey = train[0][0][0].attrib['weekdayKey']
        entries    = [x for x in train.iter('entry')]
        origin     = entries[0].attrib
        destin     = entries[-1].attrib
        unittype   = origin['trainTypeId']
        unit       = origin['trainTypeId'].split('-',1)[1]
        
        
        if unittype not in test_unittype:
            test_unittype.append(unittype)
        
        
        
        if not connections.get((run,WeekdayKey)):
            connections[(run,WeekdayKey)] = [tn]
         
        connection = [x.attrib['trainNumber'] for x in train.iter('connection')]
        if connection:
            connections[(run,WeekdayKey)].append(tn)
           

    

    dodgy_tns           = []
    wrong_tn            = []
    tn_doubles          = []
    multiunittrain      = []
    multiunitrun        = []
    mismatchedplatforms = []
    stablingissue       = []
    shortturnbacks      = []
    missingconnects     = []

    

    darr_dict        = {}
    run_dict         = {}
    run_dict_units   = {}
    oIDdID_dict      = {}
    runs_oIDdID_dict = {}
    direction_dict   = {}
    
    
    
    tn_list          = []
    
    
    originpass = []
    destinpass = []

    unassigned = []
    for train in root.iter('train'):
        tn         = train.attrib['number']
        run        = train.attrib['lineID'].split('~',1)[1][1:] if '~' in train.attrib['lineID'] else train.attrib['lineID']
        WeekdayKey = train[0][0][0].attrib['weekdayKey']
        day        = weekdaykey_dict.get(WeekdayKey)
        entries    = [x for x in train.iter('entry')]
        origin     = entries[0].attrib
        destin     = entries[-1].attrib
        unit       = origin['trainTypeId'].split('-',1)[1]
        unittype   = origin['trainTypeId']
        
        oID = origin['stationID']
        dID = destin['stationID']
        otrack = origin['trackID'][-1]
        dtrack = destin['trackID'][-1]
        loID = oID + otrack
        ldID = dID + dtrack
        
        odep = origin['departure']
        ddep = destin['departure']
        
        # stoptime = int(train[1][x].attrib.get('stopTime',0))
        stoptime = int(destin.get('stopTime','0'))
        darr = str(pd.Timedelta(ddep) - pd.Timedelta(seconds=stoptime))
        
        traintype = origin['trainTypeId']
        cars = int(re.findall(r'\d+', traintype)[0])
        
        
        
        
        sIDs = {x.attrib['stationID'] for x in train.iter('entry')}
        
        
        
        
        traintypeset = set([x.attrib['trainTypeId'] for x in train.iter('entry')])
        if len(traintypeset) > 1:
            traintypeset = ', '.join(traintypeset)
            multiunittrain.append(f'{tn} on {day} has more than 1 train type: {traintypeset}')
        
        traintype = [x.attrib['trainTypeId'] for x in train.iter('entry')][0]
        if 'Empty' not in traintype:
            stoptypes = [x.attrib['type'] for x in train.iter('entry') if x.attrib['stationID'] not in non_revenue_stations]
            
            origintype,destintype = stoptypes[0],stoptypes[-1]
            if origintype == 'pass':
                originpass.append(f' - First pass: {tn} on {weekdaykey_dict.get(day)} - ')
            if destintype == 'pass':
                destinpass.append(f' - Last pass:  {tn} on {weekdaykey_dict.get(day)} - ')
        
        
        
        
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
        
        
        oIDdID_dict[(tn,WeekdayKey)] = (oID,dID)
        
        day_tn = (tn,WeekdayKey)
        if day_tn in tn_list:
            tn_doubles.append(day_tn)
        tn_list.append(day_tn)
            
        
        tn_unittype = train_numbers_dict.get(tn[0])
        if tn_unittype != unittype:
            wrong_tn.append(f'Train Number {tn} on {day} indicates unit type is {tn_unittype} but is {unittype} instead')
        
        
        if not tn.isalnum() or len(tn)>4:
            dodgy_tns.append(tn)
            
            
            
            
        
            
    
            
        if not run_dict.get((run,WeekdayKey)):
            run_dict[(run,WeekdayKey)] = [tn]
            runs_oIDdID_dict[(run,WeekdayKey)] = [(loID,ldID)]
            run_dict_units[(run,WeekdayKey)] = [unit]
            darr_dict[(run,WeekdayKey)] = [(tn,darr)]
            direction_dict[(run,WeekdayKey)] = [direction]
            
        else:
            run_dict[(run,WeekdayKey)].append(tn)
            runs_oIDdID_dict[(run,WeekdayKey)].append((loID,ldID))
            
            
            if unit not in run_dict_units[(run,WeekdayKey)]:
                run_dict_units[(run,WeekdayKey)].append(unit)
            
            previous_tn   = darr_dict[(run,WeekdayKey)][-1][0]
            previous_darr = darr_dict[(run,WeekdayKey)][-1][-1]
            turnback = pd.Timedelta(odep) - pd.Timedelta(previous_darr)
            
            previous_direction = direction_dict[(run,WeekdayKey)][-1]
            
            if turnback < pd.Timedelta(minutes=8) and direction != previous_direction:
                tb_mins, tb_secs = map(int,str(turnback)[-5:].split(':'))
                spacer = " " if len(run)==2 else ''
                shortturnbacks.append(f'The turnback between {previous_tn} and {tn} in run {run} on {weekdaykey_dict.get(WeekdayKey)} is: {spacer}   {tb_mins}m {tb_secs}s')

            # for x in unassigned:
            #     print(f'{x[0]} is unassigned to a line and runs {x[1]} to {x[2]}, may affect direction')
            

            darr_dict[(run,WeekdayKey)].append((tn,darr))
            direction_dict[(run,WeekdayKey)].append(direction)
    

    
    if run_dict != connections:
        for k,v in run_dict.items():
            if v != connections.get(k):
                data = []
                data.append(f'Run {k[0]} on {weekdaykey_dict.get(k[1])}')
                data.append(f'Trips in run:    {v}')
                data.append(f'Connected trips: {connections.get(k)}\n')
                missingconnects.append('\n'.join(data))
    
    
    
    
    for k,v in run_dict_units.items():
        if len(v) > 1:
            run = k[0]
            day = weekdaykey_dict.get(k[1])
            units = ', '.join(v)
            multiunitrun.append(f'Run {run} on {day} has two unit types: {units}')
            # print(k,v)
    
    
    
    
    for k,v in run_dict.items():
        startofrun = oIDdID_dict.get((v[0],k[1]))[0]
        endofrun = oIDdID_dict.get((v[-1],k[1]))[-1]
    
        if startofrun not in stable_locations:
            stablingissue.append(f'Run {k[0]} on {weekdaykey_dict.get(k[1])} starts at {startofrun}')
        if endofrun not in stable_locations:
            stablingissue.append(f'Run {k[0]} on {weekdaykey_dict.get(k[1])} ends at {endofrun}')

    
    
    for k,v in runs_oIDdID_dict.items():

        for i,x in enumerate(v):
            if i==0:
                pass
            else:
                pltfm1 = v[i-1][1]
                pltfm2 = x[0]
                train1 = run_dict[k][i-1]
                train2 = run_dict[k][i]
                run    = k[0]
                day    = weekdaykey_dict.get(k[1])
                if pltfm1 != pltfm2 and run not in ('XA','XB','100','101'):
                    mismatchedplatforms.append(f'Run {run} on {day} has mismatched platforms between {train1} and {train2} - {pltfm1} then {pltfm2}')

       


       
        
    
    
    
    
    
    
    
    
    
    
    
    filename_txt = f'Errors-{filename}.txt'
    o = open(filename_txt, 'w')
    wl = o.writelines
    l =  '|'
    nl = '\n'
    
    def printwl(text):
        print(text)
        wl([text,nl])
        
        
        
    #Short turnbacks
    #Add direction #!!!
    # if shortturnbacks:
    #     print('\n\nTrains that have short turnbacks')
        
    #     for x in shortturnbacks:
    #         print(x)
    
    printwl('Taipan Error Checker')
    
    
    
    if stablingissue:
        printwl('Runs that start or end at non-stabling locations')
        for x in stablingissue:
            printwl(x)
            # print(type(x))
            # wl([x,nl])
            
    if originpass or destinpass:
        printwl('\n\nFirst station pass or last station pass through a revenue location')
        for x in originpass: printwl(x)
        for x in destinpass: printwl(x)
  
    
    if mismatchedplatforms:
        printwl('\n\nRuns that change platforms either side of a connection')
        for x in mismatchedplatforms:
            printwl(x)
            # print(type(x))
            # wl([x,nl])
    
    if multiunitrun:
        printwl('\n\nRuns that have more than one unit type')
        for x in multiunitrun:
            printwl(x)
            # wl([str(x),nl])
    
    if missingconnects:
        printwl('\n\nRuns that are missing connections')
        for x in missingconnects:
            printwl(x)
            # wl([str(x),nl])
    
    if dodgy_tns: 
        printwl('\n\nTrains with non-standardised train numbers')
        for x in dodgy_tns:
            printwl(x)
            # wl([str(x),nl])
            
    if wrong_tn:
        printwl('\n\nTrains with train numbers that don\'t line up with their unit types')
        for x in wrong_tn:
            printwl(x)
            # wl([str(x),nl])
    
    if multiunittrain: 
        printwl('\n\nTrains with more than 1 unittype') 
        for x in multiunittrain:
            printwl(x)
            # wl([str(x),nl])
    
    if tn_doubles: 
        printwl('\n\nTrains with duplicate train numbers')
        for tn,day in tn_doubles:
            printwl(f'Train with trainnumber {tn} already running on {weekdaykey_dict.get(day)}')
            # wl([f'Train with trainnumber {tn} already running on {weekdaykey_dict.get(day)}',nl])
    
    
    
    
    
    o.close
    
    
    
    
    
    
    
    print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
    
    if ProcessDoneMessagebox:
        from tkinter import messagebox
        messagebox.showinfo('Error Check and QA Process Done','Click OK to close python console')
        

except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)