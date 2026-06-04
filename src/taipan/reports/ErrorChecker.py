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
# Runs that are missing connections (enforces ordering of connections in RSX)
# Trains with non-standardised train numbers
# Trains with train numbers that don't line up with their unit types
# Trains with more than 1 unittype
# Trains with duplicate train numbers
# Check whether connecting trains share the same lineID on the same day (mismatched line IDs)
# Check if connecting train is missing for the same day (missing connecting train)
# check if the trains that stop at the same stations have the same difference between requested departure of current and requested departure of next station (aka run time). Ignores if dwell > 180 and ignores empties. 
# turnback condition - 
# short turnbacks if direction changes - check dir
# anything sub 4 minutes turnback 
# anything sub 8 but not < 4
# train x on y day (FROM-TO) 
# ??? Less than 8min tb
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



def to_seconds(t_str):
	h, m, s = map(int, t_str.split(':'))
	return (h * 3600) + (m * 60) + s


def to_minutes_only(t_str):
	h, m, s = map(int, t_str.split(':'))
	# Ignore 's' entirely to force minute-level comparisons
	return (h * 60) + m



def make_subsection(title, items):
	if not items:
		return ''

	rows = ''.join(f'<li><pre>{x}</pre></li>' for x in items)

	return f'''
	<details>
		<summary>{title} <span class="count">({len(items)})</span></summary>
		<ul>{rows}</ul>
	</details>
	'''


def count_items(items):
	if isinstance(items, dict):
		return sum(len(v) for v in items.values())
	return len(items)


def make_section(title, items):
	if not items:
		return ''

	# If dictionary → subsections
	if isinstance(items, dict):
		content = ''.join(
			make_subsection(subtitle, subitems)
			for subtitle, subitems in items.items()
			if subitems
		)
	else:
		rows = ''.join(f'<li><pre>{x}</pre></li>' for x in items)
		content = f'<ul>{rows}</ul>'
		
	safe_id = title.replace(' ', '_').replace('/', '').replace('<', '').replace('>', '')

	return f'''
	<details id="{safe_id}">
		<summary>{title} <span class="count">({count_items(items)})</span></summary>
		{content}
	</details>
	'''

def make_timing_section(title, items):
	if not items:
		return ''
	tables = []
	for item in items:
		lines = item.split('\n')
		header = lines[0]
		table_rows = ''
		diffs_str = ''
		for line in lines[1:]:
			line = line.strip()
			if not line:
				continue
			if line.startswith('Differing runtimes:'):
				diffs_str = line[len('Differing runtimes:'):].strip()
			elif line.startswith('->'):
				trains = line[2:].strip()
				# collect all diffs for this outlier group into one row
				diff_parts = []
				for part in diffs_str.split('), '):
					part = part.strip().rstrip(')')
					m = re.match(r'(\w+)\s+(\d+)m\s+\(expected\s+(\d+)m', part)
					if m:
						sid, actual, expected = m.group(1), m.group(2), m.group(3)
						diff_parts.append(f'{sid}: {actual}m (expected {expected}m)')
				if diff_parts:
					diffs_cell = '<br>'.join(diff_parts)
					table_rows += f'<tr><td class="trains">{trains}</td><td>{diffs_cell}</td></tr>'
		if table_rows:
			tables.append(f'''
			<table>
			<caption>{header}</caption>
			<thead><tr><th style="width:65%">Train(s)</th><th style="width:35%">Runtime Differs at</th></tr></thead>
			<tbody>{table_rows}</tbody>
			</table>''')
	return f'''
	<details id="timing_section">
	<summary>{title} <span class="count">({len(items)})</span></summary>
		{''.join(tables)}
	</details>'''

def build_summary(sections, inconsistent_timing):
	rows = ['<div class="summary-title">Error Summary</div>']

	for title, items in sections:
		count = count_items(items)
		if count > 0:
			
			safe_id = title.replace(' ', '_').replace('/', '').replace('<', '').replace('>', '')
			rows.append(
				f'<div>'
				f'<a href="#{safe_id}"><b>{title}:</b> {count}</a>'
				f'</div>'
			)


	if inconsistent_timing:
		rows.append(
		f'<div>'
		f'<a href="#timing_section"><b>Runtime inconsistencies:</b> {len(inconsistent_timing)}</a>'
		f'</div>'
	)

	return '\n'.join(rows)



def format_grouped_map(group_map, header_label="route"):
    output = []

    for group in sorted(group_map):
        line = f'<span class="{header_label}">[ {group} ]</span>\n'

        for item in sorted(group_map[group]):
            values = group_map[group][item]
            val_str = ', '.join(sorted(values))

            line += f'  {item} ({val_str})\n'

        output.append(line.strip())

    return output


def write_html(filename_html, filename, sections, inconsistent_timing):
	total_issues = sum(count_items(items) for _, items in sections) + len(inconsistent_timing)
	
	summary_html = build_summary(sections, inconsistent_timing)

	html = f'''<!DOCTYPE html>
	<html lang="en">
	<head>
	<meta charset="utf-8">
	<title>Errors - {filename}</title>
	<style>
	body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 2em; font-size: 15px; }}
	h1 {{ color: #ffffff; }}
	.meta {{ color: #888; margin-bottom: 2em; }}
	
	td.trains {{ word-break: break-word; white-space: normal; }}
	td.trains div {{ margin-bottom: 2px; }}
	details {{ margin-bottom: 1em; border: 1px solid #444; border-radius: 4px; box-shadow: none; transition: box-shadow 0.5s ease, border 0.3s ease; }}
	
	details.highlight {{
		border: 2px solid #4fc1ff;
		box-shadow: 0 0 10px #4fc1ff;
	}}
	.route {{
		color: #4fc1ff;   /* nice blue */
		font-weight: bold;
	}}
	summary {{ background: #2d2d2d; padding: 0.6em 1em; cursor: pointer; font-weight: bold; color: #ce9178; }}
	summary:hover {{ background: #3a3a3a; }}
	.summary {{
		background: #252526;
		border: 1px solid #444;
		border-radius: 6px;
		padding: 1em;
		margin-bottom: 2em;
		line-height: 1.6;
	}}

	a {{
    text-decoration: none;
    color: inherit;
	}}

	a:hover {{
		text-decoration: underline;
		color: #4fc1ff;
	}}
	.summary b {{ color: #9cdcfe;}}
	.summary-title {{
		font-size: 18px;
		font-weight: bold;
		margin-bottom: 0.5em;
		color: #ffffff;
	}}
	.count {{ color: #888; font-weight: normal; }}
	ul {{ margin: 0; padding: 1em 1em 1em 2em; }}
	li {{ margin-bottom: 0.4em; }}
	pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; color: #d4d4d4; }}
	table {{ border-collapse: collapse; width: 60%; margin: 0 0 1.5em 0; table-layout: fixed; }}
	caption {{ font-size: 1.1em; font-weight: bold; color: #9cdcfe; padding: 0.5em; text-align: center; letter-spacing: 0.05em; }}

	th {{ background: #3a3a3a; color: #ce9178; padding: 0.4em 0.8em; text-align: left; font-size: 14px; }}
	td {{ padding: 0.4em 0.8em; border-bottom: 1px solid #333; vertical-align: top; font-size: 14px; }}
	tr:hover td {{ background: #2a2a2a; }}
	</style>
	</head>
	<body>
	<h1>Taipan Error Checker</h1>
	<div class="meta">
		{filename} &mdash; {total_issues} issue(s) found
	</div>

	<div class="summary">
		{summary_html}
	</div>

	{''.join(make_section(title, items) for title, items in sections)}
	{make_timing_section('Same stops but inconsistent requested departure gaps', inconsistent_timing)}


	<script>
	document.querySelectorAll('a[href^="#"]').forEach(link => {{
		link.addEventListener('click', function() {{
			const target = document.querySelector(this.getAttribute('href'));
			if (!target) return;

			target.classList.add('highlight');

			setTimeout(() => {{
				target.classList.remove('highlight');
			}}, 2000);
		}});
	}});
	</script>

	
	</body>
	</html>'''
	with open(filename_html, 'w', encoding='utf-8') as f:
		f.write(html)


def extract_lineid_num(lineid):
   match = re.search(r'~\s*(\d+)', lineid)
   return match.group(1) if match else lineid


def write_txt_report(filename, sections, inconsistent_timing):
	filename_txt = f'Errors-{filename}.txt'

	with open(filename_txt, 'w') as o:
		def printwl(text):
			print(text)
			o.write(text + '\n')

		printwl('Taipan Error Checker')

		for title, items in sections:
			if not items:
				continue

			printwl(f'\n{title}')

			if isinstance(items, dict):  # e.g. shortturnbacks
				for sub, subitems in items.items():
					if subitems:
						printwl(f'\n{sub}')
						for x in subitems:
							printwl(x)
			else:
				for x in items:
					printwl(x)

		if inconsistent_timing:
			printwl('\nTrains with same stops but inconsistent requested departure gaps')
			for x in inconsistent_timing:
				printwl(x)


def write_html_report(filename, sections, inconsistent_timing):
	write_html(f'Errors-{filename}.html', filename, sections, inconsistent_timing)
	print(f'HTML report: Errors-{filename}.html')


def TTS_ERR(path, mypath = None):
	try:
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
		run_dict_tns = {}
		for t in trains:
			key = (t.run, t.weekday)
			stoptime = int(t.destin.get('stopTime', '0'))
			darr = str(pd.Timedelta(t.ddep) - pd.Timedelta(seconds=stoptime))
			otrack = t.origin['trackID'][-1]
			dtrack = t.destin['trackID'][-1]
			direction = t.direction
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
		
		mismatched_map = defaultdict(lambda: defaultdict(list))

		stablingissue       = []
		#shortturnbacks      = []
		missingconnects     = []
		lineid_mismatches   = []
		lineid_missing      = []

		originpass_map = defaultdict(lambda: defaultdict(list))
		destinpass_map = defaultdict(lambda: defaultdict(list))
		connections         = {}

		
		shortturnbacks = {
			'Turnbacks < 4 minutes': defaultdict(lambda: defaultdict(list)),
			'Turnbacks 4-8 minutes': defaultdict(lambda: defaultdict(list))
		}

		connection_map = defaultdict(lambda: defaultdict(list))

		for t in trains:
			day = WEEKDAY_KEYS_MASTER.get(t.weekday, {}).get('short', t.weekday)
			key = (t.run, t.weekday)
			# connection tracking		
			for conn in t.raw.iter('connection'):
					conn_tn = conn.attrib.get('trainNumber')
					if conn_tn:
						connection_map[key][t.number].append(conn_tn)

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
					
					route = f'{t.start_id}->{t.end_id}'

					if stoptypes[0] == 'pass':
						originpass_map[route][t.number].append(day)

					if stoptypes[-1] == 'pass':
						destinpass_map[route][t.number].append(day)

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
			run_dict_tns[key] = [entry['tn'] for entry in detail]
			run, weekday = key
			day = WEEKDAY_KEYS_MASTER.get(weekday, {}).get('short', weekday)
			for i, entry in enumerate(detail):
				if i == 0:
					continue
				prev = detail[i - 1]
				# mismatched platforms
				if prev['ldID'] != entry['loID'] and run not in ('XA', 'XB', '100', '101'):
					run_key = f'Run {run}' 
					issue = f'{prev["tn"]} -> {entry["tn"]} ({prev["ldID"]} -> {entry["loID"]})'
					mismatched_map[run_key][issue].append(day)
				# short turnbacks
				turnback = pd.Timedelta(entry['odep']) - pd.Timedelta(prev['darr'])
				
				if entry['direction'] != prev['direction']:
					tb_mins, tb_secs = map(int, str(turnback)[-5:].split(':'))
					run_key = f'Run {run}'  
					issue = f'{prev["tn"]} -> {entry["tn"]}'


					if turnback < pd.Timedelta(minutes=4):
						shortturnbacks['Turnbacks < 4 minutes'][run_key][issue].append(day)

					elif turnback < pd.Timedelta(minutes=8):
						shortturnbacks['Turnbacks 4-8 minutes'][run_key][issue].append(day)


		# missing connections
		# strict connection validation

		for key, expected in run_dict_tns.items():
			run, weekday = key

			if run != 'AA':
				continue
			day = WEEKDAY_KEYS_MASTER.get(weekday, {}).get('short', weekday)

			print(f'\n=== Run {run} ({day}) ===')
			print(f'Expected order: {expected}')
			conn_map = connection_map.get(key, {})
			issues = []
			print('Connection map:')
			for tn, conns in conn_map.items():
				print(f'  {tn} -> {conns}')

			for i in range(len(expected) - 1):
				current = expected[i]
				next_expected = expected[i + 1]
				actual_list = conn_map.get(next_expected, [])
				if not actual_list:
					issues.append(f'{next_expected} missing connection -> should connect back to {current}')
				elif current not in actual_list:
					issues.append(
						f'{next_expected} connects to {", ".join(actual_list)} -> should connect back to {current}'
					)

			if issues:
				msg = f'Run {run} ({day})\n  ' + '\n  '.join(issues)
				missingconnects.append(msg)


		# inconsistent timing for trains with the same stop sequence
		# builds a gap fingerprint (minute-level diffs between consecutive requestedDepartures)
		# and flags any train whose fingerprint differs from others with the same stops
		
		train_fingerprints = {}
		for t in trains:
			# skip empties 
			if t.is_empty_train:
				continue
			
			tn_type = train_numbers_dict.get(t.number[0], '')
			if tn_type.startswith('Empty_'):
				continue
			
			gaps = []
			prev_rd = None
			prev_sid = None

			for e in t.entries:
				rd = e.attrib.get('requestedDeparture')
				sid = e.attrib.get('stationID')

				stoptime_attr = e.attrib.get('stopTime')

				if stoptime_attr is None:
					# Train doesn't stop - skip check, label with current destination sid
					gaps.append((sid, None))
					prev_rd = None
					continue

				stoptime = int(stoptime_attr) 
				

				# It's the first station (no prev)
				if prev_rd is None:
					gaps.append((sid, None))
					prev_rd = rd 
					prev_sid = sid

				# Attributes are missing
				elif rd is None:
					gaps.append((sid, None))
					prev_rd = None
					prev_sid = sid

				# Skip if dwell is 3min or less
				elif stoptime <= 180:
					try:
						total_mins = to_minutes_only(rd) - to_minutes_only(prev_rd)
						gaps.append((sid, total_mins))
					except (ValueError, AttributeError):
						gaps.append((sid, None))

					prev_rd = rd
					prev_sid = sid

				# Dwell is over 180s
				else:
					gaps.append((sid, None))
					prev_rd = None  
					prev_sid = sid

			train_fingerprints[(t.number, t.weekday)] = (tuple(t.station_ids), tuple(gaps), t.number, t.weekday, t.lineID)

		station_seq_groups = defaultdict(list)

		for key, (station_seq, gaps, tn, weekday, lineid) in train_fingerprints.items():
			station_seq_groups[station_seq].append((tn, weekday, lineid, gaps))

		inconsistent_timing = []

		for station_seq, members in station_seq_groups.items():
			if len(members) < 2:
				continue

			gap_groups = defaultdict(list)

			for tn, weekday, lineid, gaps in members:
				gap_groups[gaps].append((tn, weekday, lineid))

			if len(gap_groups) < 2:
				continue

			majority_gaps, majority_members = max(gap_groups.items(), key=lambda x: len(x[1]))
			header = f'Route: [{station_seq[0]} -> {station_seq[-1]}]'
			
			majority_str = ', '.join(f'{sid} {m}m' for sid, m in majority_gaps if m is not None)

			majority_dict = {sid: m for sid, m in majority_gaps if m is not None}
			diff_groups = defaultdict(list)

			for gaps, members_list in gap_groups.items():
				if gaps == majority_gaps:
					continue

				# Compare station gaps explicitly by matching their station IDs, not their positions
				diffs_list = []
				for out_sid, out_mins in gaps:
					if out_mins is None:
						continue
					
					# Look up what the runtime SHOULD be for this specific station ID
					maj_mins = majority_dict.get(out_sid)
					if maj_mins is not None and out_mins != maj_mins:
						diffs_list.append((out_sid, out_mins, maj_mins))

				if diffs_list:
					diff_groups[tuple(diffs_list)].extend(members_list)
					
			outlier_lines = []

			for diffs, members_list in diff_groups.items():
				diff_str = ', '.join(f'{sid} {actual}m (expected {expected}m)' for sid, actual, expected in diffs)
				train_info = ', '.join(
					f'{tn} ({WEEKDAY_KEYS_MASTER.get(wk, {}).get("short", wk)} #{extract_lineid_num(lid)})'
					for tn, wk, lid in members_list
				)
				outlier_lines.append(f'  Differing runtimes: {diff_str}\n    -> {train_info}')

			if outlier_lines:
				inconsistent_timing.append(f'{header}\n' + '\n'.join(outlier_lines))

		# ── output ────────────────────────────────────────────────────────────
		
		tn_doubles_fmt = [
		f'Train {tn} already running on {WEEKDAY_KEYS_MASTER.get(day, {}).get("short", day)}'
		for tn, day in tn_doubles
		]

		originpass_grouped = format_grouped_map(originpass_map)
		destinpass_grouped = format_grouped_map(destinpass_map)
		mismatchedplatforms_grouped = format_grouped_map(mismatched_map, "route")
		# format <4 min (detailed)
		short_tb_under4 = format_grouped_map(shortturnbacks['Turnbacks < 4 minutes'],"route")
		short_tb_4_8 = format_grouped_map(shortturnbacks['Turnbacks 4-8 minutes'],"route")

		sections = [
		('Runs starting/ending at non-stabling locations',      stablingissue),
		('First or last station passes through a revenue location', {
				'First station is pass': originpass_grouped,
				'Last station is pass': destinpass_grouped
			}),
		('Runs that change platforms either side of connection', mismatchedplatforms_grouped),
		
		('Short turnbacks', {
			'Turnbacks < 4 minutes': short_tb_under4,
			'Turnbacks 4-8 minutes': short_tb_4_8
		}),

		('Runs with more than one unit type',                    multiunitrun),
		('Runs missing connections',                             missingconnects),
		('Non-standardised train numbers',                       dodgy_tns),
		('Train numbers not matching unit type',                 wrong_tn),
		('Trains with more than 1 unit type',                    multiunittrain),
		('Duplicate train numbers',                              tn_doubles_fmt),
		('Connected trains with mismatched lineIDs',             lineid_mismatches),
		('Connections referencing train not found on same day',  lineid_missing),
		#('test subs', {'missing numbers':[2,4,5,6]})
		#('Same stops but inconsistent requested departure gaps', inconsistent_timing),
		]
		
		write_txt_report(filename,sections, inconsistent_timing)
		write_html_report(filename,sections,inconsistent_timing)


	except Exception as e:
		logging.error(traceback.format_exc())


if __name__ == "__main__":
	app = QApplication.instance() or QApplication(sys.argv)
	path = select_file(caption='Select RSX file',directory='',filter_str='RSX Files (*.rsx);;All Files (*.*)')
	if path:
		TTS_ERR(path)