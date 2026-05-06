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

from PyQt6.QtWidgets import QApplication
from taipan.gui.base import open_file_crossplatform, show_info, select_file
from taipan.constants.locations import STATIONS_MASTER
from taipan.core.xml_parser import parse_rsx

from taipan.constants.days import WEEKDAY_KEYS_MASTER, ID_TO_SHORT
import traceback
import logging



OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True

daylist = ['120','4','2','1']
headers = ['Station','Line','Direction']
blanks  = ['']


# Replace bystation_list - all revenue stations
bystation_list = [
   [code, info['name'], info['line']]
   for code, info in STATIONS_MASTER['stations'].items()
   if not info.get('non_revenue', False)
]
# Replace byline_list - byline terminus stations only
byline_list = [
   [code, info['name'], info['line']]
   for code, info in STATIONS_MASTER['stations'].items()
   if info.get('byline_terminus', False)
   and not info.get('non_revenue', False)
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

    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir

    try:
        
        ### File 1
        ###############################################################################################

        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename1 = path.split('/')[-1]
        root1, trains1, _, _, _, _ = parse_rsx(path, want_trains=True)
        filename1 = filename1[:-4]
        ###############################################################################################
        
        
        ### File 2
        ###############################################################################################
        path2 = select_file(caption="Select RSX file", directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")
        root2, trains2, _, _, _, _ = parse_rsx(path2, want_trains=True)
        filename2 = path2.split('/')[-1]
        filename2 = filename2[:-4]
        ###############################################################################################
        
        print(filename1)
        print(filename2)
        print()
        start_time = time.time()
    
        os.chdir(directory)
        
        
        def timetrim(timestring):
            """ Format converter from hh:mm:ss to hh:mm """

            if timestring is None or timestring.isalpha() or ':' not in timestring:
                return timestring

            # get hour safely
            hour = int(timestring.split(":")[0])

            meridiem = ' AM' if hour < 12 or hour >= 24 else ' PM'

            if timestring[0] == '0':
                timestring = timestring[1:]

            elif 13 <= hour < 25:
                timestring = str(hour - 12) + timestring[len(str(hour)):]

            elif hour >= 25:
                timestring = str(hour - 24) + timestring[len(str(hour)):]

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


            for t in trains1:
                if t.weekday != day or t.is_empty_train:
                    continue
                entries = t.entries
                stations = t.station_ids
                city_idx = next((stations.index(c) for c in ['BNC', 'RS', 'RTL'] if c in stations), None)
                if city_idx is None:
                    continue
                for n, entry in enumerate(entries):
                    arr, dep = stoptime_info(n)
                    for k, v in file1_startdict.items():
                        if entry.attrib['stationID'] == k:
                            if city_idx > n and dep < v[i][0]:
                                file1_startdict[k][i][0] = dep
                            if city_idx < n and arr < v[i][1]:
                                file1_startdict[k][i][1] = arr
                    for k, v in file1_enddict.items():
                        if entry.attrib['stationID'] == k:
                            if city_idx > n and dep > v[i][0]:
                                file1_enddict[k][i][0] = dep
                            if city_idx < n and arr > v[i][1]:
                                file1_enddict[k][i][1] = arr


            for t in trains2:
                if t.weekday != day or t.is_empty_train:
                    continue
                entries = t.entries
                stations = t.station_ids
                city_idx = next((stations.index(c) for c in ['BNC', 'RS', 'RTL'] if c in stations), None)
                if city_idx is None:
                    continue
                for n, entry in enumerate(entries):
                    arr, dep = stoptime_info(n)
                    for k, v in file2_startdict.items():
                        if entry.attrib['stationID'] == k:
                            if city_idx > n and dep < v[i][0]:
                                file2_startdict[k][i][0] = dep
                            if city_idx < n and arr < v[i][1]:
                                file2_startdict[k][i][1] = arr
                    for k, v in file2_enddict.items():
                        if entry.attrib['stationID'] == k:
                            if city_idx > n and dep > v[i][0]:
                                file2_enddict[k][i][0] = dep
                            if city_idx < n and arr > v[i][1]:
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
                DoO = ID_TO_SHORT[day]
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
            print(f'\n\n(runtime: {time.time()-start_time:.2f}seconds)')
            show_info('FirstLast','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_FL(path)
        