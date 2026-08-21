import os
import openpyxl
import re
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from locations import STATIONS_MASTER, YARDS, MISC_LOCATIONS

STAGE = 4  # which stage to build: 1, 2, 3, or 4. You will also need to change DEPARTURE_TIMES_XLSX_LIST source file(s) depending on what is in the stage sheet. For example for stage 4 it contains 

INPUT_XLSX = r"C:\Users\r919150\Downloads\Regional Path Summary.xlsx" # download the sheet manually since it is slow reading from data rooms, adjust this path accordingly
print(INPUT_XLSX)

# derives times from following sheets, not regional path summary sheet. sheets in this dictionary will be searched by trainID + day
DEPARTURE_TIMES_XLSX_LIST = [
    r"C:\Users\r919150\Downloads\Reformatted_NCL_current_MTP_ALT_NOFILTER.xlsx",
    r"C:\Users\r919150\Downloads\Reformatted_StandardGauge_current_MTP_alt.xlsx",

    r"C:\Users\r919150\Downloads\Reformatted_WestMoreton_current_winter_MTP.xlsx",  # for stage 4
]

# (sheet_name, data_start_row)
STAGE_SHEETS = {
    1: ("Stage 1 Expand", 2),
    2: ("Stage 2", 3),
    3: ("Stage 3", 2),
    4: ("Stage 4 - Examples", 4),  # split into full/empty halves - see load_stage_rows
}

# each stage gets subfolder + name 
OUTPUT_BASE_DIR = r"C:\Users\r919150\SIP\timetables\sip_scripts\SIP Modelling\Freight_Timetabling"
# valid path code regex 3-5 digit code + optional platform digit + slash for multiple platforms
_VALID_CODE_RE = re.compile(r"^[A-Z]{2,5}[0-9UDL]*(?:/[0-9UDL]+)?$")


def output_path(stage=STAGE, base_dir=OUTPUT_BASE_DIR):
    return os.path.join(base_dir, f"Stage{stage}", f"trial_output_stage{stage}.rsx")


DAY_TO_CODE = {
    "Sunday": "1",
    "Monday": "64",
    "Tuesday": "32",
    "Wednesday": "16",
    "Thursday": "8",
    "Friday": "4",
    "Saturday": "2",
}
DAY_ABBREV = {
    "Sunday": "Sun",
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
}
DAY_ORDER = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]

_YARD_NAME_BY_CODE = {}
for yard_name, info in YARDS.items():
    for code in info.get("yards", []):
        _YARD_NAME_BY_CODE.setdefault(code, yard_name)

# if a station appears as unknown in the output rsx, it means code cannot identify location name so put it in this dict 
EXTRA_STATION_NAMES = {
    "ACR": "Acacia Ridge",
    "TAE": "Tamaree",
    "MYJ": "Mayne Junction",
    "MNE": "Mayne",
    "YLE": "Yarrowlea",
    "WUL": "Wulkuraka",
    # RSI gets deleted anyway but include it for matching - do not remove this 
    "RSI": "RSI",
    "AJNE": "AJNE",
    "AJN": "AJN",
    "CAM": "CAM",
    "CQA": "Corinda",
    "RKL": "Redbank Loco Maintenance Depot",
    "RKW": "Redbank Workshop",
    "DNL": "Dinmore Livestock Yard",
}

# stations to be removed from every path - deleted stations runtime is then folded into the preceding stations runtime 
# if deleted station is the first one its running time is added to start time 
# although it does not modify end time timing if the station is the last one
DELETE_STATIONS = {"TAE", "AJNE", "AJN", "MNE", "CAM", "MYJ", "RSI"}

# some 3 letter station codes railsys doesn't recognise, so rename/remap them here
STATION_RENAMES = {
"MEC": "ETS", # turn all ETS into MEC
}

# trackID replacement (used to replace for timing points but can be replaced with any letter )
TIMING_POINT_OVERRIDES = {"CEN": "T", "MYJ": "T", "YLE": "T"}  # Caboolture North

# swap exh platform 2 with 1 
PLATFORM_OVERRIDES = {("EXH", "2"): "1",}

# Stations where platform 1 and 2 is always flipped, regardless of path
# or direction. ips/yly commented out 
FLIP_PLATFORMS = {
    "TAO",  # Thagoona
    "WOQ",  # Walloon
    "KRA",  # Karrabin
    "WUL",  # Wulkuraka
    "THS",  # Thomas Street
    "RVV",
    "GDQ",
    "RSW",
}


# Stations that must always be timed as a stop, even if the computed
# dwell between the arriving and departing leg comes out to zero - used
# only by build_entries_for_path_with_departures() (the departure-time/
# dwell sheet path). Forces minStopTime/stopTime to at least 1 second and
# type="stop" whenever the train passes through one of these.
FIXED_DWELL_STATIONS = {
    "NBR",  # Nambour
    "CAB",  # Caboolture
    "PET",  # Petrie
    "NTG",  # Northgate
    "AIN",  # Albion
    "NBY",  # Normanby
    "MBN",  # Moolabin
    "SLY",  # Salisbury
    "BRD",  # Buranda
    "MJE",  # Murarrie
}

# placeholder for overriding paths
# example usage -> PATH_OVERRIDES = {'52': ['TAE1', 'GYN1', ..., 'MTZ3', 'AHF3', ..., 'MBN3'],}
PATH_OVERRIDES = {}

# manually specify direction for certain routes
REPOS_DIRECTION_OVERRIDES = {
    frozenset(["502T"]): "D",
    frozenset(["Q11T"]): "U",
    frozenset(["911T"]): "U",
    frozenset(["957T", "991T"]): "U",  # via Central
    frozenset(["957T", "971T", "975T", "979T", "981T", "986T"]): "D",  # via Exh
    # Blank-header blocks (keyed by descriptive route text - see repos_block_key)
    "Elec Flyover to Elec Stabling": "D",
    "RS10 to Elec Flyover via Moolabin": "D",
    "RS10 to Elec Flyover via Central": "U",
    "Roma St to MEC1": "D",
    "Roma St to ETF1": "U",
}

# override direction 
DIRECTION_NOTE_OVERRIDES = {
    "from holmview": "D",
}


# manual direction overrides for Repos blocks in 'Existing Paths and Times' sheet 
def repos_block_key(block):
    """Unique key for a Repos block, for REPOS_DIRECTION_OVERRIDES.
    Most blocks are identified by their train number(s); several have no
    train number at all (blank header), so those fall back to their
    descriptive route text (train_type/row 2), which is unique per block
    even when the header is blank."""
    if block["path_ids"]:
        return frozenset(block["path_ids"])
    return str(block.get("train_type") or "").strip()



"""When two Repos blocks are literally the same physical route (identical
station list) and a row's start/end platform match both equally - e.g.
'RS10 to Elec Flyover via Central' and 'Roma St to ETF1' are the same
route under two different train-type labels - break the tie by
preferring whichever block's descriptive text appears here first.
doesn't matter which is picked  since the route itself is identical either way."""
REPOS_TIE_BREAK_PREFERENCE = ["Roma St to ETF1"]

# specify livestock train types from regional path summary sheet
LIVESTOCK_CDS = {"LIVESTOCK - CW", "LIVESTOCK", "LIVESTOCK - SW"}

# Stage 3 only: livestock trains ending at these yards are the loaded
# leg and get flagged priority (5-ICE); trains starting from these yards are
# the empty return leg (Empty_5-ICE). Determined from the row's own
# start/end platform text (e.g. "HVW3", "DNL1"), not train_type_cd/7-prefix.
LIVESTOCK_PRIORITY_STATIONS = ("HVW", "DNL")


"""
Logic for mapping vizi train types to railsys traintypes (Railsys only contains certain freight trains, so we map the rest to the closest equivalent)
everything thats not ls/grain/pas = freight
----
service ids
anything ending with g is grain service
anything with m is coal
starting with 8 its full of any type
start with 6 = empty coal or H is empty grain
---
livestock same length as coal- coal loaded coal/empty
if it ends with L its livestock
incoming full, outgoing empty
# anything starting with 7 it is full
# anything else empty
# RAILSYS TYPES
Empty_Coal
Freight_1-Empty_Coal_2_2300DEL+43Wagons
Freight_1-Loaded_Coal_2_2300DEL+43Wagons
Loaded_Coal
Freight_1-AN_IM_Loaded  # this is an aurizon intermodal train
Tilt_Elec
Tilt_Dies
XPT_7
NCL Intermodal Narrow Gauge Freight 706m 12.5% Run time margin
"""

TRAIN_TYPE_ID = {
    ### map excel type to Railsys type for traintypeID
    "FREIGHT": "NCL Intermodal Narrow Gauge Freight 706m 12.5% Run time margin",
    "XPT": "XPT_7",
    "TRAV-SOOUTBACK": "Tilt_Dies",  # A diesel loco
    "TRAV-WESTLANDER": "6-NGR",  # ngr
    "Coal Full": "Loaded_Coal",
    "Coal Empty": "Empty_Coal",
    # tilt trains
    "TRAV-SPQUEENS": "Tilt_Dies",
    "TRAV-ROK TILT": "Tilt_Elec",
    "TRAV-BUND TILT": "Tilt_Elec",
    # livestock/GRAIN trains get treated the same as coal
    "LIVESTOCK - CW": "SPECIAL_CASE",  # tamaree
    "LIVESTOCK": "SPECIAL_CASE",
    "LIVESTOCK - SW": "SPECIAL_CASE",  # rsw
    "GRAIN - SW": "SPECIAL_CASE",
}

_ALL_CODES = (
    set(STATIONS_MASTER["stations"])
    | set(_YARD_NAME_BY_CODE)
    | set(MISC_LOCATIONS)
    | set(EXTRA_STATION_NAMES)
)




def assign_train_type_id(row_data, special):
    train_type_cd = row_data["train_type_cd"]
    if train_type_cd not in TRAIN_TYPE_ID:
        print("unknown train_type_cd not in dict:", train_type_cd)
        return None
    if TRAIN_TYPE_ID[train_type_cd] != "SPECIAL_CASE":
        return TRAIN_TYPE_ID[train_type_cd]

    if STAGE == 3 and train_type_cd in LIVESTOCK_CDS:
        #livestock gets empty ice/loaded ice based on start and end platform
        end_plat = str(row_data.get("end_platform") or "").strip().upper()
        start_plat = str(row_data.get("start_platform") or "").strip().upper()
        if end_plat.startswith(LIVESTOCK_PRIORITY_STATIONS):
            return "5-ICE"
        if start_plat.startswith(LIVESTOCK_PRIORITY_STATIONS):
            return "Empty_5-ICE"
        print(
            f"WARNING: Stage 3 livestock row (source_id={row_data.get('source_id')}) "
            f"neither starts nor ends at HVW/DNL (start={start_plat}, end={end_plat}) "
            f"- falling back to old Loaded/Empty_Coal logic"
        )

    mapped_value = TRAIN_TYPE_ID[train_type_cd]
    service_key = str(row_data["source_id"])
    load_status = special.get(service_key)  # Returns 'Bulk-Full' or 'Bulk-Empty'
    if train_type_cd == "LIVESTOCK - CW":
        ### IF FIRST DIGIT OF traintype CD is 7 then its full else empty
        if load_status == "Bulk-Full" or train_type_cd.startswith("7"):
            return "Loaded_Coal"
        return "Empty_Coal"
    elif train_type_cd == "LIVESTOCK - SW":
        if load_status == "Bulk-Full":
            return "Loaded_Coal"
        elif load_status == "Bulk-Empty" or train_type_cd.startswith("7"):
            return "Empty_Coal"
        return "Empty_Coal"  # default to empty if load_status is unknown
    elif train_type_cd == "LIVESTOCK":
        ### IF FIRST DIGIT OF traintype CD is 7 then its full else empty
        if load_status == "Bulk-Full" or train_type_cd.startswith("7"):
            return "Loaded_Coal"
        return "Empty_Coal"
    elif train_type_cd == "GRAIN - SW":
        if load_status == "Bulk-Full":
            return "Loaded_Coal"
        elif load_status == "Bulk-Empty":
            return "Empty_Coal"




def station_name(code):
    if code in EXTRA_STATION_NAMES:
        return EXTRA_STATION_NAMES[code]
    s = STATIONS_MASTER["stations"].get(code)
    if s:
        return s["name"]
    if code in _YARD_NAME_BY_CODE:
        return _YARD_NAME_BY_CODE[code]
    if code in MISC_LOCATIONS:
        return MISC_LOCATIONS[code]["name"]
    return "Unknown"




def _clean_seconds(value):
    """Excel duration/time cells often come back through openpyxl as
    floats with tiny binary-rounding artifacts (e.g. 120.00000039115548
    instead of 120), since a time-of-day value is stored as a fraction of
    a day and converted to seconds. Round to the nearest whole second at
    the point of reading, rather than letting that noise propagate
    through all the offset/running-time arithmetic and show up in the
    final XML. Leaves None alone."""
    if value is None:
        return None
    return round(value)


def runtime(min_s, max_s):
    """The single 'effective running time' used everywhere a station's
    travel time is added into a clock time or folded into a neighbour:
    Max running time if present, else Min running time, else 0."""
    if max_s is not None:
        return max_s
    return min_s or 0




def _looks_like_station_code(value):
    if value is None:
        return False
    return bool(_VALID_CODE_RE.match(str(value).strip()))


def load_existing_paths(xlsx_path):
    """Read the 'Existing Paths' sheet, which holds the verified/actual
    platform codes for each path (unlike 'Existing Paths and Times', where
    the platform digit may just be a placeholder typed in when the runtime
    was sourced). Returns dict: path_id (str) -> ordered list of station
    codes with the real platform included.
    Note: some columns have a single stray blank cell mid-list (a data
    entry gap, not the end of the path) - a lone blank is skipped rather
    than treated as the terminator. The list only ends once we hit
    BLANK_RUN_LIMIT consecutive blank-OR-junk cells. 'Junk' means anything
    that doesn't look like a real station code (e.g. a manually-typed note
    like "must stay the same") - these are treated like blanks rather than
    being appended as a phantom extra station, which previously caused
    spurious station-count mismatches (see path 54 in the workbook).
    """
    BLANK_RUN_LIMIT = 3
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Existing Paths"]
    max_col = ws.max_column
    max_row = ws.max_row
    row5 = [ws.cell(row=5, column=c).value for c in range(1, max_col + 1)]
    block_cols = [c + 1 for c, v in enumerate(row5) if v is not None and c + 1 != 1]
    paths = {}
    for c in block_cols:
        path_ids_raw = ws.cell(row=5, column=c).value
        path_ids = [p.strip() for p in str(path_ids_raw).split(",")]
        codes = []
        blank_run = 0
        r = 9
        while r <= max_row:
            code = ws.cell(row=r, column=c).value
            if not _looks_like_station_code(code):
                blank_run += 1
                if code is not None:
                    print(
                        f"  (ignoring non-station cell in column {c}, "
                        f"row {r}: {code!r})"
                    )
                if blank_run >= BLANK_RUN_LIMIT:
                    break
            else:
                blank_run = 0
                codes.append(str(code).strip())
            r += 1
        for pid in path_ids:
            paths[pid] = codes
    return paths


def _report_divergence(pid, times_codes, existing_codes):
    """Print exactly where two station lists for the same path ID first
    diverge, to make genuine spreadsheet inconsistencies (e.g. path 52)
    easy to track down instead of just knowing 'lengths differ'."""
    min_len = min(len(times_codes), len(existing_codes))
    first_diff = None
    for i in range(min_len):
        if times_codes[i] != existing_codes[i]:
            first_diff = i
            break
    if first_diff is None:
        print(
            f"  path {pid}: lists match up to the shorter length "
            f"({min_len}); extra tail beyond that is where they diverge."
        )
        print(f"    times tail   : {times_codes[min_len:min_len+10]}")
        print(f"    existing tail: {existing_codes[min_len:min_len+10]}")
    else:
        lo = max(0, first_diff - 2)
        print(f"  path {pid}: first mismatch at station #{first_diff + 1}")
        print(f"    times    [{lo}:{first_diff+5}] = {times_codes[lo:first_diff+5]}")
        print(f"    existing [{lo}:{first_diff+5}] = {existing_codes[lo:first_diff+5]}")


def load_path_blocks(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Existing Paths and Times"]
    max_col = ws.max_column
    max_row = ws.max_row
    real_platforms = load_existing_paths(xlsx_path)
    row5 = [ws.cell(row=5, column=c).value for c in range(1, max_col + 1)]
    block_starts = [c + 1 for c, v in enumerate(row5) if v is not None and c + 1 != 1]
    blocks = {}
    for c in block_starts:
        path_ids_raw = ws.cell(row=5, column=c).value
        path_ids = [p.strip() for p in str(path_ids_raw).split(",")]
        start_platform = ws.cell(row=6, column=c).value
        end_platform = ws.cell(row=7, column=c).value
        label2 = ws.cell(row=8, column=c + 2).value
        has_max = bool(label2 and "Max" in str(label2))
        stations = []
        r = 9
        while r <= max_row:
            code = ws.cell(row=r, column=c).value
            if code is None:
                break
            min_secs = _clean_seconds(ws.cell(row=r, column=c + 1).value)
            # Per-cell fallback: if this block has a Max column but this
            # particular row's Max cell is blank, fall back to that row's
            # Min rather than leaving it None (which would previously get
            # silently treated as 0 downstream).
            max_secs = (
                _clean_seconds(ws.cell(row=r, column=c + 2).value)
                if has_max
                else min_secs
            )
            if max_secs is None:
                max_secs = min_secs
            stations.append((str(code).strip(), min_secs, max_secs))
            r += 1

        # swap in verified platform codes from 'Existing Paths'
        # IMPORTANT: this must be done PER path ID, not once for the whole
        # comma-grouped block
        for pid in path_ids:
            real_codes = real_platforms.get(pid)
            pid_stations = stations
            pid_start_platform = start_platform
            pid_end_platform = end_platform

            if real_codes is not None:
                if len(real_codes) == len(stations):
                    pid_stations = [
                        (real_codes[i], stations[i][1], stations[i][2])
                        for i in range(len(stations))
                    ]
                    pid_start_platform = real_codes[0]
                    pid_end_platform = real_codes[-1]
                elif pid in PATH_OVERRIDES:
                    override_codes = PATH_OVERRIDES[pid]
                    if len(override_codes) == len(stations):
                        pid_stations = [
                            (override_codes[i], stations[i][1], stations[i][2])
                            for i in range(len(stations))
                        ]
                        pid_start_platform = override_codes[0]
                        pid_end_platform = override_codes[-1]
                        print(
                            f"path {pid}: using PATH_OVERRIDES entry "
                            f"(times/existing station counts disagreed: "
                            f"{len(stations)} vs {len(real_codes)})"
                        )
                    else:
                        print(
                            f"WARNING: PATH_OVERRIDES['{pid}'] has "
                            f"{len(override_codes)} stations but times "
                            f"sheet expects {len(stations)} - ignoring "
                            f"override, keeping placeholder codes"
                        )
                else:
                    print(
                        f"WARNING: path {pid} station count mismatch "
                        f"(times={len(stations)}, existing paths={len(real_codes)}) "
                        f"- keeping placeholder codes from times sheet"
                    )
                    _report_divergence(pid, [s[0] for s in stations], real_codes)
            else:
                print(
                    f"WARNING: path {pid} not found in 'Existing Paths' - "
                    f"keeping placeholder codes from times sheet"
                )

            blocks[pid] = {
                "start_platform": pid_start_platform,
                "end_platform": pid_end_platform,
                "stations": pid_stations,
                "unit_type": ws.cell(row=1, column=c).value,
                "train_type": ws.cell(row=2, column=c).value,
                "direction_note": ws.cell(row=3, column=c).value,
            }
    return blocks


def load_repos_blocks(xlsx_path):
    """Read every column block in 'Existing Paths and Times' whose row 3
    (direction_note) contains 'Repos' - these are the real paths for
    repositioning ('REP') movements in Stage 1 Expand. Some are also
    identified by train number(s) in row 5 (e.g. header '957T,991T'
    means this block is the path for trains 957T and 991T) - but several
    Repos blocks have a BLANK row 5 (no train number listed at all,
    e.g. the 'RS10 to Elec Flyover via Moolabin' block), so block starts
    are detected via row 1 (unit_type), which is always populated,
    instead of row 5. Using row 5 alone (as an earlier version of this
    function did) silently misses those blank-header blocks entirely.
    Kept as a flat list (not a dict keyed by path/train ID like
    load_path_blocks) because the SAME train number can legitimately
    appear in more than one Repos block (e.g. '957T' shows up in two
    different physical routes here) - a dict would just silently let one
    overwrite the other. match_repos_block() does the actual
    disambiguation.
    Returns a list of dicts: {'path_ids': [...] (empty list if row 5 is
    blank), 'unit_type':.., 'train_type':.. (the descriptive route text,
    e.g. 'Elec Flyover to Roma St via Central' - this doubles as the
    thing matched against Route Note keywords), 'stations': [(code,
    min_secs, max_secs), ...]}.
    """
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Existing Paths and Times"]
    max_col = ws.max_column
    max_row = ws.max_row
    block_starts = [
        c for c in range(2, max_col + 1) if ws.cell(row=1, column=c).value is not None
    ]
    repos_blocks = []
    for c in block_starts:
        note3 = ws.cell(row=3, column=c).value
        if not note3 or "repos" not in str(note3).lower():
            continue
        path_ids_raw = ws.cell(row=5, column=c).value
        path_ids = (
            [p.strip() for p in str(path_ids_raw).split(",")]
            if path_ids_raw is not None
            else []
        )
        label2 = ws.cell(row=8, column=c + 2).value
        has_max = bool(label2 and "Max" in str(label2))
        stations = []
        r = 9
        while r <= max_row:
            code = ws.cell(row=r, column=c).value
            if code is None:
                break
            min_secs = _clean_seconds(ws.cell(row=r, column=c + 1).value)
            max_secs = (
                _clean_seconds(ws.cell(row=r, column=c + 2).value)
                if has_max
                else min_secs
            )
            if max_secs is None:
                max_secs = min_secs
            stations.append((str(code).strip(), min_secs, max_secs))
            r += 1
        repos_blocks.append(
            {
                "path_ids": path_ids,
                "unit_type": ws.cell(row=1, column=c).value,
                "train_type": ws.cell(row=2, column=c).value,
                "direction_note": note3,
                "stations": stations,
            }
        )
    return repos_blocks


def _station_id_of(code):
    """Just the station ID part of a code, ignoring whatever platform
    digit/suffix it carries - e.g. 'ETF2' and 'ETF1' are both 'ETF'.
    Used for orientation matching: a repositioning row running a Repos
    block's route in the RETURN direction will naturally arrive/depart
    on a different platform at each end than the recorded (one-way)
    block uses, so platform digits must be ignored when just checking
    'is this the same physical route, in either direction'."""
    return split_station_code(str(code).strip())[0]


def _repos_orientation(block, start_plat, end_plat):
    """Does a REP row's start/end platform match this Repos block's
    first/last station - and if so, in which direction?
    Returns 'forward' (row runs the block exactly as recorded),
    'reversed' (row runs the same physical route the OTHER way - e.g.
    the return trip), or None (doesn't match this block at all).
    Compares station IDs only (see _station_id_of) - not platform
    digits - since the return trip along the same route commonly uses
    a different platform at each end than the recorded one-way block.
    """
    if not block["stations"]:
        return None
    first_id = _station_id_of(block["stations"][0][0])
    last_id = _station_id_of(block["stations"][-1][0])
    start_id = _station_id_of(start_plat) if start_plat else None
    end_id = _station_id_of(end_plat) if end_plat else None
    if start_id == first_id and end_id == last_id:
        return "forward"
    if start_id == last_id and end_id == first_id:
        return "reversed"
    return None


def _repos_keyword_match(block, keyword):
    return keyword in str(block.get("train_type") or "").lower()


def reverse_station_triples(triples):
    """Reverse a path's raw (code, min_secs, max_secs) station list so
    it represents the same physical route travelled the OTHER way -
    used when a REP row runs a Repos block's recorded route backward
    (e.g. the return trip). The running time stored against station i
    represents the time from station i to station i+1; when the order
    flips, that same timing value has to shift to sit between the new
    (i, i+1) pair - it isn't just a plain list reversal.
    The first and last station's own CODE (with its platform digit) is
    deliberately dropped here - the caller replaces those two with the
    row's own start/end platform strings instead, since a return trip
    commonly arrives/departs on a different platform than the one-way
    block used (e.g. block departs 'ETF2' outbound, return arrives
    'ETF1' - the physical route is the same, the platform isn't).
    """
    n = len(triples)
    codes = [t[0] for t in triples]
    mins = [t[1] for t in triples]
    maxs = [t[2] for t in triples]
    reversed_triples = []
    for i in range(n):
        code = codes[n - 1 - i]
        if i < n - 1:
            min_v, max_v = mins[n - 2 - i], maxs[n - 2 - i]
        else:
            min_v, max_v = None, None
        reversed_triples.append((code, min_v, max_v))
    return reversed_triples


def match_repos_block(row, repos_blocks):

    service_id = str(row["service_id"]).strip()
    start_plat = str(row.get("start_platform") or "").strip().upper()
    end_plat = str(row.get("end_platform") or "").strip().upper()
    route_note = str(row.get("route_note_1") or "").lower()

    def best_orientation_match(candidates):
        
        def resolve_tier(tier):
            if len(tier) == 1:
                return tier[0][0], tier[0][1], False
            preferred = [
                (b, o)
                for b, o in tier
                if str(b.get("train_type") or "").strip() in REPOS_TIE_BREAK_PREFERENCE
            ]
            if len(preferred) == 1:
                return preferred[0][0], preferred[0][1], True
            return None, None, None

        with_orient = [
            (b, _repos_orientation(b, start_plat, end_plat)) for b in candidates
        ]
        forward = [(b, o) for b, o in with_orient if o == "forward"]
        if forward:
            block, orient, tie_broken = resolve_tier(forward)
            if block is not None:
                return block, orient, tie_broken, None
            return None, None, None, len(forward)
        reversed_ = [(b, o) for b, o in with_orient if o == "reversed"]
        if reversed_:
            block, orient, tie_broken = resolve_tier(reversed_)
            if block is not None:
                return block, orient, tie_broken, None
            return None, None, None, len(reversed_)
        return None, None, None, 0

    keyword = next((kw for kw in ("central", "moolabin") if kw in route_note), None)
    if keyword:
        cands = [b for b in repos_blocks if _repos_keyword_match(b, keyword)]
        if not cands:
            return None, None, f"route note keyword '{keyword}' matched 0 blocks"
        block, orient, tie_broken, ambiguous_count = best_orientation_match(cands)
        if block is not None:
            suffix = ", tie-broken via REPOS_TIE_BREAK_PREFERENCE" if tie_broken else ""
            return block, orient, f"route note keyword '{keyword}' ({orient}{suffix})"
        if ambiguous_count:
            return (
                None,
                None,
                (
                    f"route note keyword '{keyword}' matched {len(cands)} "
                    f"blocks, {ambiguous_count} fit start/end "
                    f"({start_plat}->{end_plat}) equally - need exactly 1"
                ),
            )
        return (
            None,
            None,
            (
                f"route note keyword '{keyword}' matched {len(cands)} blocks, "
                f"but none fit start/end ({start_plat}->{end_plat}) in either direction"
            ),
        )

    by_number = [b for b in repos_blocks if service_id in b["path_ids"]]
    if len(by_number) == 1:
        orient = _repos_orientation(by_number[0], start_plat, end_plat)
        if orient is None:
            # Trust the train-number match even if orientation can't be
            # confirmed from station IDs, default to forward
            return (
                by_number[0],
                "forward",
                "train number (orientation unconfirmed - assumed forward, please verify)",
            )
        return by_number[0], orient, f"train number ({orient})"
    if len(by_number) > 1:
        block, orient, tie_broken, ambiguous_count = best_orientation_match(by_number)
        if block is not None:
            suffix = ", tie-broken via REPOS_TIE_BREAK_PREFERENCE" if tie_broken else ""
            return block, orient, f"train number + station match ({orient}{suffix})"
        return (
            None,
            None,
            (
                f"train number '{service_id}' matched {len(by_number)} "
                f"blocks and station-ID match did not narrow to exactly 1"
            ),
        )

    block, orient, tie_broken, ambiguous_count = best_orientation_match(repos_blocks)
    if block is not None:
        suffix = ", tie-broken via REPOS_TIE_BREAK_PREFERENCE" if tie_broken else ""
        return (
            block,
            orient,
            f"station match only, train number not listed in any block ({orient}{suffix})",
        )
    if ambiguous_count:
        return (
            None,
            None,
            f"station match found {ambiguous_count} equally-good blocks (need exactly 1)",
        )
    return None, None, "no matching block found"


def split_station_code(raw):
    """Split an excel path code like 'ACR2', 'YLYU', 'VGI2/3', 'RS13', 'AJND'
    into (station_id, platform_suffix) by matching the longest known
    station-code prefix (handles 2-letter codes like 'RS' as well as the
    more common 3-4 letter ones), so a trailing platform letter/digit isn't
    mistaken for part of the code. Whatever is left over is the platform
    suffix used to build trackID. STATION_RENAMES is applied here too, so
    every caller automatically sees the renamed ID (e.g. 'MEC' -> 'ETS')
    without needing to remember to apply it themselves."""
    letters_only = re.match(r"[A-Z]+", raw).group()
    for length in (4, 3, 2):
        if length <= len(letters_only):
            candidate = letters_only[:length]
            if candidate in _ALL_CODES:
                return STATION_RENAMES.get(candidate, candidate), raw[length:]
    # fall back: assume 3-letter code (most common), else whole alpha run
    fallback_len = 3 if len(letters_only) >= 3 else len(letters_only)
    candidate = letters_only[:fallback_len]
    return STATION_RENAMES.get(candidate, candidate), raw[fallback_len:]


def filter_deleted_stations(stations):
    """Remove DELETE_STATIONS entries from a path's station list.
    Each deleted station's *effective* running time (Max, falling back to
    Min if there's no Max - see runtime()) is folded into the preceding
    KEPT station's running time, so the travel time it represented isn't
    lost - the previous kept station's segment now covers the combined
    distance straight through to whatever comes next.
    If a deleted station has no preceding kept station (it's the first
    station in the path, or every station before it was also deleted),
    there's nothing to fold its runtime into - instead that runtime is
    accumulated into `leading_time`, which the caller folds into the
    path's start-time anchor.
    Each kept station is collapsed down to (code, running_time), where
    running_time is already the effective Max/fallback-Min value - this
    is what downstream offset math and the output's regularRunningTime
    both use directly.
    Returns (kept_stations, leading_time).
    """
    kept = []
    leading_time = 0
    for code, min_s, max_s in stations:
        station_id, _ = split_station_code(code)
        rt = runtime(min_s, max_s)
        if station_id in DELETE_STATIONS:
            if kept:
                prev_code, prev_rt = kept[-1]
                kept[-1] = (prev_code, prev_rt + rt)
            else:
                leading_time += rt
            continue
        kept.append((code, rt))
    return kept, leading_time




def direction_code(path_info):
    """'D' (Down = heading north/away from Brisbane) or 'U' (Up = heading
    south/toward Brisbane), inferred from the path block's direction note
    (e.g. 'Outbound from Acacia Ridge to NC' -> Down, 'Inbound to POB' -> Up).
    Returns None if it can't be determined from the note."""
    note = (path_info.get("direction_note") or "").lower()
    if note in DIRECTION_NOTE_OVERRIDES:
        return DIRECTION_NOTE_OVERRIDES[note]
    if "outbound" in note:
        return "D"
    if "inbound" in note:
        return "U"
    return None


def load_special_lookup(xlsx_path):
    """Read 'Full Empty Mapping' once - shared across all stage sheets."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    full_empty = wb["Full Empty Mapping"]
    headers = [cell.value for cell in full_empty[1]]
    try:
        svc_id_col = headers.index("Svc_ID") + 1
        unit_type_col = headers.index("UnitType") + 1
    except ValueError as e:
        raise ValueError(
            f"Could not find required headers ('Svc_ID' or 'UnitType'): {e}"
        )
    special_lookup = {}
    for r in range(2, full_empty.max_row + 1):
        svc_id = full_empty.cell(row=r, column=svc_id_col).value
        bulk_status = full_empty.cell(row=r, column=unit_type_col).value
        if svc_id is not None:
            special_lookup[str(svc_id).strip()] = str(bulk_status).strip()
    return special_lookup


def load_rows_generic(ws, data_start_row, col_offset, special_lookup):
    # Read one service-row block
    rows = []
    for r in range(data_start_row, ws.max_row + 1):
        vals = [ws.cell(row=r, column=col_offset + c).value for c in range(1, 14)]
        if not vals[2]:  # source_id column empty -> skip/stop
            continue
        row_dict = {
            "unit_type": vals[0],
            "train_type_cd": vals[1],
            "source_id": vals[2],
            "service_id": vals[3],
            "start_platform": vals[5],
            "start_arrival": vals[6],
            "end_platform": vals[7],
            "end_arrival": vals[8],
            "target_timing": vals[9],
            "path_id": str(vals[10]),
            "route_note_1": vals[11],
            "route_note_2": vals[12],
        }
        # get the DOW from the 'Start Platform Arrival' column instead of start day 
        row_dict["start_day"], _ = _daytime_from_value(vals[6])
        row_dict["train_type_cd"] = assign_train_type_id(row_dict, special_lookup)
        rows.append(row_dict)
    return rows


def load_stage_rows(xlsx_path, stage, special_lookup):
    """Load the service rows for stage (see STAGE_SHEETS variable at the top of
    the file for the sheet name / start row each stage uses).

    Stage 4 ('Stage 4 - Examples') is special: the sheet holds two
    side-by-side blocks - a 'full' side at col_offset=0 and an 'empty'
    side at col_offset=13 - which get combined into a single row list.
    Every other stage is just one block at col_offset=0.
    """
    if stage not in STAGE_SHEETS:
        raise ValueError(
            f"Unknown STAGE {stage!r}; expected one of {sorted(STAGE_SHEETS)}"
        )
    sheet_name, data_start_row = STAGE_SHEETS[stage]

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[sheet_name]

    if stage == 4:
        full_side = load_rows_generic(
            ws,
            data_start_row=data_start_row,
            col_offset=0,
            special_lookup=special_lookup,
        )
        empty_side = load_rows_generic(
            ws,
            data_start_row=data_start_row,
            col_offset=13,
            special_lookup=special_lookup,
        )
        return full_side + empty_side

    return load_rows_generic(
        ws, data_start_row=data_start_row, col_offset=0, special_lookup=special_lookup
    )


def parse_daytime(text):
    """'Tuesday 00:10' -> (day_name, timedelta_since_midnight_of_that_day)"""
    day_name, hm = text.split(" ")
    hh, mm = hm.split(":")
    return day_name, int(hh) * 3600 + int(mm) * 60


def _time_part(daytime_text):
    """'Tuesday 00:10' -> '00:10' (strip the day name so only the clock
    time is compared when grouping same-train-different-day rows)."""
    _, hm = daytime_text.split(" ")
    return hm


def _daytime_from_value(value):
    """Like parse_daytime(), but also accepts a raw datetime value
    straight from the cell instead of a 'Weekday HH:MM' string.
    Repositioning ('REP') rows in Stage 1 Expand store real datetime
    objects in the arrival columns rather than the formatted day/time
    text used elsewhere, so this is needed anywhere those rows are
    processed. Returns (day_name, seconds_since_midnight)."""
    if isinstance(value, str):
        return parse_daytime(value)
    if isinstance(value, datetime):
        day_name = value.strftime("%A")
        secs = value.hour * 3600 + value.minute * 60 + value.second
        return day_name, secs
    raise ValueError(f"Unrecognised arrival value: {value!r} ({type(value)})")


def _time_part_any(value):
    """Like _time_part(), but also accepts a raw datetime value (see
    _daytime_from_value) so train_group_key() works for both normal
    path rows (string arrivals) and REP/repositioning rows (datetime
    arrivals)."""
    if isinstance(value, str):
        return _time_part(value)
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    raise ValueError(f"Unrecognised arrival value: {value!r} ({type(value)})")


def train_group_key(row):
    """Rows sharing this key are the same train, just running on
    different days -> they get merged into one <train> element with a
    combined weekdayKey. Deliberately excludes start_day/end_day (that's
    the thing allowed to differ) but includes path_id and both arrival
    clock times, plus train_type/unit_type/platforms so two trains that
    just happen to share a service_id don't get merged incorrectly."""
    return (
        row["service_id"],
        row["path_id"],
        _time_part_any(row["start_arrival"]),
        _time_part_any(row["end_arrival"]),
        row["target_timing"],
        row["train_type_cd"],
        row["unit_type"],
        row["start_platform"],
        row["end_platform"],
    )


def group_rows_by_train(rows):
    """Groups rows sharing a train_group_key, preserving first-seen group
    order, with each group's rows sorted Sun->Sat for deterministic
    weekdayKey/lineID output. Rows that don't match on path/time/type
    stay in their own single-row group."""
    groups = {}
    order = []
    for row in rows:
        key = train_group_key(row)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)
    result = []
    for key in order:
        grp = sorted(groups[key], key=lambda r: DAY_ORDER.index(r["start_day"]))
        result.append(grp)
    return result


def build_entries_for_row(row, path_blocks):
    path = path_blocks.get(row["path_id"])
    if not path:
        raise ValueError(f"Path ID {row['path_id']} not found in Existing Paths sheet")
    return build_entries_for_path(row, path)


def build_entries_for_path(row, path):
    """Core entry-building logic, given an already-resolved path dict
    (with 'stations'/'direction_note' etc). Used both by
    build_entries_for_row() (normal path_id lookup) and by the REP/
    repositioning flow in main(), which resolves 'path' via
    match_repos_block() instead of a path_id lookup."""
    # Drop TAE / MNE / AJN(E) / CAM from the path, folding their effective
    # running time (Max, fallback Min) into the previous kept station's
    # segment. Any runtime with no preceding kept station to fold into
    # (i.e. it belonged to a deleted station right at the front of the
    # path) comes back as leading_time, folded into the start-time anchor
    # below. Each kept station is now just (code, running_time).
    stations, leading_time = filter_deleted_stations(path["stations"])
    # _daytime_from_value (rather than parse_daytime directly) so this
    # also works for REP/repositioning rows, whose arrival columns hold
    # raw datetime values instead of 'Weekday HH:MM' strings.
    start_day, start_secs = _daytime_from_value(row["start_arrival"])
    end_day, end_secs = _daytime_from_value(row["end_arrival"])
    n = len(stations)
    # cumulative offsets (seconds) relative to the FIRST station's clock time,
    # allowing values to run past 24*3600 if the path crosses midnight.
    offsets = [0] * n
    if row["target_timing"] == "Arrive By Start Time":
        # forward: offsets[0] = 0, offsets[i] = offsets[i-1] + running_time(i-1)
        for i in range(1, n):
            offsets[i] = offsets[i - 1] + stations[i - 1][1]
        # If the original first station(s) of the path were deleted, the
        # new first station departs later than the nominal start time by
        # however long those deleted legs took - add that runtime here.
        base_epoch_secs = (
            start_secs + leading_time
        )  # clock seconds-of-day for station 0
        base_day = start_day
    elif row["target_timing"] == "Arrive By End Time":
        # backward: offsets[n-1] = 0, offsets[i] = offsets[i+1] - running_time(i)
        offsets[n - 1] = 0
        for i in range(n - 2, -1, -1):
            offsets[i] = offsets[i + 1] - stations[i][1]
        # NOTE: leading_time only applies to the start-time anchor above.
        # A deleted station at the very END of an 'Arrive By End Time'
        # path (which would instead need end_secs adjusted) isn't handled
        # here - flag for follow-up if that combination occurs.
        base_epoch_secs = end_secs  # clock seconds-of-day for the LAST station
        base_day = end_day
    else:
        # REP rows commonly have target_timing == None (not one of the
        # two labelled values) - since we always have BOTH exact arrival
        # times (start_arrival and end_arrival) for these, anchor on the
        # start time and let the offsets/running-time math land wherever
        # it lands; there's no ambiguity to resolve either way.
        for i in range(1, n):
            offsets[i] = offsets[i - 1] + stations[i - 1][1]
        base_epoch_secs = start_secs + leading_time
        base_day = start_day
    day_order = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    base_day_idx = day_order.index(base_day)
    start_day_idx = day_order.index(start_day)
    # day shift of the anchor station relative to the train's nominal start day
    day_shift = (base_day_idx - start_day_idx) % 7
    # 'direction_override' lets a caller (e.g. the REP/repositioning flow
    # in main(), via REPOS_DIRECTION_OVERRIDES) supply a known D/U
    # directly when direction_code() can't determine one from the note
    # text - takes priority over the note-based lookup when present.
    direction = path.get("direction_override") or direction_code(
        path
    )  # 'D' (Down/north) or 'U' (Up/south), or None if unknown

    # If RSI sits at either end of the ORIGINAL (unfiltered) path, flip
    # the whole path's direction. Checked against path['stations'] rather
    # than the filtered 'stations' list because RSI is itself one of the
    # DELETE_STATIONS - by the time filtering has run, RSI is already
    # gone from 'stations', so checking there would never find it. This
    # only affects the stations that remain in the output (RSI itself is
    # never emitted as an entry either way).
    raw_stations = path["stations"]
    first_raw_id, _ = (
        split_station_code(raw_stations[0][0]) if raw_stations else (None, None)
    )
    last_raw_id, _ = (
        split_station_code(raw_stations[-1][0]) if raw_stations else (None, None)
    )
    if first_raw_id == "RSI" or last_raw_id == "RSI":
        if direction == "D":
            direction = "U"
        elif direction == "U":
            direction = "D"
    entries = []
    for i, (code, running_time) in enumerate(stations):
        total_secs = base_epoch_secs + offsets[i] + day_shift * 86400
        hh = int(total_secs // 3600)
        mm = int((total_secs % 3600) // 60)
        ss = int(total_secs % 60)
        clock = f"{hh:02}:{mm:02}:{ss:02}"
        station_id, platform = split_station_code(code)
        # fallback to the raw platform string from the path if the row's own start/end platform is blank (e.g. a REP row with no start_platform/end_platform)
        if platform:
            platform = "/".join(
                str(int(part)) if part.isdigit() else part
                for part in platform.split("/")
            )

        if "/" in platform:
            platform = platform.split("/")[0]
        # Letter platforms (U, D, L, etc.) -> default to platform 1
        if platform and not platform[0].isdigit():
            platform = "1"

        platform = PLATFORM_OVERRIDES.get((station_id, platform), platform)

        # Always flip platform 1<->2 for the designated stations, no
        # matter what path they're on. IPS and YLY are deliberately
        # excluded from FLIP_PLATFORMS and never touched by this.
        if station_id in FLIP_PLATFORMS:
            if platform == "1":
                platform = "2"
            elif platform == "2":
                platform = "1"

        # Timing-point stations (e.g. Caboolture North) use a fixed 'T'
        # prefix instead of the usual direction-based U/D prefix.
        track_prefix = TIMING_POINT_OVERRIDES.get(station_id, direction)
        track_id = f"{track_prefix}-{platform}" if track_prefix and platform else ""
        is_last = i == n - 1
        entries.append(
            {
                "stationID": station_id,
                "stationName": station_name(station_id),
                "departure": clock,
                "type": "stop" if is_last else "pass",
                "trackID": track_id,
                # This is the same effective (Max, fallback Min) value that
                # drove the offset math above - not a separately-sourced Max.
                "regularRunningTime": None if is_last else running_time,
            }
        )
    return entries


def load_departure_time_legs(xlsx_paths):
    """Read the per-leg departure-time sheet ('Sheet1') from one or more
    reformatted files: one row per station-to-station leg, ordered by
    SequenceNumber within one calendar working. Each leg carries
    OriginCode/DestCode (+ OriginName/DestName as a fallback for matching
    against the regional path summary's station codes) and the real
    ScheduledOriginDepartTS/ScheduledDestArrivalTS datetimes. Because
    those are true datetimes (not just 'Weekday HH:MM' text), day-rollover
    past 24h falls straight out of datetime subtraction once a chain is
    pulled - no separate day-of-week bookkeeping is needed for the
    clock/dwell math itself.

    IMPORTANT: TrainID is a recurring headcode, not a one-off run - the
    same TrainID reappears once for (most) days of the week it operates,
    and the actual times genuinely differ day to day (this isn't just one
    schedule repeated with different labels). So a single calendar chain
    is only isolated by (TrainID, ServiceStartDate) - grouping by TrainID
    alone silently interleaves several different days' legs together.

    xlsx_paths may be a single path (str) or a list of paths - pass a
    list when some trains' departure times live in one reformatted file
    and others live in a different one. Chains from every file are
    merged together into the same service_id -> chains dict, so a
    lookup doesn't need to know which file a given train came from.

    Returns dict: service_id (str) -> list of chains (each an ordered
    list of leg dicts). A service_id can have several chains - one per
    day it operates (and now, potentially, one per source file too). See
    find_departure_chain() for how the caller picks the right one
    (start_day + start-time closeness, since the regional path summary's
    END day is unreliable for multi-day journeys but its START day/time
    consistently matches the sheet)."""
    if isinstance(xlsx_paths, (str, os.PathLike)):
        xlsx_paths = [xlsx_paths]

    legs_by_service = {}
    for xlsx_path in xlsx_paths:
        print(f"Loading departure-time sheet: {xlsx_path}")
        file_legs_by_service = _load_departure_time_legs_one_file(xlsx_path)
        for service_id, chains in file_legs_by_service.items():
            legs_by_service.setdefault(service_id, []).extend(chains)
    return legs_by_service


def _load_departure_time_legs_one_file(xlsx_path):
    """Same as load_departure_time_legs() but for a single file. See that
    function's docstring for the column/return-shape details."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    ws = wb["Sheet1"]

    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    col = {name: i for i, name in enumerate(header)}

    required = [
        "TrainID", "ServiceID", "SequenceNumber", "ServiceStartDate",
        "OriginCode", "OriginName", "DestCode", "DestName",
        "ScheduledOriginDepartTS", "ScheduledDestArrivalTS",
        "ScheduledOriginDepartDOW", "ScheduledDestArrivalDOW",
    ]
    missing = [c for c in required if c not in col]
    if missing:
        raise ValueError(
            f"Departure-time sheet missing expected column(s): {missing}"
        )

    def _code(value):
        return str(value).strip().upper() if value not in (None, "") else None

    def _text(value):
        return str(value).strip() if value not in (None, "") else None

    # First isolate each individual calendar working: (TrainID, ServiceStartDate).
    chains = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        train_id = row[col["TrainID"]]
        if train_id is None:
            continue
        leg = {
            "service_id": str(row[col["ServiceID"]]).strip(),
            "seq": row[col["SequenceNumber"]],
            "origin_code": _code(row[col["OriginCode"]]),
            "origin_name": _text(row[col["OriginName"]]),
            "dest_code": _code(row[col["DestCode"]]),
            "dest_name": _text(row[col["DestName"]]),
            "depart_ts": row[col["ScheduledOriginDepartTS"]],
            "arrive_ts": row[col["ScheduledDestArrivalTS"]],
            "depart_dow": row[col["ScheduledOriginDepartDOW"]],
            "arrive_dow": row[col["ScheduledDestArrivalDOW"]],
        }
        chain_key = (train_id, row[col["ServiceStartDate"]])
        chains.setdefault(chain_key, []).append(leg)

    legs_by_service = {}
    for (train_id, _service_start_date), legs in chains.items():
        legs.sort(key=lambda l: l["seq"])
        service_id = legs[0]["service_id"]
        legs_by_service.setdefault(service_id, []).append(legs)
    return legs_by_service


# How close the regional path summary's start time has to be to a
# departure-time sheet chain's actual first-leg departure time (in
# seconds of day) to trust that chain - see find_departure_chain().
START_TIME_TOLERANCE_SECONDS = 30 * 60  # 30 minutes


def _circular_seconds_diff(a, b):
    """Difference between two 'seconds since midnight' values, wrapping
    correctly around the 24h boundary (so 23:55 and 00:05 are 10 minutes
    apart, not ~23h50m)."""
    d = abs(a - b) % 86400
    return min(d, 86400 - d)


def find_departure_chain(
    legs_by_service, service_id, expected_start_day, expected_start_secs,
    first_station_id, first_station_name,
):
    """Look up the departure-time chain for a regional path summary row.

    The regional summary's END day/time is unreliable for multi-day
    journeys (its running-time math undercounts how many midnights a
    long freight run actually crosses), so matching is done on the
    START instead. But a chain's very first leg isn't necessarily the
    path's first station either - some chains start with yard/stabling
    moves (e.g. a shunt from a berth to the running line) before the
    train reaches the first station that's actually in the regional
    path summary's station list. So each candidate chain is anchored on
    whichever leg departs from first_station_id/first_station_name (the
    path's own first station, matched the same way
    build_entries_for_path_with_departures matches stations), and it's
    THAT leg's time that gets compared to the regional summary's
    expected start - not the chain's literal first row.

    Candidates with no leg at all departing from that station are
    dropped (they can't be the right chain for this path). Among what's
    left, a chain whose anchor leg departs on the expected weekday is
    preferred; ties/no-day-match fall back to whichever anchor leg's
    time is closest to expected_start_secs, accepted only if within
    START_TIME_TOLERANCE_SECONDS. Returns None if nothing qualifies."""
    candidates = legs_by_service.get(service_id)
    if not candidates or first_station_id is None:
        return None

    anchored = []
    for legs in candidates:
        anchor = _match_station_to_leg(
            first_station_id, first_station_name, legs, want="origin"
        )
        if anchor is not None:
            anchored.append((legs, anchor))
    if not anchored:
        return None

    same_day = [
        (legs, anchor) for legs, anchor in anchored
        if anchor["depart_dow"] == expected_start_day
    ]
    pool = same_day if same_day else anchored

    best_legs = None
    best_diff = None
    for legs, anchor in pool:
        ts = anchor["depart_ts"]
        actual_secs = ts.hour * 3600 + ts.minute * 60 + ts.second
        diff = _circular_seconds_diff(expected_start_secs, actual_secs)
        if best_diff is None or diff < best_diff:
            best_legs, best_diff = legs, diff

    if best_legs is not None and best_diff <= START_TIME_TOLERANCE_SECONDS:
        return best_legs
    return None


def _match_station_to_leg(station_id, station_name_text, legs, want):
    """Find the leg in `legs` whose origin (want='origin') or destination
    (want='dest') matches station_id. Falls back to a case-insensitive
    name match against station_name_text if the code doesn't line up -
    the departure-time sheet's own OriginCode/DestCode is occasionally
    blank (seen in the real data at junction-like waypoints), so the name
    columns are the only way to bridge those gaps."""
    code_key = "origin_code" if want == "origin" else "dest_code"
    name_key = "origin_name" if want == "origin" else "dest_name"
    for leg in legs:
        if leg[code_key] == station_id:
            return leg
    if station_name_text:
        target = station_name_text.strip().lower()
        for leg in legs:
            nm = leg[name_key]
            if nm and nm.strip().lower() == target:
                return leg
    return None


def build_entries_for_path_with_departures(row, path, legs):
    """Like build_entries_for_path(), and keeps everything else the same
    (station list/order, platforms, direction, trackID overrides, RSI
    flip, etc. all come from the regional path summary exactly as
    before) - but the clock time for each station comes from the real
    ScheduledOriginDepartTS/ScheduledDestArrivalTS values in `legs`
    instead of being derived from cumulative min/max running times.
    regularRunningTime is dropped entirely (RailSys derives it from the
    real departure times). Where a real dwell exists at a station (i.e.
    the gap between the leg arriving there and the leg leaving there is
    non-zero), that station's type is upgraded from 'pass' to 'stop' and
    minStopTime/stopTime are both set to the dwell length in seconds -
    stations with no dwell keep their original pass/stop behaviour
    (unchanged: last station is always 'stop', everything else 'pass')."""
    stations, _leading_time = filter_deleted_stations(path["stations"])
    n = len(stations)

    direction = path.get("direction_override") or direction_code(path)

    # Same RSI-at-either-end direction flip as build_entries_for_path,
    # checked against the ORIGINAL (unfiltered) station list.
    raw_stations = path["stations"]
    first_raw_id, _ = (
        split_station_code(raw_stations[0][0]) if raw_stations else (None, None)
    )
    last_raw_id, _ = (
        split_station_code(raw_stations[-1][0]) if raw_stations else (None, None)
    )
    if first_raw_id == "RSI" or last_raw_id == "RSI":
        if direction == "D":
            direction = "U"
        elif direction == "U":
            direction = "D"

    entries = []
    prev_total_secs = None  # fallback anchor, only used if a station's leg can't be found
    anchor_date = None

    for i, (code, running_time) in enumerate(stations):
        station_id, platform = split_station_code(code)
        name = station_name(station_id)
        is_last = i == n - 1

        # The leg that STARTS at this station gives this station's
        # departure time - the last station in the path has none.
        dep_leg = None if is_last else _match_station_to_leg(
            station_id, name, legs, want="origin"
        )
        # The leg that ENDS at this station gives this station's arrival
        # time - the first station in the path has none.
        arr_leg = None if i == 0 else _match_station_to_leg(
            station_id, name, legs, want="dest"
        )

        event_ts = None
        dwell_secs = None
        if dep_leg is not None:
            event_ts = dep_leg["depart_ts"]
        elif arr_leg is not None:
            event_ts = arr_leg["arrive_ts"]

        if dep_leg is not None and arr_leg is not None:
            dwell_secs = round(
                (dep_leg["depart_ts"] - arr_leg["arrive_ts"]).total_seconds()
            )

        if event_ts is not None:
            if anchor_date is None:
                anchor_date = event_ts.date()
            day_offset = (event_ts.date() - anchor_date).days
            total_secs = (
                day_offset * 86400
                + event_ts.hour * 3600
                + event_ts.minute * 60
                + event_ts.second
            )
        else:
            print(
                f"  WARNING: no departure-time match for station "
                f"{station_id} ({row['service_id']}) - falling back to "
                f"path running time"
            )
            total_secs = (prev_total_secs or 0) + running_time
        prev_total_secs = total_secs

        hh = int(total_secs // 3600)
        mm = int((total_secs % 3600) // 60)
        ss = int(total_secs % 60)
        clock = f"{hh:02}:{mm:02}:{ss:02}"

        if platform:
            platform = "/".join(
                str(int(part)) if part.isdigit() else part
                for part in platform.split("/")
            )
        if "/" in platform:
            platform = platform.split("/")[0]
        if platform and not platform[0].isdigit():
            platform = "1"

        platform = PLATFORM_OVERRIDES.get((station_id, platform), platform)
        if station_id in FLIP_PLATFORMS:
            if platform == "1":
                platform = "2"
            elif platform == "2":
                platform = "1"

        track_prefix = TIMING_POINT_OVERRIDES.get(station_id, direction)
        track_id = f"{track_prefix}-{platform}" if track_prefix and platform else ""

        if station_id in FIXED_DWELL_STATIONS:
            if dwell_secs is None or dwell_secs <= 0:
                dwell_secs = 1

        has_dwell = dwell_secs is not None and dwell_secs > 0
        entry_type = "stop" if (is_last or has_dwell) else "pass"

        entry = {
            "stationID": station_id,
            "stationName": name,
            "departure": clock,
            "type": entry_type,
            "trackID": track_id,
            "regularRunningTime": None,
        }
        if has_dwell:
            entry["minStopTime"] = dwell_secs
            entry["stopTime"] = dwell_secs
        entries.append(entry)
    return entries


def _extract_platform_digits(raw):
    """Pull just the digit characters out of a raw platform string, e.g.
    'ETF2' -> '2', 'RS10' -> '10', 'MEC1' -> '1'."""
    digits = re.sub(r"\D", "", str(raw).strip())
    return digits if digits else "1"


def build_entries_for_reposition_fallback(row):
    # fallback for repos trains
    start_val = row["start_arrival"]
    end_val = row["end_arrival"]
    start_day, start_secs = _daytime_from_value(start_val)
    end_day, end_secs = _daytime_from_value(end_val)

    # Prefer exact calendar-date difference when both values are real
    # datetimes (as REP rows normally are) - more robust than comparing
    # weekday names, which only works cleanly within a single week.
    if isinstance(start_val, datetime) and isinstance(end_val, datetime):
        day_shift = (end_val.date() - start_val.date()).days
    else:
        day_shift = (DAY_ORDER.index(end_day) - DAY_ORDER.index(start_day)) % 7

    end_total_secs = end_secs + day_shift * 86400
    running_time = end_total_secs - start_secs

    raw_points = [
        (row["start_platform"], start_secs),
        (row["end_platform"], end_total_secs),
    ]

    entries = []
    for i, (raw_code, total_secs) in enumerate(raw_points):
        hh = int(total_secs // 3600)
        mm = int((total_secs % 3600) // 60)
        ss = int(total_secs % 60)
        clock = f"{hh:02}:{mm:02}:{ss:02}"

        station_id, _ = split_station_code(str(raw_code).strip())
        platform = _extract_platform_digits(raw_code)

        platform = PLATFORM_OVERRIDES.get((station_id, platform), platform)
        if station_id in FLIP_PLATFORMS:
            if platform == "1":
                platform = "2"
            elif platform == "2":
                platform = "1"

        # No path/direction_note available for a reposition movement, so
        # there's no 'D'/'U' to fall back on - only the fixed timing-point
        # prefix applies, same as everywhere else.
        track_prefix = TIMING_POINT_OVERRIDES.get(station_id)
        track_id = f"{track_prefix}-{platform}" if track_prefix and platform else ""

        is_last = i == len(raw_points) - 1
        entries.append(
            {
                "stationID": station_id,
                "stationName": station_name(station_id),
                "departure": clock,
                "type": "stop" if is_last else "pass",
                "trackID": track_id,
                "regularRunningTime": None if is_last else running_time,
            }
        )
    return entries


def build_train_element(rows_group, entries, pattern=None):
    """rows_group: list of rows that all share the same path/time/type
      (per train_group_key) but may differ in start_day. Produces a single
    <train> element with a combined weekdayKey (sum of each day's code)."""
    rep = rows_group[
        0
    ]  # representative row - path/time/type are identical across the group
    combined_weekday = sum(int(DAY_TO_CODE[r["start_day"]]) for r in rows_group)
    day_label = "+".join(DAY_ABBREV[r["start_day"]] for r in rows_group)
    line_id = f"FRE ~ {day_label}-{rep['train_type_cd']}"
    # For normal path-based trains this is '/Freight/<path_id>' as before. REP/repositioning rows have no real path_id (it comes through as the string 'None'), 
    # so the caller passes an explicit pattern for those instead of letting '/Freight/None' leak into the output.
    if pattern is None:
        pattern = f"/Freight/Stage{STAGE}/{rep['path_id']}"
    train = ET.Element(
        "train",
        {
            "number": str(rep["service_id"]),
            "name": str(rep["service_id"]),
            "class": "Gz",
            "pattern": pattern,
            "lineID": line_id,
        },
    )
    header = ET.SubElement(train, "header")
    service = ET.SubElement(header, "service")
    ET.SubElement(
        service,
        "opdaySection",
        {
            "weekdayKey": str(combined_weekday),
            "holidayKey": "0",
        },
    )
    tte = ET.SubElement(train, "timetableentries")
    for e in entries:
        attrs = {
            "stationID": e["stationID"],
            "stationName": e["stationName"],
            "trackID": e["trackID"],
            "bstfahrweg": "",
            "departure": e["departure"],
        }
        # regularRunningTime is never written to the output - RailSys
        # derives it from the departure times, and for entries built the
        # old offset-based way it'd just be restating what fed those
        # offsets in the first place.
        if e.get("minStopTime") is not None:
            attrs["minStopTime"] = str(e["minStopTime"])
        if e.get("stopTime") is not None:
            attrs["stopTime"] = str(e["stopTime"])
        attrs.update(
            {
                "type": e["type"],
                "trainTypeId": str(rep["train_type_cd"]),
                "constructionState": "operates",
            }
        )
        ET.SubElement(tte, "entry", attrs)
    return train


def indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i


def main():
    path_blocks = load_path_blocks(INPUT_XLSX)
    repos_blocks = load_repos_blocks(INPUT_XLSX)
    special_lookup = load_special_lookup(INPUT_XLSX)
    departure_legs_by_service = load_departure_time_legs(DEPARTURE_TIMES_XLSX_LIST)
    total_chains = sum(len(v) for v in departure_legs_by_service.values())
    print(f"Loaded {total_chains} departure-time chains across "
          f"{len(departure_legs_by_service)} service IDs")

    stage_rows = load_stage_rows(INPUT_XLSX, STAGE, special_lookup)

    # Filter out rows that will break grouping
    valid_rows = []
    reposition_rows = []  # REP rows successfully matched to a real path
    reposition_fallback_rows = []  # REP rows with no matching path found
    skipped_no_path = 0
    skipped_bad_time = 0

    print("\n=== Matching REP/repositioning rows to paths in 'Existing Paths and Times' ===")
    for row in stage_rows:

        has_valid_path = bool(row.get("path_id")) and row["path_id"] in path_blocks

        if not has_valid_path:
            # REP rows are repositioning movements. 
            # They usually have a real path in 'Existing Paths and Times' - it's just identified by train number in the block header rather 
            # than by the (blank) path_id column - see match_repos_block(). Only genuine non-REP path-lookup failures get skipped outright below.
            if row.get("source_id") == "REP":
                if not row.get("start_platform") or not row.get("end_platform"):
                    print(
                        f"SKIPPING {row['service_id']} (REP) "
                        f"- missing start/end platform"
                    )
                    skipped_no_path += 1
                    continue
                try:
                    _daytime_from_value(row["start_arrival"])
                    _daytime_from_value(row["end_arrival"])
                except ValueError as e:
                    print(f"SKIPPING {row['service_id']} (REP) - {e}")
                    skipped_bad_time += 1
                    continue

                block, orient, method = match_repos_block(row, repos_blocks)
                if block is not None:
                    row = dict(row)  # don't mutate the shared row dict
                    direction_override = REPOS_DIRECTION_OVERRIDES.get(
                        repos_block_key(block)
                    )
                    if orient == "reversed":
                        stations = reverse_station_triples(block["stations"])
                        # Reversing the block's own stored direction gives
                        # the direction for THIS row, since it's running
                        # the same physical route the other way.
                        if direction_override == "D":
                            direction_override = "U"
                        elif direction_override == "U":
                            direction_override = "D"
                    else:
                        stations = list(block["stations"])
                    # Use the row's OWN start/end platform strings at the
                    # two endpoints rather than whatever the block has
                    # stored there - a return/repositioning trip commonly
                    # arrives/departs on a different platform than theS
                    # recorded one-way block used (e.g. 'ETF2' outbound
                    # vs 'ETF1' on the way back), and the row's own value
                    # is the more trustworthy one for its own endpoints.
                    if stations:
                        stations[0] = (
                            row.get("start_platform") or stations[0][0],
                            stations[0][1],
                            stations[0][2],
                        )
                        stations[-1] = (
                            row.get("end_platform") or stations[-1][0],
                            stations[-1][1],
                            stations[-1][2],
                        )
                    row["_repos_path"] = {
                        "start_platform": stations[0][0] if stations else None,
                        "end_platform": stations[-1][0] if stations else None,
                        "stations": stations,
                        "unit_type": block["unit_type"],
                        "train_type": block["train_type"],
                        "direction_note": block.get("direction_note"),
                        "direction_override": direction_override,
                    }
                    row["_repos_match_method"] = method
                    row["_repos_block_ids"] = block["path_ids"]
                    if direction_override is None:
                        print(
                            f"  NOTE: no REPOS_DIRECTION_OVERRIDES entry for "
                            f"block {block['path_ids']} - trackID direction "
                            f"prefix will be blank for {row['service_id']}"
                        )
                    reposition_rows.append(row)
                else:
                    print(
                        f"  NO MATCH: {row['service_id']} "
                        f"(start={row.get('start_platform')}, "
                        f"end={row.get('end_platform')}, "
                        f"route_note='{row.get('route_note_1')}') "
                        f"- {method} - using origin/destination fallback"
                    )
                    reposition_fallback_rows.append(row)
                continue

            print(
                f"SKIPPING {row['service_id']} "
                f"(path_id='{row['path_id']}') - path not found"
            )
            skipped_no_path += 1
            continue

        # train_group_key() expects strings like:
        # "Monday 12:34"
        if not isinstance(row.get("start_arrival"), str):
            print(
                f"SKIPPING {row['service_id']} "
                f"- invalid start_arrival: "
                f"{row['start_arrival']} "
                f"({type(row['start_arrival'])})"
            )
            skipped_bad_time += 1
            continue

        if not isinstance(row.get("end_arrival"), str):
            print(
                f"SKIPPING {row['service_id']} "
                f"- invalid end_arrival: "
                f"{row['end_arrival']} "
                f"({type(row['end_arrival'])})"
            )
            skipped_bad_time += 1
            continue

        valid_rows.append(row)

    print(f"\nValid rows: {len(valid_rows)}")
    print(f"REP rows matched to a real path: {len(reposition_rows)}")
    print(f"REP rows with NO match (using fallback): {len(reposition_fallback_rows)}")
    print(f"Skipped (no path): {skipped_no_path}")
    print(f"Skipped (bad time): {skipped_bad_time}")

    railsys_root = ET.Element("railsys")

    ET.SubElement(
        railsys_root,
        "version",
        {
            "major": "1",
            "minor": "3",
            "patchlevel": "0",
            "build": "0",
            "comment": "Draft generated from regional_paths.xlsx",
        },
    )

    timetable = ET.SubElement(railsys_root, "timetable")

    processed = 0
    failed = 0
    reposition_processed = 0
    dwell_matched = 0
    dwell_unmatched = []  # (service_id, start_day, start_secs) with no departure-time chain found

    # distinguishes how each group's entries get built:
    #  'normal'   -> build_entries_for_path via path_blocks lookup
    #  'repos'    -> build_entries_for_path via the matched repos block
    #  'fallback' -> build_entries_for_reposition_fallback (no match found)
    all_groups = (
        [(g, "normal") for g in group_rows_by_train(valid_rows)]
        + [(g, "repos") for g in group_rows_by_train(reposition_rows)]
        + [(g, "fallback") for g in group_rows_by_train(reposition_fallback_rows)]
    )

    print("\n=== REPOS train routes (for verification) ===")

    for group, kind in all_groups:

        rep = group[0]

        try:
            if kind == "normal":
                path = path_blocks[rep["path_id"]]
                _, start_secs = _daytime_from_value(rep["start_arrival"])
                kept_stations, _leading_time = filter_deleted_stations(path["stations"])
                if kept_stations:
                    first_id, _ = split_station_code(kept_stations[0][0])
                    first_name = station_name(first_id)
                else:
                    first_id, first_name = None, None
                legs = find_departure_chain(
                    departure_legs_by_service,
                    str(rep["service_id"]).strip(),
                    rep["start_day"],
                    start_secs,
                    first_id,
                    first_name,
                )
                if legs:
                    entries = build_entries_for_path_with_departures(rep, path, legs)
                    dwell_matched += 1
                else:
                    entries = build_entries_for_path(rep, path)
                    dwell_unmatched.append(
                        (str(rep["service_id"]).strip(), rep["start_day"], start_secs)
                    )
                pattern = None
                path_label = f"path {rep['path_id']}"
            elif kind == "repos":
                path = rep["_repos_path"]
                entries = build_entries_for_path(rep, path)
                pattern = f"/Freight/Stage{STAGE}/Repos"
                path_label = (
                    f"REPOS matched via {rep['_repos_match_method']} "
                    f"-> block[{','.join(rep['_repos_block_ids'])}] "
                    f"'{path['train_type']}'"
                )
            else:  # fallback
                entries = build_entries_for_reposition_fallback(rep)
                pattern = f"/Freight/Stage{STAGE}/Repos"
                path_label = "REPOS - NO MATCH, origin/destination fallback"

            days_str = "+".join(r["start_day"] for r in group)

            print(f"--- {rep['service_id']} " f"({days_str}, {path_label}) ---")

            if kind in ("repos", "fallback"):
                # Print the full route (not just first/last 5) for
                # every REPOS train, as requested, so it's easy to
                # verify against the spreadsheet.
                route_str = " -> ".join(f"{e['stationID']}(plat {e['trackID'] or '?'}) @{e['departure']}" for e in entries)
                print(f"  route: {route_str}")
            else:
                for e in entries[:5]:
                    print(" ", e)
                if len(entries) > 5:
                    print("  ...")
                    print(" ", entries[-1])

            train_el = build_train_element(group, entries, pattern=pattern)
            timetable.append(train_el)

            processed += 1
            if kind in ("repos", "fallback"):
                reposition_processed += 1

        except Exception as e:

            print(
                f"ERROR processing "
                f"{rep['service_id']} "
                f"({kind}, path {rep.get('path_id')}): {e}"
            )

            failed += 1

    indent(railsys_root)

    tree = ET.ElementTree(railsys_root)

    outpath = output_path()
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    tree.write(outpath, encoding="UTF-8", xml_declaration=True)


    
    print("\n================================")
    print(f"Trains written : {processed}")
    print(f"  of which using real departure-time/dwell data: {dwell_matched}")
    print(f"  of which with NO departure-time match (used old running-time math): {len(dwell_unmatched)}")
    if dwell_unmatched:
        print("  Unmatched service IDs:")
        for service_id, start_day, start_secs in dwell_unmatched:
            expected_clock = (
                f"{start_secs // 3600:02}:{(start_secs % 3600) // 60:02}:{start_secs % 60:02}"
            )
            print(
                f"    {service_id}  - looked for start_day={start_day}, "
                f"start time~{expected_clock} (from regional path summary, "
                f"tolerance is {START_TIME_TOLERANCE_SECONDS // 60} min)"
            )
            candidates = departure_legs_by_service.get(service_id)
            if candidates:
                for legs in candidates:
                    ts = legs[0]["depart_ts"]
                    print(
                        f"        sheet has: start_day={legs[0]['depart_dow']}, "
                        f"start={ts.strftime('%H:%M:%S')} "
                        f"({legs[0]['depart_ts']} -> {legs[-1]['arrive_ts']})"
                    )
            else:
                print(f"        service ID not found in departure-time sheet at all")
    print(f"  of which REPOS (matched + fallback): {reposition_processed}")
    print(f"Trains failed  : {failed}")
    print(f"Rows skipped (no path): {skipped_no_path}")
    print(f"Rows skipped (bad time): {skipped_bad_time}")
    print("================================")

    print("\nWrote", outpath)


if __name__ == "__main__":
    main()
