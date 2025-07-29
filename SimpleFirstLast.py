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

daylist = ['120','4','2','1']
weekdaykey_dict  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}
headers = ['First Service (Depart)','Station','Last Service (arrive)']


stables = {
    'FYG':['24:00:00','00:00:00'],
    'BNH':['24:00:00','00:00:00'],
    'SHC':['24:00:00','00:00:00'],
    'CVN':['24:00:00','00:00:00'],
    'BDT':['24:00:00','00:00:00'],
    'VYS':['24:00:00','00:00:00'],
    'DBN':['24:00:00','00:00:00'],
    'PET':['24:00:00','00:00:00'],
    'CAB':['24:00:00','00:00:00'],
    'KPR':['24:00:00','00:00:00'],
    'NBR':['24:00:00','00:00:00'],
    'GYN':['24:00:00','00:00:00'],
    'IPS':['24:00:00','00:00:00'],
    'RSW':['24:00:00','00:00:00'],
    'SFC':['24:00:00','00:00:00'],
    'AIN':['24:00:00','00:00:00'],
    'PKR':['24:00:00','00:00:00'],
    'RS' :['24:00:00','00:00:00'],
    'DAR':['24:00:00','00:00:00']
    }

stationmaster = {
    'FYG': 'Ferny Grove',
    'BNH': 'Beenleigh',
    'SHC': 'Shorncliffe',
    'CVN': 'Cleveland',
    'BDT': 'Domestic Airport',
    'VYS': 'Varsity Lakes',
    'DBN': 'Doomben',
    'PET': 'Petrie',
    'CAB': 'Caboolture',
    'KPR': 'Kippa-Ring',
    'NBR': 'Nambour',
    'GYN': 'Gympie North',
    'IPS': 'Ipswich',
    'RSW': 'Rosewood',
    'SFC': 'Springfield Central',
    'AIN': 'Albion',
    'PKR': 'Park Road',
    'RS': 'Roma Street',
    'DAR': 'Darra'
    }



# def timetrim(timestring):
#     """ Format converter from hh:mm:ss to hh:mm """ #!!!
#     # print(timestring)
#     # if type(timestring) == list:
#     #     timestring = timestring[0]
#     meridiem = ' AM' if timestring < '12:00:00' or timestring >= '24:00:00' else ' PM'
    
#     if timestring is None or timestring.isalpha() or ':' not in timestring or 'AM' in timestring or 'PM' in timestring:
#         pass
#     else:
#         if timestring[0] == '0':
#             timestring = timestring[1:]
#         elif '13:00:00' <= timestring <'25:00:00':
#             timestring = str(int(timestring[0:2]) - 12) + timestring[2:]
#         elif timestring >= '25:00:00':
#             timestring = str(int(timestring[0:2]) - 24) + timestring[2:]
    
#         timestring = timestring[:-3]
        
#         timestring += meridiem
        
    
    
#     return timestring









def TTS_SFL(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

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
        
        
       
        tree = ET.parse(filename)
        root = tree.getroot()
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
            rsx = [x for x in root.iter('train') if x[0][0][0].attrib['weekdayKey'] == day and 'Empty' not in x[1][0].attrib['trainTypeId']]
            for train in rsx:
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
    TTS_SFL(path)