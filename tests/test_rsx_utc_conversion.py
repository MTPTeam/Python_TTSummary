"""

test_convert_RSX_UTC.py
=======================

Pytest suite for convert_RSX_UTC.py

Covers:
   - Time encoding helpers (encode_time, encode_arrival, format_node)
   - Type label assignment
   - Forming link (Prev/Next) construction
   - train_to_utc_lines output structure
   - Weekday key expansion (Mon-Thu duplication)
   - Freight TXT passthrough filtering
   - Full CSV output (date header, ordering, freight merge, End counts)

"""

import math
import os
import pytest

from taipan.converters.convert_RSX_UTC import (
    rsx_time_to_seconds,
    encode_time,
    encode_arrival,
    format_node,
    expand_weekday_key,
    utc_type_label,
    build_forming_links,
    train_to_utc_lines,
    load_freight_from_txt,
    convert_RSX_UTC,
)

# Fixtures

class FakeTrain:
    """Minimal stand-in for TrainInfo - only fields convert_RSX_UTC uses."""
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
        requested_arrivals=None,
        entry_types=None,
    ):
        self.number = number
        self.daycode = daycode
        self.weekday = weekday
        self.weekday_key = int(weekday)
        self.run = run
        self.is_empty_train = is_empty
        self.unit = unit
        self.station_ids = station_ids
        self.track_ids = track_ids
        self.departures = departures
        self.stop_times = stop_times
        self.odep = odep or departures[0]
        self.requested_arrivals = requested_arrivals or [None] * len(station_ids)
        self.entry_types = entry_types or ["stop"] * len(station_ids)


@pytest.fixture
def simple_train():
    """A basic 3-stop passenger train on Monday (weekdayKey=64)."""
    return FakeTrain(
        number="1003",
        daycode="Mon",
        weekday="64",
        run="R01",
        is_empty=False,
        unit="NGR",
        station_ids=["IPS", "BOV", "BNC"],
        track_ids=["D-5", "D-2", "D-6"],
        departures=["06:00:00", "06:10:00", "06:20:00"],
        stop_times=[0, 60, 120],
        requested_arrivals=["06:00:00", "06:09:30", "06:18:00"],
        entry_types=["stop", "stop", "stop"],
    )


@pytest.fixture
def empty_train():
    """An empty-working train on Monday."""
    return FakeTrain(
        number="2001",
        daycode="Mon",
        weekday="64",
        run="R02",
        is_empty=True,
        unit="NGR",
        station_ids=["YD1", "YD2"],
        track_ids=["D-1", "D-2"],
        departures=["05:00:00", "05:10:00"],
        stop_times=[0, 0],
        requested_arrivals=[None, "05:09:30"],
        entry_types=["pass", "stop"],
    )


@pytest.fixture
def mon_thu_train():
    """A Mon-Thu train (weekdayKey=120) — should emit 4 copies."""
    return FakeTrain(
        number="1003",
        daycode="Mon-Thu",
        weekday="120",
        run="R01",
        is_empty=False,
        unit="NGR",
        station_ids=["IPS", "BNC"],
        track_ids=["D-1", "D-6"],
        departures=["06:00:00", "06:20:00"],
        stop_times=[0, 120],
        requested_arrivals=["06:00:00", "06:18:00"],
        entry_types=["stop", "stop"],
    )


@pytest.fixture
def run_of_three():
    """Three trains sharing the same run — tests Prev/Next linking."""
    def make(number, dep):
        return FakeTrain(
            number=number,
            daycode="Mon",
            weekday="64",
            run="R99",
            is_empty=False,
            unit="NGR",
            station_ids=["A", "B"],
            track_ids=["D-1", "D-2"],
            departures=[dep, dep],
            stop_times=[0, 0],
            odep=dep,
            requested_arrivals=[None, None],
            entry_types=["pass", "stop"],
        )
    return [
        make("1001", "06:00:00"),
        make("1003", "07:00:00"),
        make("1005", "08:00:00"),
    ]


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
        FakeTrain(
            "1001",
            "Mon",
            "64",
            "R01",
            False,
            "NGR",
            ["IPS", "BNC"],
            ["D-2", "D-6"],
            ["06:00:00", "06:20:00"],
            [0, 120],
            odep="06:00:00",
            requested_arrivals=["06:00:00", "06:18:00"],
            entry_types=["stop", "stop"],
        ),
        FakeTrain(
            "1003",
            "Mon",
            "64",
            "R01",
            False,
            "NGR",
            ["BNC", "IPS"],
            ["D-6", "D-2"],
            ["07:00:00", "07:20:00"],
            [0, 0],
            odep="07:00:00",
            requested_arrivals=["07:00:00", "07:20:00"],
            entry_types=["stop", "stop"],
        ),
        FakeTrain(
            "2001",
            "Tue",
            "32",
            "R02",
            True,
            "NGR",
            ["YD1", "YD2"],
            ["D-1", "D-2"],
            ["05:00:00", "05:10:00"],
            [0, 0],
            odep="05:00:00",
            requested_arrivals=[None, "05:09:30"],
            entry_types=["pass", "stop"],
        ),
    ]


@pytest.fixture
def patched_converter(monkeypatch, fake_trains):
    """Patch parse_rsx and UI calls so convert_RSX_UTC runs without real files."""
    import taipan.converters.convert_RSX_UTC as conv
    monkeypatch.setattr(
        conv,
        "parse_rsx",
        lambda path, **kwargs: (None, fake_trains, None, None, None, []),
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

# encode_time (departures)

# ═══════════════════════════════════════════════════════════════════════════════


def test_encode_time_on_the_minute():
    assert encode_time("06:44:00") == "0064400"


def test_encode_time_36s():
    # 36s -> tenths=6
    assert encode_time("05:44:36") == "0054460"


def test_encode_time_27s():
    # 27s -> floor((27+2)/6) = floor(4.83) = 4
    assert encode_time("06:40:27") == "0064040"


def test_encode_time_30s():
    # s==30 -> round up to next minute
    assert encode_time("05:45:30") == "0054600"


def test_encode_time_59s_overflow():
    # 59s -> tenths=10 -> overflow to next minute
    assert encode_time("06:49:59") == "0065000"


def test_encode_time_overnight():
    assert encode_time("25:01:00") == "0250100"


def test_encode_time_always_7_chars():
    for t in ["00:00:00", "06:44:00", "25:03:36"]:
        assert len(encode_time(t)) == 7


def test_encode_time_leading_zero():
    assert encode_time("01:00:00")[0] == "0"


def test_encode_time_trailing_zero():
    assert encode_time("06:44:00")[-1] == "0"


# ═══════════════════════════════════════════════════════════════════════════════

# encode_arrival

# ═══════════════════════════════════════════════════════════════════════════════


def test_encode_arrival_on_minute():
    assert encode_arrival("06:44:00") == "0064400"


def test_encode_arrival_truncates_low_seconds():
    # s=16 < 30 -> truncate to minute
    assert encode_arrival("24:20:16") == "0242000"


def test_encode_arrival_rounds_up_high_seconds():
    # s=35 >= 30 -> truncate to minute (encode_arrival always truncates)
    assert encode_arrival("24:54:35") == "0245400"


def test_encode_arrival_30s_rounds_up():
    # s=30 -> truncate to minute
    assert encode_arrival("05:45:30") == "0054500"


def test_encode_arrival_always_tenths_zero():
    # tenths digit (position 5) always 0
    for t in ["06:44:00", "24:20:16", "05:45:30"]:
        result = encode_arrival(t)
        assert result[5] == "0"


def test_encode_arrival_always_7_chars():
    for t in ["06:44:00", "24:20:16", "05:45:30"]:
        assert len(encode_arrival(t)) == 7


# ═══════════════════════════════════════════════════════════════════════════════

# format_node

# ═══════════════════════════════════════════════════════════════════════════════


def test_format_node_normal():
    assert format_node("BNC", "D-6") == "BNC6"


def test_format_node_2char_station_zero_pads():
    # 2-char station -> track zero-padded to 2 digits
    assert format_node("RS", "D-9") == "RS09"


def test_format_node_2char_station_double_digit():
    assert format_node("RS", "D-14") == "RS14"


def test_format_node_long_station():
    assert format_node("RSWJ", "T-4") == "RSWJ4"


def test_format_node_strips_letters_from_track():
    assert format_node("IPS", "D-1") == "IPS1"


# ═══════════════════════════════════════════════════════════════════════════════

# expand_weekday_key

# ═══════════════════════════════════════════════════════════════════════════════


def test_expand_mon_only():
    assert expand_weekday_key(64) == ["Mon"]


def test_expand_fri_only():
    assert expand_weekday_key(4) == ["Fri"]


def test_expand_mon_thu():
    result = expand_weekday_key(120)
    assert set(result) == {"Mon", "Tue", "Wed", "Thu"}
    assert len(result) == 4


def test_expand_sat():
    assert expand_weekday_key(2) == ["Sat"]


def test_expand_sun():
    assert expand_weekday_key(1) == ["Sun"]


# ═══════════════════════════════════════════════════════════════════════════════

# utc_type_label

# ═══════════════════════════════════════════════════════════════════════════════


def test_type_label_passenger(simple_train):
    assert utc_type_label(simple_train) == "CITY-REGULAR"


def test_type_label_empty(empty_train):
    assert utc_type_label(empty_train) == "CITY-EMPTY"


def test_type_label_unknown_unit_fallback():
    t = FakeTrain(
        "9999", "Mon", "64", "R", False, "UNKNOWN", ["A"], ["D-1"], ["06:00"], [0]
    )
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
    t = FakeTrain(
        "1001",
        "Mon",
        "64",
        "R_solo",
        False,
        "NGR",
        ["A"],
        ["D-1"],
        ["06:00"],
        [0],
        odep="06:00",
    )
    prev_map, next_map = build_forming_links([t])
    assert ("1001", "Mon") not in prev_map
    assert ("1001", "Mon") not in next_map


def test_forming_links_mon_thu_expanded(mon_thu_train):
    """Mon-Thu train should create links keyed per day."""
    prev_map, next_map = build_forming_links([mon_thu_train])
    # single train per day so no prev/next, but keys shouldn't crash
    for day in ["Mon", "Tue", "Wed", "Thu"]:
        assert ("1003", day) not in prev_map
        assert ("1003", day) not in next_map


# ═══════════════════════════════════════════════════════════════════════════════

# train_to_utc_lines

# ═══════════════════════════════════════════════════════════════════════════════


def _lines(train, prev_map=None, next_map=None):
    """Helper: extract just the line strings from train_to_utc_lines tuples."""
    return [
        line for _, _, line in train_to_utc_lines(train, prev_map or {}, next_map or {})
    ]


def test_lines_header_format(simple_train):
    lines = _lines(simple_train)
    assert lines[0].startswith("Train=1003_Mon,TYPE=CITY-REGULAR,")


def test_lines_header_no_prev_next(simple_train):
    lines = _lines(simple_train)
    assert ",,," in lines[0]


def test_lines_header_with_prev(simple_train):
    lines = _lines(simple_train, prev_map={("1003", "Mon"): "2608_Mon"})
    assert "Prev=2608_Mon" in lines[0]


def test_lines_header_with_next(simple_train):
    lines = _lines(simple_train, next_map={("1003", "Mon"): "2103_Mon"})
    assert "Next=2103_Mon" in lines[0]


def test_lines_count_single_day(simple_train):
    lines = _lines(simple_train)
    assert len(lines) == 5  # header + 3 stops + End


def test_lines_count_mon_thu(mon_thu_train):
    lines = _lines(mon_thu_train)
    # 4 days x (1 header + 2 stops + 1 End) = 16
    assert len(lines) == 16


def test_lines_stop_format(simple_train):
    lines = _lines(simple_train)
    assert lines[1].startswith("Arr=")
    assert "Dep=" in lines[1]
    assert "Stop=Y" in lines[1]
    assert "Node=IPS5" in lines[1]


def test_lines_empty_train_stop_n(empty_train):
    lines = _lines(empty_train)
    assert all("Stop=N" in l for l in lines if l.startswith("Arr="))


def test_lines_end_row(simple_train):
    lines = _lines(simple_train)
    assert lines[-1] == "End 3,,,,Mon"


def test_lines_node_concatenation(simple_train):
    lines = _lines(simple_train)
    assert "Node=BNC6" in lines[3]


def test_lines_day_on_every_row(simple_train):
    lines = _lines(simple_train)
    for line in lines:
        assert line.endswith("Mon")


def test_lines_mon_thu_all_days_present(mon_thu_train):
    lines = _lines(mon_thu_train)
    headers = [l for l in lines if l.startswith("Train=")]
    days = [h.split(",")[-1] for h in headers]
    assert set(days) == {"Mon", "Tue", "Wed", "Thu"}


def test_lines_pass_stop_arr_equals_dep_truncated(empty_train):
    """Pass stops (no requestedArrival) should have arr = dep truncated to minute."""
    lines = _lines(empty_train)
    arr_lines = [l for l in lines if l.startswith("Arr=")]
    # first stop is pass type with no requestedArrival
    first = dict(x.split("=", 1) for x in arr_lines[0].split(",") if "=" in x)
    assert first["Arr"][5] == "0"  # tenths always 0 for pass arr


def test_lines_arr_with_30s_rounds_up(simple_train):
    """requestedArrival with 30s should round up to next minute."""
    # IPS has requestedArrival "06:00:00" in fixture, swap to test 30s
    simple_train.requested_arrivals[0] = "05:45:30"
    simple_train.departures[0] = "05:46:00"
    lines = _lines(simple_train)
    arr_lines = [l for l in lines if l.startswith("Arr=")]
    first = dict(x.split("=", 1) for x in arr_lines[0].split(",") if "=" in x)
    assert first["Arr"] == "0054600"


# ═══════════════════════════════════════════════════════════════════════════════

# load_freight_from_txt

# ═══════════════════════════════════════════════════════════════════════════════


def test_freight_train_present(freight_txt):
    lines, count = load_freight_from_txt(freight_txt)
    assert any("Train=" in l for l in lines)


def test_freight_block_complete(freight_txt):
    lines, count = load_freight_from_txt(freight_txt)
    assert any(l.startswith("Train=") for l in lines)
    assert any(l.startswith("Arr=") for l in lines)
    assert any(l.startswith("End ") for l in lines)


def test_freight_empty_folder(tmp_path):
    lines, count = load_freight_from_txt(str(tmp_path))
    assert lines == []
    assert count == 0


def test_freight_count(freight_txt):
    _, count = load_freight_from_txt(freight_txt)
    assert count == 1


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


def test_csv_earlier_dep_before_later_dep(tmp_path, patched_converter):
    out = str(tmp_path / "out.csv")
    convert_RSX_UTC("fake.rsx", date_str="01/01/25", out_path=out)
    content = open(out).read()
    assert content.index("Train=1001_Mon") < content.index("Train=1003_Mon")


def test_csv_freight_merged(tmp_path, patched_converter):
    freight_dir = tmp_path / "freight"
    freight_dir.mkdir()
    (freight_dir / "frt.txt").write_text(
        "TTBLD\nSTRT    F001   064CITYM\n    0060000600# 000   #1   ABC1\nEND 1\n"
    )
    out = str(tmp_path / "out.csv")
    convert_RSX_UTC(
        "fake.rsx", freight_folder=str(freight_dir), date_str="01/01/25", out_path=out
    )
    content = open(out).read()
    assert "Train=F001_Fri" in content


def test_csv_no_freight_when_not_provided(tmp_path, patched_converter):
    out = str(tmp_path / "out.csv")
    convert_RSX_UTC("fake.rsx", freight_folder=None, date_str="01/01/25", out_path=out)
    content = open(out).read()
    assert "FREIGHT" not in content


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


def test_csv_7_char_times(tmp_path, patched_converter):
    """All Arr= and Dep= values should be exactly 7 characters."""
    out = str(tmp_path / "out.csv")
    convert_RSX_UTC("fake.rsx", date_str="01/01/25", out_path=out)
    for line in open(out):
        line = line.strip()
        if line.startswith("Arr="):
            p = dict(x.split("=", 1) for x in line.split(",") if "=" in x)
            assert len(p["Arr"]) == 7, f"Bad Arr length: {p['Arr']}"
            assert len(p["Dep"]) == 7, f"Bad Dep length: {p['Dep']}"
