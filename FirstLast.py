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

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

import traceback
import logging



OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True










weekdaykey_dict  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}
daylist = ['120','4','2','1']
headers = ['Station','Line','Direction']
blanks  = ['']

byline_list = [
    ['FYG', 'Ferny Grove', 'FernyGrove'],
    ['BNH', 'Beenleigh', 'Beenleigh'],
    ['SHC', 'Shorncliffe', 'Shorncliffe'],
    ['CVN', 'Cleveland', 'Cleveland'],
    ['BDT', 'Domestic Airport', 'Domestic Airport'],
    ['VYS', 'Varsity Lakes', 'Gold Coast'],
    ['DBN', 'Doomben', 'Doomben'],
    ['PET', 'Petrie', 'Petrie'],
    ['CAB', 'Caboolture', 'Caboolture'],
    ['KPR', 'Kippa-Ring', 'RedcliffePeninsula'],
    ['NBR', 'Nambour', 'Nambour'],
    ['GYN', 'Gympie North', 'Gympie'],
    ['IPS', 'Ipswich', 'Ipswich'],
    ['RSW', 'Rosewood', 'Rosewood'],
    ['SFC', 'Springfield Central', 'Springfield'],
    ['AIN', 'Albion', 'InnerNorth'],
    ['PKR', 'Park Road', 'InnerSouth'],
    ['RS', 'Roma Street', 'City'],
    ['DAR', 'Darra', 'Inner West']
    ]

bystation_list = [
    ['AIN', 'Albion', 'InnerNorth'],
    ['ADY', 'Alderley', 'FernyGrove'],
    ['ATI', 'Altandi', 'Beenleigh'],
    ['ACO', 'Ascot', 'Doomben'],
    ['AHF', 'Auchenflower', 'InnerWest'],
    ['BDS', 'Bald Hills', 'Petrie'],
    ['BQO', 'Banoon', 'Beenleigh'],
    ['BQY', 'Banyo', 'Shorncliffe'],
    ['BNH', 'Beenleigh', 'Beenleigh'],
    ['BEB', 'Beerburrum', 'Nambour'],
    ['BWH', 'Beerwah', 'Nambour'],
    ['BTI', 'Bethania', 'Beenleigh'],
    ['BHA', 'Bindha', 'Shorncliffe'],
    ['BDE', 'Birkdale', 'Cleveland'],
    ['BZL', 'Boondall', 'Shorncliffe'],
    ['BOV', 'Booval', 'Ipswich'],
    ['BHI', 'Bowen Hills', 'City'],
    ['BPR', 'Bray Park', 'Petrie'],
    ['BDX', 'Bundamba', 'Ipswich'],
    ['BRD', 'Buranda', 'Cleveland'],
    ['BPY', 'Burpengary', 'Caboolture'],
    ['CAB', 'Caboolture', 'Caboolture'],
    ['CNQ', 'Cannon Hill', 'Cleveland'],
    ['CDE', 'Carseldine', 'Petrie'],
    ['BNC', 'Central', 'City'],
    ['CMZ', 'Chelmer', 'InnerWest'],
    ['CYF', 'Clayfield', 'Doomben'],
    ['CVN', 'Cleveland', 'Cleveland'],
    ['CXM', 'Coomera', 'GoldCoast'],
    ['CEP', 'Coopers Plains', 'Beenleigh'],
    ['COZ', 'Cooran', 'Gympie'],
    ['COO', 'Cooroy', 'Gympie'],
    ['CRO', 'Coorparoo', 'Cleveland'],
    ['CQD', 'Corinda', 'InnerWest'],
    ['DKB', 'Dakabin', 'Caboolture'],
    ['DAR', 'Darra', 'InnerWest'],
    ['DEG', 'Deagon', 'Shorncliffe'],
    ['DIR', 'Dinmore', 'Ipswich'],
    ['BDT', 'Domestic Airport', 'Airport'],
    ['DBN', 'Doomben', 'Doomben'],
    ['DUP', 'Dutton Park', 'Beenleigh'],
    ['EGJ', 'Eagle Junction', 'InnerNorth'],
    ['EIP', 'East Ipswich', 'Ipswich'],
    ['EBV', 'Ebbw Vale', 'Ipswich'],
    ['EDL', 'Eden’s Landing', 'Beenleigh'],
    ['EMH', 'Elimbah', 'Nambour'],
    ['EGG', 'Enoggera', 'FernyGrove'],
    ['EUD', 'Eudlo', 'Nambour'],
    ['EUM', 'Eumundi', 'Gympie'],
    ['FFI', 'Fairfield', 'Beenleigh'],
    ['FYG', 'Ferny Grove', 'FernyGrove'],
    ['BRC', 'Fortitude Valley', 'City'],
    ['FTG', 'Fruitgrove', 'Beenleigh'],
    ['GAI', 'Gailes', 'Ipswich'],
    ['GAO', 'Gaythorne', 'FernyGrove'],
    ['GEB', 'Geebung', 'Petrie'],
    ['GSS', 'Glasshouse Mountains', 'Nambour'],
    ['GDQ', 'Goodna', 'Ipswich'],
    ['GVQ', 'Graceville', 'InnerWest'],
    ['GOQ', 'Grovely', 'FernyGrove'],
    ['GYN', 'Gympie North', 'Gympie'],
    ['HLN', 'Helensvale', 'GoldCoast'],
    ['HMM', 'Hemmant', 'Cleveland'],
    ['HDR', 'Hendra', 'Doomben'],
    ['HVW', 'Holmview', 'Beenleigh'],
    ['IDP', 'Indooroopilly', 'InnerWest'],
    ['BIT', 'International Airport', 'Airport'],
    ['IPS', 'Ipswich', 'Ipswich'],
    ['KGR', 'Kallangur', 'RedcliffePeninsula'],
    ['KRA', 'Karrabin', 'Rosewood'],
    ['KEP', 'Keperra', 'FernyGrove'],
    ['KGT', 'Kingston', 'Beenleigh'],
    ['KPR', 'Kippa-Ring', 'RedcliffePeninsula'],
    ['KRY', 'Kuraby', 'Beenleigh'],
    ['LSH', 'Landsborough', 'Nambour'],
    ['LWO', 'Lawnton', 'Petrie'],
    ['LDM', 'Lindum', 'Cleveland'],
    ['LGL', 'Loganlea', 'Beenleigh'],
    ['LOT', 'Lota', 'Cleveland'],
    ['MGH', 'Mango Hill', 'RedcliffePeninsula'],
    ['MGE', 'Mango Hill East', 'RedcliffePeninsula'],
    ['MNY', 'Manly', 'Cleveland'],
    ['MTZ', 'Milton', 'InnerWest'],
    ['MHQ', 'Mitchelton', 'FernyGrove'],
    ['MOH', 'Mooloolah', 'Nambour'],
    ['MQK', 'Moorooka', 'Beenleigh'],
    ['MYE', 'Morayfield', 'Caboolture'],
    ['MGS', 'Morningside', 'Cleveland'],
    ['MJE', 'Murarrie', 'Cleveland'],
    ['MRD', 'Murrumba Downs', 'RedcliffePeninsula'],
    ['NBR', 'Nambour', 'Nambour'],
    ['NRB', 'Narangba', 'Caboolture'],
    ['NRG', 'Nerang', 'GoldCoast'],
    ['NWM', 'Newmarket', 'FernyGrove'],
    ['NPR', 'Norman Park', 'Cleveland'],
    ['NBD', 'North Boondall', 'Shorncliffe'],
    ['NTG', 'Northgate', 'InnerNorth'],
    ['NUD', 'Nudgee', 'Shorncliffe'],
    ['NND', 'Nundah', 'InnerNorth'],
    ['ORM', 'Ormeau', 'GoldCoast'],
    ['ORO', 'Ormiston', 'Cleveland'],
    ['OXP', 'Oxford Park', 'FernyGrove'],
    ['OXL', 'Oxley', 'InnerWest'],
    ['PAL', 'Palmwoods', 'Nambour'],
    ['PKR', 'Park Road', 'InnerSouth'],
    ['PET', 'Petrie', 'Petrie'],
    ['PMQ', 'Pomona', 'Gympie'],
    ['RDK', 'Redbank', 'Ipswich'],
    ['RHD', 'Richlands', 'Springfield'],
    ['RVV', 'Riverview', 'Ipswich'],
    ['ROB', 'Robina', 'GoldCoast'],
    ['RKE', 'Rocklea', 'Beenleigh'],
    ['RS', 'Roma Street', 'City'],
    ['RSW', 'Rosewood', 'Rosewood'],
    ['RWL', 'Rothwell', 'RedcliffePeninsula'],
    ['RUC', 'Runcorn', 'Beenleigh'],
    ['SLY', 'Salisbury', 'Beenleigh'],
    ['SGE', 'Sandgate', 'Shorncliffe'],
    ['SHW', 'Sherwood', 'InnerWest'],
    ['SHC', 'Shorncliffe', 'Shorncliffe'],
    ['SBA', 'South Bank', 'InnerSouth'],
    ['SBE', 'South Brisbane', 'InnerSouth'],
    ['SFD', 'Springfield', 'Springfield'],
    ['SFC', 'Springfield Central', 'Springfield'],
    ['SPN', 'Strathpine', 'Petrie'],
    ['SYK', 'Sunnybank', 'Beenleigh'],
    ['SSN', 'Sunshine', 'Petrie'],
    ['TIQ', 'Taringa', 'InnerWest'],
    ['TAO', 'Thagoona', 'Rosewood'],
    ['THS', 'Thomas Street', 'Rosewood'],
    ['TNS', 'Thorneside', 'Cleveland'],
    ['TBU', 'Toombul', 'InnerNorth'],
    ['TWG', 'Toowong', 'InnerWest'],
    ['TRA', 'Traveston', 'Gympie'],
    ['TDP', 'Trinder Park', 'Beenleigh'],
    ['VYS', 'Varsity Lakes', 'GoldCoast'],
    ['VGI', 'Virginia', 'Petrie'],
    ['WAC', 'Wacol', 'Ipswich'],
    ['WOQ', 'Walloon', 'Rosewood'],
    ['WPT', 'Wellington Point', 'Cleveland'],
    ['WLQ', 'Wilston', 'FernyGrove'],
    ['WID', 'Windsor', 'FernyGrove'],
    ['WOI', 'Woodridge', 'Beenleigh'],
    ['WWI', 'Wooloowin', 'InnerNorth'],
    ['WOB', 'Woombye', 'Nambour'],
    ['WUL', 'Wulkuraka', 'Rosewood'],
    ['WNM', 'Wynnum', 'Cleveland'],
    ['WNC', 'Wynnum Central', 'Cleveland'],
    ['WYH', 'Wynnum North', 'Cleveland'],
    ['YAN', 'Yandina', 'Gympie'],
    ['YLY', 'Yeerongpilly', 'Beenleigh'],
    ['YRG', 'Yeronga', 'Beenleigh'],
    ['ZLL', 'Zillmere', 'Petrie']
    ]

# stationlist = [x[0] for x in byline_list]
# stationlist = [x[0] for x in bystation_list]

file1_startdict = {}
file2_startdict = {}
file1_enddict   = {}
file2_enddict   = {}
for x in [x[0] for x in bystation_list]:
    file1_startdict[x] = [['24:00:00','24:00:00'],['24:00:00','24:00:00'],['24:00:00','24:00:00'],['24:00:00','24:00:00']]
    file2_startdict[x] = [['24:00:00','24:00:00'],['24:00:00','24:00:00'],['24:00:00','24:00:00'],['24:00:00','24:00:00']]
    file1_enddict[x]   = [['00:00:00','00:00:00'],['00:00:00','00:00:00'],['00:00:00','00:00:00'],['00:00:00','00:00:00']]
    file2_enddict[x]   = [['00:00:00','00:00:00'],['00:00:00','00:00:00'],['00:00:00','00:00:00'],['00:00:00','00:00:00']]
    





















def TTS_FL(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

    try:
        
        ### File 1
        ###############################################################################################
        # Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        # path = askopenfilename() 
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename1 = path.split('/')[-1]
        
        
       
        tree1 = ET.parse(filename1)
        root1 = tree1.getroot()
        filename1 = filename1[:-4]
        ###############################################################################################
        
        
        
        
        
        ### File 2
        ###############################################################################################
        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        path = askopenfilename() 
        tree2 = ET.parse(path)
        root2 = tree2.getroot()
        filename2 = path.split('/')[-1]
        filename2 = filename2[:-4]
        ###############################################################################################
        
        
        
        
        
        
        
        print(filename1)
        print(filename2)
        print()
        start_time = time.time()
        
        
        
        
        
        os.chdir(directory)
        
        
        
        
        
        
        
        
        
        def timetrim(timestring):
            """ Format converter from hh:mm:ss to hh:mm """
            
            # if type(timestring) == list:
            #     timestring = timestring[0]
            meridiem = ' AM' if timestring < '12:00:00' or timestring >= '24:00:00' else ' PM'
            
            if timestring is None or timestring.isalpha() or ':' not in timestring:
                pass
            else:
                if timestring[0] == '0':
                    timestring = timestring[1:]
                elif '13:00:00' <= timestring <'25:00:00':
                    timestring = str(int(timestring[0:2]) - 12) + timestring[2:]
                elif timestring >= '25:00:00':
                    timestring = str(int(timestring[0:2]) - 24) + timestring[2:]
            
                timestring = timestring[:-3]
                
                timestring += meridiem
                
            
            
            return timestring
    
        def stoptime_info(entry_index): 
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
        
        
        
        
    
        
        
            
              
        for i,day in enumerate(daylist):
            
            rsx1 = [x for x in root1.iter('train') if x[0][0][0].attrib['weekdayKey'] == day and 'Empty' not in x[1][0].attrib['trainTypeId']]
            rsx2 = [x for x in root2.iter('train') if x[0][0][0].attrib['weekdayKey'] == day and 'Empty' not in x[1][0].attrib['trainTypeId']]
        
            
        
            
            for train in rsx1:
                tn  = train.attrib['number']
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                entries = [x for x in train.iter('entry')]
                origin = entries[0]
                destin = entries[-1]
                unit   = origin.attrib['trainTypeId'].split('-',1)[1]
                    
                oID = origin.attrib['stationID']
                dID = destin.attrib['stationID']
                odep = origin.attrib['departure']
                ddep = destin.attrib['departure']
                stations = [x.attrib['stationID'] for x in entries]
                
                
                # if intersection #!!!
                for n,entry in enumerate(entries):
                    arr, dep = stoptime_info(n)
                    
                    
                    for k,v in file1_startdict.items():
                        if 'BNC' in stations and entry.attrib['stationID'] == k:
                            if stations.index('BNC') > n and dep < v[i][0]:
                                file1_startdict[k][i][0] = dep
                            if stations.index('BNC') < n and arr < v[i][1]:
                                file1_startdict[k][i][1] = arr
                            
                                
                                        
                                        
                    for k,v in file1_enddict.items():
                        if 'BNC' in stations and entry.attrib['stationID'] == k:
                            if stations.index('BNC') > n and dep > v[i][0]:
                                file1_enddict[k][i][0] = dep
                            
                            if stations.index('BNC') < n and arr > v[i][1]:
                                file1_enddict[k][i][1] = arr
    
                    
            
            
        
            
            for train in rsx2:
                tn  = train.attrib['number']
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                entries = [x for x in train.iter('entry')]
                origin = entries[0]
                destin = entries[-1]
                unit   = origin.attrib['trainTypeId'].split('-',1)[1]
                    
                
                oID = origin.attrib['stationID']
                dID = destin.attrib['stationID']
                odep = origin.attrib['departure']
                ddep = destin.attrib['departure']
                
                stations = [x.attrib['stationID'] for x in entries]
                
                # if intersection #!!!
                for n,entry in enumerate(entries):
                    arr, dep = stoptime_info(n)
                    
                    
                    for k,v in file2_startdict.items():
                        
                        
                        if 'BNC' in stations and entry.attrib['stationID'] == k:
                            if stations.index('BNC') > n and dep < v[i][0]:
                                file2_startdict[k][i][0] = dep
                            if stations.index('BNC') < n and arr < v[i][1]:
                                file2_startdict[k][i][1] = arr
                                
                                
                            
                                
                                        
                                        
                    for k,v in file2_enddict.items():
                        if 'BNC' in stations and entry.attrib['stationID'] == k:
                            if stations.index('BNC') > n and dep > v[i][0]:
                                file2_enddict[k][i][0] = dep
                            
                            if stations.index('BNC') < n and arr > v[i][1]:
                                file2_enddict[k][i][1] = arr
                                
                                
            
        def cleanup(dictionary):
            for k,v in dictionary.items():
                for i,d in enumerate(v):
                    for ii,dd in enumerate(d):
                        if dd in ['00:00:00','24:00:00']:
                            v[i][ii] = '        '
                        else:
                            v[i][ii] = timetrim(v[i][ii])
        
        def printpreview(dictionary):
            for k,v in dictionary.items():
                if k in [x[0] for x in byline_list]:
                    print(k,v)
                    print()
            print()
                            
        cleanup(file1_startdict)
        cleanup(file1_enddict)
        cleanup(file2_startdict)
        cleanup(file2_enddict)
        
                
        filename_xlsx = f'FirstLast-{filename1}-{filename2}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        info = workbook.add_worksheet('Info')
        FLbL = workbook.add_worksheet('FirstLast by Line')
        FLbS = workbook.add_worksheet('FirstLast by Station')    
        
        
        boldleft = workbook.add_format({'bold':True,'align':'left'})
        bold     = workbook.add_format({'bold':True,'align':'centre','valign':'vcentre','text_wrap':True})
        centre   = workbook.add_format({'align':'centre'})
        grey     = workbook.add_format({'bg_color':'#CCCCCC'})
        redcell    = workbook.add_format({'bg_color':'#FFB2B2','align':'centre'})
        
        info.write(0,0,'Timetable Name 1',boldleft)
        info.write(1,0,'Timetable Name 2',boldleft)
        # info.write(2,0,'Timetable Id 1',boldleft)
        # info.write(3,0,'Timetable Id 2',boldleft)
        info.write(2,0,'Report Date',boldleft)
        
        info.write(0,1,f'{filename1}.rsx')
        info.write(1,1,f'{filename2}.rsx')
        # info.write(2,1,'.')
        # info.write(3,1,'.')
        info.write(2,1,datetime.now().strftime("%d-%b-%Y %H:%M"))
        
        info.set_column(0,0,18.5)
        info.set_column(1,1,max(len(filename1),len(filename2))+5)
        
    
        
        
        
        def setupformatting(sheet,stationlist):   
            
            sheet.write_row(0,0,headers,bold)
            sheet.merge_range('D1:N1','First Train',bold)
            sheet.merge_range('P1:Z1','Last Train',bold)
            sheet.set_column(2,2,13.3)
            sheet.freeze_panes(0,3)
                
            
            
            # daylist = 2*['120','4','2','1']
            for c,day in enumerate(2*daylist,1):
                DoO = weekdaykey_dict.get(day)
                col = 3*c
                
                sheet.write(1,col,  filename1,bold)
                sheet.write(2,col,  DoO,      bold)
                sheet.set_column(col,col,len(filename1)+5)
                col += 1
                
                sheet.write(1,col,filename2,bold)
                sheet.write(2,col,DoO,      bold)
                sheet.set_column(col,col,len(filename2)+5)
                col += 1
                
                if c != 2*len(daylist):
                    sheet.write(1,col,'',       grey)
                    sheet.write(2,col,'',       grey)
                    sheet.set_column(col,col,1)
            
            
            
            
            
            
            station_width = 0
            line_width = 0   
            row = 3
            
            sheet.write('O1','',grey)
           
            for sID,station,line in stationlist:
                # print(n,station,line)
                if len(station) > station_width and '\n' not in station: station_width = len(station)
                if len(line) > line_width:                                  line_width = len(line)
                
                sheet.merge_range(row,0,row+1,0,station,bold)
                sheet.merge_range(row,1,row+1,1,line,bold)
                
                sheet.write(row,2,'Inbound (Dep)',bold)
                sheet.set_row(row,14.5)
                for c,day in enumerate(daylist):
                    firsttraincol = 3*(c+1)
                    lasttraincol  = 3*(c+1) + 12
                    sheet.write(row, firsttraincol+2, '', grey)
                    if c != len(daylist) - 1: 
                        sheet.write(row, lasttraincol+2, '', grey)
                    
                row += 1
                
                sheet.write(row,2,'Outbound (Arr)',bold)
                sheet.set_row(row,14.5)
                for c,day in enumerate(daylist):
                    firsttraincol = 3*(c+1)
                    lasttraincol  = 3*(c+1) + 12
                    sheet.write(row, firsttraincol+2, '', grey)
                    if c != len(daylist) - 1: 
                        sheet.write(row, lasttraincol+2, '', grey)
                
                row += 1
                
                if sID != stationlist[-1][0]:
                    sheet.write_row(row,0,26*blanks,grey)
                    sheet.set_row(row,6)
                    
                row += 1
                
                
                
                
                
            sheet.set_column(0,0,station_width)
            sheet.set_column(1,1,line_width) 
            
            
            
        def writedata(sheet, stationlist):
        
            # daylist = ['120']    
        
            startrow = 3
            
            for c,day in enumerate(daylist):
                firsttraincol = 3*(c+1)
                lasttraincol  = 3*(c+1) + 12
                
                            
            for k in [x[0] for x in stationlist]:
                for c,day in enumerate(daylist):
                    firsttraincol = 3*(c+1)
                    lasttraincol  = 3*(c+1) + 12
                    
                    # if file1_startdict[k][c][0] != file2_startdict[k][c][0]:
                    #     print(k,day,file1_startdict[k][c][0], file2_startdict[k][c][0])
                    # if file1_enddict[k][c][0] != file2_enddict[k][c][0]:
                    #     print(k,day,file1_enddict[k][c][0],file2_enddict[k][c][0])
                        
                    a = file1_startdict[k][c][0]
                    b = file2_startdict[k][c][0]
                    font = centre if a == b else redcell
                    
                    sheet.write(startrow, firsttraincol,     a, font) 
                    sheet.write(startrow, firsttraincol+1,   b, font) 
                    
                    
                    a = file1_enddict[k][c][0]
                    b = file2_enddict[k][c][0]
                    font = centre if a == b else redcell
                    
                    sheet.write(startrow, lasttraincol,      a,   font) 
                    sheet.write(startrow, lasttraincol+1,    b,   font) 
    
                
                startrow += 1
                
                for c,day in enumerate(daylist):
                    firsttraincol = 3*(c+1)
                    lasttraincol  = 3*(c+1) + 12
                    
                    # if file1_startdict[k][c][1] != file2_startdict[k][c][1]:
                    #     print(k,day,file1_startdict[k][c][1],file2_startdict[k][c][1])
                    # if file1_enddict[k][c][1] != file2_enddict[k][c][1]:
                    #     print(k,day,file1_enddict[k][c][1],file2_enddict[k][c][1])
                        
                    a = file1_startdict[k][c][1]
                    b = file2_startdict[k][c][1]
                    font = centre if a == b else redcell
                
                    sheet.write(startrow, firsttraincol,     a, font) 
                    sheet.write(startrow, firsttraincol+1,   b, font) 
    
                    
                    a = file1_enddict[k][c][1]
                    b = file2_enddict[k][c][1]
                    font = centre if a == b else redcell
    
                    sheet.write(startrow, lasttraincol,      a,   font) 
                    sheet.write(startrow, lasttraincol+1,    b,   font) 
    
                
                startrow += 2      
            
            
        
        setupformatting(FLbL, byline_list)
        setupformatting(FLbS, bystation_list)
    
        writedata(FLbL, byline_list)
        writedata(FLbS, bystation_list)
        
        
        
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
        #     print('Creating workbook')  
        #     workbook.close()
        #     if OpenWorkbook and __name__ == "__main__":
        #         os.startfile(rf'{filename_xlsx}')
        #         print('\nOpening workbook')   
        #     else:
        #         if copyfile:
        #             shutil.copy(filename_xlsx, mypath) 
                
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('FirstLast','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)

if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_FL(path)
        