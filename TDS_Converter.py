import math
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
import sys
import time
import shutil

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import traceback
import logging

ProcessDoneMessagebox = False
ProcessDoneMessagebox = True





weekdaykey_dict  = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
jp_daycode_dict  = {'120':'032', '4':'064', '2':'128', '1':'002'}
tds_daycode_dict = {'120':'060', '4':'064', '2':'128', '1':'002'}

sID_stableconverter = {
    'EMHS':'EMH',
    'KPRS':'KR',
    'IPSS':'IPS',
    'ROBS':'ROB',
    'BNHS':'BNH',
    'BQYS':'BQY',
    'RDKS':'RDK',
    'VYST':'VYS',
    'WOBS':'WOB',
    'RKET':'RKE',
    'PETS':'PET',
    'RSF':'RS',
    'BNT':'BNH'
    }





















def TTS_TDS(path, mypath = None):
    
    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

    try:
        
        # Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        # path = askopenfilename() 
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        if __name__ == "__main__":
            print(filename,'\n')
       
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
        
        
        
        start_time = time.time()
        
        
        
        d_list = []
        revenue_parse = [x for x in root.iter('train') if 'Empty' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'] ]
        for train in revenue_parse:
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
         
        SORT_ORDER_WEEK = ['120','4','2','1'] 
        d_list.sort(key=SORT_ORDER_WEEK.index)
        # print(d_list)
        
        
        
        
        
        
        
        run_dict = {}
        for train in root.iter('train'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            origin = entries[0].attrib
            destin = entries[-1].attrib
            unit   = origin['trainTypeId'].split('-',1)[1]
            lineID = train.attrib['lineID']
            run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
            oID = origin['stationID']
            dID = destin['stationID']
            odep = origin['departure']
            ddep = destin['departure']
            
            traintype = origin['trainTypeId']
            cars = int(re.findall(r'\d+', traintype)[0])
            
            if not run_dict.get((run,WeekdayKey)):
                trips = 1
                run_dict[(run,WeekdayKey)] = [unit,cars,trips,oID,dID,odep,ddep,[tn]]
            else:
                run_dict[(run,WeekdayKey)][2] += 1
                run_dict[(run,WeekdayKey)][4] = dID
                run_dict[(run,WeekdayKey)][6] = ddep
                run_dict[(run,WeekdayKey)][-1].append(tn)  
        
        def writesheet(day,name,daycodedict):
            if set(day).intersection(d_list):
            
            
                def timetrim(timestring):
                    if type(timestring) == list:
                        timestring = timestring[0]
                    
                    if timestring is None or timestring.isalpha() or ':' not in timestring:
                        pass
                    elif timestring[0] == '0':
                        timestring = timestring[1:-3]
                    else: timestring = timestring[:-3]
                    return timestring
                
                def stoptime_info(entry_index, condition, dwelltime): 
                    x = entry_index
                    departure = entries[x].attrib['departure'] 
                    
                    stoptime = int(entries[x].attrib.get('stopTime',0))
                    if stoptime == 1:
                        stoptime = 0
                        
                    arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))  
                    if arrival[:6] == '1 days':
                        arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
                    else: arrival = arrival[7:]
                    
                    
                    if condition:
                        arr = arrival[0:2]+arrival[3:5]+'0'
                        dep = departure[0:2]+departure[3:5]+'0'
                    else:
                        # arr = arrival[0:2]+arrival[3:5]+str( int((round((int(arrival[6:8])/60),1)%1)*10)   )
                        a_seconds = int(arrival[6:8])
                        d_seconds = int(departure[6:8])
                        a_seconds_decimal = math.floor(a_seconds/6)
                        d_seconds_decimal = math.floor(d_seconds/6)
                        arr = arrival[0:2]+arrival[3:5]+str(a_seconds_decimal)
                        dep = departure[0:2]+departure[3:5]+str(d_seconds_decimal)
                        
                    if int(dwelltime) >= 1:
                        output = arr + dep
                    elif entries[x].attrib['stationID'] in ['MOH','EUD','WOB','PAL']:
                        output = arr + dep
                    else:
                        output = dep + dep
                
                    return output
                
                
                daycodetitle = {'120':'thurs','4':'fri','2':'sat','1':'sun'}
                days = daycodetitle.get(day[0])
                
                filename_txt = f'{name}-{days}-{filename}.txt' if name == 'JourneyPlanner' else f'{name}-{filename}.txt'
                

                
                trip_list = []
                # revenue_parse = [train for train in root.iter('train') if 'Empty' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'] ]
                revenue_parse = [x for x in root.iter('train') if 'Empty' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'] and x[0][0][0].attrib['weekdayKey'] in day]
                # revenue_parse = [train for train in root.iter('train')]
                for train in revenue_parse:
                    # trip_info = [] #!!!
                    tn  = train.attrib['number']
                    weekdayKey = train[0][0][0].attrib['weekdayKey']
                    entries = [x for x in train.iter('entry')]
                    origin = entries[0].attrib
                    destin = entries[-1].attrib
                    # unit   = origin['trainTypeId'].split('-',1)[1]
                    lineID = train.attrib['lineID']
                    run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
                    oID = origin['stationID']
                    dID = destin['stationID']
                    
                    listofruns = run_dict.get((run,weekdayKey))[-1]
                    runindex   = listofruns.index(tn)
                    
                    rn = len(listofruns) - 1
                    
                    cf = listofruns[runindex-1] if runindex != 0  else '    '
                    ct = listofruns[runindex+1] if runindex != rn else '    '
                    
                    rmc_daycode = daycodedict.get(weekdayKey)
                    cfDoO = rmc_daycode if runindex != 0   else '   '
                    ctDoO = rmc_daycode if runindex != rn  else '   '
                    
                    entry_info = []
                    
                    for i,x in enumerate(entries):
                        sID = x.attrib['stationID']
                        st = int(x.get('stopTime','0'))
                        
                        
                        # if sID in ['RSWJ','AJN']:
                        if sID in ['RSWJ']:
                            pass
                        
                        else:
                            
                            track = x.attrib['trackID'][-1]
                            
                            tracknum = x.attrib['trackID'].split('-')[-1]
                            # if len(tracknum) > 1:
                            #     print(tn,sID, x.attrib['trackID'])
                            
                            
                            
                            if sID in ['AJN'] and dID != 'BDT' and oID != 'BDT':
                                if track == '1':
                                    track = 'F'
                                elif track == '2':
                                    track = 'B'
                                platform = '  '
                            
                            else:
                                track = x.attrib['trackID'][-1]
                                if track == '0':
                                    track = '10'
                                if sID == 'RSF':
                                    track = '1' + track
                                    
                                platform = '#' + track
                                
                            sID = sID_stableconverter.get(sID,sID)    
                            thrutype = 'D' if x.attrib['type'] == 'stop' else 'P'
                            
                            
                            dwell = str(math.floor(st/60))
                            if st == 90:
                                dwell = '2'
                            
                            
                            decimalbool = (thrutype == 'D') or (i == 0) or (i==len(entries)-1)
                            clock = stoptime_info(i,decimalbool,dwell) 
                            # clock = stoptime_info(i)
                            
                            clock = clock + thrutype
                            
                            if len(dwell) < 3: #!!!
                                dwell = dwell + '0'
                            if len(dwell) < 3: #!!!
                                dwell = '0' + dwell
                            
                            
                            
                            
                            if len(sID) == 2 and len(track) == 1:
                                track = '0' + track
                            lsID = sID + track
                            
                            
                            data = [clock,dwell,platform,lsID]
                            entry_info.append(data)
                    
                    # trip_info.append(tn)
                    # trip_info.append(cf)
                    # trip_info.append(ct)
                    # trip_info.append(cfDoO)
                    # trip_info.append(ctDoO)
                    # trip_info.append(weekdayKey)
                    # trip_info.append(entry_info)
                    # # trip_info.append(n)
                    
                    # trip_list.append(trip_info)
                    trip_list.append([tn,cf,ct,cfDoO,ctDoO,weekdayKey,entry_info])
                        
                
                
                trip_list.sort(key=lambda val: val[0])
                o = open(filename_txt, 'w')
                # w = open(filename_txt, 'w').write
                wl = o.writelines
                wl(['TTBL','\n']) #!!!
                
                for p,trip in enumerate(trip_list):
                    
                
                    tnum = trip[0]
                    cf = trip[1]
                    ct = trip[2]
                    fromDoO = trip[3]
                    toDoO = trip[4]
                    DoO = daycodedict.get(trip[5])
                    stations = trip[6]
                    n = str(len(stations) + 1)
                    
                    while len(n) < 6:
                        n = '0' + n
                    n = 'END ' + n
                    
                    wl(['STRT','    ',tnum,'   ',DoO+'CITYM','    ',cf,'  ',fromDoO,'                     ',ct,'  ',toDoO,'                     ','1','    ','\n'])
                    for station in stations:
                        platform_sID_break = '               ' if len(station[2]) == 2 else '              '
                        stop_info = ['    ',station[0],' ',station[1],'        ',station[2], platform_sID_break, station[3],'\n']
                        wl(stop_info)
                    wl([n,'        '])
                    if trip != trip_list[-1]:
                        wl(['\n'])
                
                    
            
                
                
                
                o.close()
                if __name__ != "__main__":
                    if copyfile:
                        shutil.copy(filename_txt, mypath) 
                    
                    
    
        writesheet(['120'],             'JourneyPlanner',   jp_daycode_dict)
        writesheet(['4'],               'JourneyPlanner',   jp_daycode_dict)
        writesheet(['2'],               'JourneyPlanner',   jp_daycode_dict)
        writesheet(['1'],               'JourneyPlanner',   jp_daycode_dict)
        writesheet(['120','4','2','1'], 'TDSExtract',       tds_daycode_dict)
        

            
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('TDS Converter','Process Done')

            
            
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_TDS(path)