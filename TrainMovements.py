import xlsxwriter
import re
import os
import sys
import time
import shutil
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import xml.etree.ElementTree as ET

# from tkinter import Tk
import tkinter as tk
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
# CreateWorkbook = True
# OpenWorkbook = True
# --------------------------------------------------------------------------------------------------- #



ampeak_srt = '06:00:00'
ampeak_end = '09:00:00'
pmpeak_srt = '15:30:00'
pmpeak_end = '18:30:00'


weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
xl_daycode_dict = {
        '64':'M______',
        '32':'_T_____',
        '16':'__W____',
        '8':'___T___',
        
        '4':'____F__',
        '2':'_____S_',
        '1':'______S'
        }

WEEK_ORDER = {
    'M______':0,
    '_T_____':1,
    '__W____':2,
    '___T___':3,
    '____F__':4,
    '_____S_':5,
    '______S':6
    }



### Column headers for workbook
headers_tm = ['Train','Day','Location','Mnemonic',
           'Location\nArrive\nPublic','Location\nArrive\nRaw','Location\nDepart\nPublic','Location\nDepart\nRaw',
           'Platform','Stop\nType','Location\nType','Track\nDirection','Direction',
           'Express\nPattern\nInbound','Express\nPattern\nOutbound','Line\nInbound','Line\nOutbound',
           'Origin\nStation','Destination\nStation','Origin\nStation\nDepart\nPublic',
           'Central\nArrive\nPublic','Central\nDepart\nPublic','Destination\nStation\nArrive\nPublic',
           'Peak','Peak\nShoulder','Car','Unit','Run','Seat\nCap','Stand\nCap','Design\nCap','Crush\nCap'
           ]
headers_tmfo = ['Train','Day','Location','Mnemonic',
           'Location\nArrive','Location\nArrive\nPublic','Location\nArrive\nRaw','Location\nDepart','Location\nDepart\nPublic','Location\nDepart\nRaw',
           'Platform','Stop\nType','Location\nType',
           'Track\nDirection',
           'Previous\nLocation','Previous\nRun\nTime','Previous\nRevenue\nLocation','Previous\nRevenue\nRun\nTime',
           'Next\nLocation','Next\nRun\nTime','Next\nRevenue\nLocation','Next\nRevenue\nRun\nTime',
           'Direction',
           'Express\nPattern\nInbound','Express\nPattern\nOutbound','Inbound\nOr\nOutbound\nOr\nCity','Line\nInbound','Line\nOutbound',
           'Origin','Origin\nDepart','Origin\nStation','Origin\nStation\nDepart','Origin\nStation\nDepart\nPublic',
           'Central\nArrive','Central\nArrive\nPublic','Central\nDepart','Central\nDepart\nPublic',
           'Destination','Destination\nArrive','Destination\nStation','Destination\nStation\nArrive','Destination\nStation\nArrive\nPublic',
           'Is\nShuttle','Station\nClosest\nTo\nCentral','Peak','Peak\nShoulder','Car','Unit','Run','Seat\nCap','Stand\nCap','Design\nCap','Crush\nCap',
           'Forms','Formed\nBy'
           ]


### Used to determine if a train has passed through a reveneue station without stopping
### This will then be factored into the 'pattern' output
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


        
        
        
        
    

        
        
        
        

def TTS_TM(path, mypath = None):

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
        
        filename_xlsx_tm = f'TrainMovements-{filename}.xlsx'
        workbook_tm = xlsxwriter.Workbook(filename_xlsx_tm)
        # # info = workbook.add_worksheet('Info')
        TM   = workbook_tm.add_worksheet('TrainMovement')
        
        
        filename_xlsx_tmfo = f'TrainMovements-{filename}-fulloutput.xlsx'
        workbook_tmfo = xlsxwriter.Workbook(filename_xlsx_tmfo)
        # info = workbook.add_worksheet('Info')
        TMFO   = workbook_tmfo.add_worksheet('TrainMovement')
        

        if __name__ != "__main__":
            workbooks = [workbook_tm,workbook_tmfo]
        else:
            count = 0
            workbooks = []

            def Add_Checkbox(var,wb):
                nonlocal count
                nonlocal workbooks
                if var.get() == 1:
                    workbooks.append(wb)
                    count += 1
                if var.get() == 0 and count > 0:
                    workbooks.remove(wb) 

            cb = tk.Tk()
            cb.title('Choose Reports to Archive')
            cb.geometry("250x100") # w x h (add 30 height for every box)
            
            var1  = tk.IntVar()
            var2  = tk.IntVar()
            
            def Add_TrainMovements():
                Add_Checkbox(var1,workbook_tm)
            
            def Add_TrainMovementsFull():
                Add_Checkbox(var2,workbook_tmfo)
                
            checkbox1 = tk.Checkbutton(cb, text='TrainMovements',               variable=var1, onvalue=1, offvalue=0, command=Add_TrainMovements)
            checkbox2 = tk.Checkbutton(cb, text='TrainMovements (Full Output)', variable=var2, onvalue=1, offvalue=0, command=Add_TrainMovementsFull)
            checkbox1.pack(anchor  = "w")
            checkbox2.pack(anchor  = "w")
            def close_window(): 
                cb.quit()
            tk.Button(cb,width=20, padx=5, pady=5, text='OK',command=close_window).pack()
            cb.mainloop()
            cb.withdraw()

        
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
    
        
        
       
        
        
        
        # excluded_locations = ['MNE']
        
        
        
        
        
        
        
        
        
        
        
        
        
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
            'Caboolture - Gympie North':  ('DKB','NRB','BPY','MYE','CAB','CAW','CAE','CEN','EMH','EMHS','BEB','GSS','BWH','LSH','MOH','EUD','PAL','WOB','WOBS','NBR','YAN','NHR','EUM','SSE','COO','PMQ','COZ','TRA','WOO','GMR','GYN'),
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
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        def stoptime_info(x):
            """ Return the arrival and deptarture times, input can either be the entry index or the entry itself """
            if type(x) == int:
                departure = entries[x].attrib['departure'] 
                stoptime = int(entries[x].attrib.get('stopTime',0))
            else:
                departure = x.attrib['departure'] 
                stoptime = int(x.attrib.get('stopTime',0))
            stoptime = 0 if stoptime == 1 else stoptime
            
            arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))
            
            if arrival[:6] == '1 days':
                arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
            else: arrival = arrival[7:]
            
            # arrival = timetrim(arrival)
            # departure = timetrim(departure)
    
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
        
        def zeroseconds(timestring):
            """ Format converter from hh:mm:ss to hh:mm:00 """
            
            timestring = timestring[:-2] + '00'
            
            return timestring
        
        
        
        
        
        
        
        
        
        
        
        
        ### Creates a list of trains in a run 
        ### Used in 'forms' and formed_by' calculations by pulling adjacent trains in the list
        run_dict = {}
        for train in root.iter('train'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            lineID = train.attrib['lineID']
            run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
            
            
            if not run_dict.get((run,WeekdayKey)):
                run_dict[(run,WeekdayKey)] = [tn]
            else:
                run_dict[(run,WeekdayKey)].append(tn)
        
        
        
        
        unassigned = []
        trainmov = []
        fulltrainmov = []
        collengths_tm   = [len(max(x.split(),key=len)) for x in headers_tm]
        collengths_tmfo = [len(max(x.split(),key=len)) for x in headers_tmfo]
        
        print('Parsing rsx')
        
        
        
        ### TQDM adds a progress bar while iterating through the rsx
        rsx = [train for train in root.iter('train') ]
        for train in tqdm(rsx,ncols=100,bar_format='{l_bar}{bar}|{n_fmt}/{total_fmt} {remaining}'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            origin = entries[0]
            destin = entries[-1]
            lineID = train.attrib['lineID']
            run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
            cars,unit   = origin.attrib['trainTypeId'].split('-',1)
            
            Empty = True if 'Empty' in cars else False
            
            seats =    '225' if cars == '3' else '450'
            standing = '375' if cars == '3' else '750'
            design =   '225' if cars == '3' else '450'
            crush =    '450' if cars == '3' else '900'
            
            
            sIDs = {x.attrib['stationID'] for x in entries}
            oID = origin.attrib['stationID']
            dID = destin.attrib['stationID']
            odep = origin.attrib['departure']
            ddep = destin.attrib['departure']
    
            
            patternentries = [x for x in entries if x.attrib['stationID'] not in non_revenue_stations]
            stoplist = [(x.attrib['stationID'],x.attrib['type']) for x in patternentries]
            # stations = [x.attrib['stationID'] for x in patternentries]
            stations = [x.attrib['stationID'] for x in entries]
            
            citystations = ['BHI','BRC','BNC','RS','NBY','EXH','CAM','MYJ','MNE','YNA','YN','RSWJ','ETF','EDJ','ETS']
            goesthrucity = set(citystations).intersection(set(sIDs))
            if goesthrucity:
                cityidx = [stations.index(x) if x in stations else '' for x in goesthrucity ]
                # cityidx.sort()
                
            else:
                ioc = 'Shuttle'#!!!
                # if tn == '1003' and WeekdayKey == '120':
                #     for s,station in enumerate(stations):
                #         print(s,station)
                #     print('\n')
                #     print(citystations)
                #     print(goesthrucity)
                #     print([stations.index(x) if x in stations else '' for x in goesthrucity ])
                #     print(cityidx,min(cityidx),max(cityidx))
            
            
            if Empty:
                service = 'empty'
                pattern = 'EDI = SPECIAL'
                
            else:
                
                service = 'revnu'
                    
                
    
                counter = []
                
                
                
                
        
                for i,x in enumerate(patternentries):
                    
                    
                    
                        
    
                    
                    
                    
                    
                    if x.attrib['type'] == 'pass':
                        counter.append(i)
                        
                        
                        # if x.attrib['stationID'] not in non_revenue_stations:
                        #     counter.append(i)
                            
                
        
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
                            else: 
                                vcbdarr = vcbdarr[7:]
                            break
                    
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
            
            
    
            
            li = lo = line #!!!
            
            epi = epo = pattern #!!!
            
            origin_loc = origin.attrib['stationName']
            destin_loc = destin.attrib['stationName']
            
            origin_dep = zeroseconds(stoptime_info(origin)[1]) 
            destin_arr = zeroseconds(stoptime_info(destin)[0]) 
            
            # rev_entries_only = [x for x in entries if x.attrib['stationID'] not in non_revenue_stations]
            
            origin_station = origin.attrib['stationName']
            destin_station = destin.attrib['stationName']
            
    
            origin_station_d  = zeroseconds(stoptime_info(origin)[1]) 
            destin_station_a  = zeroseconds(stoptime_info(destin)[0]) 
            
            origin_station_dp = timetrim(origin_station_d)
            destin_station_ap = timetrim(destin_station_a)
            
            
        
            
            if 'BNC' in stations:
                cbdID = 'BNC'
                cbdidx = stations.index(cbdID)
                cbdarr, cbddep = stoptime_info(cbdidx)
            else:
                if 'IPS' in stations and 'RSW' in stations:
                    cbdID = 'IPS'
                    cbdidx = stations.index(cbdID)
                    cbdarr, cbddep = stoptime_info(cbdidx)
            
            
            
            
            
            bnc_entries_only = [x for x in entries if x.attrib['stationID'] in ['RS','RTL']]
            ips_entries_only = [x for x in entries if x.attrib['stationID'] == 'IPS']
            
            is_shuttle = 'FALSE' if bnc_entries_only else 'TRUE'
            
            
            if bnc_entries_only:
                ca,cd = stoptime_info(bnc_entries_only[0])
            elif ips_entries_only:
                ca,cd = stoptime_info(ips_entries_only[0])
            else:
                ca = cd = vcbdarr
                
            if ca < ampeak_srt:
                peak = 'Pre-Peak'
            elif ampeak_srt <= ca < ampeak_end:
                peak = 'AM-Peak'
            elif cd < pmpeak_srt:
                peak = 'Inter-Peak'
            elif pmpeak_srt <= cd < pmpeak_end:
                peak = 'PM-Peak'
            else:
                peak = 'Post-Peak'
            
            ca  = zeroseconds(ca)
            cd  = zeroseconds(cd)
            cap = timetrim(ca)
            cdp = timetrim(cd)
            
            peak_sh = peak #!!    
            
            
            run_list = run_dict[(run,WeekdayKey)]
            run_idx  = run_list.index(tn)
    
            forms    = run_list[run_idx+1] if run_idx < len(run_list)-1 else ''
            formedby = run_list[run_idx-1] if run_idx > 0 else ''
            
            
            test = [x.attrib['stationID'] not in non_revenue_stations for x in entries]
            test2 = [x.attrib['stationID'] for x in entries]
            stoptimes = [stoptime_info(x) for x in entries]
            
            
                
            
            for i,entry in enumerate(entries):
                location = entry.attrib['stationName']
                mnemonic = entry.attrib['stationID']
                lar = stoptime_info(entry)[0] 
                la  = zeroseconds(lar)
                lap = timetrim(lar) 
                ldr = stoptime_info(entry)[1]
                ld  = zeroseconds(ldr)
                ldp = timetrim(ldr)
                platform = entry.attrib['trackID'][-1]
                stoptype = entry.attrib['type'].capitalize()
                stoptype = 'Empty_'+stoptype if Empty else stoptype
                locationtype = 'Non-Revenue' if mnemonic in non_revenue_stations else 'Station' 
                track = entry.attrib['trackID'][0]
                
                if goesthrucity:
                    
                    city = i in cityidx
                    inbound  =  i < min(cityidx)
                    outbound =  max(cityidx) < i
                    
                    
                    
                    if inbound:
                        ioc = 'Inbound'
                    elif outbound:
                        ioc = 'Outbound'
                    elif city:
                        ioc = 'City'
                        
                    # if tn == '1003' and WeekdayKey == '120':
                    #     print(i,location,ioc)
                # else:
                #     ioc = 'Shuttle'
                
                
                prevlocation = entries[i-1].attrib['stationID'] if i > 0 else ''
                nextlocation = entries[i+1].attrib['stationID'] if i < len(entries)-1 else ''
                
                prevrevlocation = ''
                for idx in reversed(range(test2.index(mnemonic))):
                    if test[idx]:
                        prevrevlocation = test2[idx]
                        break
                nextrevlocation = ''
                for idx in range(test2.index(mnemonic)+1,len(test2)):
                    if test[idx]:
                        nextrevlocation = test2[idx]
                        break
                
                def runtime(s2):
                    s1 = mnemonic
                    if not s2:
                        return ''
                    
                    else:
                        
                        if stoptimes[test2.index(s1)][1] > stoptimes[test2.index(s2)][1]:
                            start_idx = test2.index(s2)
                            stop_idx = test2.index(s1)
                        else:
                            start_idx = test2.index(s1)
                            stop_idx = test2.index(s2)
                        
                        start_time = stoptime_info(entries[start_idx])[1]
                        end_time = stoptime_info(entries[stop_idx])[0]
                        
    
                        return str(int((pd.Timedelta(end_time) - pd.Timedelta(start_time)).total_seconds())) if start_time and end_time else ''
    
                prevruntime    = runtime(prevlocation) 
                nextruntime    = runtime(nextlocation) 
                prevrevruntime = runtime(prevrevlocation) 
                nextrevruntime = runtime(nextrevlocation) 
              
                osdp = timetrim(stoptime_info(origin)[1]) #!!!
                dsap = timetrim(stoptime_info(destin)[0]) #!!!
                    
                # direction 
                # epi
                # epo
                # ioc
                # li
                # lo
                # origin_loc
                # origin_dep
                # origin_station
                # origin_station_d
                # origin_station_dp
                # ca
                # cap
                # cd 
                # cdp
                # destin_loc
                # destin_arr
                # destin_station
                # destin_station_a
                # destin_station_ap
                # is_shuttle
                closest2central = '-'
                # peak 
                # peak_sh
                # cars 
                # unit 
                # run 
                # seats 
                # standing 
                # design 
                # crush 
                # forms
                # formedby
                
                
    
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
    
                
            
                if WeekdayKey == '120':
                    for d in ['M______','_T_____','__W____','___T___']:
                        
                        row = [tn,d,location,mnemonic,lap,lar,ldp,ldr,platform,stoptype,locationtype,track,direction,
                               epi,epo,li,lo,origin_station,destin_station,osdp,cap,cdp,dsap,peak,peak_sh,cars,unit,run,seats,standing,design,crush]
                        trainmov.append(row)
                        
                        for i,r in enumerate(row):
                            if len(r) > collengths_tm[i]:
                                collengths_tm[i] = len(r)
                        
                        
                        
                        
                        row = [tn,d,location,mnemonic,la,lap,lar,ld,ldp,ldr,platform,stoptype,locationtype,track,
                               prevlocation,prevruntime,prevrevlocation,prevrevruntime,nextlocation,nextruntime,nextrevlocation,nextrevruntime,
                               direction,epi,epo,ioc,li,lo,
                               origin_loc,origin_dep,origin_station,origin_station_d,origin_station_dp,ca,cap,cd,cdp,
                               destin_loc,destin_arr,destin_station,destin_station_a,destin_station_ap,is_shuttle,closest2central,
                               peak,peak_sh,cars,unit,run,seats,standing,design,crush,forms,formedby]
                        fulltrainmov.append(row)
                        
                        for i,r in enumerate(row):
                            if len(r) > collengths_tmfo[i]:
                                collengths_tmfo[i] = len(r)
                          
                        
                                
                                
                                
                        
                else:                
                    d = xl_daycode_dict.get(WeekdayKey)
                    
                    
                    
                    row = [tn,d,location,mnemonic,lap,lar,ldp,ldr,platform,stoptype,locationtype,track,direction,
                           epi,epo,li,lo,origin_station,destin_station,osdp,cap,cdp,dsap,peak,peak_sh,cars,unit,run,seats,standing,design,crush]
                    trainmov.append(row)
                    
                    
                    
                    
                    row = [tn,d,location,mnemonic,la,lap,lar,ld,ldp,ldr,platform,stoptype,locationtype,track,
                           prevlocation,prevruntime,prevrevlocation,prevrevruntime,nextlocation,nextruntime,nextrevlocation,nextrevruntime,
                           direction,epi,epo,ioc,li,lo,
                           origin_loc,origin_dep,origin_station,origin_station_d,origin_station_dp,ca,cap,cd,cdp,
                           destin_loc,destin_arr,destin_station,destin_station_a,destin_station_ap,is_shuttle,closest2central,
                           peak,peak_sh,cars,unit,run,seats,standing,design,crush,forms,formedby]
                    fulltrainmov.append(row)
            
            
                
                    
                
        print('\nWriting train movements to table')
        
        
        
        # test = [x[1] for x in trainmov]
        # for x in test:
        #     if x not in WEEK_ORDER:
        #         print(x)
        
        fulltrainmov.sort(key=lambda x: x[0])
        fulltrainmov.sort(key=lambda x: WEEK_ORDER[x[1]])
        
        
        trainmov.sort(key=lambda x: x[0])
        trainmov.sort(key=lambda x: WEEK_ORDER[x[1]])
        
        
        
        
        for workbook in workbooks:
            if workbook == workbook_tm:
                sheet = TM
                data  = trainmov
                headers = headers_tm
                collengths = collengths_tm
                label = 'Regular TMT'

                
            else:
                sheet = TMFO
                data  = fulltrainmov
                headers = headers_tmfo
                collengths = collengths_tmfo
                label = 'Full Output'


        
            format_data    = workbook.add_format({'align':'center','font_size':8})
            format_headers = workbook.add_format({'align':'center','font_size':8,'bold':True, 'text_wrap': True,'valign':'top'})
        
            sheet.set_row(0,57)
            
            progbar = tqdm(total=len(data),ncols=100,bar_format='{l_bar}{bar}|{n_fmt}/{total_fmt} {remaining}',desc=label)
        
        
            sheet.write_row(0,0,headers,format_headers)
            for i,cols in enumerate(data,1):
                sheet.write_row(i,0,cols,format_data)
                
                progbar.update(1)
        
                
            progbar.close()
            
            for col,length in enumerate(collengths):
                sheet.set_column(col,col,length)
                
            sheet.activate()
            sheet.autofilter('A1:BC300000')
        
            
        for workbook in workbooks:
            filename_xlsx = filename_xlsx_tm if workbook == workbook_tm else filename_xlsx_tmfo
        
            
        
            
        
            
            if CreateWorkbook:
                print('\nCreating workbook') 
                workbook.close()
                if copyfile:
                    shutil.copy(filename_xlsx, mypath) 
                else:
                    if OpenWorkbook:
                        print('\nOpening workbook')  
                        os.startfile(rf'{filename_xlsx}')
                    
        
        
        # if CreateWorkbook:
        #     print('\nCreating workbook')  
        #     workbook.close()
        #     if OpenWorkbook and __name__ == "__main__":
        #         os.startfile(rf'{filename_xlsx}')
        #         print('\nOpening workbook')   
        #     else:
        #         if copyfile:
        #             shutil.copy(filename_xlsx, mypath) 
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('Train Movements Table (Full Output)','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    rsxselecta = tk.Tk()
    rsxselecta.withdraw() # we don't want a full GUI, so keep the root window from appearing
    rsxselecta.update()
    path = askopenfilename() 
    rsxselecta.destroy()
    TTS_TM(path)