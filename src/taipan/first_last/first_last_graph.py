import win32com.client as win32
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import re, sys, os
from taipan.constants.locations import STATIONS_MASTER
from taipan.constants.days import WEEKDAY_KEYS_MASTER, ID_TO_SHORT
from taipan.constants.styles import SLICER_CONFIGS, CHART_H, CHART_LEFT, CHART_W, xlSrcRange, xlCenter, xlLegendPositionBottom, xlRowField, xlPageField, xlAverage, xlXYScatter, xlOpenXMLWorkbook, xlSheetVeryHidden, xlMax
from taipan.gui.base import select_multi_rsx_files, show_error, show_info
from taipan.core.utils import _time_key, timetrim, parseTimeDelta, minutes_to_time_format, timedeltatohhmmss, hhmm_to_excel_time, td_to_hhmm, generate_colors
from PyQt6.QtWidgets import QApplication
from taipan.core.xml_parser import TrainInfo, load_rsx, extract_trains


OUTPUT_PATH = os.path.abspath(os.path.join(os.path.expanduser("~"), "FirstLastGraph.xlsx"))
CORE = {"RS", "RTL"}
CITY = {'RS','BNC','BRC','BHI','EXH','ALB','RTL','WLG','BOG'}

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

def trains_to_df(rsx_path: str) -> pd.DataFrame:
   root, _ = load_rsx(rsx_path)
   trains = extract_trains(root)
   rows = []

   for t in trains:
       if t.is_empty_train:
           continue
       for i, e in enumerate(t.entries):
           rows.append({
               'Train':     t.number,
               'Day':       ID_TO_SHORT[t.weekday],
               'Block':     t.lineID,
               'TrainType': t.train_type,
               'Station':   t.station_ids[i],
               'TrackID':   t.track_ids[i],
               'Arrive':    np.nan,
               'Depart':    e.attrib['departure'],
               'Dwell':     int(e.attrib['stopTime']) if 'stopTime' in e.attrib else np.nan,
           })

   df = pd.DataFrame(rows)
   df['ArriveTimedelta'] = df.Depart.apply(parseTimeDelta) - pd.to_timedelta(df.Dwell, unit='s')
   df['Arrive'] = df.ArriveTimedelta.astype(str).apply(timedeltatohhmmss)
   df['Arrive'] = [x if x != '' else np.nan for x in df.Arrive]
   df = df[['Train','Day','Block','TrainType','Station','TrackID','Arrive','Depart','Dwell']]
   if nonrev_map:
       df = df[~df.Station.isin(nonrev_map)]
   df = df[df["Dwell"].notna()]
   df.insert(5, 'StationName', df["Station"].map(rev_map) if rev_map else df["Station"])
   return df

def assign_directions(df: pd.DataFrame) -> pd.DataFrame:
   df = df.copy()
   df["_seq"] = df.groupby(["Train","Day"]).cumcount()
   is_core = df["Station"].isin(CORE)
   first_core_seq = df[is_core].groupby(["Train","Day"])["_seq"].min()
   df["core_seq"] = df.set_index(["Train","Day"]).index.map(first_core_seq)
   df["Direction"] = np.where(
       df["core_seq"].isna(), "Unknown",
       np.where(df["_seq"] < df["core_seq"], "Inbound", "Outbound")
   )
   df["Direction"] = np.where(df["Station"].isin(CITY), "City", df["Direction"])
   df.drop(columns=["_seq","core_seq"], inplace=True)
   df = df[df.Direction != 'City']
   return df

def aggregate_first_last(df: pd.DataFrame, rsx_path: str) -> pd.DataFrame:
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

def rsx_to_first_last(rsx_path: str) -> pd.DataFrame:
   df = trains_to_df(rsx_path)
   df = assign_directions(df)
   return aggregate_first_last(df, rsx_path)

def build_combined_df(rsx_files: list[str], colors: list) -> tuple[pd.DataFrame, str, str]:
   frames = [rsx_to_first_last(p) for p in rsx_files]
   aa = pd.concat(frames, ignore_index=True)
   unknowns = aa[aa.Direction == 'Unknown']
   if len(unknowns) > 0:
       print(unknowns)
   aa["First_t"] = aa["First"].apply(hhmm_to_excel_time) + 1
   aa["Last_t"]  = aa["Last"].apply(hhmm_to_excel_time)
   aa = aa.reset_index(drop=True)
   aa["Y"] = aa["Direction"].map({"Inbound": 2, "Outbound": 1})
   cols = ["Timetable","Day","Station","StationName","Direction","First","First_t","Last","Last_t","Y"]
   aa = aa[cols]
   timetable_names = sorted([os.path.splitext(os.path.basename(p))[0] for p in rsx_files])
   counts = aa.groupby(["Station","Day"])["Timetable"].nunique()
   common = counts[counts == len(timetable_names)]
   if len(common) == 0:
       default_station = aa["Station"].iloc[0]
       default_day     = aa["Day"].iloc[0]
   else:
       default_station, default_day = common.index[0]
   default_station_name = rev_map.get(default_station, default_station)
   return aa, default_station_name, default_day

# excel
def build_data_sheet(wb, aa: pd.DataFrame):
   ws = wb.Worksheets(1)
   ws.Name = "Data"
   headers = list(aa.columns)
   nrows   = len(aa) + 1
   end_col = chr(64 + len(headers))
   first_col = headers.index("First") + 1
   last_col  = headers.index("Last") + 1
   ws.Columns(first_col).NumberFormat = "@"
   ws.Columns(last_col).NumberFormat  = "@"
   data_with_header = [headers] + [[None if (isinstance(v, float) and np.isnan(v)) else v for v in row] for row in aa.itertuples(index=False)]
   ws.Range(f"A1:{end_col}{nrows}").Value = data_with_header
   hdr = ws.Range(f"A1:{end_col}1")
   hdr.Font.Bold           = True
   hdr.Font.Color          = 0xFFFFFF
   hdr.Interior.Color      = 0x57402E
   hdr.HorizontalAlignment = xlCenter

   for i in range(1, len(headers) + 1):
       ws.Columns(i).ColumnWidth = 16

   ws.Range("A2").Select()
   wb.Application.ActiveWindow.FreezePanes = True
   tbl = ws.ListObjects.Add(
       SourceType=xlSrcRange,
       Source=ws.Range(f"A1:{end_col}{nrows}"),
       XlListObjectHasHeaders=1
   )
   tbl.Name       = "RsxData"
   tbl.TableStyle = "TableStyleMedium9"
   return ws, tbl

def build_pivot_sheet(wb, timetable_names: list[str]):
   ws = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
   ws.Name = "PivotData"
   pc = wb.PivotCaches().Create(SourceType=1, SourceData="RsxData")
   pt = pc.CreatePivotTable(TableDestination=ws.Range("A1"), TableName="RsxPivot")

   for field in ["StationName", "Day"]:
       pt.PivotFields(field).Orientation = xlPageField

   pt.PivotFields("Timetable").Orientation = xlRowField
   pt.PivotFields("Timetable").Position    = 1
   pt.PivotFields("Direction").Orientation = xlRowField
   pt.PivotFields("Direction").Position    = 2
   pt.AddDataField(pt.PivotFields("First_t"), "First Time", xlMax)
   pt.AddDataField(pt.PivotFields("Last_t"),  "Last Time",  xlMax)
   pt.AddDataField(pt.PivotFields("Y"),       "Y Val",      xlMax)
   pt.RowAxisLayout(1)
   pt.ColumnGrand = False
   pt.RowGrand    = False
   pt.PivotFields("Direction").PivotItems("Unknown").Visible = False
   pt.PivotFields("Timetable").Subtotals = (False,) * 12
   ws.Columns("B").NumberFormat = "h:mm"
   ws.Columns("C").NumberFormat = "h:mm"
   ws.Visible = xlSheetVeryHidden
   return ws, pc, pt

def build_chart(wb, ws_pivot, ws_chart, timetable_names: list[str], colors: list):
   co    = ws_chart.ChartObjects().Add(Left=CHART_LEFT, Top=10, Width=CHART_W*2+20, Height=CHART_H)
   chart = co.Chart
   chart.ChartType = xlXYScatter
   data_start = 5  # pivot data always starts row 5 (header + 3 filter rows + 1 blank)

   for t_idx, name in enumerate(timetable_names):
       inbound_row  = data_start + t_idx * 2
       outbound_row = data_start + t_idx * 2 + 1
       for series_col in ["D", "C"]:
           s = chart.SeriesCollection().NewSeries()
           s.Name    = f"={ws_pivot.Name}!$A${inbound_row}"
           s.XValues = ws_pivot.Range(f"{series_col}{inbound_row}:{series_col}{outbound_row}")
           s.Values  = ws_pivot.Range(f"E{inbound_row}:E{outbound_row}")

   for t_idx in range(len(timetable_names)):
       for s_offset in range(2):
           s = chart.SeriesCollection(t_idx * 2 + s_offset + 1)
           s.MarkerStyle = 8
           s.MarkerSize  = 14
           s.Format.Fill.Solid()
           s.Format.Fill.Visible       = True
           s.Format.Fill.BackColor.RGB = colors[t_idx % len(colors)]
           s.Format.Fill.ForeColor.RGB = colors[t_idx % len(colors)]
           s.Format.Fill.Transparency  = 0.6
           s.Format.Line.Visible       = False

   for i in range(chart.Legend.LegendEntries().Count, 0, -1):
       if i % 2 == 0:
           chart.Legend.LegendEntries(i).Delete()

   chart.HasTitle               = False
   chart.Axes(1).HasTitle       = True
   chart.Axes(1).AxisTitle.Text = "Time of Day"
   chart.Axes(2).HasTitle       = True
   chart.Axes(2).AxisTitle.Text = "1=Inbound  2=Outbound"
   chart.HasLegend              = True
   chart.Legend.Position        = xlLegendPositionBottom
   chart.Legend.Font.Size       = 12
   ax = chart.Axes(1)
   ax.MinimumScale            = 18/24 # change x axis start time here (currently 18:00)
   ax.MaximumScale            = 1 + 6/24 # change x axis end time here (currently 06:00)
   ax.MajorUnit               = 2/24
   ax.MinorUnit               = 1/24
   ax.TickLabels.NumberFormat = "h:mm"
   ax.AxisTitle.Font.Size     = 12
   ax.TickLabels.Font.Size    = 11
   ay = chart.Axes(2)
   ay.MinimumScale            = 0
   ay.MaximumScale            = 3
   ay.MajorUnit               = 1
   ay.HasTitle                = False
   ay.TickLabels.NumberFormat = '""' # set to empty because scatter doesn't allow non numerical y axis programatically  
   ay.TickLabels.Font.Size    = 11
   return co, chart, ay

def add_chart_labels(ws_chart, co, chart, ay):
   wb = ws_chart.Parent
   wb.Application.Calculate()
   pa          = chart.PlotArea
   plot_top    = pa.Top
   plot_height = pa.Height
   y_unit      = plot_height / (ay.MaximumScale - ay.MinimumScale)
   y_at_2      = co.Top + plot_top + plot_height - (2 - ay.MinimumScale) * y_unit - 10
   y_at_1      = co.Top + plot_top + plot_height - (1 - ay.MinimumScale) * y_unit - 10 - 8

   for label, ypos in [("Inbound", y_at_2), ("Outbound", y_at_1)]:
       tb = ws_chart.Shapes.AddTextbox(1, co.Left - 65, ypos, 63, 20)
       tb.TextFrame.Characters().Text            = label
       tb.TextFrame.Characters().Font.Size       = 11
       tb.TextFrame.HorizontalAlignment          = xlCenter
       tb.Line.Visible                           = False

   chart_total_w = CHART_W * 2 + 20
   tb1 = ws_chart.Shapes.AddTextbox(1, CHART_LEFT + chart_total_w * 0.5 - 60, 15, 160, 20)
   tb1.TextFrame.Characters().Text      = "Last & First Departure"
   tb1.TextFrame.Characters().Font.Size = 16
   tb1.TextFrame.Characters().Font.Bold = True
   tb1.Line.Visible                     = False

def build_summary_table(wb, ws_chart, pc):
   table_row = 28
   pt2 = pc.CreatePivotTable(TableDestination=ws_chart.Range(f"Z{table_row}"),TableName="RsxPivotTable")
   pt2.PivotFields("Timetable").Orientation = xlRowField
   pt2.PivotFields("Timetable").Position    = 1
   pt2.PivotFields("Direction").Orientation = xlRowField
   pt2.PivotFields("Direction").Position    = 2
   pt2.AddDataField(pt2.PivotFields("First_t"), "First Departure", xlMax)
   pt2.AddDataField(pt2.PivotFields("Last_t"),  "Last Departure",  xlMax)
   pt2.RowAxisLayout(1)
   pt2.ColumnGrand = False
   pt2.RowGrand    = False
   pt2.PivotFields("Timetable").Subtotals = (False,) * 12
   pt2.PivotFields("Direction").PivotItems("Unknown").Visible = False
   pt2.TableStyle2                              = "TableStyleLight17"
   pt2.DataFields("First Departure").NumberFormat = "hh:mm"
   pt2.DataFields("Last Departure").NumberFormat  = "hh:mm"
   return pt2

def apply_slicers(wb, ws_chart, pt, pt2, default_station_name: str, default_day: str):
   for field, caption, top, left, width, height in SLICER_CONFIGS:
       sc      = wb.SlicerCaches.Add2(pt, field)
       sc.Name = f"SlicerCache_{field}"
       sl = sc.Slicers.Add(
           SlicerDestination=ws_chart,
           Name=f"Slicer_{field}",
           Caption=caption,
           Top=top, Left=left, Width=width, Height=height,
       )

       sl.Style  = "SlicerStyleLight2"
       sl.Top    = top
       sl.Left   = left
       sl.Width  = width
       sl.Height = height

   for field in ["StationName", "Day", "Timetable"]:
       wb.SlicerCaches(f"SlicerCache_{field}").PivotTables.AddPivotTable(pt2)

   sc_station = wb.SlicerCaches("SlicerCache_StationName")

   for item in sc_station.SlicerItems:
       item.Selected = (item.Name == default_station_name)

   sc_day = wb.SlicerCaches("SlicerCache_Day")

   for item in sc_day.SlicerItems:
       item.Selected = (item.Name == default_day)

def build_chart_sheet(wb, ws_pivot, pc, timetable_names: list[str], colors: list, default_station_name: str, default_day: str, pt):
   ws_chart = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
   ws_chart.Name = "Charts"
   co, chart, ay = build_chart(wb, ws_pivot, ws_chart, timetable_names, colors)
   add_chart_labels(ws_chart, co, chart, ay)
   pt2 = build_summary_table(wb, ws_chart, pc)
   apply_slicers(wb, ws_chart, pt, pt2, default_station_name, default_day)
   return ws_chart

def main():
   app = QApplication(sys.argv)
   rsx_files = select_multi_rsx_files()

   if not rsx_files:
       show_error("No RSX files selected", "You must select at least one RSX file to continue.")
       sys.exit(1)

   colors = generate_colors(len(rsx_files))
   timetable_names = sorted([os.path.splitext(os.path.basename(p))[0] for p in rsx_files])
   aa, default_station_name, default_day = build_combined_df(rsx_files, colors)
   print(f"Default filter: {default_station_name} / {default_day}")
   print(f"Data ready: {len(aa)} rows")
   excel = win32.Dispatch("Excel.Application")
   excel.Visible       = False
   excel.DisplayAlerts = False

   try:
       wb = excel.Workbooks.Add()
       build_data_sheet(wb, aa)
       ws_pivot, pc, pt = build_pivot_sheet(wb, timetable_names)
       build_chart_sheet(wb, ws_pivot, pc, timetable_names, colors,
                         default_station_name, default_day, pt)
       excel.Calculate()
       wb.Worksheets("Data").Activate()
       wb.SaveAs(OUTPUT_PATH, FileFormat=xlOpenXMLWorkbook)
       print(f"Saved to: {OUTPUT_PATH}")
       show_info("Successful", f"First Last Graph saved to {OUTPUT_PATH}. Open Charts sheet and use slicers to filter")
       print("Open the 'Charts' sheet -> use the slicers to filter.")
   finally:
       wb.Close(SaveChanges=False)
       excel.Quit()

if __name__ == "__main__":
   main()