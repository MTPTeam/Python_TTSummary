import math
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
import sys
import time
import shutil  

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

import traceback
import logging





### CreateFile toggles whether text files are generated on running the script
### ProcessDoneMessagebox toggles whether a dialogue box is created after script finishes running
###  - adds a 15 second pause if script errors

### "= False" line can be left on permanently to facilitate easy toggling
### "= True" lines must be turned on when uploading files to the taipan script library
# --------------------------------------------------------------------------------------------------- #
CreateFile = ProcessDoneMessagebox = hastuscopyfile = False
ProcessDoneMessagebox = True
CreateFile = True 


hastuscopyfile = True if os.path.basename(__file__) == 'HASTUS_Converter - Copy.py' else False
# --------------------------------------------------------------------------------------------------- #





### Dictionary used to title reports for each daycode
daycode_dict = {'120':'muwt','4':'f','2':'a','1':'s'}

### Dictionary used for printouts when running the report
weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}

### Do not want these entries included at all in the HASTUSExport
entries_to_exclude = ['RSWJ','YNA','RSF',
                      'ZZZTJN','SIG9A','SIG10D',
                      'TNYBCHJ','YLYJ','STP','NTP',
                      'BHNJ','LBR','MEJ','SLYJ','MNYE',
                      'BWJ','BEJ','ORMJ','CYJ','FRK']

### Some stations will have a double entry if dwelling at the station for long enough, one for arrive and one for depart
### Stations or locations in this list should only have a single entry regardless of dwell time otherwise it causes errors in the HASTUS Importer
excludedforloadreasons = ['SGE']

### Most locations will be output as stationID+platform
### Locations in this list will skip that step and just use their associated value given in the dictionary below
HASTUS_stableconverter = {
    'BNHS':'BNH_S',
    'BQYS':'BQY_S',
    'EMHS':'EMH_S',
    'IPSS':'IPS_S',
    'KPRS':'KPR_S',
    'PETS':'PET_S',
    'RDKS':'RDK_S',
    'ROBS':'ROB_S',
    'WOBS':'WOB_S',
    'ETS':'ETS_S',
    'ETF':'ETF_S',
    'ETB':'ETB_S',
    'CAE':'CAB_S',
    'CAW':'CAB_S',
    'YN':'MNS_S',
    'MNS':'MNS_S',
    'MWS':'MWS_S',
    'WFE':'WFE_S', #'WUL_S' 
    'WFW':'WFW_S',
    'VYST':'VYT3',
    'RKET':'RKY4',
    'MES':'MES_S',
    'MNS':'MNS_S',
    'ORMS':'ORM_S',
    # 'CPM':'CPM_S', # moved logic to line 840-ish. CPM_S only used for stablers.
    # 'FEE':'WFE_S', # 31/07 now referenced as FEE2, with FWE1 on the west
    'BWHS': 'BWH_S',
    # '':'',
    # '':'',
    # '':'',
    # '':'',
    }






















def TTS_H(path, mypath = None):
    
    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None
    
    try:
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        start_time = time.time()
        
        
        if __name__ == "__main__":
            print(filename,'\n')
        
        
        if hastuscopyfile:
            myhastuspath = '//Cptprdfps001/ServicePlan/SMTP/02 PROJECTS/WPy64-3740/_HASTUS_Repository/'
            refnum_list = [int(x) for x in next(os.walk(myhastuspath))[1]]
            new_refnum = str(      (max(refnum_list) if refnum_list else 11110) + 1     )
            myhastuspath += new_refnum
            
            if not os.path.exists(myhastuspath):
                    os.makedirs(myhastuspath)
                     
    
            print('New Timetable Reference Number Created')
            print('———————————————————————————————————————————————————————————————————————————————')
            print(myhastuspath)
            print('———————————————————————————————————————————————————————————————————————————————\n')
        
        
    
        
        
        
        
        
        
        
        
      
        tree = ET.parse(filename)
        root = tree.getroot()
        
        filename = filename[:-4]
        
        
        
        
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        ### d_list        tracks the days present in the rsx
        ### runs          creates a list of every train_number in each run for a certain day of operation
        ### oID_dID_dict  creates a list showing origin and destination station+platform pairs for each trip in a run
        ###                - used to locate instances where a train will turnback at a signal and start the 
        ###                  connecting trip at a different platform to the one it terminated the last trip at
        ###                - EDJ/SGE_dest/orig lists will store the train numbers and the day to add an 
        ###                  appropriate signal entry in to that train later when writing the HASTUSExport 
        d_list = []
        runs   = {}
        oID_dID_dict = {}
        trains = [x for x in root.iter('train') if ('DEPT' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'])]
        # trains = [x for x in root.iter('train') ]
        for train in trains:
            tn         = train.attrib['number']
            run        = train.attrib['lineID'].split('~',1)[1][1:] if '~' in train.attrib['lineID'] else train.attrib['lineID']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries    = [x for x in train.iter('entry')]
            origin     = entries[0].attrib
            destin     = entries[-1].attrib
            oID        = origin['stationID']
            dID        = destin['stationID']
            
            otrack     = origin['trackID'].split('-')[-1]
            dtrack     = destin['trackID'].split('-')[-1]
            loID       = oID + otrack
            ldID       = dID + dtrack
            
            
            if '-' not in run:
                if (run[0] == "E" and run[1].isnumeric()):
                    if run[-1] == 'A':
                        run_ = 'E'
                        for x in run[1:]:
                            if x.isnumeric():
                                run_ += x
                        run_ += '-'   
                        for x in run[1:]:
                            if x.isalpha():
                                run_ += x
                        run = run_
                        
                elif (len(run) >= 3 and run[2] == "E" and run[0].isnumeric()):
                    run_ = ''
                    if run[-1] == 'A':
                        
                        for x in run[0:]:
                            if x.isnumeric():
                                run_ += x
                        run_ += 'E'
                        run_ += '-'   
                        for x in run[3:]:
                            if x.isalpha():
                                run_ += x
                        run = run_
                    
                elif (run[0].isalpha() and run[-1] == '1'):
                    run_ = ''
                    for x in run:
                        if x.isalpha():
                            run_ += x
                    run_ += '-'   
                    for x in run:
                        if x.isnumeric():
                            run_ += x
                    run = run_
                    
                elif (run[0].isnumeric() and run[-1] == 'A'):
                    run_ = ''
                    for x in run:
                        if x.isnumeric():
                            run_ += x
                    run_ += '-'   
                    for x in run:
                        if x.isalpha():
                            run_ += x
                    run = run_
                    
            
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
                
            if not runs.get((run,WeekdayKey)):
                runs[(run,WeekdayKey)] = [tn]
                oID_dID_dict[(run,WeekdayKey)] = [(loID,ldID)]
            else:
                runs[(run,WeekdayKey)].append(tn)
                oID_dID_dict[(run,WeekdayKey)].append((loID,ldID))  
                
        EDJ_dest_list = []
        EDJ_orig_list = []
        SGE_dest_list = []
        SGE_orig_list = []
        for k,v in oID_dID_dict.items():
            for i,x in enumerate(v):
    
                if i>0:
                    if x[0] != v[i-1][1] and x[0] in ['EGJ1','EGJ2'] and v[i-1][1] in ['EGJ1','EGJ2']:
                        EDJ_dest_list.append((runs[k][i-1],k[1]))
                        EDJ_orig_list.append((runs[k][i],k[1]))
                        
                    if x[0] != v[i-1][1] and x[0] in ['SGE1','SGE2'] and v[i-1][1] in ['SGE1','SGE2']:
                        SGE_dest_list.append((runs[k][i-1],k[1]))
                        SGE_orig_list.append((runs[k][i],k[1]))
         
    
        SORT_ORDER_WEEK = ['1','2','4','120']
        d_list.sort(key=SORT_ORDER_WEEK.index)
        
                        
                        
                        
                        
                        
                        
                        
                        
                        
        
                    
        
    
              
                
        
        
        
        ### uniquestations_dict, network_vrt_dict and virtual run time (vrt) dictionaries for each line are used to determine direction (Up or Down)
        ### Originally created for the Working Timetables, selects line if train passes through a location that is unique to a line
        ### If the associated vrt integer for that line is increasing → outbound else inbound, can determine direction from that
        ### Extra logic needed for Inner city trains that have no obvious line
        ### The most error-prone function of the exporter, direction is regularly an issue
        ### Might need new method for direction selection (line irrelevant in this report)
        vrt_2Beenleigh = {
			'ORMS':	   (31, 4010),
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
            'GYN':     (41, 10613),
            'GMR':     (40, 9187),
            'WOO':     (39, 8811),
            'TRA':     (38, 8393),
            'COZ':     (37, 8163),
            'PMQ':     (36, 7673),
            'COO':     (35, 7223),
            'SSE':     (34, 6978),
            'EUM':     (33, 6893),
            'NHR':     (32, 4300),
            'YAN':     (31, 6503),
            'NBR':     (30, 7000), 
            'WOB':     (29, 5693),
            'WOBS':    (28, 5363),
            'PAL':     (27, 5483),
            'EUD':     (26, 5153),
            'MOH':     (25, 4763),
            'LSH':     (24, 4433),
            'BWH':     (23, 4163),
			'BWHS':    (22, 4163),
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
            
            'RDKS':    (18, 1960),
            'RDK':     (17, 1760),
            
            'GDQ':     (16, 1588),
            'GAI':     (15, 1464),
            'WAC':     (14, 1366),
            'DAR':     (13, 1475),
            'OXL':     (12, 993),
            # 'TNY':     (11, 600),
            # 'MBN':     (10, 500),
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
            'MNS':     (7,   1024),
            'YN':      (6,   1024 ),
            'YNA':     (5,   649 ),
            'MNE':     (4,   544 ),
            'BHI':     (3,   324 ),
            # 'BRC':     (2,   264 ),
            # 'BNC':     (1,   140 ),
            
            # 'RS':      (0,   0 ),
            # 'RSWJ':    (-1,  -60),
            # 'SBE':     (-1, -226 ),
            'SBA':     (-2, -316 ),
            
    
            'PKR':     (-4, -447 ),
            }
        
        vrt_2Milton = {
            'MES':      (7,1000), 
            'ETS':      (6,800),
            'CAM':      (5,680),
            'EXH':      (4,560),
            'NBY':      (3,410),
            'RSF':      (2,170),
            'RSWJ':     (1,140),
            'MTZ':      (0,0),
            'MBN':      (-1,-340),
            'TNY':      (-2,-350),
            'DUP':      (-3,-400),
            'PKR':      (-4,-450),
            }
        
        network_vrt_dict = {
            'Beenleigh':                  vrt_2Beenleigh,
            'Caboolture - Gympie North':  vrt_2GympieNth,
            'Cleveland':                  vrt_2Cleveland,
            'Doomben':                    vrt_2Doomben,
            'Ferny Grove':                vrt_2FernyGrove,
            'Varsity Lakes - Airport':    vrt_2VarsityLs,   
            'Springfield':                vrt_2Springfield,
            'Ipswich - Rosewood':         vrt_2Rosewood,
            'Redcliffe':                  vrt_2KippaRing,
            'Shorncliffe':                vrt_2Shorncliffe,
            'Inner City':                 vrt_2InnerCity,  
            'Normanby':                   vrt_2Milton,
            
            
            }
        
        uniquestations_dict = {
            'Beenleigh':                  ('BNHS','BNT','HVW','EDL','BTI','KGT','WOI','TDP','KRY','FTG','RUC','SYK','BQO','CEP','SLY','RKET','RKE','MQK','CPM','ORMS'), # 'TNY', 'MBN','YLY','YRG','FFI','DUP'
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','BWHS','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN'),
            'Cleveland':                  ('BRD','CRO','NPR','MGS','CNQ','MJE','HMM','LDM','LJM','WYH','WNM','WNC','MNY','LOT','TNS','BDE','WPT','ORO','CVN'),
            'Doomben':                    ('CYF','HDR','ACO','DBN'),
            'Ferny Grove':                ('WID','WLQ','NWM','ADY','EGG','GAO','MHQ','OXP','GOQ','KEP','FYG'),
            'Varsity Lakes - Airport':    ('ORM','CXM','HLN','NRG','ROB','ROBS','VYS','VYST','BIT','BDT'),
            'Springfield':                ('RHD','SFD','SFC'),
            'Ipswich - Rosewood':         ('WAC','GAI','GDQ','RDK','RDKS','RVV','DIR','EBV','BDX','BOV','EIP','IPS','IPSS','THS','FEE','WFE','WUL','KRA','WFW','FWE','WOQ','TAO','YLE','RSW'), #'MBN','TNY',
            'Redcliffe':                  ('KGR','MRD','MGH','MGE','RWL','KPR','KPRS'),
            'Shorncliffe':                ('BHA','BQY','BQYS','NUD','BZL','NBD','DEG','SGE','SHC'),
            'Inner City':                 ('BHI','BRC','BNC'),
            'Normanby':                   ('MES','ETS','CAM','EXH','NBY','RSF','MTZ'), #,'RSWJ'
            }
        
        
        
        
        
        
        def create_textfile(weekdaykey):
            """ Creates a HASTUS Export textfile for a single day of operations """
            
            def timetrim(timestring):
                """ Format converter from hh:mm:ss to [h]:mm """
                
                if type(timestring) == list:
                    timestring = timestring[0]
                    
                if timestring is None or timestring.isalpha() or ':' not in timestring:
                    pass
                # elif timestring[0] == '0':
                #     timestring = timestring[1:-3]
                else: timestring = timestring[:-3]
                return timestring
            
            def stoptime_info(n): 
                """ Returns the arrival and departure times for the nth stop in a trip """
                
                departure = entries[n].attrib['departure'] 
                
                stoptime = int(entries[n].attrib.get('stopTime',0))
                if stoptime == 1:
                    stoptime = 0
                    
                arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))  
                if arrival[:6] == '1 days':
                    arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
                else: arrival = arrival[7:]
                
                arrival = timetrim(arrival)
                departure = timetrim(departure)
    
                return (arrival,departure)
            
            
            
            
        
            ### day_trains filters out departmentals and slices the rsx by day, creates a generator function to loop through
            ### unassigned collates all trips where the logic fails and the line the train is running on cannot be determined
            ### run_dict stores data for all runs, for each trip in run will save train_number,revenue_type,direction and a breakdown_of_stops
            ###  - for each location the trip passes through, breakdown_of_stops records station+platform, arrival time and whether the train stops or not
            ###  - if the trains stops and dwells for more than 60seconds, a second entry with departure time for that location is added as well
            run_dict   = {}
            unassigned = []
            day_trains = (x for x in root.iter('train') if (x[0][0][0].attrib['weekdayKey'] == weekdaykey) and ('DEPT' not in [y for y in x.iter('entry')][0].attrib['trainTypeId']) )
            for train in day_trains:
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                tn         = train.attrib['number']
                entries    = [x for x in train.iter('entry')]
                origin     = entries[0].attrib
                destin     = entries[-1].attrib
                
                sIDs       = {x.attrib['stationID'] for x in entries}
                sIDs_list  = [x.attrib['stationID'] for x in entries]
                unit       = origin['trainTypeId'].split('-',1)[1]
                # if unit == 'IMU100':
                #     unit == 'IMU'
                # elif unit == 'HYBRID':
                #     unit == 'NGRE'
                # else:
                #     unit == unit
                unit       = 'IMU' if unit == 'IMU100' else unit
                run        = train.attrib['lineID'].split('~',1)[1][1:] if '~' in train.attrib['lineID'] else train.attrib['lineID']
    
                
                if '-' not in run:
                    if (run[0] == "E" and run[1].isnumeric()):
                        if run[-1] == 'A':
                            run_ = 'E'
                            for x in run[1:]:
                                if x.isnumeric():
                                    run_ += x
                            run_ += '-'   
                            for x in run[1:]:
                                if x.isalpha():
                                    run_ += x
                            run = run_
                            
                    elif (len(run) >= 3 and run[2] == "E" and run[0].isnumeric()):
                        run_ = ''
                        if run[-1] == 'A':
                            
                            for x in run[0:]:
                                if x.isnumeric():
                                    run_ += x
                            run_ += 'E'
                            run_ += '-'   
                            for x in run[3:]:
                                if x.isalpha():
                                    run_ += x
                            run = run_
                        
                    elif (run[0].isalpha() and run[-1] == '1'):
                        run_ = ''
                        for x in run:
                            if x.isalpha():
                                run_ += x
                        run_ += '-'   
                        for x in run:
                            if x.isnumeric():
                                run_ += x
                        run = run_
                        
                    elif (run[0].isnumeric() and run[-1] == 'A'):
                        run_ = ''
                        for x in run:
                            if x.isnumeric():
                                run_ += x
                        run_ += '-'   
                        for x in run:
                            if x.isalpha():
                                run_ += x
                        run = run_
                
                oID        = origin['stationID']
                dID        = destin['stationID']
                odep       = origin['departure']
                ddep       = destin['departure']
                
                traintype  = origin['trainTypeId']
                cars       = re.findall(r'\d+', traintype)[0]
                
                
                
                ### Some adjustments to the location+platform entry are made for special cases
                ### Using the first two stations to determine direction, with a special process for: 
                ###  - Redbank→Ipswich trains
                ###  - Trips ending at Park Road via the Tennyson loop
                ### In these special cases, the logic uses the last two stations instead to bypass the error of a starting in one direction and finishing in another
                ### Outbound and Inbound is then converted to Up or Down depending on the line
                ### May need a revamp in future, method ported from WorkingTimetable (line not needed in final report, just a means to an end)
                
                ### For each unique run, run_dict will organise the data into a list which includes a list for each trip in that run
                ### Within each trip lists are individual lists for each location the train passes through 
                ### If no errors, we now have enough information to write the HASTUS Export textfile
                count = 0
                stations = []
                for n,x in enumerate(entries):
                    
                    sID       = x.attrib['stationID']
                    trackID   = x.attrib['trackID'].split('-')
                    trackcode = trackID[0]
                    track     = trackID[1]
                    stoptype  = x.attrib['type']
                    
                    
                    if sID in HASTUS_stableconverter:
                        lsID = HASTUS_stableconverter.get(sID)
                    else:
                        if sID == 'RS':
                            track = '0' + track
    
                        firstinrun = runs.get((run,WeekdayKey))[0]
                        lastinrun  = runs.get((run,WeekdayKey))[-1]
                        
                        if tn == firstinrun and sID == 'MNY' and n == 0:
                            lsID = 'MNY_S'
                        elif tn == lastinrun and sID == 'MNY' and n == len(entries) - 1:
                            lsID = 'MNY_S'
                            
                        if tn == firstinrun and sID == 'CPM' and n == 0:
                            lsID = 'CPM_S'
                        elif tn == lastinrun and sID == 'CPM' and n == len(entries) - 1:
                            lsID = 'CPM_S'
                            
                        elif tn == firstinrun and sID == 'CEN' and n == 0:
                            lsID = 'CAB_S'
    
                        elif tn == lastinrun and sID == 'CEN' and n == len(entries) - 1:
                            lsID = 'CAB_S' 
    
                        
                        else:
                            lsID = sID + track
                    
                    if trackcode != 'Z':
                        (arr,dep) = stoptime_info(n)
                        
                        if sID in HASTUS_stableconverter:
                            thrutype = '0'
                        else:
                            thrutype = '0' if stoptype == 'stop' else '1'
                        
                        
                        if stoptype == 'stop':
                            stoptime = int(x.attrib['stopTime'])
                        else:
                            stoptime = 0
                            
                        
                        if sID in entries_to_exclude:
                            pass
                        else:
                            if stoptime >= 60 and sID not in excludedforloadreasons:
                                stations.append([lsID,arr,'0',thrutype])
                                stations.append([lsID,dep,'1',thrutype])
                            else:
                                stations.append([lsID,dep,'0',thrutype])
                                
                                
                reversedentries = reversed(entries)
                
                
                empt = '3' if 'Empty' in origin['trainTypeId'] else '0'
    
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
                        
                            
                        if oID == 'RDKS' and 'IPS' in sIDs_list:
                            increasing = True
                            decreasing = False
                            break
                            
                        
                        elif dID == 'PKR' and 'MBN' in sIDs_list:
                            for n,entry in enumerate(reversed(entries)):
    
                                if entry.attrib['stationID'] in vrt:
                                    firstonline = entry.attrib['stationID']                  
                                    first_sIDinVRT = n
                                    break
                            
                            for n,entry in enumerate(reversed(entries)):
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
                    
                
                ### 13 is Down
                ### 12 is Up                
                elif line in ['Beenleigh','Cleveland','Varsity Lakes - Airport','Ipswich - Rosewood','Springfield']:
                    drct = '13' if decreasing else '12'
                elif line in ['Caboolture - Gympie North','Doomben','Ferny Grove','Inner City','Redcliffe','Shorncliffe','Normanby']:
                    drct = '12' if decreasing else '13'
                    
                    
                # drcttest = 'Up' if drct == '12' else 'Down'
                # if tn in ['EW03','EU06']:
                #     print(f'{tn}: {drcttest} ({oID} to {dID})')
      
                    
      
    # Useful for checking errors in direction
    # =============================================================================
    #             if 'PKR' in [oID,dID] and WeekdayKey == '120':
    #                 print('\n\n\n')
    #                 print(tn)
    #                 print(line)
    #                 print()
    #                 print(sIDs_list)
    #                 print()
    #                 print([x.get('stationID') for x in reversedentries])
    #                 print()
    #                 print(firstonline,secondonline)
    #                 print(a,b)
    #                 print('↑:',increasing)
    #                 print('↓:',decreasing)
    #                 print(drct)
    #                 print('\n\n\n')
    #             
    #                 
    #             if WeekdayKey == '120' and tn in ['2W31','AB49','AD12','EP29','EQ01','EW35']:
    #             if WeekdayKey == '120' and tn in ['DM21','1M19','2614','2626','A512','A508']:
    #                 print(tn,oID,dID,line, drct)
    #             
    #             if WeekdayKey == '4' and tn in ['2W31','AB49','AD12','EP29','EQ01','EW35']:
    #             if WeekdayKey == '4' and tn in ['2508','2614','2626','1M19','A512','DM21']:
    #                 print(tn,oID,dID,line, drct)
    #                 
    #             if WeekdayKey == '1' and tn in ['AD04']:
    #                 print(tn,oID,dID,line, drct)
    #                 
    #             if oID == 'RDK' and dID == 'RDKS':
    #                 print('!',tn,oID,dID,line, drct)
    #             if oID == 'RDKS' and dID == 'RDK':
    #                 print('!',tn,oID,dID,line, drct)
    #                 
    #                 
    #                 if line == 'Normanby':
    #                     print(tn)
    #                     print('-------------')
    #                     for x in sIDs_list:
    #                         print(x)
    #                     print()
    #             
    #             if tn in ['2Q17']:
    #             # if oID == 'EXH' and dID == 'MES':
    #             if tn in ['AE27','TE27']:
    #                 print('\n\n\n')
    #                 # print('HASSSTUS')
    #                 print(tn)
    #                 print(drct)
    #                 print(line)
    #                 print(oID,dID)
    #                 print(firstonline,secondonline)
    #                 print(sIDs_list)
    #                 # print(a,b)
    #                 # print(WeekdayKey)
    #                 print('\n\n\n')
    # 
    #                 
    #             
    #             Quick check to see if the train number matches the direction
    #             if tn[-1] in ['1','3','5','7','9'] and drct == '12':
    #                 print(f'{tn} ({oID} to {dID}) is a Downward train number')
    #                 print(f'{line} - {firstonline} then {secondonline}\n')
    #                 
    #             if tn[-1] in ['0','2','4','6','8'] and drct == '13':
    #                 print(f'{tn} ({oID} to {dID}) is an Upward train number')
    #                 print(f'{line} - {firstonline} then {secondonline}\n')
    # =============================================================================
                    
                
                
                
    
                tripinfo = [tn,empt,drct,stations]
                
                if not run_dict.get((run,WeekdayKey)):
                    run_dict[(run,WeekdayKey)] = [cars+unit,[tripinfo]]
                else:
                    run_dict[(run,WeekdayKey)][-1].append(tripinfo)  
            
    
            
            for x in unassigned:
                print(f'{x[0]} is unassigned and runs {x[1]} to {x[2]}')
                
            
            daycode = daycode_dict.get(weekdaykey)
            filename_txt = f'HASTUS_Import-{daycode}-{filename}.txt'
            l =  '|'
            nl = '\n'
            if CreateFile:
                # os.chdir('C:/Users/r913332/OneDrive - Queensland Rail/04 Project Python/06 Project RSX → HASTUS') 
                o = open(filename_txt, 'w')
                wl = o.writelines
                for linenum,(key,value) in enumerate(run_dict.items()):
                    run     = key[0]
                    wkdk    = key[1]
                    daycode = daycode_dict.get(wkdk)
                    unit    = value[0]
                    entries = value[1]
                    
    
                    if linenum == 0: 
                        wl(['block',l,run,l,unit,l,run])
                    else:
                        wl([nl,'block',l,run,l,unit,l,run])
                    
                    
                    for entry in entries:
                        tn        = entry[0]
                        empty     = entry[1]
                        direction = entry[2]
                        stations  = entry[3]
                        wl([nl,'trip',l,tn,l,tn,l,'QR',l,empty,l,direction,l,daycode,l,run,l,f'{run}_{tn}',l,'1'])
                        
                        
                        for station in stations:
                            sID  = station[0]
                            hhmm = station[1]
                            zero = station[2]
                            stop = station[3]
                            
                            
                            
                            
                            
                            
                            
                            hhmmss = hhmm + ':00'
                            stationtosignal = str(pd.Timedelta(hhmmss) + pd.Timedelta(seconds=60))
                            signaltostation = str(pd.Timedelta(hhmmss) - pd.Timedelta(seconds=60))
            
                            if stationtosignal[0] == '1':
                                stationtosignal = str(int(stationtosignal[7:9])+24) + stationtosignal[9:12]
                            else:
                                stationtosignal = stationtosignal[7:12]
                            if signaltostation[0] == '1':
                                signaltostation = str(int(signaltostation[7:9])+24) + signaltostation[9:12]
                            else:
                                signaltostation = signaltostation[7:12]
       
                                
                            
                            
                            
                            ### Input EJ28 Signal Turnback before the first station to avoid mismatched plaform errors
                            if station == stations[0]:
                                if (tn,wkdk) in EDJ_orig_list:
                                    wl([nl,'triptp',l,'EJ28',l,signaltostation,l,zero,l,stop,l,f'{run}_{tn}'])
                                    #time - 1 minute
                                    
                                if (tn,wkdk) in SGE_orig_list:
                                    wl([nl,'triptp',l,'SE10',l,signaltostation,l,zero,l,stop,l,f'{run}_{tn}'])
                                    #time - 1 minute
                                
                            
                            
                            
       
                            
                            ### Write the station
                            wl([nl,'triptp',l,sID,l,hhmm,l,zero,l,stop,l,f'{run}_{tn}'])
                            
                            
    
                            
    
                            
                            
                            ### Input EJ28 Signal Turnback after the last station to avoid mismatched plaform errors
                            if station == stations[-1]:
                                if (tn,wkdk) in EDJ_dest_list:
                                    wl([nl,'triptp',l,'EJ28',l,stationtosignal,l,zero,l,stop,l,f'{run}_{tn}'])
                                    #time + 1 minutes
                                    
                                if (tn,wkdk) in SGE_dest_list:
                                    wl([nl,'triptp',l,'SE10',l,stationtosignal,l,zero,l,stop,l,f'{run}_{tn}'])
                                    #time + 1 minutes
                   
                            
                   
                    
                   
                    
                   
                    
                o.close()
                print(f'All trains on {weekdaykey_dict.get(weekdaykey)} have been processed')
                # print('—————————————————————————————————————————————————————')
                print('\n\n')
                if hastuscopyfile:
                    shutil.copy(filename_txt, myhastuspath) 
                else: 
                    if copyfile:
                        shutil.copy(filename_txt, mypath) 
    
    
    
    
    
        ### Run the create_textfile function for every day present in the rsx
        for day in d_list:
            # print('—————————————————————————————————————————————————————')
            print(f'Processing trains on {weekdaykey_dict.get(day)}...', end='\r')
            create_textfile(day)
            
                
    
        
        
        
        
        
        
        
        if __name__ == "__main__":
            print(f'(runtime: {time.time()-start_time:.2f}seconds)')
    
    
    
    
        if hastuscopyfile:
            print('\n\nProcess done, files created and copies made')
            print('\n\nCopying rsx to folder...',end='\r')
            filename = filename + '.rsx'
            shutil.copy(filename, myhastuspath)  
            print('RSX copied                 ',end='\r')
        
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            from tkinter import messagebox
            messagebox.showinfo('HASTUS Converter','Process Done')
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_H(path)
