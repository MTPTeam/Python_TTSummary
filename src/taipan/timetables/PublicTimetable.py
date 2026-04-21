import xml.etree.ElementTree as ET
import os
import sys
import pandas as pd
import xlsxwriter
import time
import shutil

from PyQt6.QtWidgets import QApplication
from taipan.constants.locations import MISC_LOCATIONS, STATIONS_MASTER, YARDS
from taipan.gui.base import open_file_crossplatform, show_info, select_file
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


weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
### Conversion between rsx weekdaykey and what this translate to in shorthand english
weekdaykey_dict2 = {'120':'M-Th', '4':'Fri', '2':'Sat', '1':'Sun'}


### Used for 'Comes From' or 'Continues To' rows to avoid having stabling locations in the public timetable
### First or last station reassigned if a non-revenue location
### Code can be changed to iterate 'entries' over only revenue locations and skip this step but this method works fine too
city = 'RS'

name_to_code = { s['name']: code for code, s in STATIONS_MASTER['stations'].items()}

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
        
        
        ### If in future, the MTP team may only require let's say a weekend timetable and a weekday timetable to be created,
        ###  this code will allow easy toggling of how many reports get generated for the user
        ### In the meantime, all useful combinations of reports will be created if the day_of_operation exists in the rsx.
        ###  That is, no blank timetable workbooks will be created
        Weekday = Weekend = MonThu = Friday = Saturday = Sunday = False
        Weekday = True
        Weekend = True
        MonThu = True
        Friday = True
        Saturday = True
        Sunday = True
        workbooks = []
        
        Weekday =  124 if Weekday  else False
        Weekend =  130 if Weekend  else False
        MonThu =   60  if MonThu   else False
        Friday =   64  if Friday   else False
        Saturday = 128 if Saturday else False
        Sunday =   2   if Sunday   else False
        
        workbooks_dict = {
            Weekday:  weekdayworkbook,
            Weekend:  weekendworkbook,
            MonThu:   monthuworkbook,
            Friday:   fridayworkbook,
            Saturday: saturdayworkbook,
            Sunday:   sundayworkbook,
            }
        
        for day in [Weekday, Weekend, MonThu, Friday, Saturday, Sunday]:
            daysheet = workbooks_dict.get(day)
            if day:
                workbooks.append(daysheet)
                
              
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
        newstations = []
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
                
                if name not in name_to_code:
                    newstations.append(name)
                    # optionally add to name_to_code so script continues without erroring
                    name_to_code[name] = stID
            
    
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
        
            def stoptime_info(entry_index): 
                """ Returns the arrival and departure times for the nth stop in a trip """
                
                x = entry_index
                departure = train[1][x].attrib['departure'] 
                
                stoptime = int(train[1][x].attrib.get('stopTime',0))
                if stoptime == 1:
                    stoptime = 0
                    
                arrival = str(pd.Timedelta(departure) - pd.Timedelta(seconds=stoptime))  
                if arrival[:6] == '1 days':
                    arrival = str(24 + int(arrival[7:9])) + str(arrival[9:])
                else: arrival = arrival[7:]
        
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
                o_line = line_station_lookup.get(oID)
                d_line = line_station_lookup.get(dID)
                condition = (o_line == line or d_line == line)
                if Outbound:
                    condition = condition and (d_line == line)
                else:
                    condition = condition and (o_line == line)

                
                if condition:
                    tripdict = {}
                    tripdict['Train ID'] = tn
                    tripdict['VirtualCBD'] = revenue_entries[0].attrib['departure']
                    # determine split point for this specific train
                    train_station_ids = {e.attrib['stationID'] for e in entries}
                    corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
                    if corridor:
                        if 'RTL' in train_station_ids:
                            train_split = CITY_TERMINUS[(corridor, True)]
                        elif 'RS' in train_station_ids or 'BNC' in train_station_ids:
                            train_split = CITY_TERMINUS[(corridor, False)]
                        else:
                            train_split = None
                    else:
                        train_split = None
                    for n, x in enumerate(entries):
                        stationName = x.attrib['stationName']
                        stationID   = x.attrib['stationID']
                        stationType = x.attrib['type']
                        dwell       = int(x.attrib['stopTime']) if x.get('stopTime') else 0
                        (arrival, departure) = stoptime_info(n)
                        if stationType == 'pass':
                            tripdict[stationID] = 'exp'
                        elif stationID == last_listed_station:
                            tripdict[stationID] = arrival
                        elif stationID in ['MOH','EUD','WOB','PAL'] and dwell >= 360:
                            tripdict[stationID] = arrival
                        else:
                            tripdict[stationID] = departure
                        if stationName == 'Roma Street':
                            tripdict['RSarr'] = arrival
                            tripdict['RSdep'] = departure
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
                    tripdict['DoO'] = weekdaykey_dict2.get(WeekdayKey)
                        
                    
                    # tripdict['DoO'] = 'M-Th' if WeekdayKey=='120' else 'Fri'

                    # use od to populate comes to and continues to since we previously filtered out the yards and misc locations 
                    tripdict['Comes From'] = oID   
                    tripdict['Continues2'] = dID


                    if 'VirtualCBD' not in tripdict:
                        print(f'{tn} missing VirtualCBD, skipping')
                        return

                    triplist.append(tripdict)
                
        
            def refine_triplist(triplist, stations):
                """
                Given a list for a line in a particular direction,
                Sort the list chronologically and merge trips that run on multiple days
                """
                SORT_ORDER = {'M-Th': 0, 'Fri': 1, 'Sat': 2, 'Sun':3}
                triplist.sort(key=lambda x: SORT_ORDER[x['DoO']])
                triplist.sort(key=lambda x: x['VirtualCBD'])
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
        
        
        
            def write_timetable(sheet, triplist, stations, line):
                """ Write the data to the worksheet, including train ID, DoO and departure times for each station """

                if not stations:
                    return
                
                (title, font1, boldfont1, font2, boldfont2, mainstations) = lineinfo_dict.get(line)
                if stations:
                    stations_long = list(zip(*stations))[0]
                    stations_abr  = list(zip(*stations))[1]
                    triplist = refine_triplist(triplist, stations_abr)
                
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
            list1  = []
            list2  = []
            list3  = []
            list4  = []
            list5  = []
            list6  = []
            list7  = []
            list8  = []
            list9  = []
            list10 = []
            list11 = []
            list12 = []
            list13 = []
            list14 = []
            list15 = []
            list16 = []
            list17 = []
            list18 = []
            list19 = []
            list20 = []
            list21 = []
            list22 = []
            list23 = []
            list24 = []
            
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

            
            print(f'all_entries count: {len(all_entries)}')
            print('Sample station IDs:', [e.attrib['stationID'] for e in all_entries[:10]])
            
            
            """line_station_order = {line: [] for line in STATIONS_MASTER['lines']}

            for e in all_entries:
                code = e.attrib['stationID']
                line = line_station_lookup.get(code)
                if line and line in line_station_order:
                    name = e.attrib['stationName']
                    if (name, code) not in line_station_order[line]:
                        line_station_order[line].append((name, code))
            # Apply corridor split point
            for line in line_station_order:
                corridor = STATIONS_MASTER['lines'].get(line, {}).get('corridor')
                split_at = CITY_TERMINUS.get((corridor, tunnel)) if corridor else None
                if split_at:
                    codes = [code for name, code in line_station_order[line]]
                    if split_at in codes:
                        line_station_order[line] = line_station_order[line][:codes.index(split_at) + 1]"""
        


            line_station_order = {line: [] for line in STATIONS_MASTER['lines']}
            for train in root.iter('train'):
                if 'Empty' in train[1][0].attrib['trainTypeId']:
                    continue
                if train[0][0][0].attrib['weekdayKey'] not in weekdaykeys:
                    continue

                train_entries = [e for e in train.iter('entry')
                                if STATIONS_MASTER['stations'].get(e.attrib['stationID'])
                                and not STATIONS_MASTER['stations'][e.attrib['stationID']]['non_revenue']]

                if not train_entries:
                    continue

                o_line = line_station_lookup.get(train_entries[0].attrib['stationID'])
                d_line = line_station_lookup.get(train_entries[-1].attrib['stationID'])
                suburban_line = o_line if o_line not in ('Inner City', 'Normanby', None) else d_line

                if not suburban_line or suburban_line not in line_station_order:
                    continue

                # only use inbound trains (origin is suburban line)

                if o_line != suburban_line:
                    continue

                corridor = STATIONS_MASTER['lines'].get(suburban_line, {}).get('corridor')
                split_at = CITY_TERMINUS.get((corridor, tunnel)) if corridor else None

                for e in train_entries:
                    code = e.attrib['stationID']
                    name = e.attrib['stationName']

                    if (name, code) not in line_station_order[suburban_line]:
                        line_station_order[suburban_line].append((name, code))

                    if split_at and code == split_at:
                        break
            


            # Build final station_lists dict
            station_lists = {}
            for line in STATIONS_MASTER['lines']:


                inbound  = [('Comes From', 'CF')] + line_station_order[line] + [('Continues To', 'CT')]
                outbound = [('Comes From', 'CF')] + list(reversed(line_station_order[line])) + [('Continues To', 'CT')]
                #inbound  = line_station_order[line] + [('Continues To', 'CT')]
                #outbound = [('Comes From', 'CF')] + list(reversed(line_station_order[line]))
                station_lists[(line, False)] = inbound
                station_lists[(line, True)]  = outbound
                                                    

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

                
                build_triplist( list1,  'Beenleigh'                                )
                build_triplist( list2,  'Beenleigh',                 Outbound=True )
                build_triplist( list3,  'Caboolture - Gympie North'                ) 
                build_triplist( list4,  'Caboolture - Gympie North', Outbound=True )
                build_triplist( list5,  'Cleveland'                                )
                build_triplist( list6,  'Cleveland',                 Outbound=True )
                build_triplist( list7,  'Doomben'                                  )
                build_triplist( list8,  'Doomben',                   Outbound=True )
                build_triplist( list9,  'Ferny Grove'                              )
                build_triplist( list10, 'Ferny Grove',               Outbound=True )
                build_triplist( list11, 'Varsity Lakes - Airport'                  )
                build_triplist( list12, 'Varsity Lakes - Airport',   Outbound=True )
                build_triplist( list15, 'Inner North'                              )
                build_triplist( list16, 'Inner North',               Outbound=True )
                build_triplist( list17, 'Inner City'                               )
                build_triplist( list18, 'Inner City',                Outbound=True )
                build_triplist( list13, 'Ipswich - Rosewood'                       )
                build_triplist( list14, 'Ipswich - Rosewood',        Outbound=True )
                build_triplist( list19, 'Redcliffe'                                )
                build_triplist( list20, 'Redcliffe',                 Outbound=True )
                build_triplist( list21, 'Shorncliffe'                              )
                build_triplist( list22, 'Shorncliffe',               Outbound=True )
                build_triplist( list23, 'Springfield'                              )
                build_triplist( list24, 'Springfield',               Outbound=True )
        
            
            write_timetable(BNH_in,      list1,  station_lists[('Beenleigh', False)],                'Beenleigh')
            write_timetable(BNH_out,     list2,  station_lists[('Beenleigh', True)],                 'Beenleigh')
            write_timetable(CAB_GYN_in,  list3,  station_lists[('Caboolture - Gympie North', False)], 'Caboolture - Gympie North')
            write_timetable(CAB_GYN_out, list4,  station_lists[('Caboolture - Gympie North', True)],  'Caboolture - Gympie North')
            write_timetable(CVN_in,      list5,  station_lists[('Cleveland', False)],                'Cleveland')
            write_timetable(CVN_out,     list6,  station_lists[('Cleveland', True)],                 'Cleveland')
            write_timetable(DBN_in,      list7,  station_lists[('Doomben', False)],                  'Doomben')
            write_timetable(DBN_out,     list8,  station_lists[('Doomben', True)],                   'Doomben')
            write_timetable(FYG_in,      list9,  station_lists[('Ferny Grove', False)],              'Ferny Grove')
            write_timetable(FYG_out,     list10, station_lists[('Ferny Grove', True)],               'Ferny Grove')
            write_timetable(VYS_in,      list11, station_lists[('Varsity Lakes - Airport', False)],  'Varsity Lakes - Airport')
            write_timetable(VYS_out,     list12, station_lists[('Varsity Lakes - Airport', True)],   'Varsity Lakes - Airport')
            write_timetable(INN_in,      list15, station_lists[('Inner North', False)],              'Inner North')
            write_timetable(INN_out,     list16, station_lists[('Inner North', True)],               'Inner North')
            write_timetable(INC_in,      list17, station_lists[('Inner City', False)],               'Inner City')
            write_timetable(INC_out,     list18, station_lists[('Inner City', True)],                'Inner City')
            write_timetable(IPS_RSW_in,  list13, station_lists[('Ipswich - Rosewood', False)],       'Ipswich - Rosewood')
            write_timetable(IPS_RSW_out, list14, station_lists[('Ipswich - Rosewood', True)],        'Ipswich - Rosewood')
            write_timetable(RDP_in,      list19, station_lists[('Redcliffe', False)],                'Redcliffe')
            write_timetable(RDP_out,     list20, station_lists[('Redcliffe', True)],                 'Redcliffe')
            write_timetable(SHC_in,      list21, station_lists[('Shorncliffe', False)],              'Shorncliffe')
            write_timetable(SHC_out,     list22, station_lists[('Shorncliffe', True)],               'Shorncliffe')
            write_timetable(SFC_in,      list23, station_lists[('Springfield', False)],              'Springfield')
            write_timetable(SFC_out,     list24, station_lists[('Springfield', True)],               'Springfield')
            titles(daycode)
            
            # IPS_RSW_in.activate()
            # CAB_GYN_in.activate()
            # SHC_in.activate()
            # INC_in.activate()
            BNH_in.activate() 
            
            print(f'\nAll trains with weekdayKey {" or ".join(weekdaykeys)} have been processed')
            
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
            VYS_in        = book.add_worksheet('VYS+BDT-In')
            VYS_out       = book.add_worksheet('VYS+BDT-Out')
            INN_in        = book.add_worksheet('INN-In')
            INN_out       = book.add_worksheet('INN-Out')
            INC_in        = book.add_worksheet('INC-In')
            INC_out       = book.add_worksheet('INC-Out')
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
                'Varsity Lakes - Airport':    (yellowtitle,   thursdayyellow, thursdayyellowbold, fridayyellow, fridayyellowbold, vys_capitalstops),
                'Inner North':                (greytitle,     thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold,         inn_capitalstops),
                'Inner City':                 (greytitle,     thursdaygrey, thursdaygreybold, fridaygrey, fridaygreybold,         inc_capitalstops),
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
                VYS_in:       yellowtitle,
                VYS_out:      yellowtitle,
                INN_in:       greytitle,
                INN_out:      greytitle,
                INC_in:       greytitle,
                INC_out:      greytitle,
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
                title(VYS_in,       'Varsity Lakes/Airport to City - Inbound')
                title(VYS_out,      'City to Varsity Lakes/Airport - Outbound')
                title(INN_in,       'Inner North to City - Inbound')
                title(INN_out,      'City to Inner North - Outbound')
                title(INC_in,       'Inner City to City - Inbound')
                title(INC_out,      'City to Inner City - Outbound')
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
