import xml.etree.ElementTree as ET
import os
import sys
import pandas as pd
import xlsxwriter
import time
import shutil

from PyQt6.QtWidgets import QApplication
from taipan.constants.locations import MISC_LOCATIONS, STATIONS_MASTER, YARDS
from taipan.constants.days import ID_TO_SHORT, ID_TO_ALIAS, NAME_TO_ID, DAY_PRIORITY, SORT_ORDER_WEEK
from taipan.gui.base import open_file_crossplatform, select_checkboxes, show_info, select_file, show_info, show_info_scroll
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
CreateWorkbook = True
OpenWorkbook = True
# --------------------------------------------------------------------------------------------------- #


RS_ORDER = [
   ('Bowen Hills', 'BHI'),
   ('Fortitude Valley', 'BRC'),
   ('Central Arr', 'BNCarr'),
   ('Central Dep', 'BNCdep'),
   ('Roma Street Arr', 'RSarr'),
   ('Roma Street Dep', 'RSdep'),
   ('South Brisbane', 'SBE'),
   ('South Bank', 'SBA'),
   ('Park Road', 'PKR'),
]


RTL_ORDER = [
   ('Boggo Rd', 'BOG'),
   ('Woolloongabba', 'WLG'),
   ('Albert St', 'ALB'),
   ('Roma St Arr', 'RTLarr'),
   ('Roma St Dep', 'RTLdep'),
   ('Exhibition', 'EXH'),
]

### Used for 'Comes From' or 'Continues To' rows to avoid having stabling locations in the public timetable
### First or last station reassigned if a non-revenue location
### Code can be changed to iterate 'entries' over only revenue locations and skip this step but this method works fine too
city = 'RS'

name_to_code = { s['name']: code for code, s in STATIONS_MASTER['stations'].items()}


def reverse_with_arrdep(order):
   # Separate out arr/dep pairs and reverse the station order
   result = []
   i = len(order) - 1
   while i >= 0:
       name, code = order[i]
       if code.endswith('dep'):
           # find the matching arr which should be just before
           arr_name, arr_code = order[i-1]
           result.append((arr_name, arr_code))
           result.append((name, code))
           i -= 2
       elif code.endswith('arr'):
           # standalone arr without dep after (shouldn't happen but just in case)
           result.append((name, code))
           i -= 1
       else:
           result.append((name, code))
           i -= 1
   return result

def TTS_PTT(path, mypath = None):

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
        
        entryelems = root.findall('.//entry')
        tunnel = 'RTL' in {x.attrib['stationID'] for x in entryelems}
        CITY_TERMINUS = {
            ('south', False): 'BHI',
            ('south', True):  'EXH',
            ('north', False): 'RS',
            ('north', True):  'BOG',
            }

        filename = filename[:-4]
        
        weekdayfilename_xlsx =  f'PublicTimetable-{filename}-Weekday.xlsx'
        weekendfilename_xlsx =  f'PublicTimetable-{filename}-Weekend.xlsx'
        monthufilename_xlsx =   f'PublicTimetable-{filename}-Mon-Thu.xlsx'
        fridayfilename_xlsx =   f'PublicTimetable-{filename}-Fri.xlsx'
        saturdayfilename_xlsx = f'PublicTimetable-{filename}-Saturday.xlsx'
        sundayfilename_xlsx =   f'PublicTimetable-{filename}-Sunday.xlsx'
        
        weekdayworkbook =  xlsxwriter.Workbook(weekdayfilename_xlsx)
        weekendworkbook =  xlsxwriter.Workbook(weekendfilename_xlsx)
        monthuworkbook =   xlsxwriter.Workbook(monthufilename_xlsx)
        fridayworkbook =   xlsxwriter.Workbook(fridayfilename_xlsx)
        saturdayworkbook = xlsxwriter.Workbook(saturdayfilename_xlsx)
        sundayworkbook =   xlsxwriter.Workbook(sundayfilename_xlsx)
        
              
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
            for tn,day in tn_doubles: print(f' - 2 trains running on {ID_TO_SHORT[day]} with train number {tn} - ')
            time.sleep(15)
            sys.exit() 
        
        start_time = time.time()

           
        ### uniquestations_dict and network_vrt_dict are used to determine what Line that trip belongs to
        ### Virtual run time (vrt) dictionaries for each line are used to order trips chronologically 
        ###  due to some trips not running through the city making sorting trips by Central arrival unavailable
       
        
        line_station_lookup = {
        code: s['line']
        for code, s in STATIONS_MASTER['stations'].items()
        }
        name_to_code = {
        s['name']: code
        for code, s in STATIONS_MASTER['stations'].items()
        }
        name_to_code['Comes From'] = 'CF'
        name_to_code['Continues To'] = 'CT'

        
        ### d_list      tracks the days present in the rsx
        ### newstations tracks if new locations have been added to the geography that haven't yet been added to stationmaster
        ###              will allow the code to continue without erroring, stationmaster should then be amended 
        d_list = []
        newstations = set()
        revtrains = [x for x in root.iter('train') if 'Empty' not in x[1][0].attrib['trainTypeId']]
        
        for train in revtrains:
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
                
            for entry in entries:
                stID = entry.attrib['stationID']
                name = entry.attrib['stationName']

                if stID not in STATIONS_MASTER['stations']:
                    newstations.add(name)
                    name_to_code[name] = stID
        


        day_options = []
        if '120' in d_list: day_options.append(('Mon-Thu',  'monthu'))
        if '4'   in d_list: day_options.append(('Friday',   'friday'))
        if '2'   in d_list: day_options.append(('Saturday', 'saturday'))
        if '1'   in d_list: day_options.append(('Sunday',   'sunday'))
        if '120' in d_list and '4' in d_list:
            day_options.insert(0, ('Weekday (Mon-Fri)', 'weekday'))
        if '1'   in d_list and '2' in d_list:
            day_options.append(('Weekend (Sat-Sun)', 'weekend'))
        selected_days = select_checkboxes(title='Select Days of Operation',message='Choose which timetables to generate:',options=day_options, default_values=[v for _, v in day_options],)  # all checked by default
        if selected_days is None:
            return  # user cancelled



        Weekday  = 'weekday'  in selected_days
        Weekend  = 'weekend'  in selected_days
        MonThu   = 'monthu'   in selected_days
        Friday   = 'friday'   in selected_days
        Saturday = 'saturday' in selected_days
        Sunday   = 'sunday'   in selected_days


        Weekday  = 124 if Weekday  else False
        Weekend  = 130 if Weekend  else False
        MonThu   = 60  if MonThu   else False
        Friday   = 64  if Friday   else False
        Saturday = 128 if Saturday else False
        Sunday   = 2   if Sunday   else False
        workbooks_dict = {
            Weekday:  weekdayworkbook,
            Weekend:  weekendworkbook,
            MonThu:   monthuworkbook,
            Friday:   fridayworkbook,
            Saturday: saturdayworkbook,
            Sunday:   sundayworkbook,
        }
            
        workbooks = []
        for day in [Weekday, Weekend, MonThu, Friday, Saturday, Sunday]:
            daysheet = workbooks_dict.get(day)
            if day:
                workbooks.append(daysheet)
            
    
        if newstations:
            print('Locations not recorded in station dictionary')
            print('--------------------------------------------')
            for x in newstations:
                print(x)
            print('--------------------------------------------')
        

        ### These will be the row headers appearing in the worksheets - can be customised
        ### zip_stations will pair each location name up with a unique abbreviated station ID
        ###  these list of tuples will be fed into the write_workbook function to print the data for each station for each trip
    
        
        def write_workbook(daycode, weekdaykeys):
            """ 
            The use of a master function to write a workbook with all other functions nested within
            Run twice, one for school days and one for weekends
            """


            AIRPORT_STATIONS = {'BDT', 'BIT', 'AJN'}
            VARSITY_STATIONS = {'VYS', 'ROB', 'MRC', 'NRG', 'HLN', 'HID', 'CXM', 'PPA', 'ORM', 'ROBS', 'VYST'}
            INNER_NORTH_STATIONS = {'NTG', 'NND', 'TBU', 'EGJ', 'WWI', 'AIN'}

            
        
            def stoptime_info(entry):
                departure = entry.attrib['departure']
                stoptime = int(entry.attrib.get('stopTime', 0))
                if stoptime == 1:
                    stoptime = 0
                arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))
                if arrival[:6] == '1 days':
                    arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
                else:
                    arrival = arrival[7:]
                return (arrival, departure)

        
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

            
            def build_triplist(triplist, line, Outbound=False):
                """ 
                Fills an empty list with trips that match conditions for each line
                Info for each trip, including DoO and departure times, are contained in a dictionary - tripdict
                """
                # get last listed station from dynamic list instead of zipped_stations_dict
                station_list = station_lists[(line, Outbound)]
                #print(station_list)
                if station_list:
                    last_listed_station = station_list[-1][1]
               
                entries = train[1].findall('entry')
                entries = revenue_entries
                o_line = line_station_lookup.get(oID)
                d_line = line_station_lookup.get(dID)

                
                if line == 'Varsity Lakes':
                    condition = oID in VARSITY_STATIONS or dID in VARSITY_STATIONS
                    if Outbound:
                        condition = condition and dID in VARSITY_STATIONS
                    else:
                        condition = condition and oID in VARSITY_STATIONS
                elif line == 'Airport':
                    condition = oID in AIRPORT_STATIONS or dID in AIRPORT_STATIONS
                    if Outbound:
                        condition = condition and dID in AIRPORT_STATIONS
                    else:
                        condition = condition and oID in AIRPORT_STATIONS

                elif line == 'Inner North':                                          # add here
                    condition = oID in INNER_NORTH_STATIONS or dID in INNER_NORTH_STATIONS
                    if Outbound:
                        condition = condition and dID in INNER_NORTH_STATIONS
                    else:
                        condition = condition and oID in INNER_NORTH_STATIONS
                else:
                    

                    condition = (o_line == line or d_line == line)
                    if Outbound:
                        condition = condition and (d_line == line)
                    else:
                        condition = condition and (o_line == line)
                    train_station_ids = {e.attrib['stationID'] for e in revenue_entries}
                    corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
                    line_termini = {
                    code for code, s in STATIONS_MASTER['stations'].items()
                    if s['line'] == line and s['byline_terminus']
                    }


                    if corridor is None:
            
                        inner_city_codes = {code for code, s in STATIONS_MASTER['stations'].items() if s['line'] == line and not s['non_revenue']}
                        condition = (o_line == line or d_line == line) and (oID in inner_city_codes or dID in inner_city_codes)
                        order = RTL_ORDER if any(e.attrib['stationID'] == 'RTL' for e in revenue_entries) else RS_ORDER
                        order_codes = [code for _, code in order]
                        ic_entries = [e for e in revenue_entries if e.attrib['stationID'] in set(order_codes)]
                        if not ic_entries:
                            condition = False
                        else:
                            ic_codes = [e.attrib['stationID'] for e in ic_entries]
                            order_positions = [order_codes.index(c) for c in ic_codes if c in order_codes]
                            if len(order_positions) < 2:
                                is_inbound = True
                            else:
                                is_inbound = order_positions == sorted(order_positions)
                            if Outbound:
                                condition = condition and not is_inbound
                            else:
                                condition = condition and is_inbound

                
                                                                
                if condition:
                    tripdict = {}
                    tripdict['Train ID'] = tn
                    tripdict['VirtualCBD'] = revenue_entries[0].attrib['departure']
                    # determine split point for this specific train
                    train_station_ids = {e.attrib['stationID'] for e in entries}
                    corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
                    if corridor and ('RTL' in train_station_ids or 'RS' in train_station_ids or 'BNC' in train_station_ids):
                        if 'RTL' in train_station_ids:
                            train_split = CITY_TERMINUS[(corridor, True)]
                        else:
                            train_split = CITY_TERMINUS[(corridor, False)]
                    else:
                        train_split = None
 
                    reached_split = False if (Outbound and train_split) else True
       
                    for n, x in enumerate(entries):
                        stationName = x.attrib['stationName']
                        stationID   = x.attrib['stationID']
                        stationType = x.attrib['type']
                        dwell       = int(x.attrib['stopTime']) if x.get('stopTime') else 0
                        (arrival, departure) = stoptime_info(x)


                        # for outbound start writing from split point
                        if Outbound and train_split and stationID == train_split:
                            reached_split = True

                        if not reached_split:
                            continue

                        if stationType == 'pass':
                            tripdict[stationID] = 'exp'
                        elif stationID == last_listed_station:
                            tripdict[stationID] = arrival
                        elif stationID in ['MOH','EUD','WOB','PAL'] and dwell >= 360:
                            tripdict[stationID] = arrival
                        else:
                            tripdict[stationID] = departure


                        if stationName == 'Roma Street':
                            if stationID == 'RTL':
                                tripdict['RTLarr'] = arrival
                                tripdict['RTLdep'] = departure
                            else:
                                tripdict['RSarr'] = arrival
                                tripdict['RSdep'] = departure

                        if stationName == 'Central':
                            tripdict['BNCarr'] = arrival
                            tripdict['BNCdep'] = departure
                        if stationName == 'Brunswick Street':
                            tripdict['BRCarr'] = arrival
                            tripdict['BRCdep'] = departure
                        if stationName == 'Bowen Hills':
                            tripdict['BHIarr'] = arrival
                            tripdict['BHIdep'] = departure
                        # stop writing at this train's split point
                        if not Outbound and train_split and stationID == train_split:
                            break
                            
                    tripdict['AM/PM'] = 'am' if origin['departure'] < '12:00:00' or origin['departure'] > '24:00:00' else 'pm'
                    tripdict['DoO'] = ID_TO_ALIAS[WeekdayKey]
                    # tripdict['DoO'] = 'M-Th' if WeekdayKey=='120' else 'Fri'

                    # use od to populate comes to and continues to since we previously filtered out the yards and misc locations 
                    tripdict['Comes From'] = oID   
                    tripdict['Continues2'] = dID


                    if train_split is None and corridor is not None:
                        #print(f'Train {tn} shuttle - has RS: {"RS" in train_station_ids}, has RTL: {"RTL" in train_station_ids}, has BNC: {"BNC" in train_station_ids}')
                        #print(f'Station IDs: {train_station_ids}')
                        shuttle_key = f'{oID}-{dID}'
                        if shuttle_key not in shuttle_trips:
                            shuttle_trips[shuttle_key] = []
                        shuttle_trips[shuttle_key].append(tripdict)
                        return


                    if 'VirtualCBD' not in tripdict:
                        print(f'{tn} missing VirtualCBD, skipping')
                        return

                    triplist.append(tripdict)     
                
        
            def refine_triplist(triplist, stations, outbound=False):
                """
                Given a list for a line in a particular direction,
                Sort the list chronologically and merge trips that run on multiple days
                """
                sort_key = 'RSdep' if outbound else 'RSarr'
                triplist.sort(key=lambda x: x.get(sort_key) or x.get('RTLdep' if outbound else 'RTLarr') or x.get('VirtualCBD'))
                DELIMITER = '|'
                refinedtriplist = []
                for tripdict in triplist:
                    if tripdict == triplist[0]:
                        refinedtriplist.append(tripdict)
                    else:
                        same_train = False
                        idx = None
                        n = 3
                        end_idx = len(refinedtriplist) - 1
                        for i, rtd in enumerate(refinedtriplist):
                            if end_idx - i <= n:
                                same_train_list = []
                                for s in stations:
                                    same_station = timetrim(tripdict.get(s)) == timetrim(rtd.get(s))
                                    same_train_list.append(same_station)
                                same_train_list.append(tripdict.get('Comes From') == rtd.get('Comes From'))
                                same_train_list.append(tripdict.get('Continues2') == rtd.get('Continues2'))
                                same_train = all(same_train_list)
                                if same_train and rtd['DoO'] != tripdict['DoO']:
                                    idx = i
                                    break
                        if same_train and idx is not None:
                            refinedtriplist[idx]['DoO'] = 'M-F' if book == weekdayworkbook else 'WE'
                            if refinedtriplist[idx]['Train ID'] != tripdict['Train ID']:
                                refinedtriplist[idx]['Train ID'] = DELIMITER.join([refinedtriplist[idx]['Train ID'], tripdict['Train ID']])
                        else:
                            refinedtriplist.append(tripdict)
                return refinedtriplist
        
        
        
            def write_timetable(sheet, triplist, stations, line, outbound=False):

                """ Write the data to the worksheet, including train ID, DoO and departure times for each station """
                if not stations:
                    return
                
                (title, font1, boldfont1, font2, boldfont2, mainstations) = lineinfo_dict.get(line)
                if stations:
                    stations_long = list(zip(*stations))[0]
                    stations_abr  = list(zip(*stations))[1]
                    triplist = refine_triplist(triplist, stations_abr, outbound=outbound)
                    active_stations = [
                    (name, code) for name, code in zip(stations_long, stations_abr)
                    if code in ('CF', 'CT') or any(trip.get(code) for trip in triplist)
                    ]

                    if not active_stations:
                        return

                    stations_long = tuple(s[0] for s in active_stations)
                    stations_abr  = tuple(s[1] for s in active_stations)

                
                sheet.write_column('A2', ['Days of Operation','Train ID','Station'], boldleft)
                sheet.freeze_panes(5, 1)
                for i in range(1,len(stations)+5):
                    sheet.set_row(i,14.5)
        
                
                # Write the station names and bold key stations
                sheet.write_column('A6',stations_long,left)
                for s in mainstations:
                    if s not in stations_abr:
                        print(f'Main station {s} not in station list for {line}')
                        continue
                    ind = stations_abr.index(s)
                    row = 5 + ind
                    col = 0
                    st  = stations_long[ind]
                    sheet.write(row,col,st,boldleft)
        
                for (i,x) in enumerate(triplist,1):
                     
                    vals = []
                    laststationdep, firststationarr = False, False
                    # firststationarr = False
                    for idx,sID in enumerate(stations_abr):
                        # sID = station[-1]
                        
                        timevalue = x.get(sID)
                        if timevalue:
                            if firststationarr or 'arr' not in sID:
                                vals.append(timetrim(timevalue))
                            else:
                                vals.append(None)
                            firststationarr = True
                        else:
                            vals.append(None)
                            
                            
                        if timevalue:
                            if 'dep' in sID:
                                laststationdep = True 
                                laststationidx = idx
                            else:
                                laststationdep = False
                                
                    if laststationdep:
                        vals[laststationidx] = None
                        
                    if len(weekdaykeys) == 1:
                        font  = default
                        bfont = bold
                    else:
                        if x.get('DoO') in ('M-Th','Sun'):
                            font  = font2
                            bfont = boldfont2
                            
                        elif x.get('DoO') in ('Fri','Sat'):
                            font  = font1
                            bfont = boldfont1
                            
                        else:
                            font  = default
                            bfont = bold
                        
                    smallfont = smallfontdict.get(font)
                    DoO = x.get('DoO')
                    tID = x.get('Train ID')
                    ToD = x.get('AM/PM')
                    
                    sheet.write(0,i,'',title)
                    sheet.write(1,i,DoO,font)
                    if len(weekdaykeys) == 1:
                        sheet.write(2,i,tID,font)
                        sheet.write(3,i,ToD,font)
                    else:
                        sheet.write(2,i,tID,smallfont)
                        sheet.write(3,i,ToD,smallfont)
                    sheet.write(4,i,'',font)
                    
                    startrow = 5
                    for ii,v in enumerate(vals):
                         
                        if stations_abr[ii] in mainstations:
                            if v == 'exp':
                                sheet.write(ii+startrow,i,v,expressbold)
                            else:
                                sheet.write(ii+startrow,i,v,bfont)
                                
                        elif v != 'exp':
                            sheet.write(ii+startrow,i,v,font)
                            
                        else:
                            sheet.write(ii+startrow,i,v,express)       
                    
                    getCF = x.get('Comes From')
                    getCT = x.get('Continues2')
                    # vline = network_vrt_dict.get(line)
                    start  = getCF if getCF not in stations_abr else None
                    finish = getCT if getCT not in stations_abr else None
                    if 'Comes From' in stations_long:
                         cf = stations_long.index('Comes From') + 5
                         sheet.write(cf,i,start,font)               
                    if 'Continues To' in stations_long:
                         ct = stations_long.index('Continues To') + 5
                         sheet.write(ct,i,finish,font)
                         
                    sheet.set_column(i,i,6.3)
                        
            ### Initialise two lists for each line - one inbound, one outbound
            trip_lists = {(line, ob): [] for line in STATIONS_MASTER['lines'] for ob in (False, True)}
            # init tunnel since theyre not in stationmaster
            trip_lists[('Inner City RS',  False)] = []
            trip_lists[('Inner City RS',  True)]  = []
            trip_lists[('Inner City RTL', False)] = []
            trip_lists[('Inner City RTL', True)]  = []

            shuttle_trips = {}
            
            # Generate a iterable of all revenue services 
            revenue = (x for x in root.iter('train') if x[0][0][0].attrib['weekdayKey'] in weekdaykeys and 'Empty' not in x[1][0].attrib['trainTypeId'])
            all_entries = [
                e
                for train in root.iter('train')
                if train[0][0][0].attrib['weekdayKey'] in weekdaykeys
                and 'Empty' not in train[1][0].attrib['trainTypeId']
                for e in train.iter('entry')
                if STATIONS_MASTER['stations'].get(e.attrib['stationID'])
                and not STATIONS_MASTER['stations'][e.attrib['stationID']]['non_revenue']
                ]

            



            line_station_order = {line: [] for line in STATIONS_MASTER['lines']}
            # init inc rs and inc rtl
            line_station_order['Inner City RS']  = RS_ORDER
            line_station_order['Inner City RTL'] = RTL_ORDER

            for line in STATIONS_MASTER['lines']:
                corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
                all_train_entries = []
                for train in root.iter('train'):
                    if 'Empty' in train[1][0].attrib['trainTypeId']:
                        continue
                    if train[0][0][0].attrib['weekdayKey'] not in weekdaykeys:
                        continue
                    train_entries = [
                        (e.attrib['stationName'], e.attrib['stationID'])
                        for e in train.iter('entry')
                        if STATIONS_MASTER['stations'].get(e.attrib['stationID'])
                        and not STATIONS_MASTER['stations'][e.attrib['stationID']]['non_revenue']
                    ]
                    if not train_entries:
                        continue
                    oID_t = train_entries[0][1]
                    dID_t = train_entries[-1][1]
                    o_line = line_station_lookup.get(oID_t)
                    d_line = line_station_lookup.get(dID_t)
                    # Same condition logic as build_triplist
                    if line == 'Varsity Lakes':
                        condition = oID_t in VARSITY_STATIONS or dID_t in VARSITY_STATIONS
                    elif line == 'Airport':
                        condition = oID_t in AIRPORT_STATIONS or dID_t in AIRPORT_STATIONS
                    elif line == 'Inner North':
                        condition = oID_t in INNER_NORTH_STATIONS or dID_t in INNER_NORTH_STATIONS
                    elif STATIONS_MASTER['lines'].get(line, {}).get('corridor') is None:
                        INBOUND_TERMINI = { 'EXH', 'RS'}

                        inner_city_codes = {
                        code for code, s in STATIONS_MASTER['stations'].items()
                        if s['line'] == line and not s['non_revenue']}
                        condition = oID_t in inner_city_codes and dID_t in inner_city_codes
                        condition = condition and dID_t in INBOUND_TERMINI

                    else:
                        condition = (o_line == line or d_line == line)
                    if not condition:
                        continue
                    
                    # Trim to the city split point so city stations
                    # don't bleed into the wrong line's list
                    train_ids = {e[1] for e in train_entries}
                    has_tunnel = 'RTL' in train_ids
                    split_at = CITY_TERMINUS.get((corridor, has_tunnel)) if corridor else None
                    trimmed = []
                    for stop in train_entries:
                        trimmed.append(stop)
                        if split_at and stop[1] == split_at:
                            break
                    if trimmed:
                        
                        all_train_entries.append(trimmed)
              
                if corridor is None:
                    line_station_order[line] = RS_ORDER + RTL_ORDER
                else:
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


            # Build final station_lists dict
            station_lists = {}
            for line in STATIONS_MASTER['lines']:


                inbound  = [('Comes From', 'CF')] + line_station_order[line] + [('Continues To', 'CT')]
                outbound = [('Comes From', 'CF')] + list(reversed(line_station_order[line])) + [('Continues To', 'CT')]
                #inbound  = line_station_order[line] + [('Continues To', 'CT')]
                #outbound = [('Comes From', 'CF')] + list(reversed(line_station_order[line]))
                station_lists[(line, False)] = inbound
                station_lists[(line, True)]  = outbound

                # RS AND rtl
                station_lists[('Inner City RS',  False)] = [('Comes From', 'CF')] + RS_ORDER + [('Continues To', 'CT')]
                #station_lists[('Inner City RS',  True)]  = [('Comes From', 'CF')] + list(reversed(RS_ORDER)) + [('Continues To', 'CT')]
                station_lists[('Inner City RS', True)]  = [('Comes From', 'CF')] + reverse_with_arrdep(RS_ORDER)  + [('Continues To', 'CT')]
                station_lists[('Inner City RTL', False)] = [('Comes From', 'CF')] + RTL_ORDER + [('Continues To', 'CT')]
                #station_lists[('Inner City RTL', True)]  = [('Comes From', 'CF')] + list(reversed(RTL_ORDER)) + [('Continues To', 'CT')]
                station_lists[('Inner City RTL', True)] = [('Comes From', 'CF')] + reverse_with_arrdep(RTL_ORDER) + [('Continues To', 'CT')]


                for key in list(station_lists.keys()):
                    lst = station_lists[key]
                    codes_in_lst = [code for _, code in lst]
                    if 'BNCarr' in codes_in_lst or 'RSarr' in codes_in_lst:
                        continue  # already has arr/dep rows, skip
                    new_lst = []
                    for name, code in lst:
                        if code not in ('RS', 'BNC', 'RTL'):
                            new_lst.append((name, code))
                        if code == 'BNC':
                            new_lst.append(('Central Arr', 'BNCarr'))
                            new_lst.append(('Central Dep', 'BNCdep'))
                        if code == 'RS':
                            new_lst.append(('Roma Street Arr', 'RSarr'))
                            new_lst.append(('Roma Street Dep', 'RSdep'))
                        if code == 'RTL':
                            new_lst.append(('Roma Street Arr', 'RTLarr'))
                            new_lst.append(('Roma Street Dep', 'RTLdep'))
                    station_lists[key] = new_lst
 
                                                    

            for train in revenue:
                tn = train.attrib['number']
                WeekdayKey = train[0][0][0].attrib['weekdayKey']
                entries = [x for x in train.iter('entry')]
                revenue_entries = [
                e for e in entries
                if STATIONS_MASTER['stations'].get(e.attrib['stationID']) and
                not STATIONS_MASTER['stations'][e.attrib['stationID']]['non_revenue']
                ]
                oID = revenue_entries[0].attrib['stationID']
                dID = revenue_entries[-1].attrib['stationID']
                origin = revenue_entries[0].attrib

                
                for (line, ob), lst in trip_lists.items():
                    build_triplist(lst, line, Outbound=ob)
            

            sheet_map = {
                ('Beenleigh',                False): BNH_in,
                ('Beenleigh',                True):  BNH_out,
                ('Caboolture - Gympie North', False): CAB_GYN_in,
                ('Caboolture - Gympie North', True):  CAB_GYN_out,
                ('Cleveland',                False): CVN_in,
                ('Cleveland',                True):  CVN_out,
                ('Doomben',                  False): DBN_in,
                ('Doomben',                  True):  DBN_out,
                ('Ferny Grove',              False): FYG_in,
                ('Ferny Grove',              True):  FYG_out,
                ('Varsity Lakes',            False): VYS_in,
                ('Varsity Lakes',            True):  VYS_out,
                ('Airport',                  False): BDT_in,
                ('Airport',                  True):  BDT_out,
                ('Inner North',              False): INN_in,
                ('Inner North',              True):  INN_out,
          
                
                ('Ipswich - Rosewood',       False): IPS_RSW_in,
                ('Ipswich - Rosewood',       True):  IPS_RSW_out,
                ('Redcliffe',                False): RDP_in,
                ('Redcliffe',                True):  RDP_out,
                ('Shorncliffe',              False): SHC_in,
                ('Shorncliffe',              True):  SHC_out,
                ('Springfield',              False): SFC_in,
                ('Springfield',              True):  SFC_out,
                }
            for (line, ob), lst in trip_lists.items():

                if line == 'Inner City':

                    rs_trips  = [t for t in lst if not t.get('RTL')]
                    rtl_trips = [t for t in lst if t.get('RTL')]
                    write_timetable(RS_in  if not ob else RS_out,  rs_trips,  station_lists[('Inner City RS',  ob)], 'Inner City RS',  outbound=ob)
                    write_timetable(RTL_in if not ob else RTL_out, rtl_trips, station_lists[('Inner City RTL', ob)], 'Inner City RTL', outbound=ob)

                elif (line, ob) in sheet_map:
                    write_timetable(sheet_map[(line, ob)], lst, station_lists[(line, ob)], line, outbound=ob)
            titles(daycode)


            BNH_in.activate() 
            
            print(f'\nAll trains with weekdayKey {" or ".join(weekdaykeys)} have been processed')

            shuttleworkbook = xlsxwriter.Workbook(f'PublicTimetable-{filename}-{daycode}-Shuttles.xlsx')
            s_default  = shuttleworkbook.add_format({'align':'center','font_size':9})
            s_left     = shuttleworkbook.add_format({'align':'left','font_size':9})
            s_bold     = shuttleworkbook.add_format({'align':'center','font_size':9,'bold':True})
            s_boldleft = shuttleworkbook.add_format({'align':'left','font_size':9,'bold':True})
            for i, (shuttle_key, trips) in enumerate(shuttle_trips.items()):
                sheet_name = f'{shuttle_key}-{i}'[:31]
                sheet = shuttleworkbook.add_worksheet(sheet_name)
                trips.sort(key=lambda x: x['VirtualCBD'])
                shuttle_stations = []
                for trip in trips:
                    for code in trip:
                        if code not in ('Train ID', 'VirtualCBD', 'AM/PM', 'DoO', 'Comes From', 'Continues2'): 
                            station = STATIONS_MASTER['stations'].get(code)
                            if station and not station['non_revenue']:
                                name = station['name']
                                if (name, code) not in shuttle_stations:
                                    shuttle_stations.append((name, code))
                shuttle_stations = [('Comes From', 'CF')] + shuttle_stations + [('Continues To', 'CT')]
                stations_long = [s[0] for s in shuttle_stations]
                stations_abr  = [s[1] for s in shuttle_stations]

                sheet.write_column('A2', ['Days of Operation', 'Train ID', 'AM/PM', 'Station'], s_boldleft)
                sheet.freeze_panes(5, 1)
                for j in range(1, len(shuttle_stations) + 5):
                    sheet.set_row(j, 14.5)
                sheet.write_column('A6', stations_long, s_left)
                for col, trip in enumerate(trips, 1):
                    sheet.write(1, col, trip.get('DoO'), s_default)
                    sheet.write(2, col, trip.get('Train ID'), s_default)
                    sheet.write(3, col, trip.get('AM/PM'), s_default)
                    sheet.write(4, col, '', s_default)
                    for row, code in enumerate(stations_abr, 5):
                        val = timetrim(trip.get(code))
                        if val is not None:
                            sheet.write(row, col, val, s_default)
                    sheet.set_column(col, col, 6.3)
            shuttleworkbook.close()


            all_trip_ids = set()
            unmatched = []
            for lst in trip_lists.values():
                for t in lst:
                    for tid in t['Train ID'].split('|'):
                        all_trip_ids.add(tid)
            for trips in shuttle_trips.values():
                for t in trips:
                    for tid in t['Train ID'].split('|'):
                        all_trip_ids.add(tid)
            for train in root.iter('train'):
                if 'Empty' in train[1][0].attrib['trainTypeId']:
                    continue
                if train[0][0][0].attrib['weekdayKey'] not in weekdaykeys:
                    continue
                tn = train.attrib['number']
                if tn not in all_trip_ids:
                    entries = [
                        e for e in train.iter('entry')
                        if STATIONS_MASTER['stations'].get(e.attrib['stationID'])
                        and not STATIONS_MASTER['stations'][e.attrib['stationID']]['non_revenue']
                    ]
                    if entries:
                        oID_p = entries[0].attrib['stationID']
                        dID_p = entries[-1].attrib['stationID']
                        print(f'Unmatched revenue train: {tn} {oID_p}->{dID_p}')
                        unmatched.append((tn, oID_p, dID_p))


            shuttle_trips.clear()
                        
            dayofop_dict = {
                weekdayworkbook:  (weekdayfilename_xlsx, 'weekday'),
                weekendworkbook:  (weekendfilename_xlsx, 'weekend'),
                monthuworkbook:   (monthufilename_xlsx,  'Mon-Thurs'),
                fridayworkbook:   (fridayfilename_xlsx,  'Friday'),
                saturdayworkbook: (saturdayfilename_xlsx,'Saturday'),
                sundayworkbook:   (sundayfilename_xlsx,  'Sunday')
                }
            
            filename_xlsx,dayname = dayofop_dict.get(book)
            
            if CreateWorkbook:
                book.close()
                if copyfile:
                    destination = os.path.join(mypath, os.path.basename(filename_xlsx))
                    if os.path.abspath(filename_xlsx) != os.path.abspath(destination):
                        shutil.copy(filename_xlsx, destination)
                    else:
                        print('Skipping copy because source and destination are the same file') 
                else:
                    if OpenWorkbook:
                        os.startfile(rf'{filename_xlsx}')
                        print(f'Opening {dayname} workbook')
        

        ### Create the worksheets
        ### Format the broadsheet
        ### Print the data
        ### Generate and open the workbook
        for book in workbooks: 
            timetableinfo = book.add_worksheet('TimetableInfo')
            BNH_in        = book.add_worksheet('BNH-In')
            BNH_out       = book.add_worksheet('BNH-Out')
            CAB_GYN_in    = book.add_worksheet('CAB+GYN-In')
            CAB_GYN_out   = book.add_worksheet('CAB+GYN-Out')
            CVN_in        = book.add_worksheet('CVN-In')
            CVN_out       = book.add_worksheet('CVN_out')
            DBN_in        = book.add_worksheet('DBN-In')
            DBN_out       = book.add_worksheet('DBN-Out')
            FYG_in        = book.add_worksheet('FYG-In')
            FYG_out       = book.add_worksheet('FYG-Out')
            VYS_in  = book.add_worksheet('VYS-In')
            VYS_out = book.add_worksheet('VYS-Out')
            BDT_in  = book.add_worksheet('BDT-In')
            BDT_out = book.add_worksheet('BDT-Out')
            INN_in        = book.add_worksheet('INN-In')
            INN_out       = book.add_worksheet('INN-Out')
       

            RS_in   = book.add_worksheet('RS-In')
            RS_out  = book.add_worksheet('RS-Out')
            RTL_in  = book.add_worksheet('RTL-In')
            RTL_out = book.add_worksheet('RTL-Out')
            IPS_RSW_in    = book.add_worksheet('IPS+RSW-In')
            IPS_RSW_out   = book.add_worksheet('IPS+RSW-Out')
            RDP_in        = book.add_worksheet('RDP-In')
            RDP_out       = book.add_worksheet('RDP-Out')
            SHC_in        = book.add_worksheet('SHC-In')
            SHC_out       = book.add_worksheet('SHC-Out')
            SFC_in        = book.add_worksheet('SFC-In')
            SFC_out       = book.add_worksheet('SFC-Out')
            
            book.formats[0].set_align('center')
            book.formats[0].set_font_size(9)
        
            #Workbook formats
            default             = book.add_format({'align':'center','font_size':9})
            left                = book.add_format({'align':'left','font_size':9})
            bold                = book.add_format({'align':'center','font_size':9,'bold':True})
            boldleft            = book.add_format({'align':'left','font_size':9,'bold':True})
            six                 = book.add_format({'align':'center','font_size':6})
            express             = book.add_format({'align':'center','font_size':9,             'bg_color':'#FFEBBE'})
            expressbold         = book.add_format({'align':'center','font_size':9,'bold':True, 'bg_color':'#FFEBBE'})
            
        
            #Worksheet title formats
            redtitle            = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#D10019'})
            greentitle          = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#007D45'})
            darkbluetitle       = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#004170'})
            purpletitle         = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#705098'})
            yellowtitle         = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#FEC938'})
            greytitle           = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#797A7C'})
            bluetitle           = book.add_format({'align':'left','font_size':14,'bold':True, 'font_color':'white','bg_color':'#0075B7'})
            
        
            thursdayred         = book.add_format({'align':'center','font_size':9, 'bg_color':'#FFCCD2'}) 
            thursdayredsmall    = book.add_format({'align':'center','font_size':6, 'bg_color':'#FFCCD2'}) 
            thursdayredbold     = book.add_format({'align':'center','font_size':9, 'bg_color':'#FFCCD2','bold':True}) 
            fridayred           = book.add_format({'align':'center','font_size':9, 'bg_color':'#FF7F8E'}) 
            fridayredsmall      = book.add_format({'align':'center','font_size':6, 'bg_color':'#FF7F8E'}) 
            fridayredbold       = book.add_format({'align':'center','font_size':9, 'bg_color':'#FF7F8E','bold':True}) 
        
            thursdaygreen       = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCFFE8'})
            thursdaygreensmall  = book.add_format({'align':'center','font_size':6, 'bg_color':'#CCFFE8'})
            thursdaygreenbold   = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCFFE8','bold':True})
            fridaygreen         = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FFFC5'})
            fridaygreensmall    = book.add_format({'align':'center','font_size':6, 'bg_color':'#7FFFC5'})
            fridaygreenbold     = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FFFC5','bold':True})
            
            thursdayblue        = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCE9FF'})
            thursdaybluesmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#CCE9FF'})
            thursdaybluebold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#CCE9FF','bold':True})
            fridayblue          = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FC9FF'})
            fridaybluesmall     = book.add_format({'align':'center','font_size':6, 'bg_color':'#7FC9FF'})
            fridaybluebold      = book.add_format({'align':'center','font_size':9, 'bg_color':'#7FC9FF','bold':True})
            
            thursdaypurple      = book.add_format({'align':'center','font_size':9, 'bg_color':'#E4DDED'})
            thursdaypurplesmall = book.add_format({'align':'center','font_size':6, 'bg_color':'#E4DDED'})
            thursdaypurplebold  = book.add_format({'align':'center','font_size':9, 'bg_color':'#E4DDED','bold':True})
            fridaypurple        = book.add_format({'align':'center','font_size':9, 'bg_color':'#BDABD3'})
            fridaypurplesmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#BDABD3'})
            fridaypurplebold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#BDABD3','bold':True})
            
            thursdayyellow      = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEDC80'})
            thursdayyellowsmall = book.add_format({'align':'center','font_size':6, 'bg_color':'#FEDC80'})
            thursdayyellowbold  = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEDC80','bold':True})
            fridayyellow        = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEEDBE'})
            fridayyellowsmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#FEEDBE'})
            fridayyellowbold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#FEEDBE','bold':True})
            
            thursdaygrey        = book.add_format({'align':'center','font_size':9, 'bg_color':'#E5E5E5'})
            thursdaygreysmall   = book.add_format({'align':'center','font_size':6, 'bg_color':'#E5E5E5'})
            thursdaygreybold    = book.add_format({'align':'center','font_size':9, 'bg_color':'#E5E5E5','bold':True})
            fridaygrey          = book.add_format({'align':'center','font_size':9, 'bg_color':'#BEBEC0'})
            fridaygreysmall     = book.add_format({'align':'center','font_size':6, 'bg_color':'#BEBEC0'})
            fridaygreybold      = book.add_format({'align':'center','font_size':9, 'bg_color':'#BEBEC0','bold':True})
            
            smallfontdict = {
                default         :six,
                thursdayred     :thursdayredsmall,
                fridayred       :fridayredsmall,
                thursdayblue    :thursdaybluesmall,
                fridayblue      :fridaybluesmall,
                thursdaygreen   :thursdaygreensmall,
                fridaygreen     :fridaygreensmall,   
                thursdaypurple  :thursdaypurplesmall,
                fridaypurple    :fridaypurplesmall,
                thursdayyellow  :thursdayyellowsmall,
                fridayyellow    :fridayyellowsmall,   
                thursdaygrey    :thursdaygreysmall,
                fridaygrey      :fridaygreysmall,   
                }
        
            bnh_capitalstops = ['BNH','PKR','BNCarr','BNCdep']  
            cab_capitalstops = ['GYN','NBR','CAB','PET', 'NTG', 'EGJ','BNCarr','BNCdep']  
            cvn_capitalstops = ['MNY','PKR','BNCarr','BNCdep']
            dbn_capitalstops = ['EGJ','BNCarr','BNCdep','PKR']
            fyg_capitalstops = ['PKR','BNCarr','BNCdep']
            vys_capitalstops = ['BNH','PKR','BNCarr','BNCdep','EGJ']
            ips_capitalstops = ['BNCarr','BNCdep','MTZ','IDP','DAR','IPSarr','IPSdep'] 
            inn_capitalstops = ['NTG','BNCarr','BNCdep']
            inc_capitalstops = ['NTG','BNCarr','BNCdep']
            rdp_capitalstops = ['PET','NTG','BNCarr','BNCdep']
            shc_capitalstops = ['PKR','BNCarr','BNCdep','NTG']
            sfc_capitalstops = ['DAR','BNCarr','BNCdep']
            
            lineinfo_dict = {
                'Beenleigh':                  (redtitle,      thursdayred, thursdayredbold, fridayred, fridayredbold,             bnh_capitalstops),
                'Caboolture - Gympie North':  (greentitle,    thursdaygreen, thursdaygreenbold, fridaygreen, fridaygreenbold,     cab_capitalstops),
                'Cleveland':                  (darkbluetitle, thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         cvn_capitalstops),
                'Doomben':                    (purpletitle,   thursdaypurple, thursdaypurplebold, fridaypurple, fridaypurplebold, dbn_capitalstops),
                'Ferny Grove':                (redtitle,      thursdayred, thursdayredbold, fridayred, fridayredbold,             fyg_capitalstops),
                'Varsity Lakes': (yellowtitle, thursdayyellow, thursdayyellowbold, fridayyellow, fridayyellowbold, ['VYS','PKR','BHI']),
                'Airport': (yellowtitle, thursdayyellow, thursdayyellowbold, fridayyellow, fridayyellowbold, ['BDT','BIT','RS']),
                'Inner North':                (greytitle,     thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold,         inn_capitalstops),

                'Inner City RS':  (greytitle, thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold, ['BHI', 'BNC', 'RS', 'PKR']),
                'Inner City RTL': (greytitle, thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold, ['EXH', 'BOG']),

                'Ipswich - Rosewood':         (greentitle,    thursdaygreen, thursdaygreenbold, fridaygreen, fridaygreenbold,     ips_capitalstops),
                'Redcliffe':                  (bluetitle,     thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         rdp_capitalstops),
                'Shorncliffe':                (darkbluetitle, thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         shc_capitalstops),
                'Springfield':                (bluetitle,     thursdayblue, thursdaybluebold, fridayblue, fridaybluebold,         sfc_capitalstops)
            }
            
            linefont_dict = {
                BNH_in:       redtitle,
                BNH_out:      redtitle,
                CAB_GYN_in:   greentitle,
                CAB_GYN_out:  greentitle,
                CVN_in:       darkbluetitle,
                CVN_out:      darkbluetitle,
                DBN_in:       purpletitle,
                DBN_out:      purpletitle,
                FYG_in:       redtitle,
                FYG_out:      redtitle,
                VYS_in:  yellowtitle,
                VYS_out: yellowtitle,
                BDT_in:  yellowtitle,
                BDT_out: yellowtitle,
                INN_in:       greytitle,
                INN_out:      greytitle,
                RS_in:   greytitle,
                RS_out:  greytitle,
                RTL_in:  greytitle,
                RTL_out: greytitle,
                IPS_RSW_in:   greentitle,
                IPS_RSW_out:  greentitle,
                RDP_in:       bluetitle,
                RDP_out:      bluetitle,
                SHC_in:       darkbluetitle,
                SHC_out:      darkbluetitle,
                SFC_in:       bluetitle,
                SFC_out:      bluetitle,
                }
                
            def titles(daysofoperation):
                daysofoperation = ' - ' + daysofoperation
                def title(sheet,text):
                    font = linefont_dict.get(sheet)
                    text = text + daysofoperation
                    sheet.set_column(0,0,len(text)*1.43)
                    sheet.write('A1',text,font)
                title(BNH_in,       'Beenleigh to City - Inbound')
                title(BNH_out,      'City to Beenleigh - Outbound')
                title(CAB_GYN_in,   'Caboolture/Nambour/Gympie North to City - Inbound')
                title(CAB_GYN_out,  'City to Caboolture/Nambour/Gympie North - Outbound')
                title(CVN_in,       'Cleveland to City - Inbound')
                title(CVN_out,      'City to Cleveland - Outbound')
                title(DBN_in,       'Doomben to City - Inbound')
                title(DBN_out,      'City to Doomben - Outbound')
                title(FYG_in,       'Ferny Grove to City - Inbound')
                title(FYG_out,      'City to Ferny Grove - Outbound')
                title(VYS_in, 'Varsity Lakes to City - Inbound')
                title(VYS_out, 'City to Varsity Lakes - Outbound')
                title(BDT_in, 'Airport to City - Inbound')
                title(BDT_out, 'City to Airport - Outbound')
                title(INN_in,       'Inner North to City - Inbound')
                title(INN_out,      'City to Inner North - Outbound')
                title(RS_in,   'Roma Street to City - Inbound')
                title(RS_out,  'City to Roma Street - Outbound')
                title(RTL_in,  'RTL to City - Inbound')
                title(RTL_out, 'City to RTL - Outbound')
                title(IPS_RSW_in,   'Ipswich/Rosewood to City - Inbound')
                title(IPS_RSW_out,  'City to Ipswich/Rosewood - Outbound')
                title(RDP_in,       'Redcliffe Peninsula to City - Inbound')
                title(RDP_out,      'City to Redcliffe Peninsula - Outbound')
                title(SHC_in,       'Shorncliffe to City - Inbound')
                title(SHC_out,      'City to Shorncliffe - Outbound')
                title(SFC_in,       'Springfield to City - Inbound')
                title(SFC_out,      'City to Springfield - Outbound')
        
            if book == weekdayworkbook:
                if '120' in d_list and '4' in d_list:
                    write_workbook('Mon to Fri', ['120','4']) 
                    
            elif book == weekendworkbook:
                if '1' in d_list and '2' in d_list:
                    write_workbook('Sat to Sun', ['1','2']) 
                    
            elif book == monthuworkbook:
                if '120' in d_list:
                    write_workbook('Mon to Thu', ['120'])
                    
            elif book == fridayworkbook:
                if '4' in d_list:
                    write_workbook('Friday', ['4'])
                    
            elif book == saturdayworkbook:
                if '2' in d_list:
                    write_workbook('Saturday', ['2'])
                    
            elif book == sundayworkbook:
                if '1' in d_list:
                    write_workbook('Sunday', ['1'])
           
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            show_info('Public Timetable','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    path = select_file(caption="Select RSX file", directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")
    TTS_PTT(path)
