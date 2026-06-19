import os
import re
import sys
import string
import time
import traceback
import logging

from taipan.core.xml_parser import TrainInfo, load_rsx_with_tree, extract_trains
from taipan.constants.locations import YARDS
#from taipan.constants.trains import TRAIN_TYPES
from taipan.gui.base import select_file, show_info_scroll_safe
from taipan.constants.days import ID_TO_SHORT
from PyQt6.QtWidgets import QApplication
ProcessDoneMessagebox = True

TRAIN_TYPES = {
'EMU': 'EMU',
'SMU': 'EMU',
'IMU100': 'IMU',
'NGR': 'NGR',
'NGRE': 'NGR',
'QMU': 'REP',
}


ALL_YARD_CODES = {yard for info in YARDS.values() for yard in info['yards']}


# generate ID ranges dynamically instead of using fixed lists — easier to maintain and modify if we want to change the scheme later
def generate_ew(prefixes):
    result = []
    for p in prefixes:
        for c in string.ascii_uppercase:
            result.append(p + c)
    return result
def generate_numeric(start, end):
    return [str(i).zfill(2) for i in range(start, end + 1)]

# NGR 01-499 and QMU 500-999, IMU/EMU as per RMC document but no differing across days
RANGES = {
   'EMU': generate_ew(list('ABCDEIJOP')),   # AA-EZ, IA-JZ, OA-PZ (234)
   'IMU': generate_ew(list('FGKQ')),        # FA-GZ, KA-KZ, QA-QZ (104)
   'REP': generate_numeric(500, 999),       # 500-999 (500)
   'NGR': generate_numeric(1, 499),         # 01-499 (499)
}

WEEKDAY_RANGES = RANGES
SAT_RANGES     = RANGES
SUN_RANGES     = RANGES

# weekdayKey -> (lineID day prefix, ranges dict)
DAY_CONFIG = {
'120': ('PSG-MTh', WEEKDAY_RANGES),
'64': ('PSG-MTh', WEEKDAY_RANGES),
'32': ('PSG-MTh', WEEKDAY_RANGES),
'16': ('PSG-MTh', WEEKDAY_RANGES),
'8': ('PSG-MTh', WEEKDAY_RANGES),
'4': ('PSG-Fri', WEEKDAY_RANGES),
'2': ('PSG-Sat', SAT_RANGES),
'1': ('PSG-Sun', SUN_RANGES),
}


# helper functions
def parse_time(t):
    """HH:MM:SS or HH:MM -> minutes from midnight. Handles times past 24h."""
    parts = t.strip().split(':')
    return int(parts[0]) * 60 + int(parts[1])
def earliest_yard_time(block, train_index):
    times = []
    for key in block:
        t = train_index[key]
        for sid, dep in zip(t.station_ids, t.departures):
            if sid in ALL_YARD_CODES:
                times.append(parse_time(dep))
    return min(times) if times else None

def earliest_yard_train(block, train_index):
    """Return (train_number, earliest_yard_time) or (None, None) if no yard departures."""
    earliest_time = None
    earliest_train = None
    for key in block:
        t = train_index[key]
        for sid, dep in zip(t.station_ids, t.departures):
            if sid in ALL_YARD_CODES:
                dep_time = parse_time(dep)
                if earliest_time is None or dep_time < earliest_time:
                    earliest_time = dep_time
                    earliest_train = t.number
    return (earliest_train, earliest_time)

def block_sort_key(block, train_index):
    yt = earliest_yard_time(block, train_index)
    if yt is not None:
        return (0, yt)
    first_deps = [parse_time(train_index[k].odep) for k in block]
    return (1, min(first_deps))


# main

def assign_line_ids(path):
    try:
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        print(filename, '\n')
        tree, root, filename_wo_ext = load_rsx_with_tree(path)
        output_filename = filename_wo_ext + ' (lineID).rsx'
        start_time = time.time()


        # parse all trains via trainInfo 
        all_trains = extract_trains(root)
        # Index by (number, weekday)
        train_index = {(t.number, t.weekday): t for t in all_trains}
        # Split into supported and skipped
        skipped = [t for t in all_trains if TRAIN_TYPES.get(t.unit) is None]
        trains = [t for t in all_trains if TRAIN_TYPES.get(t.unit) is not None]
        if skipped:
            print('\nSkipped trains (unsupported unit type, no lineID assigned):')
            for t in sorted(skipped, key=lambda x: x.number):
                print(f' {t.number} unit={t.unit} day={ID_TO_SHORT.get(t.weekday, t.weekday)}')


        # Build connection chains
        # connection tag on train A has trainNumber=B meaning A -> B.
        # Build forward map then find heads (not pointed to by anyone).
        forward = {}  # (number, weekday) -> (next_number, next_weekday)
        supported_keys = {(t.number, t.weekday) for t in trains}
        for t in trains:
            if t.connection is None:
                continue
            next_tn = t.connection.attrib.get('trainNumber')
            if not next_tn:
                continue
            # prefer same-day match
            next_key = None
            if (next_tn, t.weekday) in train_index:
                next_key = (next_tn, t.weekday)
            else:
                for candidate in trains:
                    if candidate.number == next_tn:
                        next_key = (candidate.number, candidate.weekday)
                        break
            # only follow into supported trains
            if next_key and next_key in supported_keys:
                forward[(t.number, t.weekday)] = next_key
        pointed_to = set(forward.values())
        heads = [
            (t.number, t.weekday)
            for t in trains
            if (t.number, t.weekday) not in pointed_to
        ]
        # Walk forward from heads to build blocks
        visited = set()
        blocks = []
        for head in heads:
            if head in visited:
                continue
            block = []
            cur = head
            while cur and cur not in visited:
                visited.add(cur)
                block.append(cur)
                cur = forward.get(cur)
            blocks.append(block)
        # Catch any trains not reached (isolated, no connections)
        for t in trains:
            key = (t.number, t.weekday)
            if key not in visited:
                blocks.append([key])
                visited.add(key)

        # group blocks by (day, unit) and sort within each bucket by earliest yard departure (or first departure if no yard)
        from collections import defaultdict
        day_unit_blocks = defaultdict(list)
        for block in blocks:
            first = train_index[block[0]]
            unit = TRAIN_TYPES[first.unit]
            day = first.weekday
            day_unit_blocks[(day, unit)].append(block)
        for key in day_unit_blocks:
            day_unit_blocks[key].sort(key=lambda b: block_sort_key(b, train_index))
    # match blocks across day pairs based on their stop patterns to assign the same lineID suffix where possible
        def block_signature(block, train_index, n=3):
            first_t = train_index[block[0]]
            stops = []
            for sid, dep in zip(first_t.station_ids, first_t.departures):
                hhmm = ':'.join(dep.split(':')[:2])
                stops.append((sid, hhmm))
                if len(stops) == n:
                    break
            return tuple(stops)
        # MTh<->Fri, Sat<->Sun
        DAY_PAIRS = [('120', '4'), ('2', '1')]
        # (day, unit, block_id) -> forced ew_index
        forced_ew = {}
        cross_match_details = []  # Store details for summary messagebox
        for day_a, day_b in DAY_PAIRS:
            for unit in RANGES:
                blocks_a = day_unit_blocks.get((day_a, unit), [])
                blocks_b = day_unit_blocks.get((day_b, unit), [])
                # build signature -> index map for day_a
                sig_to_index = {}
                for i, block in enumerate(blocks_a):
                    sig = block_signature(block, train_index)
                    sig_to_index[sig] = i
                # match day_b blocks against day_a
                for block in blocks_b:
                    sig = block_signature(block, train_index)
                    if sig in sig_to_index:
                        matched_idx = sig_to_index[sig]
                        forced_ew[(day_b, unit, id(block))] = matched_idx
                        train_nums = [k[0] for k in block]
                        cross_match_details.append({
                            'day_a': day_a, 'day_b': day_b, 'unit': unit,
                            'trains': train_nums, 'matched_idx': matched_idx
                        })
                        print(
                            f'Cross-day match: {ID_TO_SHORT.get(day_b, day_b)} block '
                            f'{train_nums} -> index {matched_idx} '
                            f'(matches {ID_TO_SHORT.get(day_a, day_a)})'
                        )
        # assign new line IDs within each (day, unit) bucket, using forced matches where applicable and filling the rest sequentially from the appropriate pool
        assigned = {}
        no_yard_warn = []
        for (day, unit), block_list in day_unit_blocks.items():
            cfg = DAY_CONFIG.get(day)
            if not cfg:
                print(f'Warning: unknown day code {day}, skipping')
                continue
            prefix, ranges = cfg
            ew_list = ranges.get(unit)
            if ew_list is None:
                print(f'Warning: no range defined for {unit} on {ID_TO_SHORT.get(day, day)}')
                continue
            # track which indices are taken by forced matches for this (day, unit)
            forced_indices = {
                forced_ew[(day, unit, id(block))]
                for block in block_list
                if (day, unit, id(block)) in forced_ew
            }
            # free indices in order, skipping forced ones
            free_indices = [i for i in range(len(ew_list)) if i not in forced_indices]
            free_iter = iter(free_indices)
            for block in block_list:
                forced_idx = forced_ew.get((day, unit, id(block)))
                if forced_idx is not None:
                    if forced_idx >= len(ew_list):
                        print(
                            f'ERROR: forced index {forced_idx} out of range for '
                            f'{unit} on {ID_TO_SHORT.get(day, day)}'
                        )
                        continue
                    ew = ew_list[forced_idx]
                else:
                    try:
                        idx = next(free_iter)
                    except StopIteration:
                        print(
                            f'ERROR: Ran out of lineIDs for {unit} on '
                            f'{ID_TO_SHORT.get(day, day)} — exhausted at block '
                            f'starting with train {block[0][0]}\n'
                            f'  Total lineIDs available: {len(ew_list)}\n'
                            f'  Forced slots used: {len(forced_indices)}'
                        )
                        break
                    ew = ew_list[idx]
                line_id_str = f'{prefix} ~ {ew}'
                train_numbers = [key[0] for key in block]
                if forced_idx is not None:
                    print(
                        f'Forced cross-day lineID for {ID_TO_SHORT.get(day, day)} block '
                        f'{train_numbers}: {line_id_str} (forced index {forced_idx})'
                    )
                earliest_train, earliest_time = earliest_yard_train(block, train_index)
                if earliest_time is not None:
                    hhmm = f'{earliest_time // 60:02d}:{earliest_time % 60:02d}'
                    print(f'Block {ew}: {train_numbers} -> {line_id_str} (first: train {earliest_train} at {hhmm})')
                else:
                    first_t = train_index[block[0]]
                    mins = parse_time(first_t.odep)
                    hhmm = f'{mins // 60:02d}:{mins % 60:02d}'
                    print(f'Block {ew}: {train_numbers} -> {line_id_str} (first: train {first_t.number} at {hhmm}, no yard dep)')
                yt = earliest_yard_time(block, train_index)
                if yt is None:
                    first_t = train_index[block[0]]
                    mins = parse_time(first_t.odep)
                    hhmm = f'{mins // 60:02d}:{mins % 60:02d}'
                    no_yard_warn.append(
                        f' Block {ew} ({ID_TO_SHORT.get(day, day)}): no yard departure — '
                        f'using first departure of train {first_t.number} '
                        f'at {first_t.start_id} {hhmm}'
                    )
                for key in block:
                    assigned[key] = line_id_str
        if no_yard_warn:
            print(f'\nWarning: {len(no_yard_warn)} block(s) with no yard departure:')
            for w in no_yard_warn:
                print(w)
    
        # Write output RSX
        # Replace lineID="..." on each <train> line.
        # Update any <connection> lines that reference the old run string.
    
        patterndaydict = {(t.number, t.pattern): t.weekday for t in all_trains}
        
        def get_old_run(t):
            lid = t.lineID
            return lid.split('~', 1)[1].strip() if '~' in lid else lid.strip()
        # (number, weekday) -> (old_run_str, new_run_str, new_full_lid)
        rename_map = {}
        for (tn, day), new_lid in assigned.items():
            t = train_index[(tn, day)]
            old = get_old_run(t)
            new = new_lid.split('~', 1)[1].strip()
            rename_map[(tn, day)] = (old, new, new_lid)
        print(f'Found {len(rename_map)} trains to rename')
        out_file = open(output_filename, 'w')
        wl = out_file.writelines
        cur_old_run = None
        cur_new_run = None
        print('Starting to process XML file...')
        debug_count = 0
        train_line_count = 0
        with open(path) as f:
            for line in f:
                if '<train' in line:
                    train_line_count += 1
                    tn_m = re.findall(r'number="([^"]+)"', line)
                    pat_m = re.findall(r'pattern="([^"]+)"', line)
                    if tn_m and pat_m:
                        tn = tn_m[0]
                        day = patterndaydict.get((tn, pat_m[0]))
                        rn = rename_map.get((tn, day))
                        if rn:
                            cur_old_run, cur_new_run, new_lid = rn
                            line = re.sub(r'lineID="[^"]*"', f'lineID="{new_lid}"', line)
                            
                        else:
                            if debug_count < 5:  # Only show first 5 non-matches
                                print(f'No rename mapping found for train {tn} (pattern: {pat_m[0]}, day: {day})')
                            cur_old_run = cur_new_run = None
                        debug_count += 1
                    wl(line)
                elif '<connection' in line and cur_old_run:
                    line = re.sub(re.escape(f'~ {cur_old_run}'),f'~ {cur_new_run}',line)
                    line = re.sub(f'"{re.escape(cur_old_run)}"',f'"{cur_new_run}"',line)
                    wl(line)
                else:
                    wl(line)
        out_file.close()
        print(f'\nOutput written to: {output_filename}')
        print(f'Runtime: {time.time() - start_time:.2f}s')
        if ProcessDoneMessagebox:
        
            summary_parts = [
                f"LineID assignment completed successfully!",
                f"Output: {output_filename}",
                f"Runtime: {time.time() - start_time:.2f}s",
                f"Total trains processed: {len(all_trains)}",
                f"Trains with new lineIDs: {len(assigned)}"
            ]

            if no_yard_warn:
                summary_parts.append(f"\n STABLING WARNINGS ({len(no_yard_warn)} blocks):")
                for w in no_yard_warn:
                    summary_parts.append(f"  {w}")

            # Count forced cross-day assignments
            forced_count = len([idx for idx in forced_ew.values() if idx is not None])
            if forced_count > 0:
                summary_parts.append(f"\n CROSS-DAY MATCHES ({forced_count} blocks):")
                summary_parts.append("  Blocks matched across day pairs (Mon-Thu->Fri, Sat->Sun)")
                for detail in cross_match_details[:10]:  # Show first 10 details
                    day_a_label = ID_TO_SHORT.get(detail['day_a'], detail['day_a'])
                    day_b_label = ID_TO_SHORT.get(detail['day_b'], detail['day_b'])
                    summary_parts.append(
                        f"  {day_b_label} {detail['trains']} -> {detail['unit']} index {detail['matched_idx']} "
                        f"(matches {day_a_label})"
                    )
                if len(cross_match_details) > 10:
                    summary_parts.append(f"  ... and {len(cross_match_details) - 10} more matches")

            summary_message = "\n".join(summary_parts)
            show_info_scroll_safe("LineID Assignment Complete", summary_message)
    except Exception:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(
        caption="Select RSX file",
        filter_str="RSX Files (*.rsx);;All Files (*.*)"
    )

    if path:
        assign_line_ids(path)

if __name__ == "__main__":
    main()
