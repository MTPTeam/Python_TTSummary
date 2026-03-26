import re 
import os 
import pytest

import taipan.SectoriseRSX as sectorise

@pytest.fixture(autouse=True)
def mock_sector_data(monkeypatch):
    #Replace global station + yard lookups with small predictable data
    

    monkeypatch.setattr(
        sectorise,
        "CODE_TO_SECTOR",
        {
            "GYN": {"Sector1"},
            "GMR": {"Sector1"},
            "PKR": {"Sector3"},
            "RS": {"Sector2", "Sector3"},   # shared
            "BHI": {"Sector2", "Sector3"},  # shared
        },
    )

    monkeypatch.setattr(
        sectorise,
        "YARD_CODE_LOOKUP",
        {
            "WFW": {"sector": 2},
            "IPSS": {"yards": ["GYN", "PKR"]},  # shared yard
        },
    )


def test_sector_basic_same_station_sector():
    assert sectorise.get_common_sector("GYN", "GMR") == "Sector1"

def test_sector_single_shared():
    result = sectorise.get_common_sector("RS", "PKR")
    assert result == "Sector3"


def test_sector_both_shared():
    result = sectorise.get_common_sector("RS", "BHI")
    assert result is None


def test_sector_yard_simple():
    # BOTH are sector 2
    result = sectorise.get_common_sector("WFW", "IPSS")
    assert result == "Sector2"

def test_sector_shared_yard():
    # should resolve to sec3
    result = sectorise.get_common_sector("IPSS", "PKR")
    assert result == "Sector3"

def test_sector_unknown_codes():
    result = sectorise.get_common_sector("XXX", "YYY")
    assert result is None





