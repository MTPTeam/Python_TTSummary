from xml_parser import TrainInfo, extract_trains, load_rsx_with_tree
import gui
import sys 

from MTP_constants import WEEKDAY_KEYS_MASTER, MON_THU_MASK
from utils import get_weekday_short
import os


### EXPAND THIS AND PUT INTO MTPCONSTANTS WHEN DONE 

Sector1 = {
    'Caboolture': ['CAB', 'CAW', 'CAE'],
    'SunshineCoast': ['NBR', 'CRD', 'BIR'],
    'Gympie': ['GYN'],
    'Redcliffe': ['KPR'],
    'Beenleigh': ['BNH', 'BNHS', 'BNT', 'KRY', 'CEP'],
    'GoldCoast': ['VYS', 'VYST'],
    'City': ['BOG', 'RTL']
}

Sector2 = {
    'Rosewood': ['RSW'],
    'Ipswich': ['IPS', 'IPSS'],
    'Springfield': ['SFC', 'DAR'],
    'Airport': ['BDT'],
    'Shorncliffe': ['SHC', 'NTG'],
    'Doomben': ['DBN'],
    'FernyGrove': ['FYG'],
    'City': ['RS', 'BHI']
}

Sector3 = {
    'Cleveland': ['CVN', 'MNY', 'CNQ'],
    'FernyGrove': ['FYG'],
    'City': ['RS', 'BHI']
}


def get_common_sector(code1, code2):
    all_sectors = {'Sector1': Sector1,'Sector2': Sector2,'Sector3': Sector3,}
    code1 = code1.upper()
    code2 = code2.upper()

    for name, sector in all_sectors.items():
        all_codes = [c for sublist in sector.values() for c in sublist]

        if code1 in all_codes and code2 in all_codes:
            return name   

    return None


# Quick Test:
#print(are_in_same_sector('CAB', 'NBR'))  # True (Both in Sector1)
#print(are_in_same_sector('CAB', 'IPS'))  # False (Sector1 vs Sector2)


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



if __name__ == "__main__":

    path = gui.select_file(caption="Select RSX file", directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")

    tree, root, filename = load_rsx_with_tree(path)
        
    base, ext = os.path.splitext(path)
    out_path = f"{base}_sectorised{ext}"


    trains = extract_trains(root)

    if check_CRR(trains):
        gui.show_info('ERROR', 'RS present but RTL missing (Please check for CRR)')
        sys.exit("CRITICAL ERROR: RS present but RTL missing (no CRR)")

    # for debugging 
    non_revenue = 0
    revenue = 0
    same_sector_pairs = 0
    diff_sector_pairs = 0 
    connections = 0
    diff_sector_list = set() # keep it unique for readability

    for t in trains:
        if t.is_empty_train:
            non_revenue += 1 # skip if its non revenue 
            continue
        else:
            revenue += 1


        start_stn = t.stations[0]
        end_stn = t.stations[-1]
        sector = get_common_sector(start_stn, end_stn)

        # keep a running total of same vs diff sectors 
        if sector:
            pattern_str = create_pattern(t, sector)
            t.raw.set("pattern", pattern_str) # set pattern to the pattern string we made with sector

            #print("t, raw set", t.raw.get('pattern')) # checking if it changed
            same_sector_pairs += 1

            if t.connection is not None:
                # means a connection was found
                t.connection.set("trainPattern", pattern_str)  # update connection 'trainPattern' to equal pattern 
                connections += 1
                #print("connection trainpattern", t.connection.get("trainPattern")) # checking if it changed

        else:
            # OD either does not match sectors or arent in the dict
            diff_sector_pairs += 1
            diff_sector_list.add((start_stn, end_stn))

    tree.write(out_path, encoding="utf-8", xml_declaration=True)

    print(f"{same_sector_pairs}/{same_sector_pairs + diff_sector_pairs} revenue pairs have been sectorised!")

        
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

    #print("different O/D sectors: ", diff_sector_list)

    """



