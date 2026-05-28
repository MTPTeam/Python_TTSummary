import os
import re
import sys
import time
import logging
import traceback
import pandas as pd
from collections import defaultdict
from PyQt6.QtWidgets import QApplication
from taipan.core.xml_parser import parse_rsx, normalise_days, sort_days
from taipan.constants.locations import MISC_LOCATIONS, STATIONS_MASTER, YARDS
from taipan.constants.days import WEEKDAY_KEYS_MASTER
from taipan.gui.base import open_file_crossplatform, show_info, select_file, show_error_safe, show_info_safe


ProcessDoneMessagebox = True
train_numbers_dict = {
	'1':'6-EMU',
	'2':'Empty_6-EMU',
	'A':'Empty_6-IMU100',
	'B':'Empty_3-IMU100',
	'C':'Empty_3-EMU',
	'D':'6-NGR',
	'E':'Empty_6-NGR',
	'J':'3-EMU',
	'T':'6-IMU100',
	'U':'3-IMU100',
	'H':'Empty_6-DEPT',
	'F':'6-REP',
	'G':'Empty_6-REP',
	'X':'6-NGRE',
	'W':'Empty_6-NGRE'
}

# Features
#------------------------------------------------
# Runs that start or end at non-stabling locations (VYST is yard if start or end of run)
# Runs that change platforms either side of a connection
# Runs that have more than one unit type
# Runs that are missing connections
# Trains with non-standardised train numbers
# Trains with train numbers that don't line up with their unit types
# Trains with more than 1 unittype
# Trains with duplicate train numbers
# Check whether connecting trains share the same lineID on the same day (mismatched line IDs)
# Check if connecting train is missing for the same day (missing connecting train)
# check if the same trains have the same difference between requested departure and requested departure of next station. same train = same stops
# ??? Less than 8min tb
#
#
#
#
#------------------------------------------------


LINES_TO_CHECK = [l for l in STATIONS_MASTER['lines']
	if l not in ('Normanby', 'Caboolture', 'Gympie North')]


# Build stable locations from YARDS
stable_locations = {code for yard in YARDS.values() for code in yard['yards'] if code not in ('RS', 'BHI')}
yard_codes = {code for yard in YARDS.values() for code in yard['yards']}
misc_codes = set(MISC_LOCATIONS.keys())
non_revenue_stations = {
	code for code, s in STATIONS_MASTER['stations'].items()
	if s['non_revenue']
} | yard_codes | misc_codes


def extract_lineid_num(lineid):
   match = re.search(r'\{(\d+)\}', lineid)
   return match.group(1) if match else lineid

def get_direction(t):
	"""Determine Up/Down direction for a train using STATIONS_MASTER. Direction is relative to city"""
	city_codes = {'RS', 'BNC', 'BRC', 'BHI', 'PKR', 'SBE', 'SBA', 'RTL', 'EXH', 'BOG', 'WLG', 'ALB'}
	entry_codes = t.station_ids
	sIDs = set(entry_codes)
	for candidate in LINES_TO_CHECK:
		line_codes = {
			code for code, s in STATIONS_MASTER['stations'].items()
			if s['line'] == candidate and s.get('unique', True)
		}
		if not sIDs & line_codes:
			continue
		line_all_codes = {
			code for code, s in STATIONS_MASTER['stations'].items()
			if s['line'] == candidate
		}
		line_indices = [i for i, c in enumerate(entry_codes) if c in line_all_codes]
		city_indices = [i for i, c in enumerate(entry_codes) if c in city_codes]
		if line_indices and city_indices:
			increasing = min(line_indices) > min(city_indices)
		else:
			increasing = False
		return 'Down' if increasing else 'Up'
	return None

def main(path=None):
	try:
		app = QApplication.instance() or QApplication(sys.argv)
		if not path:
			path = select_file(
				caption="Select RSX file",
				directory="",
				filter_str="RSX Files (*.rsx);;All Files (*.*)"
			)
		if not path:
			return
		directory = '\\'.join(path.split('/')[0:-1])
		os.chdir(directory)
		filename = path.split('/')[-1][:-4]
		print(filename, '\n')
		start_time = time.time()
		root, trains, d_list, u_list, run_dict, duplicates = parse_rsx(
			path,
			want_trains=True,
			want_days=True,
			want_units=True,
			want_runs=True,
			want_duplicates=True,
		)
		# VYST - only treat as yard if run starts or ends there
		vyst_runs = {k for k, rec in run_dict.items() if rec[3] == 'VYST' or rec[4] == 'VYST'}
		if vyst_runs:
			stable_locations.add('VYST')

		# build lineid lookup for connection checks
		lineid_lookup = {(t.number, t.weekday): t.lineID for t in trains}
		# build per-run detail dict for checks that need per train info
		# { (run, weekday): [ {tn, darr, otrack, dtrack, direction} ] }

		run_detail = {}
		for t in trains:
			key = (t.run, t.weekday)
			stoptime = int(t.destin.get('stopTime', '0'))
			darr = str(pd.Timedelta(t.ddep) - pd.Timedelta(seconds=stoptime))
			otrack = t.origin['trackID'][-1]
			dtrack = t.destin['trackID'][-1]
			direction = get_direction(t)
			if key not in run_detail:
				run_detail[key] = []
			run_detail[key].append({
				'tn':        t.number,
				'darr':      darr,
				'otrack':    otrack,
				'dtrack':    dtrack,
				'loID':      t.start_id + otrack,
				'ldID':      t.end_id + dtrack,
				'direction': direction,
				'odep':      t.odep,
			})

		# sort each run's trains by departure time
		for detail in run_detail.values():
			detail.sort(key=lambda x: x['odep'])

		# check lists
		dodgy_tns           = []
		wrong_tn            = []
		tn_doubles          = [(tn, day) for tn, day in (duplicates or [])]
		multiunittrain      = []
		multiunitrun        = []
		mismatchedplatforms = []
		stablingissue       = []
		shortturnbacks      = []
		missingconnects     = []
		lineid_mismatches   = []
		lineid_missing      = []
		originpass          = []
		destinpass          = []
		connections         = {}

		for t in trains:
			day = WEEKDAY_KEYS_MASTER.get(t.weekday, {}).get('short', t.weekday)
			key = (t.run, t.weekday)
			# connection tracking
			if key not in connections:
				connections[key] = [t.number]
			for conn in t.raw.iter('connection'):
				conn_tn = conn.attrib.get('trainNumber')
				if conn_tn:
					connections[key].append(t.number)
			# connection lineID checks
			for conn in t.raw.iter('connection'):
				conn_tn = conn.attrib.get('trainNumber')
				if not conn_tn:
					continue
				conn_lineid = lineid_lookup.get((conn_tn, t.weekday))
				if conn_lineid is None:
					lineid_missing.append(
						f'Train {t.number} on {day} connects to {conn_tn} which is not found on the same day'
					)
				elif conn_lineid != t.lineID:
					lineid_mismatches.append(
						f'Train {t.number} on {day} (lineID {t.lineID}) connects to {conn_tn} (lineID {conn_lineid})'
					)
			# multi unit train
			traintypeset = {e.attrib['trainTypeId'] for e in t.entries}
			if len(traintypeset) > 1:
				multiunittrain.append(
					f'{t.number} on {day} has more than 1 train type: {", ".join(traintypeset)}'
				)
			# first/last pass check
			if not t.is_empty_train:
				stoptypes = [
					e.attrib['type'] for e in t.entries
					if e.attrib['stationID'] not in non_revenue_stations
				]
				if stoptypes:
					if stoptypes[0] == 'pass':
						originpass.append(f' - First pass: {t.number} on {day} {t.start_id}->{t.end_id} - ')
					if stoptypes[-1] == 'pass':
						destinpass.append(f' - Last pass: {t.number} on {day} {t.start_id}->{t.end_id} - ')
			# train number format
			if not t.number.isalnum() or len(t.number) > 4:
				dodgy_tns.append(t.number)
			# train number vs unit type
			tn_unittype = train_numbers_dict.get(t.number[0])
			if tn_unittype != t.train_type_raw:
				wrong_tn.append(
					f'Train Number {t.number} on {day} indicates unit type is {tn_unittype} but is {t.train_type_raw} instead'
				)

		# multi unit run
		run_units = {}
		for t in trains:
			key = (t.run, t.weekday)
			run_units.setdefault(key, set()).add(t.unit)
		for key, units in run_units.items():
			if len(units) > 1:
				day = WEEKDAY_KEYS_MASTER.get(key[1], {}).get('short', key[1])
				multiunitrun.append(f'Run {key[0]} on {day} has two unit types: {", ".join(units)}')

		# stabling check using run_dict
		for key, rec in run_dict.items():
			run, weekday = key
			day = WEEKDAY_KEYS_MASTER.get(weekday, {}).get('short', weekday)
			start_sID = rec[3]
			end_sID   = rec[4]
			if start_sID not in stable_locations:
				stablingissue.append(f'Run {run} on {day} starts at {start_sID}')
			if end_sID not in stable_locations:
				stablingissue.append(f'Run {run} on {day} ends at {end_sID}')

		# platform + turnback checks using run_detail
		for key, detail in run_detail.items():
			run, weekday = key
			day = WEEKDAY_KEYS_MASTER.get(weekday, {}).get('short', weekday)
			for i, entry in enumerate(detail):
				if i == 0:
					continue
				prev = detail[i - 1]
				# mismatched platforms
				if prev['ldID'] != entry['loID'] and run not in ('XA', 'XB', '100', '101'):
					mismatchedplatforms.append(
						f'Run {run} on {day} has mismatched platforms between {prev["tn"]} and {entry["tn"]} - {prev["ldID"]} then {entry["loID"]}'
					)
				# short turnbacks
				turnback = pd.Timedelta(entry['odep']) - pd.Timedelta(prev['darr'])
				if turnback < pd.Timedelta(minutes=8) and entry['direction'] != prev['direction']:
					tb_mins, tb_secs = map(int, str(turnback)[-5:].split(':'))
					spacer = " " if len(run) == 2 else ''
					shortturnbacks.append(
						f'The turnback between {prev["tn"]} and {entry["tn"]} in run {run} on {day} is: {spacer}   {tb_mins}m {tb_secs}s'
					)

		# missing connections
		run_dict_tns = {}
		for t in trains:
			key = (t.run, t.weekday)
			run_dict_tns.setdefault(key, []).append(t.number)
		for key, tns in run_dict_tns.items():
			if tns != connections.get(key):
				run, weekday = key
				day = WEEKDAY_KEYS_MASTER.get(weekday, {}).get('short', weekday)
				missingconnects.append(
					f'Run {run} on {day}\n'
					f'Trips in run:    {tns}\n'
					f'Connected trips: {connections.get(key)}\n'
				)

		# inconsistent timing for trains with the same stop sequence
		# builds a gap fingerprint (minute-level diffs between consecutive requestedDepartures)
		# and flags any train whose fingerprint differs from others with the same stops
		tn_day_lineid = defaultdict(list)
		for t in trains:
			tn_day_lineid[t.number].append((t.weekday, t.lineID))
		train_fingerprints = {}
		for t in trains:
			gaps = []
			prev_rd = None
			for e in t.entries:
				rd = e.attrib.get('requestedDeparture')
				if rd and prev_rd:
					delta = pd.Timedelta(rd) - pd.Timedelta(prev_rd)
					total_mins = round(delta.total_seconds() / 60)
					gaps.append(total_mins)
				prev_rd = rd
			train_fingerprints[t.number] = (tuple(t.station_ids), tuple(gaps))
		station_seq_groups = defaultdict(list)
		for tn, (station_seq, gaps) in train_fingerprints.items():
			station_seq_groups[station_seq].append((tn, gaps))
		inconsistent_timing = []

		for station_seq, members in station_seq_groups.items():
			if len(members) < 2:
				continue
			gap_groups = defaultdict(list)
			for tn, gaps in members:
				gap_groups[gaps].append(tn)
			if len(gap_groups) < 2:
				continue
			majority_gaps, majority_trains = max(gap_groups.items(), key=lambda x: len(x[1]))
			outlier_lines = []
			for gaps, tns in gap_groups.items():
				if gaps == majority_gaps:
					continue
				train_info = ', '.join(
					f'{tn} ({" / ".join(WEEKDAY_KEYS_MASTER.get(wk, {}).get("short", wk) + " #" + extract_lineid_num(lid) for wk, lid in tn_day_lineid[tn])})'
					for tn in tns
				)
				outlier_lines.append(f'  Outlier {list(gaps)} mins -> {train_info}')
			if outlier_lines:
				inconsistent_timing.append(
					f'Stops: {", ".join(station_seq)}\n'
					f'  Majority {list(majority_gaps)} mins -> {", ".join(majority_trains)}\n' +
					'\n'.join(outlier_lines)
				)

		# ── output ────────────────────────────────────────────────────────────
		filename_txt = f'Errors-{filename}.txt'
		o = open(filename_txt, 'w')
		def printwl(text):
			print(text)
			o.write(text + '\n')
		printwl('Taipan Error Checker')

		if stablingissue:
			printwl('\nRuns that start or end at non-stabling locations')
			for x in stablingissue: printwl(x)
		if originpass or destinpass:
			printwl('\n\nFirst station pass or last station pass through a revenue location')
			for x in originpass: printwl(x)
			for x in destinpass: printwl(x)
		if mismatchedplatforms:
			printwl('\n\nRuns that change platforms either side of a connection')
			for x in mismatchedplatforms: printwl(x)
		if multiunitrun:
			printwl('\n\nRuns that have more than one unit type')
			for x in multiunitrun: printwl(x)
		if missingconnects:
			printwl('\n\nRuns that are missing connections')
			for x in missingconnects: printwl(x)
		if dodgy_tns:
			printwl('\n\nTrains with non-standardised train numbers')
			for x in dodgy_tns: printwl(x)
		if wrong_tn:
			printwl('\n\nTrains with train numbers that don\'t line up with their unit types')
			for x in wrong_tn: printwl(x)
		if multiunittrain:
			printwl('\n\nTrains with more than 1 unittype')
			for x in multiunittrain: printwl(x)
		if tn_doubles:
			printwl('\n\nTrains with duplicate train numbers')
			for tn, day in tn_doubles:
				day_str = WEEKDAY_KEYS_MASTER.get(day, {}).get('short', day)
				printwl(f'Train with trainnumber {tn} already running on {day_str}')
		if lineid_mismatches:
			printwl('\n\nConnected trains with mismatched lineIDs')
			for x in lineid_mismatches: printwl(x)
		if lineid_missing:
			printwl('\n\nConnections referencing a train not found on the same day')
			for x in lineid_missing: printwl(x)
		if inconsistent_timing:
			printwl('\n\nTrains with same stops but inconsistent requested departure gaps')
			for x in inconsistent_timing: printwl(x)

		o.close()
		print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')

	except Exception as e:
		logging.error(traceback.format_exc())
		if ProcessDoneMessagebox:
			time.sleep(15)


if __name__ == "__main__":
	main()
