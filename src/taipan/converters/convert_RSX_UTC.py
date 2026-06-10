
"""
convert_RSX_UTC.py
==================

Converts a Railsys RSX file (passenger trains) into a UTC CSV file with optional freight train merging. 

Example format
---------------------------------
Date=26/05/25,,,,
Train=1003_Mon,TYPE=CITY-REGULAR,,Next=2Y29_Mon,Mon
Arr=0054400,Dep=0054400,Stop=Y,Node=IPS5,Mon
...
End 28,,,,Mon
Node = stationID + trackID concatenated (e.g. 'BNC' + '6' -> 'BNC6')
Time encoding: 6 character 0HHMMd (leading 0, HH, MM, tenth of min)

"""


import math
import os
import re
import sys
from collections import defaultdict
from datetime import date
from taipan.core.xml_parser import parse_rsx
from taipan.gui.base import select_file, select_folder, show_info_scroll_safe
from PyQt6.QtWidgets import QApplication


UNIT_TYPE_LABELS = {
   "IMU":    "CITY-REGULAR",
   "IMU100": "CITY-REGULAR",
   "NGR":    "CITY-REGULAR",
   "QMU":    "CITY-REGULAR",
   "EMU":    "CITY-REGULAR",
}
DEFAULT_PASSENGER_LABEL = "CITY-REGULAR"
DEFAULT_EMPTY_LABEL     = "CITY-EMPTY"
DAY_ORDER = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

# Freight TXT day code mapping (VR bit-array to short day name). 
VR_DAYCODE = { # all of them should be mapped from daycodesVR files, but these are the ones that show up in the example files
   "004": "Mon", "008": "Tue", "016": "Wed", "032": "Thu",
   "064": "Fri", "128": "Sat", "002": "Sun",
}

# Freight TXT train type first-char sets from utcrevamp
REV_FIRSTCHAR = {'1', 'T', 'D', 'J', 'X', 'U'}
EMP_FIRSTCHAR = {'2', 'A', 'E', 'C', 'W', 'B'}

# ── RSX helpers ───────────────────────────────────────────────────────────────
def utc_type_label(train_info):
	"""Return the UTC TYPE string for a TrainInfo object."""
	if train_info.is_empty_train:
		return DEFAULT_EMPTY_LABEL
	return UNIT_TYPE_LABELS.get(train_info.unit, DEFAULT_PASSENGER_LABEL)

def rsx_time_to_seconds(rsx_time: str) -> int:
   """Parse RSX time string (e.g. '06:44', '06:44:30', '25:03:00') to seconds."""
   parts = rsx_time.strip().split(":")
   h, m = int(parts[0]), int(parts[1])
   s = int(parts[2]) if len(parts) > 2 else 0
   return h * 3600 + m * 60 + s

def seconds_to_utc_time(total_seconds: int) -> str:
   """Convert seconds from midnight to 6-char 0HHMMd format."""
   hours   = total_seconds // 3600
   remain  = total_seconds % 3600
   minutes = remain // 60
   seconds = remain % 60
   tenths  = round(seconds / 6) % 10
   return f"0{hours:02d}{minutes:02d}{tenths:02d}"

def arr_dep_times(departure_str: str, stop_time_seconds) -> tuple:
   """Return (arr_utc, dep_utc) - arrival is departure minus dwell."""
   dep_secs = rsx_time_to_seconds(departure_str)
   dwell    = 0 if (stop_time_seconds is None or
					(isinstance(stop_time_seconds, float) and math.isnan(stop_time_seconds))
				   ) else int(stop_time_seconds)
   return seconds_to_utc_time(dep_secs - dwell), seconds_to_utc_time(dep_secs)

# ── RSX forming links ─────────────────────────────────────────────────────────
def build_forming_links(trains):
	"""
	Within each run+weekday group, sort by departure and link sequentially.
	Returns (prev_map, next_map) keyed by (train_number, daycode).
	"""
	run_groups = defaultdict(list)
	for t in trains:
		run_groups[(t.run, t.weekday)].append(t)
	for key in run_groups:
		run_groups[key].sort(key=lambda t: rsx_time_to_seconds(t.odep))
	prev_map, next_map = {}, {}
	for group in run_groups.values():
		for i, t in enumerate(group):
			k = (t.number, t.daycode)
			if i > 0:
				p = group[i - 1]
				prev_map[k] = f"{p.number}_{p.daycode}"
			if i < len(group) - 1:
				n = group[i + 1]
				next_map[k] = f"{n.number}_{n.daycode}"
	return prev_map, next_map

# RSX -> UTC lines
def train_to_utc_lines(t, prev_map, next_map):
	"""Generate UTC CSV lines for a single RSX TrainInfo."""
	key      = (t.number, t.daycode)
	day      = t.daycode
	train_id = f"{t.number}_{day}"
	ttype    = utc_type_label(t)
	stop_yn  = "Stop=N" if t.is_empty_train else "Stop=Y"
	prev_str = f"Prev={prev_map[key]}" if key in prev_map else ""
	next_str = f"Next={next_map[key]}" if key in next_map else ""
	yield f"Train={train_id},TYPE={ttype},{prev_str},{next_str},{day}"
	for station, track, dep_str, dwell in zip(
			t.station_ids, t.track_ids, t.departures, t.stop_times):
		arr_utc, dep_utc = arr_dep_times(dep_str, dwell)
		# Replaced track.strip() with a generator that extracts only digits
		yield f"Arr={arr_utc},Dep={dep_utc},{stop_yn},Node={station}{''.join(filter(str.isdigit, track))},{day}"

	yield f"End {len(t.station_ids)},,,,{day}"


def _parse_freight_file(filepath: str) -> list:
	"""
	Parse a single ITOPS freight TXT file into UTC CSV lines.
	TXT format:
		TTBLD... (header, skipped)
		STRT    1502   064CITYM   ...prev...   ...next...
			0342003420# 000   #6   YN06
		END 13
	"""
	utc_lines     = []
	train_header  = None
	stop_lines    = []
	day           = None
	with open(filepath, encoding="utf-8", errors="replace") as fh:
		lines = fh.readlines()[1:]  # skip TTBLD header
	for line in lines:
		if not line.strip():
			continue
		if "STRT" in line:
			# flush previous block
			if train_header and stop_lines:
				utc_lines.append(train_header)
				utc_lines.extend(stop_lines)
				utc_lines.append(f"End {len(stop_lines)},,,,{day}")
			indexes      = [(m.start(), m.end()) for m in re.finditer(r'\S+', line)]
			index_starts = [x[0] for x in indexes]
			train   = line[8:12].strip()
			daycode = re.findall(r'\d+', line[15:23])[0]
			day     = VR_DAYCODE.get(daycode, daycode)
			raw_type_match = re.findall(r'\D+', line[15:23])
			raw_type = raw_type_match[0] if raw_type_match else ""
			raw_type_match = re.findall(r'\D+', line[15:23])
			ttype = raw_type_match[0].strip() if raw_type_match else ""
			prev_str, next_str = "", ""
			if len(indexes) == 8:
				prev_str = f"Prev={line[27:31].strip()}_{day}"
				next_str = f"Next={line[57:61].strip()}_{day}"
			elif len(indexes) != 4:
				if 27 in index_starts:
					prev_str = f"Prev={line[27:31].strip()}_{day}"
				if 57 in index_starts:
					next_str = f"Next={line[57:61].strip()}_{day}"
			train_header = f"Train={train}_{day},TYPE={ttype},{prev_str},{next_str},{day}"
			stop_lines   = []
		elif "END" in line:
			if train_header and stop_lines:
				utc_lines.append(train_header)
				utc_lines.extend(stop_lines)
				utc_lines.append(f"End {len(stop_lines)},,,,{day}")
			train_header = None
			stop_lines   = []
			day          = None
		elif train_header is not None:
			tokens = line.split()
			if not tokens:
				continue
			time_block = tokens[0]           # e.g. '0342003420'
			arr = "0" + time_block[:5] + "0"
			dep = "0" + time_block[5:10] + "0"
			flag_match = re.search(r'[#D]', line[10:20])
			flag    = flag_match.group() if flag_match else "#"
			stop_yn = "Stop=Y" if flag == "#" else "Stop=N"
			node = tokens[-1].strip()
			stop_lines.append(f"Arr={arr},Dep={dep},{stop_yn},Node={node},{day}")
	return utc_lines

def load_freight_from_txt(folder: str) -> tuple:
	freight_lines = []
	txt_files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".txt"))
	for fname in txt_files:
		freight_lines.extend(_parse_freight_file(os.path.join(folder, fname)))
	train_count = sum(1 for l in freight_lines if l.startswith("Train="))
	return freight_lines, train_count


def convert_RSX_UTC(rsx_path, freight_folder=None, date_str=None, out_path=None):
	"""
	Convert RSX to UTC CSV.
	Parameters
	----------
	rsx_path       : str  Path to the .rsx file
	freight_folder : str  Optional folder of ITOPS freight TXT files to merge
	date_str       : str  Date header DD/MM/YY (default: today)
	out_path       : str  Output CSV path (default: <rsx_name>_conv.csv)
	"""
	if date_str is None:
		date_str = date.today().strftime("%d/%m/%y")
	if out_path is None:
		out_path = os.path.splitext(rsx_path)[0] + "_UTCconv.csv"
	_, trains, _, _, _, duplicates = parse_rsx(
		rsx_path,
		want_trains=True,
		want_duplicates=True,
		want_runs=True,
	)
	
	if duplicates:
		show_info_scroll_safe("Duplicate trains found", "\n".join(str(d) for d in duplicates))
	prev_map, next_map = build_forming_links(trains)
	trains_sorted = sorted(
		trains,
		key=lambda t: (DAY_ORDER.get(t.daycode, 99), rsx_time_to_seconds(t.odep))
	)
	passenger_lines = []
	for t in trains_sorted:
		passenger_lines.extend(train_to_utc_lines(t, prev_map, next_map))
	freight_lines, freight_count = load_freight_from_txt(freight_folder) if freight_folder else ([], 0)

	with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
		fh.write(f"Date={date_str},,,,\n")
		for line in passenger_lines:
			fh.write(line + "\n")
		for line in freight_lines:
			fh.write(line + "\n")
	show_info_scroll_safe("UTC Export Complete", (
		f"Output: {out_path}\n\n"
		f"Passenger trains : {len(trains_sorted)}\n"
		f"Freight trains   : {freight_count}\n"
		f"Total CSV rows   : {1 + len(passenger_lines) + len(freight_lines):,}"
	))
	return out_path

if __name__ == "__main__":
	app = QApplication.instance() or QApplication(sys.argv)
	rsx_path = select_file(caption="Select RSX file",directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")
	if not rsx_path:
		sys.exit(0)
	freight_folder = select_folder(
		caption="Select freight TXT folder (cancel to skip)",
		directory=os.path.dirname(rsx_path),
	) or None
	convert_RSX_UTC(rsx_path, freight_folder=freight_folder)