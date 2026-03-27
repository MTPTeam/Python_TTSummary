import os
import re
import time
import xml.etree.ElementTree as ET
import sys 


from taipan.gui.base import select_file, show_info, show_error, open_file_crossplatform
from taipan.gui.slicer import ask_slice_options, SliceDialog
from taipan.xml_parser import parse_rsx
from taipan.constants.days import SORT_ORDER_WEEK, ID_TO_SHORT

from PyQt6.QtWidgets import QApplication

class DuplicateTrainError(Exception):
    pass


def detect_blocks(rsx_path: str) -> list[str]:
    """
    Dynamically detect blocks from input RSX file. Use these to populate blocks matrix in GUI so all possible blocks are selectable rather than user-specified. 
    """
    blocks = set()

    with open(rsx_path, "r") as f:
        for line in f:
            if 'lineID="' in line:
                # Try "~ XXXX" form first
                m = re.findall(r'lineID=".+~\s(.{1,4})"', line)
                if m:
                    blocks.add(m[0].upper())
                else:
                    m = re.findall(r'lineID="(.{1,4})"', line)
                    if m:
                        blocks.add(m[0].upper())

    return sorted(blocks, key=lambda x: (0, int(x)) if x.isdigit() else (1, x)) 


def slice_rsx(rsx_path: str,desired_blocks: list[str],desired_days: list[str]) -> str:
    _, trains, _, _, _, duplicates = parse_rsx(rsx_path, want_trains=True, want_duplicates=True)
    if duplicates:
        msg = "\n".join(f"{tn} on {ID_TO_SHORT.get(day)}" for tn, day in duplicates)
        raise DuplicateTrainError(msg)
    patterndaydict = {(t.number, t.pattern): t.weekday for t in trains}


    directory, filename = os.path.split(rsx_path)
    name = os.path.splitext(filename)[0]

    blocks_str = ", ".join(desired_blocks)
    days_str = ", ".join(ID_TO_SHORT[d] for d in desired_days)  #weekdaykey replace 

    output_path = os.path.join(
        directory,
        f"{name} ({days_str}) and ({blocks_str}).rsx"
    )

    desired_blocks = {b.upper().strip() for b in desired_blocks}
    desired_days.sort(key=SORT_ORDER_WEEK.index)

    start = time.time()
    writeblock = True
    # count written trains
    trains_written = 0

    with open(rsx_path) as inp, open(output_path, "w") as out:
        for line in inp:
            if line.lstrip().startswith("<train"):
                tn = re.findall(r'number="(.{4,6})"', line)[0]
                pattern = re.findall(r'pattern="([^"]+)"', line)[0]

                run = re.findall(r'lineID=".+~\s(.{1,4})"', line)
                run = run[0] if run else re.findall(r'lineID="(.*)"', line)[0]

                day = patterndaydict.get((tn, pattern))
                writeblock = run in desired_blocks and day in desired_days

                if writeblock:
                    trains_written += 1
                    out.write(line)

            elif (line.lstrip().startswith("</timetable>") or line.lstrip().startswith("</railsys>")):
                out.write(line)

            elif writeblock:
                out.write(line)

    # delete the file and raise an error if no trains were written
    if trains_written == 0:
        os.remove(output_path)
        raise ValueError("No trains matched the selected blocks and days.")

    return output_path



def main():
    app = QApplication(sys.argv)
    rsx_path = select_file("Select RSX file", filter_str="RSX Files (*.rsx)")

    if not rsx_path:
        print("No File Selected")
        return

    available_blocks = detect_blocks(rsx_path)

    dialog = SliceDialog(available_blocks)
    if not dialog.exec():
        return

    if not dialog.blocks or not dialog.days:
        show_error("Invalid input", "Please select at least one block and one day.")
        return

    try:
        output = slice_rsx(rsx_path, dialog.blocks, dialog.days)
        show_info("RSX Slicer", f"Process complete:\n\n{output}")
        open_file_crossplatform(output)

    except DuplicateTrainError as e:
        # duplicate trains
        show_error("Duplicate trains detected", str(e))


    except ValueError as e:
        # no results found for the chosen block and day
        show_error("No results found", str(e))


    except Exception as e:
        # catch everything else
        show_error("Unexpected error", str(e))
    


if __name__ == "__main__":
    main()


