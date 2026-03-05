import os
import xml.etree.ElementTree as ET
import re

class TrainInfo:

    def __init__(self, train):

        # to extend - add the metadata you want from the RSX into this init function. 
        # then add parsing logic function in this file and call it in parse_rsx 

        self.raw = train

        self.weekday = train[0][0][0].attrib['weekdayKey'] #extract weekdaykey

        # Basic metadata 
        self.number = train.attrib['number'] 
        self.lineID = train.attrib['lineID']

        # entries
        self.entries = list(train.iter('entry')) 
        self.origin = self.entries[0].attrib 
        self.destin = self.entries[-1].attrib

        # train type ID + cars 
        self.unit = self.origin['trainTypeId'].split('-', 1)[1] 
        self.cars = int(re.findall(r'\d+', self.origin['trainTypeId'])[0])

        # stationlist
        self.stations = [e.attrib['stationID'] for e in self.entries]

        # times 
        self.odep = self.origin['departure']
        self.ddep = self.destin['departure']


def load_rsx(path):
    # loads rsx from user specified directory 
    directory = '\\'.join(path.split('/')[0:-1])
    os.chdir(directory)
    filename = path.split('/')[-1] 
    tree = ET.parse(filename) 
    return tree.getroot(), filename[:-4]


def extract_trains(root):
    return [TrainInfo(t) for t in root.iter('train')]


def detect_duplicates(trains):
    # detects duplicates 
    seen = set()

    dup = []

    for t in trains:
        key = (t.number, t.weekday)
        if key in seen:
            dup.append(key)
        seen.add(key)
    return dup


#def extract_day_and_unit_lists(trains):


def extract_day_and_unit_lists(trains):
    d_list = []
    u_list = []

    for t in trains:
        if t.weekday not in d_list:
            d_list.append(t.weekday)
        if t.unit not in u_list:
            u_list.append(t.unit)
    return d_list, u_list



## TTS_SB specific function
def build_run_dict(trains):
    run_dict = {}


    for t in trains:
        run = t.lineID.split('~', 1)[1][1:] if '~' in t.lineID else t.lineID
        key = (run, t.weekday)

        if key not in run_dict:
             run_dict[key] = [
                t.unit,
                t.cars,
                1,
                t.origin['stationID'],
                t.destin['stationID'],
                t.odep,
                t.ddep,
                [t.number]
            ]
        else:
            rec = run_dict[key]
            rec[2] += 1
            rec[4] = t.destin['stationID']
            rec[6] = t.ddep
            rec[-1].append(t.number)
    return run_dict
        

def parse_rsx(path, *, want_trains = False, want_duplicates = False, want_days = False, want_units = False, want_runs = False):
    root , _ = load_rsx(path)


    trains = extract_trains(root) if (want_trains or want_duplicates or want_days or want_units or want_runs) else None
    duplicates = detect_duplicates(trains) if want_duplicates else None
    d_list, u_list = extract_day_and_unit_lists(trains) if (want_days or want_units) else (None, None)
    run_dict = build_run_dict(trains) if want_runs else None

    return root, trains, d_list, u_list, run_dict, duplicates



