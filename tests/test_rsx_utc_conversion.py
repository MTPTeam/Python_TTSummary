"""
test_convert_RSX_UTC.py
=======================
Pytest suite for convert_RSX_UTC.py
Covers:
   - Time conversion helpers (rsx_time_to_seconds, seconds_to_utc_time, arr_dep_times)
   - Type label assignment
   - Forming link (Prev/Next) construction
   - train_to_utc_lines output structure
   - Freight TXT passthrough filtering
   - Full CSV output (date header, ordering, freight merge, End counts)
"""
import os
import pytest
from taipan.converters.convert_RSX_UTC import (
   rsx_time_to_seconds,
   seconds_to_utc_time,
   arr_dep_times,
   utc_type_label,
   build_forming_links,
   train_to_utc_lines,
   load_freight_from_txt,
   convert_RSX_UTC,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════
class FakeTrain:
   """Minimal stand-in for TrainInfo class - only the fields convert_RSX_UTC uses."""
   def __init__(
       self,
       number,
       daycode,
       weekday,
       run,
       is_empty,
       unit,
       station_ids,
       track_ids,
       departures,
       stop_times,
       odep=None,
   ):
       self.number         = number
       self.daycode        = daycode
       self.weekday        = weekday
       self.run            = run
       self.is_empty_train = is_empty
       self.unit           = unit
       self.station_ids    = station_ids
       self.track_ids      = track_ids
       self.departures     = departures
       self.stop_times     = stop_times
       self.odep           = odep or departures[0]

@pytest.fixture
def simple_train():
   """A basic 3-stop passenger train on Monday."""
   return FakeTrain(
       number="1003", daycode="Mon", weekday="8", run="R01",
       is_empty=False, unit="NGR",
       station_ids=["IPS", "BOV", "BNC"],
       track_ids=["5", "2", "6"],
       departures=["06:00:00", "06:10:00", "06:20:00"],
       stop_times=[0, 60, 120],
   )

@pytest.fixture
def empty_train():
   """An empty-working train."""
   return FakeTrain(
       number="2001", daycode="Mon", weekday="8", run="R02",
       is_empty=True, unit="NGR",
       station_ids=["YD1", "YD2"],
       track_ids=["1", "2"],
       departures=["05:00:00", "05:10:00"],
       stop_times=[0, 0],
   )

@pytest.fixture
def run_of_three():
   """Three trains sharing the same run — used to test Prev/Next linking."""
   def make(number, dep):
       return FakeTrain(
           number=number, daycode="Mon", weekday="8", run="R99",
           is_empty=False, unit="NGR",
           station_ids=["A", "B"], track_ids=["1", "2"],
           departures=[dep, dep], stop_times=[0, 0], odep=dep,
       )
   return [make("1001", "06:00:00"), make("1003", "07:00:00"), make("1005", "08:00:00")]

@pytest.fixture
def freight_txt(tmp_path):
   content = (
       "TTBLD20250831\n"
       "STRT    FRT1   064CITYM\n"
       "    0060000600# 000        #1               ABC1\n"
       "END 1\n"
   )
   (tmp_path / "freight.txt").write_text(content, encoding="utf-8")
   return str(tmp_path)

@pytest.fixture
def fake_trains():
   return [
       FakeTrain("1001", "Mon", "8", "R01", False, "NGR",
                 ["IPS", "BNC"], ["2", "6"],
                 ["06:00:00", "06:20:00"], [0, 120], odep="06:00:00"),
       FakeTrain("1003", "Mon", "8", "R01", False, "NGR",
                 ["BNC", "IPS"], ["6", "2"],
                 ["07:00:00", "07:20:00"], [0, 0], odep="07:00:00"),
       FakeTrain("2001", "Tue", "16", "R02", True, "NGR",
                 ["YD1", "YD2"], ["1", "2"],
                 ["05:00:00", "05:10:00"], [0, 0], odep="05:00:00"),
   ]

@pytest.fixture
def patched_converter(monkeypatch, fake_trains):
   """Patch parse_rsx and UI calls so convert_RSX_UTC runs without real files."""
   import taipan.converters.convert_RSX_UTC as conv
   monkeypatch.setattr(
       conv, "parse_rsx",
       lambda path, **kwargs: (None, fake_trains, None, None, None, [])
   )
   monkeypatch.setattr(conv, "show_info_scroll_safe", lambda title, msg: None)

# ═══════════════════════════════════════════════════════════════════════════════
# rsx_time_to_seconds
# ═══════════════════════════════════════════════════════════════════════════════
def test_time_to_seconds_hhmm():
   assert rsx_time_to_seconds("06:44") == 6 * 3600 + 44 * 60
def test_time_to_seconds_hhmmss():
   assert rsx_time_to_seconds("06:44:30") == 6 * 3600 + 44 * 60 + 30
def test_time_to_seconds_overnight():
   assert rsx_time_to_seconds("25:03:00") == 25 * 3600 + 3 * 60
def test_time_to_seconds_midnight():
   assert rsx_time_to_seconds("00:00:00") == 0

# ═══════════════════════════════════════════════════════════════════════════════
# seconds_to_utc_time
# ═══════════════════════════════════════════════════════════════════════════════
def test_utc_time_on_the_minute():
   assert seconds_to_utc_time(6 * 3600 + 44 * 60) == "0064400"
def test_utc_time_with_30s():
   assert seconds_to_utc_time(6 * 3600 + 44 * 60 + 30) == "0064405"

def test_utc_time_overnight():
   assert seconds_to_utc_time(25 * 3600 + 1 * 60) == "0250100"
def test_utc_time_always_7_chars():
   for secs in [0, 3600, 86399, 90000]:
       assert len(seconds_to_utc_time(secs)) == 7
def test_utc_time_leading_zero():
   assert seconds_to_utc_time(3600)[0] == "0"

# ═══════════════════════════════════════════════════════════════════════════════
# arr_dep_times
# ═══════════════════════════════════════════════════════════════════════════════
def test_arr_dep_no_dwell():
   arr, dep = arr_dep_times("06:44:00", 0)
   assert arr == dep == "0064400"

def test_arr_dep_with_dwell():
   arr, dep = arr_dep_times("06:44:00", 60)
   assert dep == "0064400"
   assert arr == "0064300"
def test_arr_dep_nan_dwell():
   arr, dep = arr_dep_times("07:00:00", float("nan"))
   assert arr == dep
def test_arr_dep_none_dwell():
   arr, dep = arr_dep_times("07:00:00", None)
   assert arr == dep

# ═══════════════════════════════════════════════════════════════════════════════
# utc_type_label
# ═══════════════════════════════════════════════════════════════════════════════
def test_type_label_passenger(simple_train):
   assert utc_type_label(simple_train) == "CITY-REGULAR"
def test_type_label_empty(empty_train):
   assert utc_type_label(empty_train) == "CITY-EMPTY"
def test_type_label_unknown_unit_fallback():
   t = FakeTrain("9999", "Mon", "8", "R", False, "UNKNOWN",
                 ["A"], ["1"], ["06:00"], [0])
   assert utc_type_label(t) == "CITY-REGULAR"

# ═══════════════════════════════════════════════════════════════════════════════
# build_forming_links
# ═══════════════════════════════════════════════════════════════════════════════
def test_forming_links_middle_has_both(run_of_three):
   prev_map, next_map = build_forming_links(run_of_three)
   assert ("1003", "Mon") in prev_map
   assert ("1003", "Mon") in next_map
def test_forming_links_first_no_prev(run_of_three):
   prev_map, _ = build_forming_links(run_of_three)
   assert ("1001", "Mon") not in prev_map
def test_forming_links_last_no_next(run_of_three):
   _, next_map = build_forming_links(run_of_three)
   assert ("1005", "Mon") not in next_map
def test_forming_links_correct_values(run_of_three):
   prev_map, next_map = build_forming_links(run_of_three)
   assert prev_map[("1003", "Mon")] == "1001_Mon"
   assert next_map[("1003", "Mon")] == "1005_Mon"
def test_forming_links_single_train():
   t = FakeTrain("1001", "Mon", "8", "R_solo", False, "NGR",
                 ["A"], ["1"], ["06:00"], [0], odep="06:00")
   prev_map, next_map = build_forming_links([t])
   assert ("1001", "Mon") not in prev_map
   assert ("1001", "Mon") not in next_map

# ═══════════════════════════════════════════════════════════════════════════════
# train_to_utc_lines
# ═══════════════════════════════════════════════════════════════════════════════
def test_lines_header_format(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert lines[0].startswith("Train=1003_Mon,TYPE=CITY-REGULAR,")
def test_lines_header_no_prev_next(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert ",,," in lines[0]
def test_lines_header_with_prev(simple_train):
   lines = list(train_to_utc_lines(simple_train, {("1003", "Mon"): "2608_Mon"}, {}))
   assert "Prev=2608_Mon" in lines[0]
def test_lines_header_with_next(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {("1003", "Mon"): "2103_Mon"}))
   assert "Next=2103_Mon" in lines[0]
def test_lines_count(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert len(lines) == 5  # header + 3 stops + End
def test_lines_stop_format(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert lines[1].startswith("Arr=")
   assert "Dep=" in lines[1]
   assert "Stop=Y" in lines[1]
   assert "Node=IPS5" in lines[1]
def test_lines_empty_train_stop_n(empty_train):
   lines = list(train_to_utc_lines(empty_train, {}, {}))
   assert all("Stop=N" in l for l in lines if l.startswith("Arr="))
def test_lines_end_row(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert lines[-1] == "End 3,,,,Mon"
def test_lines_node_concatenation(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   assert "Node=BNC6" in lines[3]
def test_lines_day_on_every_row(simple_train):
   lines = list(train_to_utc_lines(simple_train, {}, {}))
   for line in lines:
       assert line.endswith("Mon")

# ═══════════════════════════════════════════════════════════════════════════════
# load_freight_from_txt
# ═══════════════════════════════════════════════════════════════════════════════
def test_freight_only_freight_returned(freight_txt):
   lines, count = load_freight_from_txt(freight_txt)
   assert any("Train=" in l for l in lines)
def test_freight_passenger_excluded(freight_txt):
   lines, count = load_freight_from_txt(freight_txt)
   assert not any("CITY-REGULAR" in l for l in lines)  # remove if TRAVM behaviour kept
def test_freight_block_complete(freight_txt):
   lines, count = load_freight_from_txt(freight_txt)
   assert any(l.startswith("Train=") for l in lines)
   assert any(l.startswith("Arr=")   for l in lines)
   assert any(l.startswith("End ")   for l in lines)
def test_freight_empty_folder(tmp_path):
   lines, count = load_freight_from_txt(str(tmp_path))
   assert lines == []
   assert count == 0

def test_freight_coal_keyword(tmp_path):
   (tmp_path / "coal.txt").write_text(
       "TTBLD\nSTRT    C01    064COAL\n    0060000600# 000   #1   X11\nEND 1\n"
   )
   lines, count = load_freight_from_txt(str(tmp_path))
   assert count == 1

# ═══════════════════════════════════════════════════════════════════════════════
# Full CSV output
# ═══════════════════════════════════════════════════════════════════════════════
def test_csv_date_header(tmp_path, patched_converter):
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", date_str="26/05/25", out_path=out)
   assert open(out).readline().strip() == "Date=26/05/25,,,,"
   
def test_csv_all_trains_present(tmp_path, patched_converter):
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", date_str="01/01/25", out_path=out)
   content = open(out).read()
   assert "Train=1001_Mon" in content
   assert "Train=1003_Mon" in content
   assert "Train=2001_Tue" in content

def test_csv_monday_before_tuesday(tmp_path, patched_converter):
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", date_str="01/01/25", out_path=out)
   content = open(out).read()
   assert content.index("Train=1001_Mon") < content.index("Train=2001_Tue")

def test_csv_freight_merged(tmp_path, patched_converter):
   freight_dir = tmp_path / "freight"
   freight_dir.mkdir()
   (freight_dir / "frt.txt").write_text(
       "TTBLD\nSTRT    F001   064CITYM\n    0060000600# 000   #1   ABC1\nEND 1\n"
   )
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", freight_folder=str(freight_dir), date_str="01/01/25", out_path=out)
   content = open(out).read()
   assert "Train=F001_Fri" in content

def test_csv_no_freight_when_not_provided(tmp_path, patched_converter):
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", freight_folder=None, date_str="01/01/25", out_path=out)
   assert "FREIGHT" not in open(out).read()

def test_csv_end_counts_match_stops(tmp_path, patched_converter):
   out = str(tmp_path / "out.csv")
   convert_RSX_UTC("fake.rsx", date_str="01/01/25", out_path=out)
   current_stops = 0
   for line in open(out):
       line = line.strip()
       if line.startswith("Train="):
           current_stops = 0
       elif line.startswith("Arr="):
           current_stops += 1
       elif line.startswith("End "):
           declared = int(line.split(",")[0].split()[1])
           assert declared == current_stops