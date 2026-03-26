import pytest
import xml.etree.ElementTree as ET
import os
import sys 

from taipan.xml_parser import TrainInfo

import xml.etree.ElementTree as ET
from taipan.xml_parser import TrainInfo, load_rsx_with_tree

def test_traininfo_full_rsx_parse(tmp_path):
    # Does a full parse of test_data/traininfo_init.rsx file (dummy file which is structurally equivalent to the rsx files) and checks whether parsing functions return the correctly formated variables when TrainInfo object is initialised.

    rsx_path = os.path.join(os.path.dirname(__file__),"test_data","traininfo_init.rsx",)
    tree, root, filename = load_rsx_with_tree(rsx_path)
    train_elem = root.find("train")
    assert train_elem is not None, "No <train> element found in RSX"
    t = TrainInfo(train_elem)

    # Basic metadata
    assert t.number == "AS14"
    assert t.lineID == "PSG-_____S_ ~ 174"
    assert t.run == "174"
    assert t.weekday == "4"

    # pattern/sector 
    assert t.pattern == "/Fr/Sector 3/ETF-PKR/To"
    assert t.sector == 3

    # entries
    assert t.stations == ["ETF", "EDJ", "PKR"]
    assert t.origin["stationID"] == "ETF"
    assert t.destin["stationID"] == "PKR"

    # times 
    assert t.odep == "04:05:45"
    assert t.ddep == "04:32:53"

    # traintypes
    assert t.train_type_raw == "Empty_6-IMU100"
    assert t.is_empty_train is True
    assert t.unit == "IMU100"
    assert t.cars == 6

    # connection 
    assert t.connection is not None

    # aliases 
    assert t.start_id == "ETF"
    assert t.end_id == "PKR"
    assert t.start_time == "04:05:45"
    assert t.end_time == "04:32:53"