import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import xlsxwriter
import time
import os
import sys
import shutil

import traceback
import logging


OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True

from taipan.constants.days import ID_TO_SHORT
from taipan.gui.base import open_file_crossplatform, show_info_safe, select_file

from PyQt6.QtWidgets import QApplication

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
    ('MJE-MNY','Bowen Hills','Cleveland'):'1541',
    ('All Stations','Bowen Hills','Park Road'):'1542',
    ('All Stations','Bowen Hills','Manly'):'1545',
    ('All Stations','Beenleigh','Bowen Hills'):'2014',
    ('MQK-PKR','Coopers Plains','Bowen Hills'):'2017',
    ('MQK-PKR','Kuraby','Bowen Hills'):'2018',
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
    ('CQD-IDP,IDP-MTZ','Coopers Plains','Bowen Hills'):'3380',
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
    ('BHI-EGJ,EGJ-NTG','Milton','Kippa-Ring'):'3867',
    ('All Stations','Cleveland','Bowen Hills'):'4014',
    ('MNY-MGS','Cleveland','Bowen Hills'):'4017',
    ('MNY-MJE','Cleveland','Bowen Hills'):'4019',
    ('All Stations','Cleveland','Shorncliffe'):'4050',
    ('All Stations','Cleveland','Northgate'):'4064',
    ('All Stations','Cleveland','Ferny Grove'):'4080',
    ('MNY-MJE','Cleveland','Shorncliffe'):'4151',
    ('MNY-MGS','Cleveland','Doomben'):'4155',
    ('MNY-MJE','Cleveland','Doomben'):'4156',
    ('All Stations','Park Road','Bowen Hills'):'4214',
    ('All Stations','Park Road','Shorncliffe'):'4250',
    ('All Stations','Park Road','Doomben'):'4255',
    ('All Stations','Park Road','Northgate'):'4264',
    ('All Stations','Park Road','Ferny Grove'):'4280',
    ('All Stations','Park Road','Domestic'):'4290',
    ('All Stations','Manly','Bowen Hills'):'4514',
    ('All Stations','Manly','Shorncliffe'):'4550',
    ('All Stations','Manly','Doomben'):'4555',
    ('All Stations','Manly','Northgate'):'4564',
    ('All Stations','Cannon Hill','Bowen Hills'):'4614',
    ('All Stations','Cannon Hill','Shorncliffe'):'4650',
    ('All Stations','Cannon Hill','Northgate'):'4664',
    ('BHI-EGJ,EGJ-NTG','Cannon Hill','Kippa-Ring'):'4980',
    ('All Stations','Shorncliffe','Roma Street'):'5010',
    ('PKR-ATI,ATI-LGL,LGL-BNH','Doomben','Varsity Lakes'):'5025',
    ('PKR-CEP','Doomben','Kuraby'):'5026',
    ('All Stations','Shorncliffe','Springfield Central'):'5031',
    ('All Stations','Shorncliffe','Cleveland'):'5040',
    ('All Stations','Shorncliffe','Park Road'):'5041',
    ('All Stations','Shorncliffe','Manly'):'5045',
    ('All Stations','Shorncliffe','Cannon Hill'):'5046',
    ('PKR-CNQ','Shorncliffe','Cannon Hill'):'5047',
    ('PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Doomben','Varsity Lakes'):'5126',
    ('MJE-MNY','Shorncliffe','Cleveland'):'5140',
    ('All Stations','Doomben','Roma Street'):'5510',
    ('All Stations','Doomben','Kuraby'):'5522',
    ('All Stations','Doomben','Cleveland'):'5540',
    ('MGS-MNY','Doomben','Cleveland'):'5541',
    ('All Stations','Doomben','Park Road'):'5542',
    ('All Stations','Doomben','Manly'):'5545',
    ('MJE-MNY','Doomben','Cleveland'):'5640',
    ('PET-NTG','Caboolture','Roma Street'):'6011',
    ('All Stations','Caboolture','Ipswich'):'6030',
    ('All Stations','Kippa-Ring','Cleveland'):'6040',
												  
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Roma Street'):'6111',
    ('MTZ-IDP,IDP-DAR','Caboolture','Ipswich'):'6131',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Milton'):'6132',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Springfield Central'):'6135',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Rosewood'):'6136',
    ('PET-NTG','Caboolture','Ipswich'):'6230',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Ipswich'):'6231',
    ('PET-NTG,NTG-EGJ,EGJ-BHI,MTZ-IDP,IDP-DAR','Caboolture','Ipswich'):'6232',
    ('PET-NTG','Caboolture','Springfield Central'):'6235',
    ('All Stations','Northgate','Roma Street'):'6410',
    ('NTG-EGJ,EGJ-BHI,PKR-YRG,YRG-CEP,CEP-ATI,ATI-WOI,WOI-LGL,LGL-BNH','Northgate','Varsity Lakes'):'6426',
    ('All Stations','Northgate','Cleveland'):'6440',
    ('MJE-MNY','Northgate','Cleveland'):'6441',
    ('All Stations','Northgate','Park Road'):'6442',
    ('All Stations','Northgate','Manly'):'6445',
    ('All Stations','Northgate','Cannon Hill'):'6446',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Caboolture','Cleveland'):'6510',
    ('All Stations','Petrie','Roma Street'):'6611',
    ('All Stations','Kippa-Ring','Roma Street'):'6710',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Roma Street'):'6711',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Milton'):'6712',
    ('All Stations','Kippa-Ring','Beenleigh'):'6720',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Ipswich'):'6731',
    ('NTG-EGJ,EGJ-BHI','Kippa-Ring','Springfield Central'):'6735',
    ('CAB-PET,PET-NTG,NTG-BHI','Nambour','Roma Street'):'7110',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Roma Street'):'7113',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Milton'):'7114',
    ('PET-NTG','Nambour','Ipswich'):'7130',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Ipswich'):'7131',
    ('PET-NTG,NTG-EGJ,EGJ-BHI','Nambour','Springfield Central'):'7135',
    ('CAB-PET,PET-NTG,NTG-BHI','Gympie North','Roma Street'):'7612',
    ('All Stations','Ferny Grove','Roma Street'):'8010',
    ('All Stations','Ferny Grove','Beenleigh'):'8020',
    ('All Stations','Ferny Grove','Kuraby'):'8022',
    ('All Stations','Ferny Grove','Coopers Plains'):'8023',
    ('All Stations','Ferny Grove','Cleveland'):'8040',
    ('All Stations','Ferny Grove','Lota'):'8041',
    ('All Stations','Ferny Grove','Park Road'):'8042',
    ('PKR-MQK','Ferny Grove','Beenleigh'):'8121',    
    ('PKR-CEP','Ferny Grove','Kuraby'):'8122',
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

    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir

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
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {ID_TO_SHORT[day]} with train number {tn} - ')
            time.sleep(15)
            sys.exit()  
        
        if originpass or destinpass:
            print('           Error: First station pass or last station pass through a revenue location')
            for tn,day in originpass: print(f' - First pass: {tn} on {ID_TO_SHORT[day]} - ')
            for tn,day in destinpass: print(f' - Last pass:  {tn} on {ID_TO_SHORT[day]} - ')
            time.sleep(15)
            sys.exit() 
        
        
        
        start_time = time.time()
        
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


            # handle empty OD
            if entries:
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
                
                
            
                pattern_len = len(pattern) if len(pattern) > pattern_len else pattern_len
                origin_len  = len(oID) if len(oID) > origin_len else origin_len
                destin_len  = len(dID) if len(dID) > destin_len else destin_len
           
                
            
            
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
                    y[0] = ID_TO_SHORT[day]
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
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            show_info_safe('VAS Extract','Process Done')
        
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_VAS(path)
    