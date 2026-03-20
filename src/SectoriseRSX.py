from xml_parser import TrainInfo, extract_trains, load_rsx_with_tree
import gui
import sys 

from MTP_constants import WEEKDAY_KEYS_MASTER, MON_THU_MASK, YARDS
from utils import get_weekday_short
import os
from collections import defaultdict


### EXPAND THIS AND PUT INTO MTPCONSTANTS WHEN DONE 
Sector1 = {
    'Caboolture': ['CAB', 'CAW', 'CAE'],
    'SunshineCoast': ['NBR', 'CRD', 'BIR'],
    'Gympie': ['GYN'],
    'Redcliffe': ['KPR'],
    'Beenleigh': ['BNH', 'BNHS', 'BNT', 'KRY', 'CEP'],
    'GoldCoast': ['VYS', 'VYST'],
    'City': ['BOG', 'RTL'],
    'Exhibition': ['EXH'],
    'Yeerongpilly' : ['YLY'],
    'Lawnton': ['LWO']
}

Sector2 = {
    'Rosewood': ['RSW'],
    'Ipswich': ['IPS', 'IPSS'],
    'Springfield': ['SFC', 'DAR'],
    'Airport': ['BDT'],
    'Shorncliffe': ['SHC', 'NTG'],
    'Doomben': ['DBN'],
    'City': ['RS', 'BHI'],
    'Auchenflower': ['AHF'],
    'Corinda': ['CQD'],
    'Toowong': ['TWG'],
    'Milton': ['MTZ'],
    'Thagoona': ['TAO']


}

Sector3 = {
    'Cleveland': ['CVN', 'MNY', 'CNQ'],
    'FernyGrove': ['FYG'],
    'City': ['RS', 'BHI'],
    'Park Rd': ['PKR']
}


def build_code_to_sector_map():
    all_sectors = {
        'Sector1': Sector1,
        'Sector2': Sector2,
        'Sector3': Sector3,
    }

    lookup = {}
    for sector_name, sector in all_sectors.items():
        for codes in sector.values():
            for code in codes:
                lookup.setdefault(code.upper(), set()).add(sector_name)

    return lookup

def build_yard_code_lookup(yards):
    lookup = {}
    for _, data in yards.items():
        for code in data.get('yards', []):
            lookup[code.upper()] = data
    return lookup

CODE_TO_SECTOR = build_code_to_sector_map()
YARD_CODE_LOOKUP = build_yard_code_lookup(YARDS)

def resolve_possible_sectors(code):
    code = code.upper()

    # if its a yard
    if code in YARD_CODE_LOOKUP:
        yard = YARD_CODE_LOOKUP[code]

        if 'sector' in yard:
            return {f"Sector{yard['sector']}"}

        # shared yard (ETS / ETF / Mayne West)
        possible = set()
        for yard_code in yard['yards']:
            sectors = CODE_TO_SECTOR.get(yard_code)
            if sectors:
                possible |= sectors  

        return possible

    # otherwise its a regular station
    sectors = CODE_TO_SECTOR.get(code)
    if sectors:
        return set(sectors)

    return set()



def get_common_sector(code1, code2):
    s1 = resolve_possible_sectors(code1)
    s2 = resolve_possible_sectors(code2)

    # direct intersection
    common = s1 & s2
    if len(common) == 1:
        return common.pop()

    # logic for shared yards 
    # if one side is ambiguous (shared sectors) and the other is single-sector, 
    # inherit the single-sector side
    if len(s1) > 1 and len(s2) == 1:
        return next(iter(s2))

    if len(s2) > 1 and len(s1) == 1:
        return next(iter(s1))
    
    ## add special logic for classifying when both O/D have multiple sectors here (if needed)

    # fallback if not found 
    return None


#print("CLEVELAND", get_common_sector('ETF', 'CVN'))

def check_CRR(trains):
    """
    Checks if any of the trainstation IDs have 'RS' or 'RTL'
    if all trainstation IDs in entries across the whole file have 'RS' and not 'RTL' then it means the file has no CRR 
    if both or just RTL are present its okay
    """
    rs_seen = False
    rtl_seen = False

    for t in trains:
        if 'RS' in t.stations:
            rs_seen = True
        if 'RTL' in t.stations:
            rtl_seen = True

    return rs_seen and not rtl_seen


def create_pattern(train, sector):
    weekday_str = get_weekday_short(train.weekday)
    # Extract just the number from "Sector2" / "Sector 2"
    sector_num = ''.join(filter(str.isdigit, str(sector)))
    return f"/{weekday_str}/Sector {sector_num}"


def create_unassigned_pattern(train):
    weekday_str = get_weekday_short(train.weekday)
    return f"/{weekday_str}/Unassigned"



def extract_sector_from_pattern(pattern):
    if not pattern:
        return None
    if "Sector" in pattern:
        return pattern.split("Sector")[-1].strip()
    return None


if __name__ == "__main__":

    path = gui.select_file(caption="Select RSX file", directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")

    tree, root, filename = load_rsx_with_tree(path)
        
    base, ext = os.path.splitext(path)
    out_path = f"{base}_sectorised_lineid{ext}"


    trains = extract_trains(root)

    if check_CRR(trains):
        gui.show_info('ERROR', 'RS present but RTL missing (Please check for CRR)')
        sys.exit("CRITICAL ERROR: RS present but RTL missing (no CRR)")

    # for debugging / summary stats of matched and unmatched 
    non_revenue = revenue = same_sector_pairs = diff_sector_pairs = same_sector_revenue = same_sector_empty = connections = upgraded = 0

    diff_sector_list = set() # keep it unique for readability
    trains_by_line_and_day = defaultdict(list) # save trains by LineID and day 

    for t in trains:
        if t.is_empty_train:
            non_revenue += 1 # skip if its non revenue 
        else:
            revenue += 1


        start_stn = t.stations[0]
        end_stn = t.stations[-1]
        sector = get_common_sector(start_stn, end_stn)
        weekday = get_weekday_short(t.weekday)
        line_id = t.raw.get("lineID")
        trains_by_line_and_day[(line_id, weekday)].append(t)


        # keep a running total of same vs diff sectors 
        if sector:
            pattern_str = create_pattern(t, sector)
            t.raw.set("pattern", pattern_str) # set pattern to the pattern string we made with sector

            #print("t, raw set", t.raw.get('pattern')) # checking if it changed
            same_sector_pairs += 1

            if t.is_empty_train:
                same_sector_empty += 1
            else:
                same_sector_revenue += 1


            if t.connection is not None:
                # means a connection was found
                t.connection.set("trainPattern", pattern_str)  # update connection 'trainPattern' to equal pattern 
                connections += 1
                #print("connection trainpattern", t.connection.get("trainPattern")) # checking if it changed

        else:
            # OD either does not match sectors or arent in the dict
            # it is unassigned
            pattern_str = create_unassigned_pattern(t)
            t.raw.set("pattern", pattern_str) # set pattern to the pattern string we made with sector
            if t.connection is not None:
                # means a connection was found
                t.connection.set("trainPattern", pattern_str)  # update connection 'trainPattern' to equal pattern 
                connections += 1

            #print(pattern_str)
            diff_sector_pairs += 1
            diff_sector_list.add((start_stn, end_stn))

    
    upgraded = 0
    
    mixed_lineid_flags = []


    for (line_id, weekday), line_trains in trains_by_line_and_day.items():
        sectors_seen = set()
        unassigned_trains = []

        for t in line_trains:
            pattern = t.raw.get("pattern")
            sector = extract_sector_from_pattern(pattern)

            if sector:
                sectors_seen.add(sector)
            else:
                unassigned_trains.append(t)

        # only upgrade if exactly one sector exists 
        if len(sectors_seen) == 1 and unassigned_trains:
            sector = sectors_seen.pop()
            for t in unassigned_trains:
                new_pattern = f"/{weekday}/Sector {sector}"
                t.raw.set("pattern", new_pattern)

                if t.connection is not None:
                    t.connection.set("trainPattern", new_pattern)
                
                upgraded += 1
                same_sector_pairs += 1
                diff_sector_pairs -= 1
                
                if t.is_empty_train:
                    same_sector_empty += 1
                else:
                    same_sector_revenue += 1
        
        elif len(sectors_seen) > 1:
            mixed_lineid_flags.append({
                "line_id": line_id,
                "weekday": weekday,
                "sectors_seen": sorted(sectors_seen),
                "unassigned_count": len(unassigned_trains),
                "total_trains": len(line_trains),
            })



    tree.write(out_path, encoding="utf-8", xml_declaration=True)

    print(f"Revenue sectorised: {same_sector_revenue}/{revenue}")
    print(f"Empty sectorised: {same_sector_empty}/{non_revenue}")
    print(f"Total sectorised: {same_sector_pairs}/{same_sector_pairs + diff_sector_pairs}")
    print(f"Upgraded {upgraded} previously unassigned trains via lineID inference")



        
    print(f"\nLineID/day combinations with mixed sectors (connection breaks): {len(mixed_lineid_flags)}")

    ### DEBUG PRINT
    for flag in mixed_lineid_flags:
        print(
            f"LineID {flag['line_id']} | {flag['weekday']} | "
            f"Sectors: {flag['sectors_seen']} | "
            f"Unassigned: {flag['unassigned_count']} / {flag['total_trains']}"
        )


    #### GUI PRINT
    if mixed_lineid_flags:
        for flag in mixed_lineid_flags:
            gui.show_info(
                "Broken connections",
                f"LineID {flag['line_id']} \n{flag['weekday']}\n"
                f"Sectors: {', '.join(flag['sectors_seen'])}\n"
                f"Unassigned: {flag['unassigned_count']} / {flag['total_trains']}"
            )



        
    """
    print("same: ", same_sector_pairs)
    print("diff: ", diff_sector_pairs)
    start_stn = t.stations[0]
    end_stn = t.stations[-1]
    print("revenue:", revenue)
    print("non_revenue", non_revenue)
    print("START DIFF SECTORS NOW")
    

    for elem in diff_sector_list:
        print(elem)


    """


    
    
    final_diff = set()

    for (o, d) in diff_sector_list:
        # check if still unassigned
        # simplest approach: look for any train with this OD still marked Unassigned
        for t in trains:
            if t.stations[0] == o and t.stations[-1] == d:
                pattern = t.raw.get("pattern")
                if pattern and "Unassigned" in pattern:
                    final_diff.add((o, d))
                    break



    #print("different O/D sectors: ", diff_sector_list)

    



