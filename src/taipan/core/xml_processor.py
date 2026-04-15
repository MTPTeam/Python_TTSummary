from typing import List, Dict

from taipan.constants.trains import SORT_ORDER_UNIT
from taipan.constants.days import WEEKDAY_KEYS_MASTER, ID_TO_LONG

from taipan.core.utils import timetrim
from taipan.core.xml_parser import resolve_DoO
from taipan.core.utils import csl, _time_key
import numpy as np

def init_store(locations_dict, day_codes):
    # Change 'yard' to 'loc_data['yards']' to handle the new nested structure
    return {
        name: {code: {'out': [], 'in': []} for code in day_codes} 
        for name in locations_dict.keys()
    }



def build_daylists(daylist_out,daylist_in,wkdk,stable,run_dict,count=False,merge_for_count=False):
    DoO = resolve_DoO(wkdk)

    # OLD RULES preserve historical delta rules for each mode:
    # - balance: unit == 'NGR' -> 1; else 2 if cars==6 else 1
    # - count:   unit in ('NGR','NGRE') -> 1; else 2 if cars==6 else 1

    ### NEW RULE - all trains 6 cars = 1, 3 cars = 0.5

    for k, v in run_dict.items():
        run, D_o_run = k
        unit, cars, trips, start_sID, end_sID, start_t, finish_t, *_ = v        
        delta = 0.5 if cars == 3 else 1

        if D_o_run in wkdk:
            # STARTS at a stable location
            if start_sID in stable:
                signed_delta = -delta if count else delta
                daylist_out.append([
                    run, DoO, unit, cars, trips, start_sID, end_sID, start_t, signed_delta
                ])

            # ENDS at a stable location
            if end_sID in stable:
                daylist_in.append([
                    run, DoO, unit, cars, trips, start_sID, end_sID, finish_t, +delta
                ])

    # Sort by time first
    daylist_out.sort(key=lambda v: v[7])
    daylist_in.sort(key=lambda v: v[7])

    # Then by unit order (stable sort retains time order within unit)
    order = {u: i for i, u in enumerate(SORT_ORDER_UNIT)}
    daylist_out.sort(key=lambda v: order.get(v[2], 999))
    daylist_in.sort(key=lambda v: order.get(v[2], 999))

    # Final: trim times
    for x in daylist_out:
        x[7] = timetrim(x[7])
    for x in daylist_in:
        x[7] = timetrim(x[7])

    # If the caller wants the legacy 'single list' output in count mode, return it
    if count and merge_for_count:
        combined = daylist_out + daylist_in

        # Sort combined the same way: time, then unit
        combined.sort(key=lambda v: v[7])
        combined.sort(key=lambda v: order.get(v[2], 999))

        return combined

    return None



def build_weeklists(mon_out, tue_out, wed_out, thu_out, mth_out, fri_out, sat_out, sun_out,
                    mon_in,  tue_in,  wed_in,  thu_in,  mth_in,  fri_in,  sat_in,  sun_in,
                    stableoptions, d_list, run_dict, count):
    if '120' in d_list:
        build_daylists(mth_out, mth_in, ('120',), stableoptions, run_dict, count)
    if '64' in d_list:
        build_daylists(mon_out, mon_in, ('64',), stableoptions, run_dict, count)
    if '32' in d_list:
        build_daylists(tue_out, tue_in, ('32',), stableoptions, run_dict, count)
    if '16' in d_list:
        build_daylists(wed_out, wed_in, ('16',), stableoptions, run_dict, count)
    if '8' in d_list:
        build_daylists(thu_out, thu_in, ('8',), stableoptions, run_dict, count)
    if '4' in d_list:
        build_daylists(fri_out, fri_in, ('4',), stableoptions, run_dict, count)
    if '2' in d_list:
        build_daylists(sat_out, sat_in, ('2',), stableoptions, run_dict, count)
    if '1' in d_list:
        build_daylists(sun_out, sun_in, ('1',), stableoptions, run_dict, count)



def build_weeklists_into_store(store, yard_name, options, day_order, d_list, run_dict, count):
    outs = [store[yard_name][c]['out'] for c in day_order]
    ins  = [store[yard_name][c]['in']  for c in day_order]
    build_weeklists(*outs, *ins, options, d_list, run_dict, count)



def make_legacy_stables_dict_from_store(store, day_order):
    legacy = {}
    for yard in store.keys():
        out_lists = [store[yard][c]['out'] for c in day_order]
        in_lists  = [store[yard][c]['in']  for c in day_order]
        legacy[yard] = tuple(out_lists + in_lists)  # 16 tuples rather than 16 lists 
    return legacy


def write_sheet_from_store(ws, store, yard_name, day_order, write_sheet_legacy):
    o = [store[yard_name][c]['out'] for c in day_order]
    i = [store[yard_name][c]['in']  for c in day_order]
    write_sheet_legacy(ws, *o, *i)


def find_runs_without_stable(run_dict, acceptable_stables):
    runs_without_stable = []

    for key, run in run_dict.items():
        try:
            runID   = key[0]
            DoO     = key[1]
            run_oID = run[3]
            run_dID = run[4]
        except:
            continue # add some debugging lines here
        if run_oID not in acceptable_stables or run_dID not in acceptable_stables:
            runs_without_stable.append([runID, DoO, run_oID, run_dID])

    return runs_without_stable

def build_singletrip_col(d_list, run_dict):

    # auto detect combined
    combined_id = None
    for k, v in WEEKDAY_KEYS_MASTER.items():
        if v['short'].lower() == 'mon-thu' or v['alias'].lower() == 'm-th':
            combined_id = k
            break
    # fallback if not found
    if combined_id is None:
        combined_id = '120'
    # detect mon-thu
    mon_thu_components = []
    for k, v in WEEKDAY_KEYS_MASTER.items():
        if v['long'] in ('Monday', 'Tuesday', 'Wednesday', 'Thursday'):
            mon_thu_components.append(k)

    # create match map
    day_match = {}
    for day_id in WEEKDAY_KEYS_MASTER:
        match_set = {day_id}
        if day_id in mon_thu_components:
            match_set.add(combined_id)
        day_match[day_id] = match_set
    per_day = {day_id: [] for day_id in WEEKDAY_KEYS_MASTER}

    # collect single trip runs
    for key, run in run_dict.items():
        try:
            runID = key[0]
            DoO   = key[1]
            trips = run[2]
        except:
            continue

        if trips != 1:
            continue

        for day_id, match_set in day_match.items():
            if DoO in match_set:
                per_day[day_id].append(runID)

    # dynamically build output lines 
    singletrip_col = []
    for day_id in d_list:
        if day_id not in per_day:
            continue

        label = ID_TO_LONG.get(day_id, day_id)
        count = len(set(per_day[day_id]))

        singletrip_col.append(
            f"{count} Runs with only a single trip on {label}: {csl(per_day[day_id])}"
        )

    return singletrip_col


def merge_out_in_per_day(out_list, in_list, sort_by_unit=True):
    """
    Merge OUT + IN into a single legacy day list.
    Sort by time (primary) and unit (secondary). Times are trimmed before sort.
    """
    
    merged = list(out_list) + list(in_list)

    unit_idx = {u: i for i, u in enumerate(SORT_ORDER_UNIT)}
    if sort_by_unit:
        merged.sort(key=lambda v: (_time_key(v[7]), unit_idx.get(v[2], 999)))
    else:
        merged.sort(key=lambda v: _time_key(v[7]))

    return merged


def startofdayunitcount(daylist, u_list):
    """ 
    Finds the minimum number of units stabled at each location at the start of the day
    Could be other, unused units
    If SORT_ORDER_UNIT is updated then this function will update automatically and calculate new unit types if needed 
    """
    
    # adjust these if the row layout changes
    UNIT_IDX = 2   # where the unit type string lives, e.g NGR, EMU
    DELTA_IDX = 8  # where the +1/-1 (or other delta) lives

    # init running totals and min prefix per unit from the list,
    # so everything is present even if a unit never appears in the daylist.
    running = {u: 0 for u in SORT_ORDER_UNIT}
    min_prefix = {u: 0 for u in SORT_ORDER_UNIT}

    # Walk the day's events and track its running sum and its minimum per unit
    for row in (daylist or []):
        unit = row[UNIT_IDX]
        delta = row[DELTA_IDX]

        # If a unit appears that's not in SORT_ORDER_UNIT, init on the fly (so if new traintypes are added to SORT_ORDER_UNIT this will propagate through to this function)
        if unit not in running:
            running[unit] = 0
            min_prefix[unit] = 0

        running[unit] += float(delta)
        if running[unit] < min_prefix[unit]:
            min_prefix[unit] = running[unit]

    # The number required at start of day for each unit is -min_prefix (never negative)
    per_unit_dict = {u: float(max(0.0, -min_prefix.get(u, 0.0))) for u in SORT_ORDER_UNIT}

    # Produce output aligned to u_list (matches Summary writing order)
    per_unit_aligned = [per_unit_dict.get(u, 0.0) for u in u_list]

    total_required = float(sum(per_unit_aligned))
    return [total_required] + per_unit_aligned


def endofdayunitcount(daylist, u_list, change_matrix):
   """
   Finds the end of day balance between units at the start of the day and units at the end of the day
   An output of zero means the stabling location is balanced for that day
   """
   startcount = startofdayunitcount(daylist, u_list)
   stablechange = np.array(startcount)
   for entry in daylist:
       if entry[8] < 0:
           stablechange -= np.array(change_matrix.get(entry[2])) * abs(entry[8])
       else:
           stablechange += np.array(change_matrix.get(entry[2])) * abs(entry[8])
   total = stablechange[0] - startcount[0]
   breakdown = list(stablechange[1:] - np.array(startcount[1:]))
   return total, breakdown



def overnightstabling(daylist, u_list, change_matrix):
   """
   Finds the number of units back in each location at the end of the day
   Uses the startofdayunitcount function as a startpoint, minimum required units for that day
   Could be other, unused units which never left
   """
   startcount = startofdayunitcount(daylist, u_list)
   stablechange = np.array(startcount)
   for entry in daylist:
       if entry[8] < 0:
           stablechange -= np.array(change_matrix.get(entry[2])) * abs(entry[8])
       else:
           stablechange += np.array(change_matrix.get(entry[2])) * abs(entry[8])
   if max(stablechange[0], startcount[0]) == stablechange[0]:
       return stablechange[0], stablechange[1:]
   else:
       return startcount[0], startcount[1:]
    


    
def interpeakstabling(daylist, u_list):
   """
   Finds the maximum number of trains stabled at each location during interpeak
   Returns the total and the unit breakdown at that point in time
   """
   ip_tracker = []
   prepeak = True
   ip = startofdayunitcount(daylist, u_list)[0]
   for t, x in enumerate(daylist):
       if len(x[7]) == 4:
           x[7] = '0' + x[7]
       ip += x[8]
       if '09:00:00' < x[7] < '15:30:00':
           while prepeak == True:
               ip_tracker.append(
                   (daylist[t-1][7], ip - daylist[t][8])
               )
               prepeak = False
           ip_tracker.append((x[7], ip))
   if ip_tracker:
       traincount = [x[1] for x in ip_tracker]
       output_total = max(traincount)
       idx = traincount.index(output_total)
       max_oclock = ip_tracker[idx][0]
   else:
       output_total = 0
   unit_subtotals = []
   for u in u_list:
       unit_ip = startofdayunitcount(daylist, u_list)[1:][u_list.index(u)]
       for x in daylist:
           try:
               max_oclock
               if x[2] == u:
                   unit_ip += x[8]
               if x[7] == max_oclock:
                   break
           except:
               break
       if output_total == 0:
           unit_ip = 0
       unit_subtotals.append(unit_ip)
   return output_total, unit_subtotals