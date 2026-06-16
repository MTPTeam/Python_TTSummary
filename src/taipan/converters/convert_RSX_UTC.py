
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

IGNORE_STATIONS = []


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


WEEKDAY_BITS = {64: "Mon", 32: "Tue", 16: "Wed", 8: "Thu",
			   4: "Fri",  2: "Sat",  1: "Sun"}
DAY_ORDER    = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
			   "Fri": 4, "Sat": 5, "Sun": 6}

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



def expand_weekday_key(key: int) -> list[str]:
   """120 -> ['Mon','Tue','Wed','Thu'], 64 -> ['Mon'] etc."""
   return [day for bit, day in WEEKDAY_BITS.items() if key & bit]

def encode_time(time_str: str) -> str:
	parts = time_str.strip().split(":")
	h, m, s = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
	if s == 30:
		h, m = divmod(h * 60 + m + 1, 60)
		s = 0
	tenths = math.floor((s + 2) / 6) 
	if tenths >= 10:
		h, m = divmod(h * 60 + m + 1, 60)
		tenths = 0
	return f"0{h:02d}{m:02d}{tenths}0"


def encode_arrival(time_str: str) -> str:
   """Encode arrival time - always truncate to minute, no seconds."""
   parts = time_str.strip().split(":")
   h, m = int(parts[0]), int(parts[1])
   return f"0{h:02d}{m:02d}00"


def format_node(station_id: str, track_id: str) -> str:
	"""BNC+D-6 -> BNC6, RS+D-9 -> RS09 (2-char stations zero-pad track)."""
	digit = ''.join(filter(str.isdigit, track_id))
	if len(station_id) == 2:
		digit = digit.zfill(2)
	return f"{station_id}{digit}"


def build_forming_links(trains):
	run_groups = defaultdict(list)
	for t in trains:
		for day in expand_weekday_key(t.weekday_key):
			run_groups[(t.run, day)].append((t, day))
	prev_map, next_map = {}, {}
	for group in run_groups.values():
		group.sort(key=lambda td: rsx_time_to_seconds(td[0].odep))
		for i, (t, day) in enumerate(group):
			k = (t.number, day)
			if i > 0:
				p, pd = group[i - 1]
				prev_map[k] = f"{p.number}_{pd}"
			if i < len(group) - 1:
				n, nd = group[i + 1]
				next_map[k] = f"{n.number}_{nd}"
	return prev_map, next_map

# RSX -> UTC lines
def train_to_utc_lines(t, prev_map, next_map) -> list[tuple]:
	"""
	Returns list of (day_order, odep_secs, line) tuples.
	Mon-Thu trains emit 4 copies, one per day.
	"""
	days     = expand_weekday_key(t.weekday_key)
	odep_sec = rsx_time_to_seconds(t.odep)
	results  = []
	for day in days:
		key      = (t.number, day)
		train_id = f"{t.number}_{day}"
		ttype    = utc_type_label(t)
		stop_yn  = "Stop=N" if t.is_empty_train else "Stop=Y"
		prev_str = f"Prev={prev_map[key]}" if key in prev_map else ""
		next_str = f"Next={next_map[key]}" if key in next_map else ""
		day_ord  = DAY_ORDER.get(day, 99)
		stop_lines = []
		for station, track, dep_str, arr_str, etype in zip(
				t.station_ids, t.track_ids, t.departures,
				t.requested_arrivals, t.entry_types):
			if station in IGNORE_STATIONS:
				continue
			node    = format_node(station, track)
			dep_utc = encode_time(dep_str)
			#arr_utc = encode_time(arr_str) if arr_str else dep_utc
			if etype == "pass" or not arr_str:
				arr_utc = encode_arrival(dep_str)
			else:
				arr_utc = encode_time(arr_str)


			stop_lines.append(
				f"Arr={arr_utc},Dep={dep_utc},{stop_yn},Node={node},{day}")
		results.append((day_ord, odep_sec,
			f"Train={train_id},TYPE={ttype},{prev_str},{next_str},{day}"))
		for sl in stop_lines:
			results.append((day_ord, odep_sec, sl))
		results.append((day_ord, odep_sec,
			f"End {len(stop_lines)},,,,{day}"))
	return results


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
			if node[:-1] in IGNORE_STATIONS:
				continue
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
	
	# passenger
	all_lines = []
	for t in trains:
		if t.number == "1005":
			lines = train_to_utc_lines(t, prev_map, next_map)
			for _, _, line in lines:
				if "YLE" in line:
					print(line)
		all_lines.extend(train_to_utc_lines(t, prev_map, next_map))
	# freight - parse then tag with day_order for sorting
	raw_freight = load_freight_from_txt(freight_folder)[0] if freight_folder else []
	freight_tagged = []
	current_day_ord, current_odep = 99, 0
	for line in raw_freight:
		if line.startswith("Train="):
			day = line.split(",")[-1].strip()
			current_day_ord = DAY_ORDER.get(day, 99)
			# use dep of first stop as sort key - grab it next iteration
			current_odep = 0
		elif line.startswith("Arr="):
			if current_odep == 0:
				dep_str = line.split("Dep=")[1].split(",")[0]
				# convert 0HHMMd0 back to seconds for sorting
				current_odep = int(dep_str[1:3]) * 3600 + int(dep_str[3:5]) * 60
		freight_tagged.append((current_day_ord, current_odep, line))
	all_lines.extend(freight_tagged)
	all_lines.sort(key=lambda x: (x[0], x[1]))
	passenger_lines = [line for _, _, line in all_lines]  # reuse var for write loop
	with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
		fh.write(f"Date={date_str},,,,\n")
		for line in passenger_lines:
			fh.write(line + "\n")

	freight_count = sum(1 for l in passenger_lines if l.startswith("Train=") and "CITY" not in l)
	passenger_count = sum(1 for l in passenger_lines if l.startswith("Train=") and "CITY" in l)
	show_info_scroll_safe("UTC Export Complete", (
	f"Output: {out_path}\n\n"
	f"Passenger trains : {passenger_count}\n"
	f"Freight trains   : {freight_count}\n"
	f"Total CSV rows   : {1 + len(passenger_lines):,}"
	))

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