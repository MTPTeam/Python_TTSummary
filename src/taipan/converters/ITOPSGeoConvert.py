from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilenames
from lxml import etree as ET
import re

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
items = list(askopenfilenames())

for item in items:
    if item.endswith(".rsl"):
        tree = ET.parse(item)
        root = tree.getroot()
        treestring = ET.tostring(tree,pretty_print=True).decode("utf-8")
# =============================================================================
#         rep = {"""type="atcBoard""": """type="atcBoard" interlockingMachine="Base2016""",
#              """type="entry""": """type="entry" interlockingMachine="Base2016""",
#              """type="exit""": """type="exit" interlockingMachine="Base2016""",
#              """type="shunting""": """type="atcBoard" interlockingMachine="Base2016"""
#              }
#         updated_treestring = treestring
#         new_treestring = replace_all(updated_treestring, rep)
# =============================================================================
        new_treestring = re.sub(r'(type=\"(atcBoard|entry|exit|shunting|etcsMarkerBoard)\")',
                        r'\1 interlockingMachine="Base2016"', treestring)
        tree = ET.fromstring(new_treestring)
        tree = ET.ElementTree(tree)
        with open(item, 'wb') as f:
            f.write(ET.tostring(tree,pretty_print=True,encoding='utf-8'))
            
for item in items:
    if item.endswith(".rsl"):
        with open(item,'r') as contents:
            save = contents.read()
        with open(item,'w') as contents:
            contents.write("""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n""")
        with open(item,'a') as contents:
            contents.write(save)
            
from tkinter import messagebox

messagebox.showinfo("ITOPSGeoConvert", "Process Done")            
