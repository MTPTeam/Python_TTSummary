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

from taipan.constants.locations import STATIONS_MASTER
from taipan.core.xml_parser import parse_rsx

from PyQt6.QtWidgets import QApplication

import traceback
import logging
from taipan.gui.base import open_file_crossplatform, show_info_safe, select_file



OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True

daylist = ['120','4','2','1']
weekdaykey_dict  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}
headers = ['First Service (Depart)','Station','Last Service (arrive)']


stables = {
   code: ['24:00:00', '00:00:00']
   for code, info in STATIONS_MASTER['stations'].items()
   if info.get('byline_terminus', False)
   and not info.get('non_revenue', False)
}


stationmaster = {
   code: info['name']
   for code, info in STATIONS_MASTER['stations'].items()
   if info.get('byline_terminus', False)
   and not info.get('non_revenue', False)
}


def TTS_SFL(path, mypath = None):

    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir

    try:
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        
        
        def timetrim(timestring):
            """ Format converter from hh:mm:ss to hh:mm """
            
            if type(timestring) == list:
                timestring = timestring[0]
            
            if timestring is None or timestring.isalpha() or ':' not in timestring or len(timestring) < 8:
                pass
            else:
                timestring = timestring[:-3]
            
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
        
        
       
        root, trains, _, _, _, _ = parse_rsx(path, want_trains=True)
        filename = filename[:-4]
        
        if __name__ == "__main__":
            print(filename,'\n')
            
        start_time = time.time()
        
        
        
        filename_xlsx = f'SimpleFirstLast-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        SFL = workbook.add_worksheet('SFL')
    
        redheader  = workbook.add_format({'bold':True,'align':'centre','valign':'vcentre','text_wrap':True,'bg_color':'#C00000','font_color':'white'})
        blueheader = workbook.add_format({'bold':True,'align':'centre','valign':'vcentre','text_wrap':True,'bg_color':'#0070C0','font_color':'white'})
        bold = workbook.add_format({'bold':True,'align':'centre'})
        centre = workbook.add_format({'align':'centre'})
        boldleft = workbook.add_format({'bold':True})
        
        SFL.write(0,0,filename,boldleft)
        
        for i,day in enumerate(daylist):
            for t in trains:
                if t.weekday != day or t.is_empty_train:
                    continue
                entries = t.entries
                            
                # if intersection #!!!
                for n,entry in enumerate(entries):
                    arr, dep = stoptime_info(n)
                    stationID = entry.attrib['stationID']
                    stationName = entry.attrib['stationName']
                    
    
                    if stationID in stables:
                        if dep < stables[stationID][0]:
                            stables[stationID][0] = dep
                            
                        if arr > stables[stationID][1]:
                            stables[stationID][1] = arr
                  
            startrow = 2
            startcol = 2
            
            startcol = i*4 + startcol
            endcol = startcol + 2
            d = weekdaykey_dict.get(day)
            SFL.merge_range(startrow,startcol,startrow,endcol,d, blueheader)
            startrow += 1
            SFL.write_row(startrow,startcol,headers, redheader)
            startrow += 1
            
            SFL.set_column(startcol+1,startcol+1,20)
            
            
            
            print(d)
            for row,(k,v) in enumerate(stables.items(),startrow):
                if v[0] == '24:00:00':
                    v[0] = '     '
                if v[1] == '00:00:00':
                    v[1] = '     '
                
                
                v[0] = timetrim(v[0])
                v[1] = timetrim(v[1])
                
                
                
                SFL.write(row,startcol  , v[0]                , centre)
                SFL.write(row,startcol+1, stationmaster.get(k), bold)
                SFL.write(row,startcol+2, v[1]                , centre)
                
                if k == 'RS':
                    k = 'RS '
                print(k,v)
                
                
                
                
                # print(stationmaster.get(k),v)
            print()
        
                    
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
        
        
        
        
        
        
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_SFL(path)
        