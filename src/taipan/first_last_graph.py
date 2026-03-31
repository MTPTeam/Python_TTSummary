
import win32com.client as win32
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import re, sys, os
from taipan.constants.locations import STATIONS_MASTER
import pandas
from taipan.constants.days import WEEKDAY_KEYS_MASTER, ID_TO_SHORT
from taipan.constants.styles import SLICER_CONFIGS, CHART_H, CHART_LEFT, CHART_W

# ── CONFIG — edit these ───────────────────────────────────────────────────────

RSX_FILES = [r"C:/Users/r919150/Downloads/RSX files/3STT MRTP Refresh v1.3.rsx",r"C:/Users/r919150/Downloads/RSX files/Soft Open MRTP Refresh v2.3.rsx"]
OUTPUT_PATH = os.path.abspath(os.path.join(os.path.expanduser("~"), "rsx_scatter.xlsx"))
COLORS = [0xC44244, 0x47AD70, 0x31D7ED, 0xF5A623]  # add more if needed

# Revenue and non revenue maps based on master
rev_map = {
    code: info['name']
    for code, info in STATIONS_MASTER['stations'].items()
    if not info.get('non_revenue', False)
}

nonrev_map = {
    code
    for code, info in STATIONS_MASTER['stations'].items()
    if info.get('non_revenue', False)
}


CORE = {"RS", "RTL"}
City = ['RS','BNC','BRC','BHI','EXH','ALB','RTL','WLG','BOG']



def parseTimeDelta(s):
    if str(s) == 'nan':
        return np.nan
    d = re.match(
        r'((?P<days>\d+) days, )?(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)',
        str(s)).groupdict(0)
    from datetime import timedelta
    return timedelta(**{k: int(v) for k, v in d.items()})

def minutes_to_time_format(chart_obj):
    """Format X axis as HH:MM by using a custom number format on the axis."""
    ax = chart_obj.Axes(1)
    ax.TickLabels.NumberFormat = '[h]:mm'
    ax.MajorUnit = 60    # tick every 60 minutes
    ax.MinimumScale = 0
    ax.MaximumScale = 24 * 60


def timedeltatohhmmss(s):
    s = str(s)
    if s == 'NaT' or s == '': return ''
    
    # Example: "1 days 00:07:35.000000" -> split into ["1", "days", "00:07:35.000000"]
    parts = s.split()
    
    if len(parts) == 3:  # Case: "1 days 02:30:00"
        days = int(parts[0])
        timestamp = parts[2].split('.')[0] # Get "02:30:00", ignore decimals
        h, m, s = map(int, timestamp.split(':'))
        total_hours = (days * 24) + h
        return f"{total_hours:02}:{m:02}:{s:02}"
        
    elif len(parts) == 1: # Case: "02:30:00" (no days mentioned)
        return parts[0].split('.')[0]
        
    return s # Fallback


def hhmm_to_excel_time(hhmm):
   if not hhmm or pd.isna(hhmm): return np.nan
   try:
       parts = str(hhmm).split(':')
       minutes = int(parts[0]) * 60 + int(parts[1])
       return minutes / 1440.0   # back to fraction
   except:
       return np.nan


def td_to_hhmm(td):
    if pd.isna(td): return None
    total_minutes = int(td.total_seconds() // 60)
    hh, mm = divmod(total_minutes, 60)
    return f"{hh:02d}:{mm:02d}"

# ── RSX PARSER ────────────────────────────────────────────────────────────────

def rsx_to_first_last(rsx_path):
    tree = ET.parse(rsx_path)
    root = tree.getroot()

    train_nums, daycodes, blocks, train_types = [], [], [], []
    stationsinTrains, trackIDinTrains, departureinTrains, stopTimesinTrains = [], [], [], []

    for train in root.findall('./timetable/train'):
        train_num = train.attrib['number']
        block     = train.attrib.get('lineID', '')
        entryelems = [e for e in train.iter() if e.tag == 'entry']

        stationsinTrain    = [e.attrib['stationID']   for e in entryelems]
        trackIDinTrain     = [e.attrib['trackID']      for e in entryelems]
        departureinTrain   = [e.attrib['departure']    for e in entryelems]
        stopTimesinTrain   = [int(e.attrib['stopTime']) if 'stopTime' in e.attrib else np.nan for e in entryelems]

        train_type  = list(set([e.attrib['trainTypeId'] for e in train.iter() if 'trainTypeId' in e.attrib]))
        weekdayKey  = list(set([e.attrib['weekdayKey']  for e in train.iter() if 'weekdayKey'  in e.attrib]))

        if len(weekdayKey) > 1:
            sys.exit(f"{train_num} - Has 2 daycodes - Please fix")
        daycode = ID_TO_SHORT[weekdayKey[0]]

        if len(train_type) > 1:
            sys.exit(f"{train_num} - {daycode} - Has 2 traintypes - Please fix")

        n = len(departureinTrain)
        train_nums        += [train_num]  * n
        daycodes          += [daycode]    * n
        blocks            += [block]      * n
        train_types       += [train_type[0]] * n
        stationsinTrains  += stationsinTrain
        trackIDinTrains   += trackIDinTrain
        departureinTrains += departureinTrain
        stopTimesinTrains += stopTimesinTrain

    df = pd.DataFrame({
        'Train': train_nums, 'Day': daycodes, 'Block': blocks,
        'TrainType': train_types, 'Station': stationsinTrains,
        'TrackID': trackIDinTrains, 'Arrive': np.nan,
        'Depart': departureinTrains, 'Dwell': stopTimesinTrains,
    })

    df['ArriveTimedelta'] = df.Depart.apply(parseTimeDelta) - pd.to_timedelta(df.Dwell, unit='s')
    df['Arrive'] = df.ArriveTimedelta.astype(str).apply(timedeltatohhmmss)
    df['Arrive'] = [x if x != '' else np.nan for x in df.Arrive]
    df = df[['Train','Day','Block','TrainType','Station','TrackID','Arrive','Depart','Dwell']]
    df = df[~df.TrainType.str.contains('Empty')]
    if nonrev_map:
        df = df[~df.Station.isin(nonrev_map)]
    df = df[df["Dwell"].notna()]
    df.insert(5, 'StationName', df["Station"].map(rev_map) if rev_map else df["Station"])

    df = df.copy()
    df["_seq"] = df.groupby(["Train","Day"]).cumcount()

    is_core = df["Station"].isin(CORE)
    first_core_seq = df[is_core].groupby(["Train","Day"])["_seq"].min()
    df["core_seq"] = df.set_index(["Train","Day"]).index.map(first_core_seq)

    df["Direction"] = np.where(
        df["core_seq"].isna(), "Unknown",
        np.where(df["_seq"] < df["core_seq"], "Inbound", "Outbound")
    )
    df["Direction"] = np.where(df["Station"].isin(City), "City", df["Direction"])
    df.drop(columns=["_seq","core_seq"], inplace=True)
    df = df[df.Direction != 'City']

    df["Depart_td"] = pd.to_timedelta(df["Depart"], errors="coerce")

    aa = (
        df.groupby(["Day","Station","StationName","Direction"])["Depart_td"]
        .agg(First="min", Last="max")
        .reset_index()
    )

    aa["First"]     = aa["First"].apply(td_to_hhmm)
    aa["Last"]      = aa["Last"].apply(td_to_hhmm)
    aa["Timetable"] = os.path.splitext(os.path.basename(rsx_path))[0]
    return aa

# ── LOAD & COMBINE RSX FILES ──────────────────────────────────────────────────

frames = [rsx_to_first_last(p) for p in RSX_FILES]
aa = pd.concat(frames, ignore_index=True)

if len(aa[aa.Direction == 'Unknown']) > 0:
    print(aa[aa.Direction == 'Unknown'])
    
    #sys.exit('Unknown Train Directions — fix before continuing')

# Add numeric time columns for scatter (minutes since midnight)

aa["First_t"] = aa["First"].apply(hhmm_to_excel_time)
aa["Last_t"]  = aa["Last"].apply(hhmm_to_excel_time)

# Y value: just a row index — spreads dots vertically so they don't overlap

aa = aa.reset_index(drop=True)
aa["Y"] = aa["Direction"].map({"Inbound": 1, "Outbound": 2})


# Final column order for the Excel table
cols = ["Timetable","Day","Station","StationName","Direction","First","First_t","Last","Last_t","Y"]

aa = aa[cols]

last_min = aa["Last_t"].min()
last_max = aa["Last_t"].max()
LAST_AXIS_MIN = max(0, (last_min - 1/24))  # 1 hour before earliest, floored at 0
LAST_AXIS_MAX = last_max + 1/24             # 1 hour after latest


timetable_names = [os.path.splitext(os.path.basename(p))[0] for p in RSX_FILES]
counts = aa.groupby(["Station", "Day"])["Timetable"].nunique()
common = counts[counts == len(timetable_names)]
if len(common) == 0:
   print(" No station+day combo exists in all timetables, using first available")
   DEFAULT_STATION = aa["Station"].iloc[0]
   DEFAULT_DAY     = aa["Day"].iloc[0]
else:
   DEFAULT_STATION, DEFAULT_DAY = common.index[0]
   DEFAULT_STATION_NAME = rev_map.get(DEFAULT_STATION, DEFAULT_STATION)

print(f"Default filter: {DEFAULT_STATION} / {DEFAULT_DAY}")

print(f"Data ready: {len(aa)} rows")

# ── EXCEL CONSTANTS ───────────────────────────────────────────────────────────

xlSrcRange             = 1
xlCenter               = -4108
xlLegendPositionBottom = -4107
xlRowField             = 1
xlPageField            = 3
xlAverage              = -4106
xlXYScatter            = 74
xlOpenXMLWorkbook      = 51
xlSheetVeryHidden      = 2
xlMax = -4136


# ── LAUNCH EXCEL ──────────────────────────────────────────────────────────────

excel = win32.Dispatch("Excel.Application")
excel.Visible       = False
excel.DisplayAlerts = False

try:
    wb = excel.Workbooks.Add()

    # ── 1. DATA SHEET ─────────────────────────────────────────────────────────
    ws_data = wb.Worksheets(1)
    ws_data.Name = "Data"

     
    headers = list(aa.columns)
    nrows   = len(aa) + 1
    end_col = chr(64 + len(headers))  

    for c, h in enumerate(headers, 1):
        ws_data.Cells(1, c).Value = h

    
    data_with_header = [headers] + [[None if (isinstance(v, float) and np.isnan(v)) else v for v in row] for row in aa.itertuples(index=False)]
    ws_data.Range(f"A1:{end_col}{nrows}").Value = data_with_header
    nrows = len(aa) + 1  # +1 for header

    # Style header
    hdr = ws_data.Range(f"A1:{chr(64+len(headers))}1")
    hdr.Font.Bold           = True
    hdr.Font.Color          = 0xFFFFFF
    hdr.Interior.Color      = 0x57402E
    hdr.HorizontalAlignment = xlCenter

    for i, col in enumerate(headers, 1):
        ws_data.Columns(i).ColumnWidth = 16

    ws_data.Range("A2").Select()
    excel.ActiveWindow.FreezePanes = True

    # Excel Table
    tbl = ws_data.ListObjects.Add(
        SourceType=xlSrcRange,
        Source=ws_data.Range(f"A1:{chr(64+len(headers))}{nrows}"),
        XlListObjectHasHeaders=1
    )
    tbl.Name       = "RsxData"
    tbl.TableStyle = "TableStyleMedium9"

    # ── 2. PIVOT SHEET (hidden) ───────────────────────────────────────────────
    # One pivot with Station, Day, Timetable, Direction as page/row fields
    # Values: Avg of First_min, Avg of Last_min, Avg of Y
    ws_pivot = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
    ws_pivot.Name = "PivotData"

    pc = wb.PivotCaches().Create(SourceType=1, SourceData="RsxData")
    pt = pc.CreatePivotTable(
        TableDestination=ws_pivot.Range("A1"),
        TableName="RsxPivot"
    )

    # Slicer fields as page fields (hidden filters, slicers will control these)
    for field in ["StationName", "Day"]:
        pt.PivotFields(field).Orientation = xlPageField

    # Row fields
    pt.PivotFields("Timetable").Orientation = xlRowField
    pt.PivotFields("Timetable").Position    = 1
    pt.PivotFields("Direction").Orientation = xlRowField
    pt.PivotFields("Direction").Position    = 2

    # Value fields
    pf_first = pt.AddDataField(pt.PivotFields("First_t"), "First Time", xlMax)
    #pf_first.NumberFormat = "0.0"
    pf_last  = pt.AddDataField(pt.PivotFields("Last_t"),  "Last Time",  xlMax)
    #pf_last.NumberFormat  = "0.0"
    pf_y     = pt.AddDataField(pt.PivotFields("Y"),       "Y Val",      xlMax)
    #pf_y.NumberFormat     = "0.0"

    pt.RowAxisLayout(1)   # tabular
    pt.ColumnGrand = False
    pt.RowGrand    = False

    pt.PivotFields("Direction").PivotItems("Unknown").Visible = False
    pt.RowGrand = False  # already there
    # Hide subtotals on Timetable field
    pt.PivotFields("Timetable").Subtotals = (False,False,False,False,False,False,False,False,False,False,False,False)


    for i in range(1, 14):
        print(f"Row {i}: A={ws_pivot.Range(f'A{i}').Value} B={ws_pivot.Range(f'B{i}').Value} C={ws_pivot.Range(f'C{i}').Value} D={ws_pivot.Range(f'D{i}').Value}")

    ws_pivot.Columns("B").NumberFormat = "h:mm"
    ws_pivot.Columns("C").NumberFormat = "h:mm"
    excel.Calculate()

    ws_pivot.Visible = 1  # temporarily visible
    excel.Calculate()
    print("Pivot A2:", ws_pivot.Range("A2").Value)
    print("Pivot A3:", ws_pivot.Range("A3").Value)
    print("Pivot B2:", ws_pivot.Range("B2").Value)
    print("Pivot B3:", ws_pivot.Range("B3").Value)
    print("Pivot D2:", ws_pivot.Range("D2").Value)
    print("Pivot D3:", ws_pivot.Range("D3").Value)
    ws_pivot.Visible = xlSheetVeryHidden

    # ── 3. CHART SHEET ────────────────────────────────────────────────────────
    ws_chart = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
    ws_chart.Name = "Charts"

    co    = ws_chart.ChartObjects().Add(Left=CHART_LEFT, Top=10, Width=CHART_W*2+20, Height=CHART_H)
    chart = co.Chart
    chart.ChartType = xlXYScatter
    timetable_names = [os.path.splitext(os.path.basename(p))[0] for p in RSX_FILES]
    data_start = 5
    for t_idx, name in enumerate(timetable_names):
        inbound_row  = data_start + t_idx * 2
        outbound_row = data_start + t_idx * 2 + 1
        # Last departure first
        s2 = chart.SeriesCollection().NewSeries()
        s2.Name    = f"={ws_pivot.Name}!$A${inbound_row}"
        s2.XValues = ws_pivot.Range(f"D{inbound_row}:D{outbound_row}")
        s2.Values  = ws_pivot.Range(f"E{inbound_row}:E{outbound_row}")
        s2.MarkerStyle           = 8
        s2.MarkerSize            = 10
        s2.MarkerForegroundColor = COLORS[t_idx % len(COLORS)]
        s2.MarkerBackgroundColor = COLORS[t_idx % len(COLORS)]
        s2.Format.Line.Visible   = False
        # First departure second
        s = chart.SeriesCollection().NewSeries()
        s.Name    = f"={ws_pivot.Name}!$A${inbound_row}"
        s.XValues = ws_pivot.Range(f"C{inbound_row}:C{outbound_row}")
        s.Values  = ws_pivot.Range(f"E{inbound_row}:E{outbound_row}")
        s.MarkerStyle           = 8
        s.MarkerSize            = 10
        s.MarkerForegroundColor = COLORS[t_idx % len(COLORS)]
        s.MarkerBackgroundColor = COLORS[t_idx % len(COLORS)]
        s.Format.Line.Visible   = False

    # Hide First series from legend (odd indices: 2, 4, ...)
    for t_idx in range(len(timetable_names)):
        chart.SeriesCollection(t_idx * 2 + 2).Name = '=""'
    chart.HasTitle  = False
    chart.Axes(1).HasTitle       = True
    chart.Axes(1).AxisTitle.Text = "Time of Day"
    chart.Axes(2).HasTitle       = True
    chart.Axes(2).AxisTitle.Text = "1=Inbound  2=Outbound"
    chart.HasLegend              = True
    chart.Legend.Position        = xlLegendPositionBottom
    chart.Legend.Font.Size = 12
    ax = chart.Axes(1)
    ax.MinimumScale = 0.0
    ax.MaximumScale = 27/24
    ax.MajorUnit    = 2/24
    ax.TickLabels.NumberFormat = "h:mm"
    ax.AxisTitle.Font.Size = 12  # <--- Change Axis Title Size

    ax.TickLabels.Font.Size = 11 # <--- Change Label/Ticks Size
    ay = chart.Axes(2)
    ay.MinimumScale = 0
    ay.MaximumScale = 3
    ay.MajorUnit    = 1
    ay.HasTitle     = False
    #ay.AxisTitle.Font.Size = 12  

    ay.TickLabels.Font.Size = 11 
    chart_total_w = CHART_W * 2 + 20
    quarter       = CHART_LEFT + chart_total_w * 0.25
    three_quarter = CHART_LEFT + chart_total_w * 0.75
    tb1 = ws_chart.Shapes.AddTextbox(1, quarter - 50, 15, 120, 20)
    tb1.TextFrame.Characters().Text        = "Last Departure"
    tb1.TextFrame.Characters().Font.Size   = 14
    tb1.TextFrame.Characters().Font.Italic = True
    tb1.TextFrame.Characters().Font.Bold   = True
    tb1.Line.Visible = False
    tb2 = ws_chart.Shapes.AddTextbox(1, three_quarter - 50, 15, 120, 20)
    tb2.TextFrame.Characters().Text        = "First Departure"
    tb2.TextFrame.Characters().Font.Size   = 14
    tb2.TextFrame.Characters().Font.Italic = True
    tb2.TextFrame.Characters().Font.Bold   = True
    tb2.Line.Visible = False


    

    # ── 4. SLICERS (Station, Day, Timetable) ─────────────────────────────────
    for field, caption, top, left, width, height in SLICER_CONFIGS:
        sc      = wb.SlicerCaches.Add2(pt, field)
        sc.Name = f"SlicerCache_{field}"
        sl = sc.Slicers.Add(
            SlicerDestination=ws_chart,
            Name=f"Slicer_{field}",
            Caption=caption,
            Top=top,
            Left=left,
            Width=width,
            Height=height,
        )
        sl.Style = "SlicerStyleLight2"
        
        print(f"{field}: Top={sl.Top}, Left={sl.Left}, Width={sl.Width}, Height={sl.Height}")
        sl.Top = top
        sl.Left = left
        sl.Width = width
        sl.Height = height

    # ── 5. SAVE ───────────────────────────────────────────────────────────────
    sc_station = wb.SlicerCaches("SlicerCache_StationName")
    for item in sc_station.SlicerItems:
        item.Selected = (item.Name == DEFAULT_STATION_NAME)
    sc_day = wb.SlicerCaches("SlicerCache_Day")
    for item in sc_day.SlicerItems:
        item.Selected = (item.Name == DEFAULT_DAY)
    excel.Calculate()
    ws_data.Activate()
    wb.SaveAs(OUTPUT_PATH, FileFormat=xlOpenXMLWorkbook)
    print(f"Saved to: {OUTPUT_PATH}")
    print("    Open the 'Charts' sheet — use the slicers on the left to filter.")
        

finally:
    wb.Close(SaveChanges=False)
    excel.Quit()




