
import sys

import xlsxwriter
import os
from collections import defaultdict

from taipan.gui.base import open_file_crossplatform, show_info, select_file
from taipan.core.xml_parser import parse_rsx, normalise_days, sort_days, sort_units
from taipan.core.xml_processor import init_store, build_weeklists_into_store, merge_out_in_per_day, startofdayunitcount

from taipan.constants.locations import NON_STABLE_LOCATIONS, YARDS
from taipan.constants.days import SORT_ORDER_WEEK, ID_TO_SHORT, WEEKDAY_KEYS_MASTER
from taipan.core.utils import mins_to_excel_time, hhmm_to_mins
import win32com.client
import pythoncom
from PyQt6.QtWidgets import QApplication


def build_change_matrix(u_list):
    n = len(u_list)
    matrix = {}
    for i, unit in enumerate(u_list):
        row = [0] * (n + 1)
        row[0] = 1
        row[i + 1] = 1
        matrix[unit] = row
    return matrix


def detect_fleet_violations(stables_dict, yard_meta):
    violations = []

    for yard_name, stables_tuple in stables_dict.items():
        meta = yard_meta[yard_name]

        yard_units = {entry[2] for daylist in stables_tuple if daylist for entry in daylist}

        ngr_units = [u for u in yard_units if u in ('NGR', 'NGRE')]
        qr_units  = [u for u in yard_units if u not in ('NGR', 'NGRE')]

        if meta.get('ngr_only') and qr_units:
            violations.append({'yard': yard_name, 'type': 'ngr_only','offending_units': qr_units})

        if meta.get('qr_only') and ngr_units:
            violations.append({'yard': yard_name,'type': 'qr_only','offending_units': ngr_units})

    return violations


def extract_regular_series(daylist, u_list, change_matrix, interval_mins=1):
    # this runs stabling count but at a finer resolution
    # change interval _mins to change the x axis (time) ticks for each stabling yard 
   if not daylist:
       return [], {}
   start        = startofdayunitcount(daylist, u_list)
   stablechange = list(map(float, start))
   events = []
   for entry in daylist:
       unit  = entry[2]
       t_str = entry[7]
       delta = entry[8]
       cm = change_matrix[unit]
       diff = [delta * c for c in cm]
       events.append((hhmm_to_mins(t_str), diff))
   t_start = events[0][0]
   t_end   = events[-1][0]
   change_at = defaultdict(lambda: [0.0] * (len(u_list) + 1))
   for t, diff in events:
       existing  = change_at[t]
       change_at[t] = [e + d for e, d in zip(existing, diff)]
   ticks  = []
   counts = defaultdict(list)
   state  = list(stablechange)
   for tick in range(t_start, t_end + interval_mins, interval_mins):
       if tick in change_at:
           diff  = change_at[tick]
           state = [s + d for s, d in zip(state, diff)]
       ticks.append(mins_to_excel_time(tick))
       counts['Total'].append(int(state[0]))
       for i, u in enumerate(u_list):
           counts[u].append(int(state[i + 1]))
   return ticks, dict(counts), t_start, t_end


def write_yard_chart(workbook, yard_name, stables_tuple, u_list, change_matrix,d_list, capacity, filename, data_sheet, data_col_offset,violations=None): #by default no violations 
   # write data + chart for a single yard 
   graph_sheet = workbook.add_worksheet(yard_name)
   graph_sheet.set_tab_color('#2563EB')
   graph_sheet.hide_gridlines(2)
   graph_sheet.set_zoom(90)
   title_fmt = workbook.add_format({
       'font_size':  14,
       'font_name':  'Aptos',
       'align':      'left',
       'valign':     'vcenter',
       'font_color': '#0F172A',
       'bold':       True,
   })
   hdr_fmt  = workbook.add_format({'bold': True})
   time_fmt = workbook.add_format({'num_format': '[h]:mm'})
   graph_sheet.set_row(0, 32)
   graph_sheet.merge_range(
       0, 0, 0, 14,
       f'{yard_name}  ·  Stabling Utilisation  ·  {filename}',
       title_fmt
   )
   col = data_col_offset
   day_slots = [(dow, daylist) for dow, daylist in zip(SORT_ORDER_WEEK, stables_tuple) if dow in d_list]

   for dow, daylist in day_slots:
       if not daylist:
           continue
       ticks, counts, t_start, t_end = extract_regular_series(daylist, u_list, change_matrix)
       if not ticks:
           continue
       
       n_rows = len(ticks)
       time_col  = col
       total_col = col + 1
       unit_cols = {u: col + 2 + i for i, u in enumerate(u_list)}
       block_w   = 2 + len(u_list)
       data_row_start = 1
       data_sheet.write(0, time_col,  f'{yard_name}_{dow}_time',  hdr_fmt)
       data_sheet.write(0, total_col, f'{yard_name}_{dow}_Total', hdr_fmt)

       for u, uc in unit_cols.items():
           data_sheet.write(0, uc, f'{yard_name}_{dow}_{u}', hdr_fmt)
       for r, t in enumerate(ticks):
           data_sheet.write(data_row_start + r, time_col, t, time_fmt)
       for r, v in enumerate(counts['Total']):
           data_sheet.write(data_row_start + r, total_col, v)
       for u, uc in unit_cols.items():
           for r, v in enumerate(counts[u]):
               data_sheet.write(data_row_start + r, uc, v)

       if isinstance(capacity, int):
           cap_col = col + block_w
           data_sheet.write(0, cap_col, f'{yard_name}_{dow}_capacity', hdr_fmt)
           for r in range(n_rows):
               data_sheet.write(data_row_start + r, cap_col, capacity)
           block_w += 1
       col += block_w

   if violations:
       warn_fmt = workbook.add_format({
           'font_name': 'Aptos', 'font_size': 12, 'bold': True,
           'font_color': '#DC2626', 'bg_color': '#FEF2F2',
       })
       unit_fmt = workbook.add_format({
           'font_name': 'Aptos', 'font_size': 12,
           'font_color': '#7C2D12', 'bg_color': '#FEF2F2',
       })
       banner_row = 30
       banner_last_col = 7

       graph_sheet.merge_range(banner_row, 0, banner_row, banner_last_col, '⚠ Fleet violation — incorrect unit types stabled at this yard:', warn_fmt )
       for i, v in enumerate(violations):
           
        graph_sheet.merge_range(
            banner_row + 1 + i, 0, banner_row + 1 + i, banner_last_col,
            f"  {', '.join(v['offending_units'])} — "
            f"{'QR' if v['type'] == 'ngr_only' else 'NGR'} units should not be here",
            unit_fmt
        )

   return col

def create_charts_via_com(xlsx_path, stables_dict, u_list, change_matrix,d_list, capacity_map):
   pythoncom.CoInitialize()
   excel = win32com.client.DispatchEx('Excel.Application')
   excel.Visible       = False
   excel.DisplayAlerts = False

   try:
       wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
       data_sheet = wb.Worksheets('_ChartData')
       for yard_name, stables_tuple in stables_dict.items():
           ws = wb.Worksheets(yard_name)
           day_slots = [
               (dow, daylist)
               for dow, daylist in zip(SORT_ORDER_WEEK, stables_tuple)
               if dow in d_list
           ]

           used_cols  = data_sheet.UsedRange.Columns.Count
           headers    = data_sheet.Range(
           data_sheet.Cells(1, 1),
           data_sheet.Cells(1, used_cols)).Value[0]
           header_map = {v: i + 1 for i, v in enumerate(headers) if v}

           chart_col   = 0   # in Excel columns
           chart_count = 0
           chart_w     = 780  # width 
           chart_h     = 380  # height 
         
           for dow, daylist in day_slots:
               if not daylist:
                   continue
               ticks, counts, t_start, t_end = extract_regular_series(daylist, u_list, change_matrix)
               if not ticks:
                   continue

               time_col_idx  = header_map.get(f'{yard_name}_{dow}_time')
               total_col_idx = header_map.get(f'{yard_name}_{dow}_Total')
               cap_col_idx   = header_map.get(f'{yard_name}_{dow}_capacity')
               unit_col_idxs = {u: header_map.get(f'{yard_name}_{dow}_{u}') for u in u_list}                
               present_units = [u for u in u_list if any(v != 0 for v in counts.get(u, []))]

               dow_label = WEEKDAY_KEYS_MASTER.get(dow, {}).get('long', dow)
   
               if time_col_idx is None:
                   continue
               n_rows = len(ticks)
               data_row_start = 2  # 1-indexed, row 1 is header
               left = chart_col * (chart_w + 30) + 5
               top  = 35
               co    = ws.ChartObjects().Add(left, top, chart_w, chart_h)
               chart = co.Chart
               chart.ChartType = 75  # COM-fragile - xlXYScatterLinesNoMarkers
               # total series
               s = chart.SeriesCollection().NewSeries()
               s.Name    = 'Total'
               s.XValues = data_sheet.Range(data_sheet.Cells(data_row_start, time_col_idx),data_sheet.Cells(data_row_start + n_rows - 1, time_col_idx))
               s.Values = data_sheet.Range(data_sheet.Cells(data_row_start, total_col_idx),data_sheet.Cells(data_row_start + n_rows - 1, total_col_idx))
               s.Format.Line.Weight = 2.5 # COM-fragile
               # per-unit series
               for u in present_units:
                   uc = unit_col_idxs.get(u)
                   if uc is None:
                       continue
                   s = chart.SeriesCollection().NewSeries()
                   s.Name    = u
                   s.XValues = data_sheet.Range(data_sheet.Cells(data_row_start, time_col_idx),data_sheet.Cells(data_row_start + n_rows - 1, time_col_idx))
                   s.Values = data_sheet.Range(data_sheet.Cells(data_row_start, uc),data_sheet.Cells(data_row_start + n_rows - 1, uc))
                   s.Format.Line.Weight = 1.5
               # capacity series
               capacity = capacity_map.get(yard_name)
               if isinstance(capacity, int) and cap_col_idx:
                   s = chart.SeriesCollection().NewSeries()
                   s.Name    = f'Capacity ({capacity})'
                   s.XValues = data_sheet.Range(
                       data_sheet.Cells(data_row_start, time_col_idx),
                       data_sheet.Cells(data_row_start + n_rows - 1, time_col_idx)
                   )
                   s.Values = data_sheet.Range(
                       data_sheet.Cells(data_row_start, cap_col_idx),
                       data_sheet.Cells(data_row_start + n_rows - 1, cap_col_idx)
                   )
                   s.Format.Line.DashStyle  = 4  # COM-fragile msoLineDash
                   s.Format.Line.Weight     = 1.0
               # axes
               ax = chart.Axes(1)  # x
               ax.MinimumScale            = mins_to_excel_time(t_start)
               ax.MaximumScale            = mins_to_excel_time(t_end)
               ax.MajorUnit               = mins_to_excel_time(60) # COM-fragile
               ax.TickLabels.NumberFormat = 'h:mm'
               ax.TickLabels.Font.Size    = 8
               ax.HasTitle                = False
               ay = chart.Axes(2)  # y
               ay.MinimumScale         = 0
               ay.HasTitle             = False
               ay.TickLabels.Font.Size = 8
               chart.HasTitle  = True
               chart.ChartTitle.Text          = dow_label
               chart.ChartTitle.Font.Size     = 12
               chart.ChartTitle.Font.Bold     = False
               chart.HasLegend           = True
               chart.Legend.Position     = -4107  # COM-fragile xlLegendPositionRight
               chart.Legend.Font.Size    = 8
               # apply style — works because COM owns the chart from creation
               chart.ChartStyle = 240  # COM-fragile
               #chart.ChartColor = 2
               chart_count += 1
               chart_col += 1
       wb.Save()
       wb.Close()
   finally:
       excel.Quit()
       pythoncom.CoUninitialize()


def write_summary_sheet(workbook, violations, filename):
   """
   violations: list of dicts with keys:
       yard, type ('ngr_only' | 'qr_only'), offending_units
   """
   sheet = workbook.add_worksheet('Summary')
   sheet.activate()
   # ── formats ───────────────────────────────────────────────────────────────
   title_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 18, 'bold': True,
       'font_color': '#0F172A',
   })
   header_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 12, 'bold': True,
       'font_color': '#FFFFFF', 'bg_color': '#1E3A5F',
       'border': 1, 'border_color': '#E2E8F0',
   })
   warn_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 12,
       'font_color': '#DC2626', 'bold': True,
       'bg_color': '#FEF2F2',
       'border': 1, 'border_color': '#FECACA',
   })
   unit_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 12,
       'font_color': '#7C2D12',
       'bg_color': '#FEF2F2',
       'border': 1, 'border_color': '#FECACA',
   })
   ok_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 12,
       'font_color': '#166534',
       'bg_color': '#F0FDF4',
       'border': 1, 'border_color': '#BBF7D0',
   })
   note_fmt = workbook.add_format({
       'font_name': 'Aptos', 'font_size': 10,
       'font_color': '#6B7280', 'italic': True,
   })
   sheet.set_column(0, 0, 20)  # Yard
   sheet.set_column(1, 1, 18)  # Expected fleet
   sheet.set_column(2, 2, 30)  # Offending units
   sheet.set_column(3, 3, 40)  # Message
   sheet.set_row(0, 28)
   sheet.write(0, 0, 'Stabling Fleet Violations', title_fmt)
   sheet.set_row(2, 18)
   sheet.write(2, 0, 'Yard',             header_fmt)
   sheet.write(2, 1, 'Expected Fleet',   header_fmt)
   sheet.write(2, 2, 'Offending Units',  header_fmt)
   sheet.write(2, 3, 'Issue',            header_fmt)
   if not violations:
       sheet.write(3, 0, '✓ No violations found', ok_fmt)
       return
   for i, v in enumerate(violations):
       row = 3 + i
       sheet.set_row(row, 16)
       expected   = 'NGR only' if v['type'] == 'ngr_only' else 'QR only'
       units_str  = ', '.join(v['offending_units'])
       wrong_type = 'QR' if v['type'] == 'ngr_only' else 'NGR'
       message    = f"{wrong_type} units stabled at {expected} yard"
       sheet.write(row, 0, v['yard'],   warn_fmt)
       sheet.write(row, 1, expected,    warn_fmt)
       sheet.write(row, 2, units_str,   unit_fmt)
       sheet.write(row, 3, message,     warn_fmt)
   sheet.write(4 + len(violations), 0, f'Generated: {filename}', note_fmt)


def TTS_Graph(path):
    root, trains, d_list, u_list, run_dict, _ = parse_rsx(path, want_trains=True, want_days=True, want_units=True, want_runs=True,)
    run_dict = {(run, str(day)): v for (run, day), v in run_dict.items()}
    d_list   = [str(d) for d in d_list]
    d_list   = normalise_days(sort_days(d_list), collapse_mon_thu=False)
    u_list   = sort_units(u_list)
    change_matrix = build_change_matrix(u_list)
    store = init_store(YARDS, SORT_ORDER_WEEK)

    for yard_name, meta in YARDS.items():
        build_weeklists_into_store(store, yard_name=yard_name, options=meta['yards'], day_order=SORT_ORDER_WEEK, d_list=d_list, run_dict=run_dict, count=True)

    stables_dict = {}
    for yard_name in YARDS:
        merged = [merge_out_in_per_day(store[yard_name][code]['out'], store[yard_name][code]['in']) for code in SORT_ORDER_WEEK]
        stables_dict[yard_name] = tuple(merged)
    
    # detect + store violations 
    violations = detect_fleet_violations(stables_dict, YARDS)

    # build workbook
    filename  = path.split('/')[-1].replace('.rsx', '')
    xlsx_path = f'StablingGraph-{filename}.xlsx'
    os.chdir('\\'.join(path.split('/')[0:-1]))
    workbook = xlsxwriter.Workbook(xlsx_path)
    # Summary is created first -> leftmost tab, activate() makes it open first
    write_summary_sheet(workbook, violations, filename)
    # Hidden data sheet second
    data_sheet = workbook.add_worksheet('_ChartData')
    #data_sheet.hide()  # to unhide data 
    # Yard chart sheets follow
    col_ptr = 0
    
    for yard_name, stables_tuple in stables_dict.items():
        meta     = YARDS[yard_name]
        capacity = meta.get('capacity')
        col_ptr  = write_yard_chart(workbook, yard_name, stables_tuple, u_list, change_matrix, d_list, capacity, filename,data_sheet, col_ptr, violations=[v for v in violations if v['yard'] == yard_name])
    workbook.close()
    print(f'Saved: {xlsx_path}')
    print('Creating charts...')
    capacity_map = {yard_name: YARDS[yard_name].get('capacity') for yard_name in YARDS}
    create_charts_via_com(xlsx_path, stables_dict, u_list, change_matrix, d_list, capacity_map)
    print('Done.')
    open_file_crossplatform(xlsx_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = select_file(caption='Select RSX file',directory='',filter_str='RSX Files (*.rsx);;All Files (*.*)')
    TTS_Graph(path)
