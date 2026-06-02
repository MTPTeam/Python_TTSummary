from importlib.resources import path
import os
import sys
import sys
import xml.etree.ElementTree as ET
import re
import typing
from taipan.constants.trains import SORT_ORDER_UNIT, TRAIN_TYPE_MASK
from taipan.constants.days import WEEKDAY_KEYS_MASTER, DAY_PRIORITY, SORT_ORDER_WEEK, ID_TO_SHORT
import numpy as np
from taipan.gui.base import show_info
from PyQt6.QtWidgets import QApplication
        
# collect unknown units for reporting at the end of parsing (don't want to spam popups during parsing, but still want to know if we have unrecognised units)        
UNKNOWN_UNITS = set()

def rep_to_qmu_tokenwise(text):
    # replace standalone REP tokens with QMU (preserve delimiters)
    # token = [A-Za-z0-9]+ delimited by non-alnum (or start/end)
    out = []
    i = 0
    while i < len(text):
        m = re.search(r'[A-Za-z0-9]+', text[i:])
        if not m:
            out.append(text[i:])
            break
        start = i + m.start()
        end   = i + m.end()
        out.append(text[i:start])
        token = text[start:end]
        if token.upper() == 'REP':
            out.append('QMU')
        else:
            out.append(token)
        i = end
    return ''.join(out)


def normalise_train_type(raw):
    """
      - Apply TRAIN_TYPE_MASK if exact (case-insensitive) key exists.
      - Replace standalone 'REP' tokens with 'QMU'.
      - If '(AW0)' present -> ensure 'Empty_' prefix.
      - If '(AW3)' present -> ensure NO 'Empty_' prefix.
      - Strip trailing '_S' and '_Surface'.
      - Keep everything else unchanged.
    """
    if not raw:
        return ''

    s = raw.strip()

    # mask (case insensitive exact key)
    
    low = s.lower()
    if low in TRAIN_TYPE_MASK:
        s = TRAIN_TYPE_MASK[low]
        # fall back - still allow AW enforcement + suffix strip in case mask value carries them
    # else: keep s as-is

    s = rep_to_qmu_tokenwise(s)

    # detect AW state (without removing it yet)
    aw0 = bool(re.search(r'\(AW0\)', s, flags=re.IGNORECASE))
    aw3 = bool(re.search(r'\(AW3\)', s, flags=re.IGNORECASE))

    # enforce empty from AW states
    has_empty = s.lower().startswith('empty_')
    core = s[6:] if has_empty else s  # remove existing Empty_ to re-apply cleanly

    if aw0:
        # must be Empty_
        if not has_empty:
            s = 'Empty_' + core
        else:
            s = 'Empty_' + core  # already had it
    elif aw3:
        # must NOT be Empty_
        s = core
    else:
        # keep whatever was there originally
        s = ('Empty_' + core) if has_empty else core

    # Strip trailing '_S' and '_Surface' (case-insensitive)
    s = re.sub(r'(_S|_Surface)$', '', s, flags=re.IGNORECASE)

    # Also remove any remaining '(AWx)' tags from the tail 
    s = re.sub(r'\(AW\d\)', '', s, flags=re.IGNORECASE)

    # collapse accidental double underscores produced by removals
    s = re.sub(r'__+', '_', s).strip('_')

    return s

def tag_vyst_trains(trains, run_dict):
   """
   For each train, stamp .vyst_is_yard = True if its runID's
   first origin or last destination is VYST.
   """
   vyst_runs = {
       key for key, rec in run_dict.items()
       if rec[3] == 'VYST' or rec[4] == 'VYST'
   }
   for t in trains:
       t.vyst_is_yard = (t.run, t.weekday) in vyst_runs


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

        # train type ID + cars (NORMALISED)
        self.train_type_raw = self.origin.get('trainTypeId', '')
        self.train_type = normalise_train_type(self.train_type_raw)   # raw variant
        
        #self.train_type_revenue = self.train_type.replace('Empty_', '') # revenue only train 

        self.is_empty_train = self.train_type.startswith('Empty_')

        self.unit = self._extract_unit_from_normalised(self.train_type)
        self.cars = self._extract_cars_from_normalised(self.train_type)

        if self.unit not in SORT_ORDER_UNIT:
            UNKNOWN_UNITS.add((self.unit, self.train_type, self.train_type_raw))

        # add upward/downward direction here
        self.direction = self._get_direction()

        # pattern attribute includes day, sector, empty or not, return/to. can use it to get other info if you want 
        self.pattern = train.attrib['pattern']

        # this is the sector (as an integer)
        match = re.search(r"Sector\s+(\d+)", self.pattern)
        self.sector = int(match.group(1)) if match else None

        #print("sector: ", self.sector)

        # stationlist
        self.stations = [e.attrib['stationID'] for e in self.entries]

        # get connection elem if present - at most there will be one for each train
        self.connection = next((e.find('connection') for e in self.entries if e.find('connection') is not None),None)
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

        # data from entries 
        self.departures  = [e.attrib['departure'] for e in self.entries]
        self.stop_times  = [int(e.attrib['stopTime']) if 'stopTime' in e.attrib else np.nan for e in self.entries]
        self.station_ids = [e.attrib['stationID'] for e in self.entries]
        self.track_ids   = [e.attrib['trackID'] for e in self.entries]
        self.daycode     = ID_TO_SHORT[self.weekday]

        self.vyst_is_yard = False  # to be set later based on run info DELETE when VYST is actual yard 
            

    @staticmethod
    def _extract_unit_from_normalised(train_type):
        """
        From normalised type like:
        "Empty_6-QMU" -> "QMU"
        "6-NGR"       -> "NGR"
        "3-IMU100"    -> "IMU100"
        """
        t = train_type
        if t.startswith('Empty_'):
            t = t[len('Empty_'):]
        if '-' in t:
            return t.split('-', 1)[1]
        return t

    @staticmethod
    def _extract_cars_from_normalised(train_type):
        """
        Extract 3/6 from normalised label. Defaults to 0 if not found.
        """
        t = train_type
        if t.startswith('Empty_'):
            t = t[len('Empty_'):]
        m = re.match(r'(\d+)-', t)
        return int(m.group(1)) if m else 0

    
    def _get_direction(self):
        """
        Determine Up/Down direction based on 4th character of train number:
        - Odd → Down
        - Even → Up
        """
        tn = self.number

        if len(tn) < 4:
            return None

        char = tn[3]

        if not char.isdigit():
            return None

        digit = int(char)
        return 'Down' if digit % 2 == 1 else 'Up'


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
    for day in DAY_PRIORITY:
        if day in wkdk:
            #print("DEBUG:", day, type(WEEKDAY_KEYS_MASTER[day]))
            return WEEKDAY_KEYS_MASTER[day]['short']   # or long/alias
    return None


def parse_rsx(path, *, want_trains = False, want_duplicates = False, want_days = False, want_units = False, want_runs = False):

    UNKNOWN_UNITS.clear()
    root , _ = load_rsx(path)

    trains = extract_trains(root) if (want_trains or want_duplicates or want_days or want_units or want_runs) else None
    duplicates = detect_duplicates(trains) if want_duplicates else None
    d_list, u_list = extract_day_and_unit_lists(trains) if (want_days or want_units) else (None, None)
    run_dict = build_run_dict(trains) if want_runs else None


    if run_dict and trains:
        # tag whether VYST should be treated as stabling based on start and end run
        # REMOVE and add VYST to the master list of yards in locations.py once it becomes one!
        tag_vyst_trains(trains, run_dict)

    if UNKNOWN_UNITS:
        msg = "Unrecognised train units found:\n\n"
        for unit, norm, raw in sorted(UNKNOWN_UNITS):
            msg += f"• {unit} (normalised: {norm}, raw: {raw})\n"

        show_info("Unrecognised Units", msg)


    return root, trains, d_list, u_list, run_dict, duplicates


def sort_days(days):
    return sorted(days, key=SORT_ORDER_WEEK.index)

def sort_units(units):
    return sorted(units, key=SORT_ORDER_UNIT.index)


def normalise_days(days: typing.Iterable[str], *, collapse_mon_thu: bool = True) -> typing.List[str]:
    # Sorts days and optionally removes 120 when Mon–Thu codes are present. '120' = Mon–Thu composite code, explicit codes are {'64','32','16','8'} 
    
    sorted_days = sort_days(days)

    if collapse_mon_thu:
        weekday_codes = {'64', '32', '16', '8'}

        # if any explicit weekday exists and '120' is present then remove '120'. 
        if any(d in sorted_days for d in weekday_codes) and '120' in sorted_days:
            sorted_days = [d for d in sorted_days if d != '120']
    return sorted_days

def load_rsx_with_tree(path):
    tree = ET.parse(path)
    filename_wo_ext = os.path.splitext(os.path.basename(path))[0]
    return tree, tree.getroot(), filename_wo_ext