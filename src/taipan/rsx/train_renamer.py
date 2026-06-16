"""
append_tnum.py
Python port of the VBA AppendTNum macro.
Renames train number attributes in a standard-format RailSys (.rsx) XML file.
Usage:
python append_tnum.py <input_file.rsx> <output_folder>
If arguments are omitted the script falls back to interactive prompts.
"""
import sys
import os
import time
from pathlib import Path
from collections import defaultdict

from lxml import etree
from PyQt6.QtWidgets import QApplication

from taipan.gui.base import select_file

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
WEEKDAY_MAP = {
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
    "7": "Sunday",
}
MAINS_RS_TRACKS = {"U-8", "U-9", "U-10", "D-8", "D-9", "D-10"}
MAINS_BHI_TRACKS = {"U-3", "U-4", "D-3", "D-4"}
BAD_DIRECTION_STATIONS = {
    # Stations whose track-ID direction indicator is misleading for stabling moves.
    # Add station mnemonics here as needed.
}


def convert_day_key_to_string(weekday_key: str) -> str:
    return WEEKDAY_MAP.get(str(weekday_key), f"Unknown({weekday_key})")


def is_in_array(value: str, arr) -> bool:
    return value in arr


def all_array_is(arr, val) -> bool:
    return all(x == val for x in arr)


def time_string_as_double(time_str: str) -> float:
    """Convert HH:MM:SS to a comparable float (seconds since midnight)."""
    parts = time_str.split(":")
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s


def station_is_bad_direction(station_id: str) -> bool:
    return station_id in BAD_DIRECTION_STATIONS


# -----------------------------------------------------------------------------
# XML helpers
# -----------------------------------------------------------------------------

def get_entries(x_node):
    """Return a list of <entry> elements under timetableentries."""
    return x_node.findall("timetableentries/entry")


def get_attr(element, attr: str, default=None):
    return element.get(attr, default)


# -----------------------------------------------------------------------------
# Duplicate-number detection
# -----------------------------------------------------------------------------

def duplicate_num_function(trains) -> list:
    """
    Return a list parallel to `trains` where non-zero values indicate
    the (1-based) index of a same-day duplicate train number.
    """
    seen = {}  # (number, numbervar, weekday_key) -> first index (1-based)
    result = [0] * len(trains)

    for idx, node in enumerate(trains):
        number = get_attr(node, "number", "")
        numbervar = get_attr(node, "numbervar")
        key_parts = (number, numbervar)
        opday = node.find("header/service/opdaySection")
        weekday_key = get_attr(opday, "weekdayKey", "") if opday is not None else ""
        full_key = key_parts + (weekday_key,)
        if full_key in seen:
            result[idx] = idx + 1
        else:
            seen[full_key] = idx + 1
    return result


# -----------------------------------------------------------------------------
# Character 1 – train type
# -----------------------------------------------------------------------------
TRAIN_TYPE_MAP = {
   "Empty_6-EMU":    "2",
   "Empty_6-SMU":    "2",
   "Empty_9-EMU":    "2",
   "6-EMU":          "1",
   "6-SMU":          "1",
   "Empty_3-EMU":    "C",
   "Empty_3-SMU":    "C",
   "3-EMU":          "J",
   "3-SMU":          "J",
   "6-HYBRID":       "T",
   "6-IMU100":       "T",
   "Empty_6-HYBRID": "A",
   "Empty_6-IMU100": "A",
   "Empty_3-IMU100": "B",
   "3-IMU100":       "U",
   "Empty_5-ICE":    "W",
   "5-ICE":          "X",
   "Empty_6-NGR":    "E",
   "6-NGR":          "D",
   "Empty_6-DEPT":   "H",
   "Empty_6-REP":    "G",  # NEW QTMP/REP
   "6-REP":          "F",  # New Empty QTMP/REP
}

def first_character_write(x_node) -> str:
    te = x_node.find("timetableentries")
    first_entry = list(te)[0] if te is not None else None
    train_type_id = get_attr(first_entry, "trainTypeId", "") if first_entry is not None else ""
    char = TRAIN_TYPE_MAP.get(train_type_id)
    if char is None:
        raise ValueError(f"Unrecognised unit type: '{train_type_id}'")
    return char


# -----------------------------------------------------------------------------
# Character 2 – destination / corridor
# -----------------------------------------------------------------------------
ARR1 = ["DKB", "NRB", "BPY", "MYE", "CAB", "CABT", "CABS", "CAW", "CAE", "MYD", "CRD", "BRS", "EMHS"]
ARR4 = ["YAN", "NHR", "EUM", "SSE", "COO", "PMQ", "COZ", "TRA", "WOO", "GMR", "GYN", "GYP"]
ARR5 = ["RVV", "DIR", "EBV", "BDX", "BOV", "EIP", "IPS", "IPSW", "IPSS"]
ARR6 = ["THS", "KRA", "WOQ", "TAO", "YLE", "EBE", "RSW"]
ARR7 = ["TDP", "WOI", "KGT", "LGL", "BTI", "EDL", "HVW", "BNH", "BNT", "BNHS", "ORMS"]
ARR8 = ["LOT", "TNS", "BDE", "WPT", "ORO", "CVN"]
ARR9R = ["ETS", "CAM", "EXH", "NBY", "RS", "BNC", "ESY", "MES"]
ARR0M = ["ETB", "MNE", "BHI", "ETF", "MNS", "YN"]
ARRA = ["BHA", "BQY", "NUD", "BZL", "NBD", "DEG", "SGE", "SHC", "SHCT", "BQYS", "BQS"]
ARRB = ["CYF", "HDR", "ACO", "DBN"]
ARRD = ["MTZ", "AHF", "TWG", "TIQ", "IDP", "CMZ", "GVQ", "SHW", "CQD", "OXL", "DAR", "WAC", "GAI", "GDQ", "RDK", "RDKS"]
ARRE = ["WID", "WLQ", "NWM", "ADY", "EGG", "GAO", "MHQ", "OXP", "GOQ", "KEP", "FYG"]
ARRG = ["ORM", "CXM", "HLN", "NRG", "ROB", "ROBS", "VYS", "VYST"]
ARRH = ["BRD", "CRO", "NPR", "MGS", "CNQ", "MJE", "HMM", "LJN", "LDM", "WYH", "WNM", "WNC", "MNY", "MNYS"]
ARRK = ["RHD", "EGE", "SFD", "SFC"]
ARRL = ["EMH", "BEB", "GSS", "BWH", "LSH", "MOH", "EUD", "PAL", "WOB", "WOBS", "NBR", "NBRS", "WOY"]
ARRP = ["BIT", "BDT"]
ARRS = ["SBE", "SBA", "PKR"]
ARRT = ["RTL", "ALB", "WLG", "BOG"]  # Cross River Rail section was missing entirely from original - this came from compareTTUI 
ARRU = ["WUL", "WULS", "WFE", "WFW", "FWE", "FEE"]
ARRV = ["DUP", "FFI", "YRG", "YLY", "MQK", "CPM", "RKE", "RKET", "SLY", "XPT", "CEP", "ACR", "BQO", "SYK", "ATI", "RUC", "FTG", "KRY"]
ARRW = ["AIN", "WWI", "EGJ", "AJN", "TBU", "NND", "NTG"]
ARRY = ["VGI", "SSN", "GEB", "ZLL", "CDE", "BDS", "SPN", "BPR", "LWO", "PET", "PETS", "KGR", "MRD", "MGH", "MGE", "RWL", "KPR", "KPRS"]
DEST_ARRAYS = [
   ARR1, ARR4, ARR5, ARR6, ARR7, ARR8,
   ARR9R, ARR0M,
   ARRA, ARRB, ARRD, ARRE, ARRG, ARRH, ARRK, ARRL, ARRP, ARRS, ARRT, ARRU, ARRV, ARRW, ARRY,
]
DEST_CHARS = "145678+-ABDEGHKLPSTUVWY"

def check_destination_case(x_node, check_arr: list, char_arr: str) -> str:
    entries = x_node.findall("timetableentries/entry")
    last_station = get_attr(entries[-1], "stationID", "") if entries else ""
    for i, arr in enumerate(check_arr):
        if is_in_array(last_station, arr):
            return char_arr[i]
    raise ValueError(f"Unrecognised destination station: '{last_station}'")


def service_passes_station(x_node, station_id: str) -> bool:
    entries = x_node.findall("timetableentries/entry")
    for entry in reversed(entries):
        if get_attr(entry, "stationID") == station_id:
            return True
    return False


def is_mains(x_node) -> bool:
    entries = x_node.findall("timetableentries/entry")
    for entry in reversed(entries):
        sid = get_attr(entry, "stationID")
        tid = get_attr(entry, "trackID", "")
        if sid == "RS":
            return tid in MAINS_RS_TRACKS
        if sid == "BHI":
            return tid in MAINS_BHI_TRACKS
    # Service doesn't pass Bowen Hills or Roma Street
    return (service_passes_station(x_node, "MTZ") or
            service_passes_station(x_node, "VGI"))


def second_character_write(x_node) -> str:
    out = check_destination_case(x_node, DEST_ARRAYS, DEST_CHARS)
    if out == "+":
        entries = x_node.findall("timetableentries/entry")
        last_sid = get_attr(entries[-1], "stationID", "") if entries else ""
        if last_sid == "ETS":
            if service_passes_station(x_node, "RSF"):
                return "Q"
            te = x_node.find("timetableentries")
            first_entry = list(te)[0] if te is not None else None
            ttid = get_attr(first_entry, "trainTypeId", "") if first_entry is not None else ""
            if "Empty" in ttid:
                return "0"
        return "9" if is_mains(x_node) else "R"
    if out == "-":
        return "0" if is_mains(x_node) else "M"
    return out


# -----------------------------------------------------------------------------
# Character 3 – stopping pattern / peak
# -----------------------------------------------------------------------------
X1 = ["MTZS", "AHFP", "TWGP", "TIQP", "IDPS", "CMZP", "GVQP", "SHWP", "CQDP", "OXLP", "DARS"]
X2 = ["MGSS", "CNQP", "MJEP", "HMMP", "LDMP", "WYHP", "WNMP", "WNCP", "MNYS"]
T1 = ["MNYS", "WNCP", "WNMP", "WYHP", "LDMP", "HMMP", "MJEP", "CNQP", "MGSS"]
T2 = ["DARS", "OXLP", "CQDP", "SHWP", "GVQP", "CMZP", "IDPS", "TIQP", "TWGP", "AHFP", "MTZS"]
M1 = ["MNYS *"]
M2 = ["KRYS *"]


def stop_pattern_chk(x_node, cmp_str_arr: list) -> bool:
    entries = x_node.findall("timetableentries/entry")
    cmp_str = " " + " ".join(cmp_str_arr)
    build = ""
    for entry in entries:
        sid = get_attr(entry, "stationID", "")
        etype = get_attr(entry, "type", "")
        build += f" {sid}"
        if etype == "pass":
            build += "P"
        elif etype == "stop":
            build += "S"
    build += " *"
    return cmp_str in build


def check_am_pm(x_node) -> str:
    entries = x_node.findall("timetableentries/entry")
    am_start = time_string_as_double("06:00:00")
    am_end = time_string_as_double("09:00:00")
    pm_start = time_string_as_double("15:30:00")
    pm_end = time_string_as_double("18:30:00")
    for entry in entries:
        if get_attr(entry, "stationID") == "BNC":
            depart = get_attr(entry, "departure", "")
            if not depart:
                return "OFF"
            t = time_string_as_double(depart)
            if am_start < t < am_end:
                return "AM"
            if pm_start < t < pm_end:
                return "PM"
            return "OFF"
    return "OFF"


def third_character_write(x_node) -> str:
    peak = check_am_pm(x_node)
    if (stop_pattern_chk(x_node, X1) or stop_pattern_chk(x_node, X2)) and peak == "PM":
        return "X"
    if (stop_pattern_chk(x_node, M1) or stop_pattern_chk(x_node, M2)) and peak == "PM":
        return "M"
    #if (stop_pattern_chk(x_node, T1) or stop_pattern_chk(x_node, T2)) and peak == "AM":  # commented out in compareTT 
        #return "T"
    return "0"


# -----------------------------------------------------------------------------
# Character 4 – direction
# -----------------------------------------------------------------------------

def fourth_character_write(x_node) -> str:
    entries = x_node.findall("timetableentries/entry")
    tentative = None
    for entry in reversed(entries):
        tid = get_attr(entry, "trackID", "")
        sid = get_attr(entry, "stationID", "")
        first = tid[0] if tid else ""
        if tentative is None and not station_is_bad_direction(sid):
            if first == "U":
                tentative = "0"
            elif first == "D":
                tentative = "1"
        # Central overrides everything
        if sid == "BNC":
            if first == "U":
                return "0"
            if first == "D":
                return "1"
    if tentative is not None:
        return tentative
    raise ValueError("Cannot determine direction for train node.")


# -----------------------------------------------------------------------------
# Number template builder & XML updater
# -----------------------------------------------------------------------------

def build_number_template(x_node, choices: set) -> str:
   n1 = first_character_write(x_node)  if "1" in choices else "_"
   n2 = second_character_write(x_node) if "2" in choices else "_"
   n3 = third_character_write(x_node)  if "3" in choices else "_"
   n4 = fourth_character_write(x_node) if "4" in choices else "_"
   return n1 + n2 + n3 + n4


def step_xml_template(trains, number_templates: list) -> None:
    """
    Apply the generated number templates back onto the XML train nodes.
    Mirrors VBA's StepXMLTemplate: assigns unique identifiers where multiple
    trains share the same base template by appending a counter suffix.
    """
    count = defaultdict(int)

    for node, template in zip(trains, number_templates):
        count[template] += 1
        unique_id = f"{template}{count[template]:02d}"
        node.set("number", unique_id)


# -----------------------------------------------------------------------------
# Duplicate reporting helper
# -----------------------------------------------------------------------------

def report_duplicates(trains, duplicate_numbers: list) -> None:
    print("\n- Duplicate Train Numbers -")
    print(f"{'Index':<8} {'Train #':<20} {'Day'}")
    print("-" * 50)
    for i, dup_idx in enumerate(duplicate_numbers):
        if dup_idx != 0:
            node = trains[dup_idx - 1]
            number = get_attr(node, "number", "")
            numbervar = get_attr(node, "numbervar")
            num_str = f"{number}-{numbervar}" if numbervar else number
            opday = node.find("header/service/opdaySection")
            wk = get_attr(opday, "weekdayKey", "") if opday is not None else ""
            day = convert_day_key_to_string(wk)
            print(f"{dup_idx - 1:<8} {num_str:<20} {day}")
    print()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main(path: str, choices: set) -> None:
    input_path = Path(path)
    base, ext = os.path.splitext(path)
    output_path = Path(f"{base}_updated_train_numbers{ext}")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Parsing: {input_path}")
    tree = etree.parse(str(input_path))
    root = tree.getroot()
    trains = root.findall("timetable/train")
    if not trains:
        raise ValueError("No <train> nodes found under railsys/timetable.")

    print(f"Found {len(trains)} train(s). Checking for duplicates...")
    duplicates = duplicate_num_function(trains)
    if not all_array_is(duplicates, 0):
        report_duplicates(trains, duplicates)
        raise SystemExit(
            "Input contains same-day duplicate train numbers. "
            "Please resolve them before re-running."
        )

    print("No duplicates found. Building number templates...")
    start = time.perf_counter()
    number_templates = []
    for i, node in enumerate(trains):
        template = build_number_template(node, choices)
        number_templates.append(template)
        print(f"  [{i:>4}] base number: {template}", end="\r")
    print()

    print("Applying templates to XML...")
    step_xml_template(trains, number_templates)
    print(f"Saving output to: {output_path}")
    tree.write(str(output_path), xml_declaration=True, encoding="UTF-8", pretty_print=True)

    elapsed = time.perf_counter() - start
    print(f"\nTrain numbers updated! Time taken: {elapsed:.2f} seconds")


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    path = select_file(
        caption="Select RSX file",
        directory="",
        filter_str="RSX Files (*.rsx);;All Files (*.*)",
    )
    if path:
        main(path, choices = {"1", "2", "3", "4"})
