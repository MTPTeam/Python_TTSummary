import sys
import os
import pytest

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

from xml_parser import TrainInfo
import xml.etree.ElementTree as ET


TRAIN_XML_SNIPPET = """
<train number="2SB6" lineID="PSG-_____S_ ~ 174">
    <header>
        <service>
            <opdaySection weekdayKey="2" holidayKey="0"/>
        </service>
    </header>
    <timetableentries>
        <entry stationID="ETF" departure="24:46:11" trainTypeId="Empty_6-EMU" />
        <entry stationID="EDJ" departure="24:52:11" trainTypeId="Empty_6-EMU" />
        <entry stationID="BHI" departure="24:55:12" trainTypeId="Empty_6-EMU" />
    </timetableentries>
</train>
"""


@pytest.fixture
def train_obj():
    # Convert the snippet into an Element
    element = ET.fromstring(TRAIN_XML_SNIPPET)
    return TrainInfo(element)

def test_basic_attributes(train_obj):
    assert train_obj.number == "2SB6"
    assert train_obj.weekday == "2"
    assert train_obj.run == "174"

def test_stations_and_times(train_obj):
    # Testing that it finds the first and last entry correctly
    assert train_obj.origin['stationID'] == "ETF"
    assert train_obj.destin['stationID'] == "BHI"
    assert train_obj.stations == ["ETF", "EDJ", "BHI"]

def test_train_types(train_obj):
    # Testing normalisation logic
    assert train_obj.unit == "EMU"
    assert train_obj.cars == 6
    #assert train_obj.train_type_revenue == "6-EMU"


if __name__ == "__main__":
    # Disable BOTH dash and hypothesis to be safe from internal errors - both libraries are conflicting with pytest 
    pytest.main([__file__, "-p", "no:dash", "-p", "no:hypothesis"])