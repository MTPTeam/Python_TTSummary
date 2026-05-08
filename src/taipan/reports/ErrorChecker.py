import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import os
import re
import time
import sys


from PyQt6.QtWidgets import QApplication
from taipan.constants.locations import MISC_LOCATIONS, STATIONS_MASTER, YARDS
from taipan.gui.base import open_file_crossplatform, show_info, select_file, show_error_safe, show_info_safe

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
# Check whether connecting trains share the same lineID on the same day (mismatched line IDs)
# Check if connecting train is missing for the same day (missing connecting train)
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





LINES_TO_CHECK = [l for l in STATIONS_MASTER['lines']
                 if l not in ('Normanby', 'Caboolture', 'Gympie North')]



 
 
yard_codes = {code for yard in YARDS.values() for code in yard['yards']}
misc_codes = set(MISC_LOCATIONS.keys())
non_revenue_stations = {
   code for code, s in STATIONS_MASTER['stations'].items()
   if s['non_revenue']
} | yard_codes | misc_codes


def main(path=None):
    try:

        
        app = QApplication.instance() or QApplication(sys.argv)

        if not path:
            path = select_file(
                caption="Select RSX file",
                directory="",
                filter_str="RSX Files (*.rsx);;All Files (*.*)"
            )

        if not path:
            return

        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        print(filename,'\n')
        
        tree = ET.parse(filename)
        root = tree.getroot()
        filename = filename[:-4]
        start_time = time.time()

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
        

        lineid_lookup = {}
        for train in root.iter('train'):
            tn = train.attrib['number']
            wk = train[0][0][0].attrib['weekdayKey']
            lineid_lookup[(tn, wk)] = train.attrib.get('lineID', '')

            
        
        
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
        lineid_mismatches   = []
        lineid_missing      = []

        

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

            # update to use xml_parser.py
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


            for conn in train.iter('connection'):
                conn_tn = conn.attrib.get('trainNumber')
                if not conn_tn:
                    continue
                conn_lineid = lineid_lookup.get((conn_tn, WeekdayKey))
                parent_lineid = train.attrib.get('lineID', '')
                if conn_lineid is None:
                    lineid_missing.append(f'Train {tn} on {day} connects to {conn_tn} which is not found on the same day')
                elif conn_lineid != parent_lineid:
                    lineid_mismatches.append(f'Train {tn} on {day} (lineID {parent_lineid}) connects to {conn_tn} (lineID {conn_lineid})')


            
            traintypeset = set([x.attrib['trainTypeId'] for x in train.iter('entry')])
            if len(traintypeset) > 1:
                traintypeset = ', '.join(traintypeset)
                multiunittrain.append(f'{tn} on {day} has more than 1 train type: {traintypeset}')
            
            traintype = [x.attrib['trainTypeId'] for x in train.iter('entry')][0]
            if 'Empty' not in traintype:
                stoptypes = [x.attrib['type'] for x in train.iter('entry') if x.attrib['stationID'] not in non_revenue_stations]
                
                origintype,destintype = stoptypes[0],stoptypes[-1]
                if origintype == 'pass':
                    originpass.append(f' - First pass: {tn} on {day} {oID}->{dID} - ')
                if destintype == 'pass':
                    destinpass.append(f' - Last pass: {tn} on {day} {oID}->{dID} - ')
            
            
            
            
            
            city_codes = {'RS', 'BNC', 'BRC', 'BHI', 'PKR', 'SBE', 'SBA', 'RTL', 'EXH', 'BOG', 'WLG', 'ALB'}
            entry_codes = [e.attrib['stationID'] for e in entries]
            line = None
            for candidate in LINES_TO_CHECK:
                line_codes = {
                    code for code, s in STATIONS_MASTER['stations'].items()
                    if s['line'] == candidate and s.get('unique', True)
                }
                if not sIDs & line_codes:
                    continue
                line = candidate
                line_all_codes = {
                    code for code, s in STATIONS_MASTER['stations'].items()
                    if s['line'] == candidate
                }
                line_indices = [i for i, c in enumerate(entry_codes) if c in line_all_codes]
                city_indices = [i for i, c in enumerate(entry_codes) if c in city_codes]
                if line_indices and city_indices:
                    increasing = min(line_indices) > min(city_indices)
                    decreasing = not increasing
                else:
                    increasing = decreasing = False
                break
            if line is None:
                unassigned.append([tn, oID, dID])
                direction = None
            else:
                direction = 'Down' if increasing else 'Up'

            

            if 'Empty' not in unittype:
                pass
                #print(f'{tn} {oID}->{dID} line={line} dir={direction} inc={increasing} dec={decreasing}, day ={weekdaykey_dict.get(WeekdayKey)}')
            
            
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
        
        if lineid_mismatches:
            printwl('\n\nConnected trains with mismatched lineIDs')
            for x in lineid_mismatches:
                printwl(x)

        if lineid_missing:
            printwl('\n\nConnections referencing a train not found on the same day')
            for x in lineid_missing:
                printwl(x)

        o.close
        print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
        
  
            

    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)



if __name__ == "__main__":
    main()
