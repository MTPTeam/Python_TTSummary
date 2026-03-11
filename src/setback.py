import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import sys
import re
from datetime import timedelta
import os
import logging
import traceback
import time

def parseTimeDelta(s):
    if str(s) != 'nan':
        d = re.match(
                r'((?P<days>\d+) days, )?(?P<hours>\d+):'
                r'(?P<minutes>\d+):(?P<seconds>\d+)',
                str(s)).groupdict(0)
        return timedelta(**dict(( (key, int(value))
                              for key, value in d.items() ))) 
    else:
        return np.NaN

def timedeltatohhmmss(timegiven):
    timegiven = str(timegiven)
    if timegiven == 'NaT':
        return ''
    elif ( timegiven.split()[0] == '0' and
          timegiven.split()[1] == 'days' ):
        return timegiven.split()[2]
    elif timegiven[:9] == '1 days 00':
        return '24' + timegiven[9:]
    elif timegiven[:9] == '1 days 01':
        return '25' + timegiven[9:]
    elif timegiven[:9] == '1 days 02':
        return '26' + timegiven[9:]
    elif timegiven[:9] == '1 days 03':
        return '27' + timegiven[9:]
    elif timegiven[:9] == '1 days 04':
        return '28' + timegiven[9:]
    elif timegiven[:9] == '1 days 05':
        return '29' + timegiven[9:]
    else:
        sys.exit('Failed in timedeltahhmmss function - Check Script')

def returnday(str2):
    if str2 == '120':
        str2 = 'MTh'
        return str2
    elif str2 == '4':
        str2 = 'Fri'
        return str2
    elif str2 == '2':
        str2 = 'Sat'
        return str2
    elif str2 == '1':
        str2 = 'Sun'
        return str2

    else:
        return None

try:
    from tkinter import Tk     # from tkinter import Tk for Python 3.x
    from tkinter.filedialog import askopenfilename
    
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    print(path,'\n')
    
    directory = '\\'.join(path.split('/')[0:-1])
    os.chdir(directory)
    filename = path.split('/')[-1]

    tree = ET.parse(filename)
    root = tree.getroot()
    
    train_nums,daycodes,train_types = [],[],[]
    stationsinTrains,trackIDinTrains,departureinTrains,stopTimesinTrains = [],[],[],[]
    setback_stations  = ["MOH", "EUD", "PAL", "WOB"]
    
    for train in root.findall('./timetable/train'):
        
        train_num = train.attrib['number']
        if train_num[0] == 'H':
            continue
        weekdayKey = list(set([elem.attrib['weekdayKey'] for elem in train.iter() if 'weekdayKey' in elem.attrib ]))
        #block = find_between(block, '~ ', '\">')
        entryelems = [elem for elem in train.iter() if elem.tag == 'entry' if elem.attrib['stationID'] in setback_stations]
        stationsinTrain = [elem.attrib['stationID'] for elem in entryelems]
        trackIDinTrain = [elem.attrib['trackID'] for elem in entryelems]
        departureinTrain = [elem.attrib['departure'] for elem in entryelems]
        stopTimesinTrain = [int(elem.attrib['stopTime']) if 'stopTime' in elem.attrib else np.NaN for elem in entryelems]
        train_type = list(set([elem.attrib['trainTypeId'] for elem in train.iter() if 'trainTypeId' in elem.attrib ]))
        weekdayKey = list(set([elem.attrib['weekdayKey'] for elem in train.iter() if 'weekdayKey' in elem.attrib ]))
        
        daycode = returnday(weekdayKey[0])
        if daycode is None:
            pass
        
        train_nums = train_nums + [train_num]*len(departureinTrain)
        daycodes = daycodes + [daycode]*len(departureinTrain)
        train_types = train_types + [train_type[0]]*len(departureinTrain)
        
        stationsinTrains = stationsinTrains + stationsinTrain
        trackIDinTrains = trackIDinTrains + trackIDinTrain
        departureinTrains = departureinTrains + departureinTrain
        stopTimesinTrains = stopTimesinTrains + stopTimesinTrain
    
    df = pd.DataFrame({
                       'Train' : train_nums, 'Day': daycodes,'TrainType': train_types,
                       'Station' : stationsinTrains, 'TrackID': trackIDinTrains,'Arrive': np.NaN,
                       'Depart': departureinTrains, 'Dwell' : stopTimesinTrains
                       })
    
    df['ArriveTimedelta'] = df.Depart.apply(parseTimeDelta) - pd.to_timedelta(df.Dwell, unit = 's') 
    df['Arrive'] = df.ArriveTimedelta.astype(str).apply(timedeltatohhmmss)
    df['Arrive'] = [ x if x != '' else np.NaN for x in df.Arrive ]
    df = df[['Train', 'Day', 'TrainType', 'Station','TrackID', 'Arrive', 'Depart', 'Dwell']]
    
    
    df = df[~df.TrainType.str.contains('Empty')]
    aa = df.groupby(['Day','Station','Arrive','Depart','Dwell','TrackID'])['Train'].apply(list)
    aa = aa.reset_index()
    aa['Train'] = [x[0] for x in aa.Train]
    
    sminus1 = (aa[aa.Dwell >= 360].index - 1).tolist()
    s0 = (aa[aa.Dwell >= 360].index).tolist()
    splus1 = (aa[aa.Dwell >= 360].index + 1).tolist()
    
    index_list = sorted(sminus1 + s0 + splus1)
    ab = aa.loc[aa.index[index_list]]
    
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))
    
    j = 0
    for i in chunker(ab,3):
        if (parseTimeDelta(i.iloc[1].Arrive) - parseTimeDelta( i.iloc[0].Arrive ) >= timedelta( minutes = 3 ) and
            parseTimeDelta(i.iloc[2].Arrive) - parseTimeDelta( i.iloc[1].Arrive ) >= timedelta( minutes = 3) ):
            ab.loc[i.iloc[1].name, "Setback"] = i.iloc[1].Station + '1'
        else:
            ab.loc[i.iloc[1].name, "Setback"] = i.iloc[1].Station + '2'
            
        j = j + 1
        ab.loc[i.index, "TrainGroup"] = j
        
    ac = ab.dropna()
    
    for train in root.findall('./timetable/train'):
        
        weekdayKey = list(set([elem.attrib['weekdayKey'] for elem in train.iter() if 'weekdayKey' in elem.attrib ]))
        daycode = returnday(weekdayKey[0])
        
        set_df = ac[(ac.Train == train.attrib['number']) & (ac.Day == daycode)]
            
        for entry in train.findall('.//entry'):
            try:
                del entry.attrib["comment"]
            except KeyError:
                pass
            if len(set_df) >= 1:
                if entry.attrib['stationID'] in set_df.Station.tolist():
                    entry.attrib['comment'] = set_df[set_df.Station == entry.attrib['stationID']].Setback.values[0]
    
    new_name = filename.split('.rsx')[0] + "_s" + ".rsx"
    tree.write(new_name)
    
    from tkinter import messagebox
    messagebox.showinfo('ITOPS Setback Nodes added','Process Done')
        
except Exception as e:
    logging.error(traceback.format_exc())
    time.sleep(15)
