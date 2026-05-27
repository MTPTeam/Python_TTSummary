import math
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
import sys
import time
import shutil  

import traceback
import logging

from taipan.core.xml_parser import load_rsx, extract_trains, detect_duplicates, sort_days
from taipan.gui.base import open_file_crossplatform, select_file
from taipan.core.utils import _time_key, timetrim
from taipan.constants.locations import STATIONS_MASTER, YARDS
from PyQt6.QtWidgets import QApplication


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



line_station_lookup = {
   code: s['line']
   for code, s in STATIONS_MASTER['stations'].items()
}
CITY_TERMINUS = {
   ('south', False): 'BHI',
   ('south', True):  'EXH',
   ('north', False): 'RS',
   ('north', True):  'BOG',
}


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

yard_codes = {
   code for y in YARDS.values()
   for code in y['yards']
   if code not in STATIONS_MASTER['stations']
}

terminus_codes = {v['terminus'] for v in STATIONS_MASTER['lines'].values() if v.get('terminus')}


def TTS_H(path, mypath = None):
    
    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir
    
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
        
        

        root, filename = load_rsx(path)
        all_trains = extract_trains(root)
        dup = detect_duplicates(all_trains)


        if dup:
            print('           Error: Duplicate train numbers')
            for tn, day in dup:
                print(f' - 2 trains running on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit()

        
        def format_run(run):
            if '-' in run:
                return run

            newrun = ''
            # ETCS case for E12A, E12B runs to become E12-A, E12-B runs - and for regular E12 runs
            if run.startswith("E") and run[1].isnumeric():
                digits = ''.join(x for x in run[1:] if x.isnumeric())
                letters = ''.join(x for x in run[1:] if x.isalpha())
                newrun = f"E{digits}-{letters}" if run.endswith(('A','B')) else f"E{digits}"
            
            # ETCS case for 34EA, 34EB runs to become 34E-A, 34E-B runs - and for regular 34E runs
            elif len(run) >= 3 and run[0].isnumeric() and run[2] == "E":
                digits = ''.join(x for x in run if x.isnumeric())
                letters = ''.join(x for x in run[3:] if x.isalpha())
                newrun = f"{digits}E-{letters}" if run.endswith(('A','B')) else f"{digits}E"
            
            # Case for 12A, 12B runs to become 12-A, 12-B runs
            elif run[0].isnumeric() and run.endswith(('A','B')):
                digits = ''.join(x for x in run if x.isnumeric())
                letters = ''.join(x for x in run if x.isalpha())
                newrun = f"{digits}-{letters}"
            
            # Case for AB1, AB2 runs to become AB-1, AB-2 runs
            elif run[0].isalpha() and run.endswith(('1','2')):
                letters = ''.join(x for x in run if x.isalpha())
                digits = ''.join(x for x in run if x.isnumeric())
                newrun = f"{letters}-{digits}"

            return newrun if newrun else run
        
        
        
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
        #trains = [x for x in root.iter('train') if ('DEPT' not in [y for y in x.iter('entry')][0].attrib['trainTypeId'])]

        non_dept_trains = [t for t in all_trains if 'DEPT' not in t.train_type_raw]



        # trains = [x for x in root.iter('train') ]
        for t in non_dept_trains:

            tn         = t.number
            run        = format_run(t.run)
            WeekdayKey = t.weekday
            entries    = t.entries
            origin     = t.origin
            destin     = t.destin
            oID        = t.start_id
            dID        = t.end_id
            otrack     = origin['trackID'].split('-')[-1]
            dtrack     = destin['trackID'].split('-')[-1]
            loID       = oID + otrack
            ldID       = dID + dtrack

            
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
        d_list = sort_days(d_list)


        city_codes = {'RS', 'BNC', 'BRC', 'BHI', 'PKR', 'SBE', 'SBA', 'EXH', 'BOG', 'RTL'}
        line_codes_cache = {
        line: {code for code, s in STATIONS_MASTER['stations'].items() if s['line'] == line}
        for line in STATIONS_MASTER['lines']
        }


        print('IPS in Ipswich-Rosewood codes:', 'IPS' in line_codes_cache.get('Ipswich - Rosewood', set()))
        print('DAR in Ipswich-Rosewood codes:', 'DAR' in line_codes_cache.get('Ipswich - Rosewood', set()))
        print('BNH in Ipswich-Rosewood codes:', 'BNH' in line_codes_cache.get('Ipswich - Rosewood', set()))
        print('Ipswich - Rosewood codes:', line_codes_cache.get('Ipswich - Rosewood'))

        revenue_trains = [t for t in non_dept_trains if not t.is_empty_train]
        line_station_order = {line: [] for line in STATIONS_MASTER['lines']}
        for line in STATIONS_MASTER['lines']:
            corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
            all_train_entries = []
            for t in revenue_trains:
                train_station_ids = set(t.stations)
                build_codes = line_codes_cache.get(line, set())
                o_line_t = line_station_lookup.get(t.start_id)
                d_line_t = line_station_lookup.get(t.end_id)
                if corridor is None:
                    condition = o_line_t == line or d_line_t == line
                else:
                    condition = (o_line_t == line or d_line_t == line) and bool(train_station_ids & build_codes)
                if not condition:
                    continue
                train_entries = [(e.attrib['stationName'], e.attrib['stationID']) for e in t.entries
                                    if e.attrib['stationID'] in build_codes]
                if train_entries:
                    all_train_entries.append(train_entries)
               
            all_train_entries.sort(key=len, reverse=True)
            canonical = []
            for train_entries in all_train_entries:
                last_idx = -1
                for stop in train_entries:
                    if stop in canonical:
                        last_idx = canonical.index(stop)
                    else:
                        last_idx += 1
                        canonical.insert(last_idx, stop)
            line_station_order[line] = canonical



            for line, canonical in line_station_order.items():
                terminus = STATIONS_MASTER['lines'].get(line, {}).get('terminus')
                if canonical and terminus and canonical[0][1] == terminus:
                    line_station_order[line] = list(reversed(canonical))


        
        
        
        ### uniquestations_dict, network_vrt_dict and virtual run time (vrt) dictionaries for each line are used to determine direction (Up or Down)
        ### Originally created for the Working Timetables, selects line if train passes through a location that is unique to a line
        ### If the associated vrt integer for that line is increasing → outbound else inbound, can determine direction from that
        ### Extra logic needed for Inner city trains that have no obvious line
        ### The most error-prone function of the exporter, direction is regularly an issue
        ### Might need new method for direction selection (line irrelevant in this report)
        
        
        def create_textfile(weekdaykey):
            """ Creates a HASTUS Export textfile for a single day of operations """
            
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
            day_trains = [t for t in non_dept_trains if t.weekday == weekdaykey]


            for t in day_trains:
                

                WeekdayKey = t.weekday
                tn         = t.number
                entries    = t.entries
                origin     = t.origin
                destin     = t.destin
                unit       = 'IMU' if t.unit == 'IMU100' else t.unit
                cars       = str(t.cars)
                run        = format_run(t.run)
                oID        = t.start_id
                dID        = t.end_id
                odep       = t.odep
                ddep       = t.ddep
                traintype  = t.train_type_raw
                sIDs       = set(t.stations)
                sIDs_list  = t.stations
                empt       = '3' if t.is_empty_train else '0'


                entry_codes  = [e.attrib['stationID'] for e in entries]
                o_line       = line_station_lookup.get(oID)
                d_line       = line_station_lookup.get(dID)
                

                o_line = line_station_lookup.get(oID)
                d_line = line_station_lookup.get(dID)
                if o_line and o_line != 'Inner City' and d_line and d_line != 'Inner City' and o_line != d_line:
                    matched_line = o_line
                elif d_line and d_line != 'Inner City':
                    matched_line = d_line
                else:
                    matched_line = o_line
                if not matched_line:
                    for line, codes in line_codes_cache.items():
                        if sIDs.intersection(codes):
                            matched_line = line
                            break


                
                # explicit overrides
                if oID == 'RDKS' and 'IPS' in sIDs_list:
                    is_inbound = True
                elif dID == 'PKR' and 'MBN' in sIDs_list:
                    is_inbound = False
                else:

                    
                    line_codes = line_codes_cache.get(matched_line, set())
                    if oID in city_codes:
                        is_inbound = False
                    elif dID in city_codes:
                        is_inbound = True
            
                    else:
                        first_two = [c for c in entry_codes if c in line_codes][:2]
                        if len(first_two) == 2:
                            canonical = line_station_order.get(matched_line, [])
                            canonical_codes = [c for _, c in canonical]
                            a = canonical_codes.index(first_two[0]) if first_two[0] in canonical_codes else None
                            b = canonical_codes.index(first_two[1]) if first_two[1] in canonical_codes else None
                            if a is not None and b is not None:
                                is_inbound = b < a
                            else:
                                is_inbound = True
                        else:
                            is_inbound = True

                     
                corridor = STATIONS_MASTER['lines'].get(matched_line, {}).get('corridor') if matched_line else None
                if corridor == 'south':
                    drct = '13' if is_inbound else '12'
                else:
                    drct = '12' if is_inbound else '13'

                


                if tn == 'E401':
                    print(f'first_two={first_two} a={a} b={b} canonical_codes[:10]={canonical_codes[:10]}')

                

       

                
                
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
                            track = track.zfill(2)   # RS10 fix
    
                        firstinrun = runs.get((run,WeekdayKey))[0]
                        lastinrun  = runs.get((run,WeekdayKey))[-1]
                        
                        if tn == firstinrun and sID == 'MNY' and n == 0:
                            lsID = 'MNY_S'
                        elif tn == lastinrun and sID == 'MNY' and n == len(entries) - 1:
                            lsID = 'MNY_S'

                        # Restored CPM_S to CPM1/2 here    
                        #if tn == firstinrun and sID == 'CPM' and n == 0:
                            #lsID = sID + track          
                        #elif tn == lastinrun and sID == 'CPM' and n == len(entries) - 1:
                            #lsID = sID + track     

                        
                        # IF trains start/end at CPM then set to CPM_S or if they just pass through then set based on its trackID as usual
                        ### THIS NEEDS TO BE FIXED !!!!! BASED ON GEO
                        if sID == 'CPM' and n == 0 and oID == 'CPM':
                            lsID = 'CPM_S'
                        elif sID == 'CPM' and n == len(entries) - 1 and dID == 'CPM':
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
                    destination = os.path.join(myhastuspath, os.path.basename(filename_txt))
                    if os.path.abspath(filename_txt) != os.path.abspath(destination):
                        shutil.copy(filename_txt, destination)
                    else:
                        print('Skipping copy because source and destination are the same file') 
                else: 
                    if copyfile:
                        destination = os.path.join(mypath, os.path.basename(filename_txt))
                        if os.path.abspath(filename_txt) != os.path.abspath(destination):
                            shutil.copy(filename_txt, destination)
                        else:
                            print('Skipping copy because source and destination are the same file') 
    
    
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
        
        
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
   
    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_H(path)