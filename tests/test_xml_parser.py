import sys
import os

# this needs to come before EVERY test file!!

import pytest
from taipan.xml_parser import normalise_train_type 

@pytest.mark.parametrize("raw, expected", [
    ("Empty_6-NGR",             "Empty_6-NGR"),
    ("6-NGR",                   "6-NGR"),
    ("Empty_6-REP",             "Empty_6-QMU"),
    ("6-REP",                   "6-QMU"),
    ("6-QMU_(AW0)_Surface",     "Empty_6-QMU"),
    ("6-QMU_(AW3)_Surface",     "6-QMU"),
    ("6-NGR_(AW0)_Surface",     "Empty_6-NGR"),
    ("6-NGR_(AW3)_Surface",     "6-NGR"),
    ("Empty_3-IMU100",          "Empty_3-IMU100"),
    ("3-IMU100",                "3-IMU100"),
    ("Empty_3-EMU",             "Empty_3-EMU"),
    ("3-EMU",                   "3-EMU"),
    ("Empty_6-IMU100",          "Empty_6-IMU100"),
    ("6-IMU100",                "6-IMU100"),
    ("Empty_6-EMU",             "Empty_6-EMU"),
    ("6-EMU",                   "6-EMU"),
])

def test_normalise_train_type(raw, expected):
    assert normalise_train_type(raw) == expected




"""if __name__ == "__main__":
    # Disable BOTH dash and hypothesis to be safe from internal errors - both libraries are conflicting with pytest 
    pytest.main([__file__, "-p", "no:dash", "-p", "no:hypothesis"])

"""

