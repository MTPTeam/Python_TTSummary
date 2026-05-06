"""
itops_file_prep.py
------------------
Python port of the VBA ITOPSFilePrep macro.
Prepares a RailSys (.rsx) file for ITOPS by:
 - Removing ignorePzb90 attributes from train nodes
 - Reformatting lineID run IDs with a dash separator
 - Clearing entry comments
 - Fixing KPRS track IDs
 - Normalising stopTime values to allowed intervals
Output is saved as "ITOPS_<filename>.rsx" next to the input file.
"""
import sys
import os
import re
import math
from lxml import etree
from PyQt6.QtWidgets import QApplication
from taipan.gui.base import select_file, show_info

# ---------------------------------------------------------------------------
# lineID run ID reformatting
# ---------------------------------------------------------------------------
def reformat_run_id(ole: str) -> str | None:
   """
   Apply the three VBA lineID reformat rules to the right-hand side of the
   lineID split. Returns the reformatted string, or None if no rule matched.
   Rules (matching VBA exactly):
     1. len==4, starts with E, ends with A  -> first 3 chars + "-" + last char
     2. len==3, first two chars are letters, last is digit -> first 2 + "-" + last
     3. len==3, first two chars are digits, last is uppercase letter -> first 2 + "-" + last
   """
   if len(ole) == 4 and ole[0] == "E" and ole[-1] == "A":
       return ole[:3] + "-" + ole[-1]
   if (len(ole) == 3
           and ole[0].isalpha()
           and ole[1].isalpha()
           and ole[2].isdigit()):
       return ole[:2] + "-" + ole[-1]
   if (len(ole) == 3
           and ole[0].isdigit()
           and ole[1].isdigit()
           and ole[2].isupper()):
       return ole[:2] + "-" + ole[-1]
   return None

def process_train_nodes(trains) -> None:
   for node in trains:
       # Remove ignorePzb90 attribute if present
       if "ignorePzb90" in node.attrib:
           del node.attrib["ignorePzb90"]
       line_id = node.get("lineID", "")
       if "~" in line_id:
           parts   = line_id.split("~", 1)
           prefix  = parts[0]
           ole     = parts[1].lstrip(" ")          # LTrim equivalent
           new_run_id = reformat_run_id(ole)
           if new_run_id is not None:
               node.set("lineID", f"{prefix}~ {new_run_id}")

# ---------------------------------------------------------------------------
# Entry node processing
# ---------------------------------------------------------------------------
ALLOWED_STOP_TIMES = {"1", "30", "90"}

def normalise_stop_time(raw: str) -> str:
   """
   Mirror the VBA stopTime normalisation logic:
     - If already 1, 30, or 90 -> leave as-is (handled by caller)
     - Floor to nearest whole minute (floor(seconds / 60))
     - If floored result is 0 -> return "30"
     - Otherwise -> return str(minutes * 60)
   Then, after normalisation, 90 -> 120.
   """
   seconds = int(raw)
   minutes = math.floor(seconds / 60)
   if minutes == 0:
       result = "30"
   else:
       result = str(minutes * 60)
   if result == "90":
       result = "120"
   return result

def process_entry_nodes(entries) -> None:
   for entry in entries:
       # Clear comment attribute
       if entry.get("comment") is not None:
           entry.set("comment", "")
       # Fix KPRS track IDs
       if entry.get("stationID") == "KPRS":
           track = entry.get("trackID", "")
           if track == "D-0":
               entry.set("trackID", "D-10")
           elif track == "U-0":
               entry.set("trackID", "U-10")
       # Normalise stopTime
       stop_time = entry.get("stopTime")
       if stop_time is not None:
           if stop_time not in ALLOWED_STOP_TIMES:
               entry.set("stopTime", normalise_stop_time(stop_time))
           elif stop_time == "90":
               entry.set("stopTime", "120")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(path: str = None) -> None:
    if not path:
        path = select_file(
            caption="Select RailSys file for ITOPS changes",
            filter_str="RSX Files (*.rsx)"
        )

    if not path:
        return

    base, ext   = os.path.splitext(path)
    filename    = os.path.basename(path)
    out_path    = os.path.join(os.path.dirname(path), f"ITOPS_{filename}")
    tree  = etree.parse(path)
    root  = tree.getroot()
    trains  = root.findall("timetable/train")
    entries = root.findall(".//entry")
    process_train_nodes(trains)
    process_entry_nodes(entries)
    tree.write(out_path, xml_declaration=True, encoding="UTF-8", pretty_print=True)
    show_info("Success", "Output Saved!")

if __name__ == "__main__":
   app = QApplication.instance() or QApplication(sys.argv)
   path = select_file(caption="Select RailSys file for ITOPS changes", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
   if path:
       main(path)