import re
from lxml import etree as ET

from taipan.gui.base import select_multi_rsx_files, show_info
from PyQt6.QtWidgets import QApplication
import sys


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def run_geo_convert(paths=None):

    if not paths:
        paths = select_multi_rsx_files()

    if not paths:
        return

    for item in paths:
        if item.endswith(".rsl"):

            tree = ET.parse(item)
            treestring = ET.tostring(tree, pretty_print=True).decode("utf-8")

            new_treestring = re.sub(
                r'(type=\"(atcBoard|entry|exit|shunting|etcsMarkerBoard)\")',
                r'\1 interlockingMachine="Base2016"',
                treestring
            )

            tree = ET.fromstring(new_treestring)
            tree = ET.ElementTree(tree)

            with open(item, 'wb') as f:
                f.write(ET.tostring(tree, pretty_print=True, encoding='utf-8'))

    # fix XML header
    for item in paths:
        if item.endswith(".rsl"):
            with open(item, 'r') as contents:
                save = contents.read()

            with open(item, 'w') as contents:
                contents.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')

            with open(item, 'a') as contents:
                contents.write(save)

    show_info("ITOPSGeoConvert", "Process Done")


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)

    paths = select_multi_rsx_files()
    if paths:
        run_geo_convert(paths)