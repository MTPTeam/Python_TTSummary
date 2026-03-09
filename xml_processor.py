from typing import List, Dict
from MTP_constants import SORT_ORDER_WEEK
import MTP_constants
from utils import timetrim
from xml_parser import resolve_DoO
from utils import csl


def init_store(yards: Dict[str, List[str]], day_codes: List[str]):
    # initialise the long stabling dictionary dynamically
    return {yard: {code: {'out': [], 'in': []} for code in day_codes} for yard in yards.keys()}


def build_daylists(daylist_out, daylist_in, wkdk, stable, run_dict):
    DoO = resolve_DoO(wkdk)
    for k, v in run_dict.items():
        run, D_o_run = k
        unit, cars, trips, start_sID, end_sID, start_t, finish_t, *_ = v
        delta = 1 if unit in ('NGR', 'NGRE') else (2 if cars == 6 else 1)
        if D_o_run in wkdk:
            if start_sID in stable:
                daylist_out.append([run, DoO, unit, cars, trips, start_sID, end_sID, start_t, delta])
            if end_sID in stable:
                daylist_in.append([run, DoO, unit, cars, trips, start_sID, end_sID, finish_t, delta])

    daylist_out.sort(key=lambda v: v[7]); daylist_in.sort(key=lambda v: v[7])
    order = {u: i for i, u in enumerate(MTP_constants.SORT_ORDER_UNIT)}
    daylist_out.sort(key=lambda v: order.get(v[2], 999))
    daylist_in.sort(key=lambda v: order.get(v[2], 999))
    for x in daylist_out: x[7] = timetrim(x[7])
    for x in daylist_in:  x[7] = timetrim(x[7])

def build_weeklists(mon_out, tue_out, wed_out, thu_out, mth_out, fri_out, sat_out, sun_out,
                    mon_in,  tue_in,  wed_in,  thu_in,  mth_in,  fri_in,  sat_in,  sun_in,
                    stableoptions, d_list, run_dict):
    if '120' in d_list:
        build_daylists(mth_out, mth_in, ('120',), stableoptions, run_dict)
    if '64' in d_list:
        build_daylists(mon_out, mon_in, ('64',), stableoptions, run_dict)
    if '32' in d_list:
        build_daylists(tue_out, tue_in, ('32',), stableoptions, run_dict)
    if '16' in d_list:
        build_daylists(wed_out, wed_in, ('16',), stableoptions, run_dict)
    if '8' in d_list:
        build_daylists(thu_out, thu_in, ('8',), stableoptions, run_dict)
    if '4' in d_list:
        build_daylists(fri_out, fri_in, ('4',), stableoptions, run_dict)
    if '2' in d_list:
        build_daylists(sat_out, sat_in, ('2',), stableoptions, run_dict)
    if '1' in d_list:
        build_daylists(sun_out, sun_in, ('1',), stableoptions, run_dict)


def singletrip_populator(d_list, mon, tue, wed, thu, mth, fri, sat, sun):
    # Map the code to (label, the actual list passed in)
    days_map = {
        '64':  ("Monday", mon),
        '32':  ("Tuesday", tue),
        '16':  ("Wednesday", wed),
        '8':   ("Thursday", thu),
        '120': ("school nights", mth),
        '4':   ("Friday", fri),
        '2':   ("Saturday", sat),
        '1':   ("Sunday", sun)
    }
    
    singletrip_col = []
    for code, (label, st_list) in days_map.items():
        if code in d_list:
            count = len(set(st_list))
            trips = csl(st_list)
            singletrip_col.append(f'{count} Runs with only a single trip on {label}: {trips}')
            
    return singletrip_col


def build_weeklists_into_store(store, yard_name, options, day_order, d_list, run_dict):
    outs = [store[yard_name][c]['out'] for c in day_order]
    ins  = [store[yard_name][c]['in']  for c in day_order]
    build_weeklists(*outs, *ins, options, d_list, run_dict)

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