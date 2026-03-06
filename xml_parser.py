from importlib.resources import path
import os
import xml.etree.ElementTree as ET
import re
import MTP_constants
import typing
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

        # additional (used by SC)
        self.start_id = self.origin.get('stationID')
        self.end_id   = self.destin.get('stationID')
        self.start_time = self.odep
        self.end_time   = self.ddep

        # run ID 
        self.run = self.lineID.split('~', 1)[1][1:] if '~' in self.lineID else self.lineID
    
    @staticmethod
    def threecar_scalar(unit: str, cars: int) -> int:
        # Return the scalar (unit delta) used in SC 
        # - NGR/NGRE are single consist (1), other are 2 if 6 cars, else 1)
        
        if unit in ('NGR', 'NGRE'):
            return 1
        return 2 if cars == 6 else 1

def load_rsx(path):
    # loads rsx from user specified directory (using absolute path)
    tree = ET.parse(path)
    filename_wo_ext = os.path.splitext(os.path.basename(path))[0]
    return tree.getroot(), filename_wo_ext



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




def build_run_dict(trains):

    # { (run, weekday): [unit, cars, trips, start_station, end_station, start_time, end_time, [train_numbers]] }
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
        


def resolve_DoO(wkdk):
    # wkdk is a tuple of strings like ('120','64')
    for day in MTP_constants.DAY_PRIORITY:
        if day in wkdk:
            print("DEBUG:", day, type(MTP_constants.WEEKDAY_KEYS_MASTER[day]))
            return MTP_constants.WEEKDAY_KEYS_MASTER[day]['short']   # or long/alias
    return None


def parse_rsx(path, *, want_trains = False, want_duplicates = False, want_days = False, want_units = False, want_runs = False):
    root , _ = load_rsx(path)


    trains = extract_trains(root) if (want_trains or want_duplicates or want_days or want_units or want_runs) else None
    duplicates = detect_duplicates(trains) if want_duplicates else None
    d_list, u_list = extract_day_and_unit_lists(trains) if (want_days or want_units) else (None, None)
    run_dict = build_run_dict(trains) if want_runs else None

    return root, trains, d_list, u_list, run_dict, duplicates


def sort_days(days):
    ORDER = ['64','32','16','8','120','4','2','1']
    return sorted(days, key=ORDER.index)

def sort_units(units):
    ORDER = ['REP','NGR','NGRE','IMU100','EMU','SMU','HYBRID','ICE','DEPT']
    return sorted(units, key=ORDER.index)


def normalise_days(days: typing.Iterable[str], *, collapse_mon_thu: bool = True) -> typing.List[str]:
    # Sorts days and optionally removes 120 when Mon–Thu codes are present. '120' = Mon–Thu composite code, explicit codes are {'64','32','16','8'} 
    
    sorted_days = sort_days(days)

    if collapse_mon_thu:
        weekday_codes = {'64', '32', '16', '8'}

        # if any explicit weekday exists and '120' is present then remove '120'. 
        if any(d in sorted_days for d in weekday_codes) and '120' in sorted_days:
            sorted_days = [d for d in sorted_days if d != '120']

    return sorted_days




