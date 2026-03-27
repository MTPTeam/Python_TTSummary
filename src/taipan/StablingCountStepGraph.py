# stabling_graph.py

import sys

import xlsxwriter
import os
from collections import defaultdict

from taipan.gui.base import open_file_crossplatform, show_info, select_file
from taipan.xml_parser import parse_rsx, normalise_days, sort_days, sort_units
from taipan.xml_processor import init_store, build_weeklists_into_store, merge_out_in_per_day, startofdayunitcount

from taipan.constants.locations import NON_STABLE_LOCATIONS, YARDS, NON_STABLE_LOCATIONS
from taipan.constants.days import SORT_ORDER_WEEK, ID_TO_SHORT, WEEKDAY_KEYS_MASTER
from taipan.constants.styles import FAMILY_BG, _UNIT_COLOURS, _TOTAL_COLOUR, _CAPACITY_COLOUR, _GRID_COLOUR, _AXIS_COLOUR

from PyQt6.QtWidgets import QApplication

# ── helpers ───────────────────────────────────────────────────────────────────

def hhmm_to_mins(t: str) -> int:
    h, m = t.split(':')
    return int(h) * 60 + int(m)


def mins_to_excel_time(m: int) -> float:
    return m / 1440


def build_change_matrix(u_list):
    n = len(u_list)
    matrix = {}
    for i, unit in enumerate(u_list):
        row = [0] * (n + 1)
        row[0] = 1
        row[i + 1] = 1
        matrix[unit] = row
    return matrix


def extract_regular_series(daylist, u_list, change_matrix, interval_mins=1):

    # this runs stabling count but at a finer resolution
    # change interval _mins to change the x axis (time) ticks for each stabling yard 
    
    if not daylist:
        return [], {}

    start        = startofdayunitcount(daylist, u_list)
    stablechange = list(map(float, start))

    events = []
    for entry in daylist:
        print(entry)
        unit  = entry[2]
        cars  = entry[3]
        t_str = entry[7]
        delta = entry[8]

        scalar = 1
        if unit not in ('NGR', 'NGRE'):
            scalar = 2 if cars == 6 else 1

        cm   = change_matrix[unit]
        sign = -1 if delta < 0 else 1
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

    return ticks, dict(counts)



# ── write data + chart for one yard ──────────────────────────────────────────

def write_yard_chart(workbook, yard_name, stables_tuple, u_list,change_matrix, d_list, capacity, filename,data_sheet, data_col_offset):

    graph_sheet = workbook.add_worksheet(yard_name)
    graph_sheet.set_tab_color('#2563EB')

    title_fmt = workbook.add_format({
        'font_size': 13,
        'font_name': 'Aptos',
        'align':     'center',
        'valign':    'vcenter',
        'font_color': '#0F172A',
    })
    graph_sheet.set_row(0, 24)
    graph_sheet.merge_range(
        0, 0, 0, 10,
        f'{yard_name}  ·  Stabling Utilisation  ·  {filename}',
        title_fmt
    )

    hdr_fmt  = workbook.add_format({'bold': True})
    time_fmt = workbook.add_format({'num_format': '[h]:mm'})

    col       = data_col_offset
    chart_col = 0
    chart_row = 1

    day_slots = [
        (dow, daylist)
        for dow, daylist in zip(SORT_ORDER_WEEK, stables_tuple)
        if dow in d_list
    ]

    for dow, daylist in day_slots:
        if not daylist:
            continue

        dow_label = WEEKDAY_KEYS_MASTER.get(dow, {}).get('long', dow)
        ticks, counts = extract_regular_series(daylist, u_list, change_matrix)

        
        present_units = [
            u for u in u_list
            if any(v != 0 for v in counts.get(u, []))
        ]


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

        # ── chart ─────────────────────────────────────────────────────────────
        chart = workbook.add_chart({'type': 'line'})   #original

        #chart = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'}) # new 

        chart.set_title({
            'name':    dow_label,
            'overlay': False,
            'layout':  {'x': 0.02, 'y': 0.02},
        })

        chart.set_chartarea({
            'border': {'none': True},
            'fill':   {'color': '#FFFFFF'},
        })

        chart.set_plotarea({
            'border': {'none': True},
            'fill':   {'color': '#FAFAFA'},
        })

        chart.set_x_axis({
            'name':         '',
            'num_format':   '[h]:mm',
            'num_font':     {
                'name':     'Aptos',
                'size':     8,
                'color':    _AXIS_COLOUR,
                'rotation': -45,
            },
            'line':         {'color': '#E2E8F0'},
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'none',
        })

        chart.set_y_axis({
            'name':      '',
            'num_font':  {
                'name':  'Aptos',
                'size':  8,
                'color': _AXIS_COLOUR,
            },
            'min':       0,
            'line':      {'none': True},
            'major_gridlines': {
                'visible': True,
                'line': {
                    'color':     _GRID_COLOUR,
                    'dash_type': 'solid',
                    'width':     0.5,
                },
            },
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'none',
        })

        chart.set_legend({
            'position':  'bottom',
            'font':      {'name': 'Aptos', 'size': 8, 'color': _AXIS_COLOUR},
        })

        chart.set_size({'width': 580, 'height': 380})

        data_sn = data_sheet.get_name()

        # Total — thick near-black solid line
        chart.add_series({
            'name':       'Total',
            'categories': [data_sn, data_row_start, time_col,
                           data_row_start + n_rows - 1, time_col],
            'values':     [data_sn, data_row_start, total_col,
                           data_row_start + n_rows - 1, total_col],
            'line':       {'color': _TOTAL_COLOUR, 'width': 2.25},
            'marker':     {'type': 'none'},
        })

        # per-unit — thinner, slightly transparent-looking via lighter shade
        for i, u in enumerate(present_units):
            uc     = unit_cols[u]
            colour = _UNIT_COLOURS[i % len(_UNIT_COLOURS)]
            chart.add_series({
                'name':       u,
                'categories': [data_sn, data_row_start, time_col,
                               data_row_start + n_rows - 1, time_col],
                'values':     [data_sn, data_row_start, uc,
                               data_row_start + n_rows - 1, uc],
                'line':       {'color': colour, 'width': 2},
                'marker':     {'type': 'none'},
            })

        # capacity — dashed red
        if isinstance(capacity, int):
            cap_col = col + block_w - 1
            chart.add_series({
                'name':       f'Capacity ({capacity})',
                'categories': [data_sn, data_row_start, time_col,
                               data_row_start + n_rows - 1, time_col],
                'values':     [data_sn, data_row_start, cap_col,
                               data_row_start + n_rows - 1, cap_col],
                'line':       {'color': _CAPACITY_COLOUR, 'width': 1.25,
                               'dash_type': 'round_dot'},
                'marker':     {'type': 'none'},
            })

        graph_sheet.insert_chart(chart_row, chart_col, chart,
                                 {'x_offset': 5, 'y_offset': 5})

        chart_col += 10
        col       += block_w

    return col


def TTS_Graph(path):
    root, trains, d_list, u_list, run_dict, _ = parse_rsx(path,want_trains=True,want_days=True,want_units=True,want_runs=True,)

    run_dict = {(run, str(day)): v for (run, day), v in run_dict.items()}
    d_list   = [str(d) for d in d_list]
    d_list   = normalise_days(sort_days(d_list), collapse_mon_thu=False)
    u_list   = sort_units(u_list)

    change_matrix = build_change_matrix(u_list)

    store = init_store(YARDS, SORT_ORDER_WEEK)
    for yard_name, meta in YARDS.items():
        build_weeklists_into_store(store, yard_name=yard_name,options=meta['yards'], day_order=SORT_ORDER_WEEK,d_list=d_list,run_dict=run_dict,count=True)

    stables_dict = {}
    for yard_name in YARDS:
        merged = [
            merge_out_in_per_day(store[yard_name][code]['out'],store[yard_name][code]['in'])
            for code in SORT_ORDER_WEEK
        ]
        stables_dict[yard_name] = tuple(merged)

    filename  = path.split('/')[-1].replace('.rsx', '')
    xlsx_path = f'StablingGraph-{filename}.xlsx'
    os.chdir('\\'.join(path.split('/')[0:-1]))

    workbook   = xlsxwriter.Workbook(xlsx_path)
    data_sheet = workbook.add_worksheet('_ChartData')
    data_sheet.hide()

    col_ptr = 0
    for yard_name, stables_tuple in stables_dict.items():
        capacity = YARDS[yard_name].get('capacity')
        col_ptr  = write_yard_chart(
            workbook, yard_name, stables_tuple,
            u_list, change_matrix, d_list,
            capacity, filename,
            data_sheet, col_ptr
        )

    workbook.close()
    print(f'Saved: {xlsx_path}')
    open_file_crossplatform(xlsx_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = select_file(caption='Select RSX file',directory='',filter_str='RSX Files (*.rsx);;All Files (*.*)')
    TTS_Graph(path)
