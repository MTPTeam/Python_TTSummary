import xlsxwriter
import re
import os
import sys
import time
import shutil
import numpy as np
from datetime import datetime
import xml.etree.ElementTree as ET

from taipan.gui.base import open_file_crossplatform, show_info, select_file
from taipan.core.utils import timetrim, csl
from taipan.core.xml_parser import parse_rsx, TrainInfo, sort_days, sort_units, normalise_days, resolve_DoO
from taipan.core.xml_processor import build_singletrip_col, find_runs_without_stable, init_store, build_weeklists_into_store, merge_out_in_per_day, startofdayunitcount, endofdayunitcount, overnightstabling, interpeakstabling
from taipan.core.ExcelWriter import build_excel_formats, summary_writerow, summary_writetotals, summary_totalheaders
from taipan.constants.locations import NON_STABLE_LOCATIONS, YARDS, NON_STABLE_LOCATIONS
from taipan.constants.days import SORT_ORDER_WEEK, ID_TO_SHORT, WEEKDAY_KEYS_MASTER
from taipan.constants.styles import STEPS_COL

import traceback
import logging
from collections import defaultdict

from PyQt6.QtWidgets import QApplication


OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True 
OpenWorkbook = True



def capacity_exceeded(yard_name, meta, os_total, os_bkdwn, u_list):
   """
   Returns True if capacity is exceeded or wrong train type is stabled.
   QMU is excluded from all counts.
   """
   capacity = meta.get('capacity')
   ngr_only = meta.get('ngr_only', False)
   qr_only  = meta.get('qr_only', False)
   # build per-unit dict from breakdown, excluding QMU
   unit_counts = {
       u: float(v)
       for u, v in zip(u_list, os_bkdwn)
       if u != 'QMU'
   }
   ngr_count = unit_counts.get('NGR', 0) + unit_counts.get('NGRE', 0)
   qr_count  = sum(v for u, v in unit_counts.items() if u not in ('NGR', 'NGRE'))
   total     = ngr_count + qr_count
   if ngr_only:
       # red if any non-NGR present, or capacity exceeded for ngr only yards 
       wrong_type = qr_count > 0
       over_cap   = capacity is not None and ngr_count > capacity
       return wrong_type or over_cap
   if qr_only:
       # red if any NGR present, or QR count exceeds capacity
       wrong_type = ngr_count > 0
       over_cap   = capacity is not None and qr_count > capacity
       return wrong_type or over_cap
   # mixed yard — one shared capacity, all trains (ex QMU)
   over_cap = capacity is not None and os_total > capacity
   return over_cap




def weekend_exceeds(value, max_value, is_weekend, has_weekdays):
    return has_weekdays and is_weekend and value > max_value




def TTS_SC(path, mypath = None):

    source_dir = os.path.abspath(os.path.dirname(path))
    dest_dir = os.path.abspath(mypath) if mypath is not None else None
    copyfile = dest_dir is not None and source_dir != dest_dir

    try:
        
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]    
        
        root, trains, d_list, u_list, run_dict, duplicates = parse_rsx(
        path,
        want_trains=True,
        want_days=True,
        want_units=True,
        want_runs=True,
        want_duplicates=True)
        run_dict = {(run, str(day)): v for (run, day), v in run_dict.items()}
        d_list   = [str(d) for d in d_list]
        
        filename = filename[:-4]
        filename_xlsx = f'StablingCount-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        formats = build_excel_formats(workbook)
        
        ### Check for duplicate train numbers before executing the script
        if duplicates:
            print("Error - duplicate train numbers")
            for tn, day in duplicates:
                print(f' - 2 trains running on {ID_TO_SHORT.get(day, day)} with train number {tn} - ')
        

        start_time = time.time()
        runs_without_stable = []
        
        # Sort the day and unit lists
        # Remove mon-thu (120) if individual mon,tue,wed,thu days exist within the rsx
        d_list = normalise_days(sort_days(d_list), collapse_mon_thu=False)
        u_list = sort_units(u_list)

        ndays = len(d_list)
        n     = len(u_list)        
        
        # Create an identity matrix using unit types 
        # This will be used to update the row representing the number of units in a stabling location, using element-wise addition
        # A ones column is appended for the total
        change_matrix = {}
        for i,unittype in enumerate(u_list):
            change_matrix[unittype] = [1] + list(np.zeros((n,)))
            change_matrix[unittype][i+1] = 1

        store = init_store(YARDS, SORT_ORDER_WEEK)
            
    
        def write_day(sheet, daylist, row):
            """ Prints each run to the workbook and updates the unit count, printing the subsequent balance of all units """
            startcount = startofdayunitcount(daylist, u_list)
            if daylist:
                sheet.write_column(row, 0, ['Start of Day Unit Count', 'End of Day Unit Count'], size14)
                sheet.write(row, 9, startcount[0], tborder)
                sheet.write_row(row, 10, startcount[1:], border)
                row += 2
                stablechange = np.array(startcount)
                for idx, entry in enumerate(daylist, row):
                    if entry[8] < 0:
                        stablechange -= np.array(change_matrix.get(entry[2])) * abs(entry[8])
                    else:
                        stablechange += np.array(change_matrix.get(entry[2])) * abs(entry[8])
                    stablechange = list(stablechange)
                    for j, cell in enumerate(entry + stablechange):
                        sheet.write(idx, j, cell, formats[entry[2]]["normal"])
                    if entry[5] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, 5, entry[5], formats[entry[2]]["boldred"])
                    if entry[6] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, 6, entry[6], formats[entry[2]]["boldred"])
                sheet.write(row - 1, 9, stablechange[0], tborder)
                sheet.write_row(row - 1, 10, stablechange[1:], border)
                row += len(daylist)
                total = stablechange[0] - startcount[0]
                breakdown = stablechange[1:] - np.array(startcount[1:])
                unbalanced = any([total] + list(breakdown))
                if unbalanced:
                    sheet.write(row, 9, total, rborder)
                    sheet.write_row(row, 10, breakdown, rborder)
                    sheet.set_tab_color('#CC194C')
                else:
                    sheet.write(row, 9, total, tborder)
                    sheet.write_row(row, 10, breakdown, border)
                sheet.write(row, 0, 'Daily Difference', size14)
            
        def write_sheet(sheet,mon,tue,wed,thu,mth,fri,sat,sun):
            """ Populates the sheet with runs and totals for the whole week """
            
            sheet.merge_range('A1:N1',f'{sheet.get_name()} stabling balance - {filename}', title)
            sheet.write_row(    1,0,headers,header)
            sheet.freeze_panes(2, 0)

         
        
            firstrow = 2
            for d in [mon,tue,wed,thu,mth,fri,sat,sun]:
                write_day(sheet,d,firstrow)
                firstrow += len(d) + 2*bool(d)
        
        title                 = workbook.add_format({'bold':True,'align':'center'})
        header                = workbook.add_format({'bold':True,'align':'center','bg_color':'#CCCCCC'})
        size14                = workbook.add_format({'font_size':14})
        boldleft              = workbook.add_format({'bold':True,'align':'left'})
        boldleft_bottom       = workbook.add_format({'bold':True,'align':'left','bottom':1})
        boldcenter            = workbook.add_format({'bold':True,'align':'center'})
        boldcenter_bottom     = workbook.add_format({'bold':True,'align':'center','bottom':1})
        boldright             = workbook.add_format({'bold':True,'align':'right'})
        greyedouttext         = workbook.add_format({'align':'center','font_color':'#666666'})
        redboldleft           = workbook.add_format({'bold':True,'align':'left','font_color':'#CC194C'})
        redleft               = workbook.add_format({'align':'left','font_color':'#CC194C'})
        centered              = workbook.add_format({'align':'center'})
        
        boldleftvc            = workbook.add_format({'bold':True,'align':'left','valign':'vcenter'})
        boldleftvc_unbalanced = workbook.add_format({'bold':True,'align':'left','valign':'vcenter','bg_color':'#CC194C','font_color':'white'})
        boldcentervc14        = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':14})
        boldcentervc14_red = workbook.add_format({
           'bold': True, 'align': 'center', 'valign': 'vcenter',
           'font_size': 14, 'bg_color': '#FF0000', 'font_color': 'white'
       })
        
        border                = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','font_size':14})
        tborder               = workbook.add_format({'border':2, 'border_color':'#000000', 'align':'center','font_size':14})
        rborder               = workbook.add_format({'border':1, 'border_color':'#CC194C', 'align':'center','font_size':14,'font_color':'#CC194C'})
        
        boldborder            = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','bold':True})
        boldborderred         = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','bold':True,'font_color':'#FF0000'})
        interpeak_flag        = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','bold':True,'font_color':'#FF0000','bg_color':'#CCB233'})
        
        top                   = workbook.add_format({'top':1})
        bottom                = workbook.add_format({'bottom':1})
        
        
        headers = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Dep/Arr', 'Δ (6car)','Count'] + u_list
        
        # Create a list of legimate stabling options in order to flag any runs that do not end at one of these locations
        
        acceptable_stables = [code for v in YARDS.values() for code in v['yards']]
                
        for bad in ('RS', 'BHI'):
            if bad in acceptable_stables:   # works for list or set
                acceptable_stables.remove(bad)

        print(store)
        # Fill the empty lists with runs given it starts or finishes at one of the options
        for yard_name, meta in YARDS.items():
            build_weeklists_into_store(store, yard_name=yard_name, options = meta['yards'], day_order=SORT_ORDER_WEEK, d_list=d_list, run_dict=run_dict, count = True)
        
        # Create blank worksheets for each stabling yard
        Info = workbook.add_worksheet('Info')
        Summary = workbook.add_worksheet('Summary')
        
        # Use the lists we've just filled to populate the blank worksheets we've just created
        sheets = {}

        for yard_name in YARDS:
            sheets[yard_name] = workbook.add_worksheet(yard_name)
        
        # Summary
        Summary.write_row(  0,0,                list((3*n+8)*' '),                   bottom)
        Summary.write_row(  1,0,                list((3*n+8)*' '),                   bottom)
        Summary.merge_range(0,2,0,3,            'Daily Difference',             boldleft_bottom)
        Summary.write(      1,2,                'Daily Total',                  boldcenter_bottom)
        Summary.merge_range(0,5+n,0,7+n,        'Overnight Stabling Demand',    boldleft_bottom)
        Summary.write(      1,4+n,              'Capacity',                     boldcenter_bottom)
        Summary.write(      1,5+n,              'Required',                     boldcenter_bottom)
        Summary.merge_range(0,7+2*n,0,9+2*n,    'Interpeak Stabling Demand',    boldleft_bottom)
        Summary.write(      1,7+2*n,            'Required',                     boldcenter_bottom)
        Summary.set_column( 0,0,15)
        Summary.set_tab_color('#7FE57F')
        # Summary.freeze_panes('C3')
        # Summary.freeze_panes('A3')

        Summary.freeze_panes(2, 0)

        
        
        # Write the column headers for unit types
        for i,uu in enumerate(u_list):
            row = 3+i
            font = formats[uu]["bold"]
            Summary.write(1,row,uu,font)
            row += 3 + n
            Summary.write(1,row,uu,font)
            row += 2 + n
            Summary.write(1,row,uu,font)
        
        stable_capacities = {yard: meta.get('capacity') for yard, meta in YARDS.items()}

        stables_dict = {}

        for yard_name in YARDS:
            merged = [merge_out_in_per_day(store[yard_name][code]['out'], store[yard_name][code]['in']) for code in SORT_ORDER_WEEK]
            stables_dict[yard_name] = tuple(merged)


        for yard_name, ws in sheets.items():
            write_sheet(ws, *stables_dict[yard_name])
        

        # an accumulator for overnight totals 
        overnight_totals = defaultdict(lambda: defaultdict(int))
        day_index = {d: i for i, d in enumerate(SORT_ORDER_WEEK)}
        
        # Loop through all stabling locations and write totals and unit subtotals to worksheet
        # Add unit subtotals for all days and write under 'total overnight stabling'
        yard_summary_dicts = {}
        for i,(k,v) in enumerate(stables_dict.items()):
            firstrow = 2+(ndays+2)*i
            lastrow = firstrow + ndays - 1
            if i != 0:
                Summary.write_row(firstrow-1,0, list((3*n+8)*' '),bottom)
            Summary.write_row(    lastrow+1, 0, list((3*n+8)*' '),top)

            days = dict(zip(SORT_ORDER_WEEK, v))

            summary_dict = {}

            for dow, day in days.items():
                total, bkdwn       = endofdayunitcount(day, u_list, change_matrix)
                os_total, os_bkdwn = overnightstabling(day, u_list, change_matrix)
                ip_total, ip_bkdwn = interpeakstabling(day, u_list)

                summary_dict[dow] = (day, total, bkdwn, os_total, os_bkdwn, ip_total, ip_bkdwn)
            
            yard_summary_dicts[k] = summary_dict


        

            #Use a red font if the total is unbalanced at a stabling location at any point during the week
            unbalanced_totals = any(summary_dict[d][1] for d in summary_dict)
            totals_font = boldborderred if unbalanced_totals else boldborder
            
            # Highlight any stabling location if any unit is unbalanced at any point during the week
            #breakdown_list = [mon_bkdwn,tue_bkdwn,wed_bkdwn,thu_bkdwn,mth_bkdwn,fri_bkdwn,sat_bkdwn,sun_bkdwn]
            unbalanced_subtotals = any(any(summary_dict[d][2]) for d in summary_dict)
            stablefont = boldleftvc_unbalanced if unbalanced_subtotals else boldleftvc

            d_list_s = [str(d) for d in d_list]
            WEEKDAY_KEYS = [d for d in d_list_s if WEEKDAY_KEYS_MASTER.get(d, {}).get('short') in ('Mon-Thu', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri')]
            WEEKEND_KEYS = [d for d in d_list_s if WEEKDAY_KEYS_MASTER.get(d, {}).get('short') in ('Sat', 'Sun')]
            weekday_max_total = max((summary_dict[d][3] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None),default=0)
            weekday_max_by_unit = [max((summary_dict[d][4][i] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None),default=0) for i in range(n)]
            weekday_max_breakdown = [max((summary_dict[d][2][i] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None),default=0) for i in range(n)]
            weekday_max_diff_total = max((summary_dict[d][1] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None), default=0)

            weekday_max_ip_total = max((summary_dict[d][5] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None), default=0)
            weekday_max_ip_breakdown = [max((summary_dict[d][6][i] for d in WEEKDAY_KEYS if d in summary_dict and summary_dict[d][0] is not None),default=0) for i in range(n)]



            cap_exceeded_any_day = any(
               capacity_exceeded(
                   k,
                   YARDS[k],
                   max(summary_dict[d][3], summary_dict[d][5]),
                   summary_dict[d][4] if summary_dict[d][3] >= summary_dict[d][5] else summary_dict[d][6],  # os_bkdwn or ip_bkdwn
                   u_list
               )
               for d in d_list_s
               if d in summary_dict and summary_dict[d][0] is not None
           )

            cap_format = boldcentervc14_red if cap_exceeded_any_day else boldcentervc14
            if ndays == 1:
                Summary.write(firstrow, 3+n, None)
                Summary.write(firstrow, 6+2*n, None)
                Summary.write(firstrow, 0,   k,                        stablefont)
                Summary.write(firstrow, 4+n, stable_capacities.get(k), cap_format)
            else:
                Summary.merge_range(firstrow, 3+n, lastrow, 3+n, None)
                Summary.merge_range(firstrow, 6+2*n, lastrow, 6+2*n, None)
                Summary.merge_range(firstrow, 0,    lastrow, 0,   k,                        stablefont)
                Summary.merge_range(firstrow, 4+n,  lastrow, 4+n, stable_capacities.get(k), cap_format)
                
            # Write days
            Summary.write_column(firstrow,1,[WEEKDAY_KEYS_MASTER.get(d, {}).get('short') for d in d_list])

            row_ptr = firstrow # local pointer so we don't clobber firstrow used above
            #yard_days_present = [d for d, info in summary_dict.items() if info[0] is not None]
            d_list_s = [str(d) for d in d_list]

            has_weekdays = len(WEEKDAY_KEYS) > 0

            for DoW in SORT_ORDER_WEEK:
                #day_obj, total, breakdown, os_total, os_breakdown, ip_total, ip_breakdown = summary_info

                if DoW not in d_list_s:
                        continue
                
                day_obj, total, breakdown, os_total, os_breakdown, ip_total, ip_breakdown = summary_dict[DoW]
        
                # Render row if the day exists
                if day_obj is not None:
                    #Summary.write(row_ptr, 2, total, totals_font)
                    #summary_writerow(row_ptr, 3, breakdown, Summary, centered, greyedouttext)
                    #Summary.write(row_ptr, 5 + n, os_total, boldborder)
                    #summary_writerow(row_ptr, 6 + n, os_breakdown, Summary, centered, greyedouttext)
                    

                    is_weekend = DoW in WEEKEND_KEYS


                    # daily difference
                    
                    diff_total_fmt = boldborderred if weekend_exceeds(
                        total, weekday_max_diff_total, is_weekend, has_weekdays) else totals_font

                    Summary.write(row_ptr, 2, total, diff_total_fmt)
                    for ui in range(n):
                       val = float(breakdown[ui])
                       max_val = float(weekday_max_breakdown[ui])
                       fmt = boldborderred if weekend_exceeds(val, max_val, is_weekend, has_weekdays) else greyedouttext
                       Summary.write(row_ptr, 3 + ui, val, fmt)

                    # overnight stabling
                    os_total_fmt = boldborderred if weekend_exceeds(os_total, weekday_max_total, is_weekend, has_weekdays) else boldborder
                    Summary.write(row_ptr, 5 + n, os_total, os_total_fmt)
                    for ui, (unit_val, unit_max) in enumerate(zip(os_breakdown, weekday_max_by_unit)):
                       unit_fmt = boldborderred if weekend_exceeds(unit_val, unit_max, is_weekend, has_weekdays) else centered
                       Summary.write(row_ptr, 6 + n + ui, unit_val, unit_fmt)
                    if k == 'Mayne West':
                       print(f"Mayne West {DoW}: is_weekend={is_weekend}, os_breakdown={os_breakdown}, weekday_max_by_unit={weekday_max_by_unit}, weekday_max_total={weekday_max_total}, os_total={os_total}")
                    


                    #Summary.write(row_ptr, 7 + 2 * n, ip_total, boldborder)
                    #summary_writerow(row_ptr, 8 + 2 * n, ip_breakdown, Summary, centered, greyedouttext)

                    ip_total_fmt = boldborderred if weekend_exceeds(ip_total, weekday_max_ip_total, is_weekend, has_weekdays) else boldborder

                    if ip_total > os_total:
                        ip_total_fmt = interpeak_flag
                    Summary.write(row_ptr, 7 + 2 * n, ip_total, ip_total_fmt)
                    
                    for ui in range(n):  
                        val = float(ip_breakdown[ui]) if ip_breakdown is not None and len(ip_breakdown) > ui else 0
                        max_val = float(weekday_max_ip_breakdown[ui])
                        if weekend_exceeds(val, max_val, is_weekend, has_weekdays):
                            fmt = boldborderred
                        elif val == 0:
                            fmt = greyedouttext
                        else:
                            fmt = centered
                        Summary.write(row_ptr, 8 + 2 * n + ui, val, fmt)

                # Accumulate only if day exists AND breakdown has elements
                has_day = day_obj is not None
                has_os = (
                    os_breakdown is not None and
                    ((os_breakdown.size > 0) if isinstance(os_breakdown, np.ndarray) else len(os_breakdown) > 0)
                )
                if has_day and has_os:
                    for unit, cnt in zip(u_list, os_breakdown):
                        overnight_totals[unit][DoW] += float(cnt)  # int() in case cnt is a numpy scalar

                if DoW in d_list and day_obj is not None:
                    row_ptr += 1

        for yard_name, ws in sheets.items():
            summary_dict = yard_summary_dicts[yard_name]
            d_list_s = [str(d) for d in d_list]


            if yard_name == 'Clapham':
                for d in d_list_s:
                    if d in summary_dict and summary_dict[d][0] is not None:
                        os_total = summary_dict[d][3]
                        os_bkdwn = summary_dict[d][4]
                        result = capacity_exceeded(yard_name, YARDS[yard_name], os_total, os_bkdwn, u_list)
            tab_exceeded = any(
               capacity_exceeded(
                   yard_name,
                   YARDS[yard_name],
                   max(summary_dict[d][3], summary_dict[d][5]),
                   summary_dict[d][4] if summary_dict[d][3] >= summary_dict[d][5] else summary_dict[d][6],
                   u_list
               )
               for d in d_list_s
               if d in summary_dict and summary_dict[d][0] is not None
           )
            
            if tab_exceeded:
                ws.set_tab_color('#FF0000')


        dailytotals_dict = {d: sum(overnight_totals[u].get(d, 0) for u in u_list) for d in SORT_ORDER_WEEK}
        type_dict = {u: [overnight_totals[u].get(d, 0) for d in SORT_ORDER_WEEK] for u in u_list}
        totals_col = [dailytotals_dict.get(d, 0) for d in d_list]
        daylist_dict_all = {d: [type_dict[u][day_index[d]] for u in u_list] for d in SORT_ORDER_WEEK}
        daylist_dict = {d: daylist_dict_all[d] for d in d_list}
    
        
        row = len(stables_dict)*(ndays+2)+2
        endrow = row + ndays
        if ndays == 1:
            # Summary.write(row+1,n,'Total Overnight Stabling',boldcentervc14)
            Summary.write(row,n+4,'Day',boldleft_bottom)
            Summary.write(row,n+5,'Total',boldcenter_bottom)
            Summary.merge_range(row+1,n,row+1,3+n,'Total Overnight Stabling',boldcentervc14)
        else:
            Summary.merge_range(row+1,n,endrow+1,3+n,'Total Overnight Stabling',boldcentervc14)    
            Summary.write(row,n+4,'Day',boldleft_bottom)
            Summary.write(row,n+5,'Total',boldcenter_bottom)
        
        col = n
        for unit in u_list:
            summary_totalheaders(unit, row, col, Summary, formats)    
            col += 1

        row_start = row
        for day in d_list:
            summary_writetotals(day, row, d_list, Summary, totals_col, daylist_dict, boldcenter, centered, n)
            row += 1

        # --- 3-car breakdown table ---
        row_header = row_start
        three_car_col_start = 2*n + 7  # starts right after the 6-car totals table

        # Filter once and reuse everywhere
        filtered_units = [u for u in u_list if u not in ('NGR', 'QMU')]
        
        total_3car = sum(v * 2 for u, v in zip(u_list, daylist_dict[day]) if u not in ('NGR', 'QMU'))
        Summary.write(row_header - 1, three_car_col_start, '3-car')
        Summary.write(row_header,     three_car_col_start,     'Day',   boldleft_bottom)
        Summary.write(row_header,     three_car_col_start + 1, 'Total', boldcenter_bottom)

        # ----- headers -----
        three_car_col = three_car_col_start - 4
        for unit in filtered_units:
            summary_totalheaders(unit, row_header, three_car_col, Summary, formats)
            three_car_col += 1

        # ----- rows -----
        row_ptr = row_header + 1
        for day in d_list:
            short = WEEKDAY_KEYS_MASTER.get(day, {}).get('short')
            day_idx = d_list.index(day)

            # filter breakdown values to match filtered_units
            breakdown_3car = [
                v * 2
                for u, v in zip(u_list, daylist_dict[day])
                if u not in ('NGR', 'QMU')
            ]

            total_3car = sum(breakdown_3car)


            Summary.write(row_ptr, three_car_col_start,     short,      boldcenter)
            Summary.write(row_ptr, three_car_col_start + 1, total_3car, boldcenter)
            summary_writerow(row_ptr, three_car_col_start + 2, breakdown_3car, Summary, centered, greyedouttext)

            row_ptr += 1
        # --- end 3-car table ---
        
        info_col  = ['Timetable Name:','Timetable Id:','Report Date:','Report Type:']
        info_col2 = [filename,'',datetime.now().strftime("%d-%b-%Y %H:%M"),'Stabling count by run']
        Info.set_column(0,0,15)
        
        singletrip_col = build_singletrip_col(d_list, run_dict)
        runs_without_stable = find_runs_without_stable(run_dict, acceptable_stables)
        
        Info.write_column('A1',info_col,boldright)
        Info.write_column('B1',info_col2)
        Info.write_column('A7',STEPS_COL,boldleft)
        Info.write_column('A13',singletrip_col,boldleft)
        
        
        if runs_without_stable:
            Info.write(13+ndays,0,f'{len(runs_without_stable)} Runs not starting or ending at an adequate stabling location:',  redboldleft)
            Info.set_tab_color('#CC194C')
            for row,run in enumerate(runs_without_stable,14+ndays):
                runID     = run[0]
                DoO = WEEKDAY_KEYS_MASTER.get(run[1], {}).get('short')
                start_sID = run[2]
                end_sID   = run[3]
                
                Info.merge_range(row,0,row,10,f'{runID} on {DoO} starts the run at {start_sID} and ends at {end_sID}',redleft)
        
        Summary.activate()
        
        
        if CreateWorkbook:
            workbook.close()
            print('Creating workbook')  
            if copyfile:
                destination = os.path.join(mypath, os.path.basename(filename_xlsx))
                if os.path.abspath(filename_xlsx) != os.path.abspath(destination):
                    shutil.copy(filename_xlsx, destination)
                else:
                    print('Skipping copy because source and destination are the same file') 
            else:
                if OpenWorkbook:
                    open_file_crossplatform(filename_xlsx)
                    print('\nOpening workbook')

        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
    
if __name__ == "__main__":
    
    app = QApplication.instance() or QApplication(sys.argv)

    path = select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    if path:
        TTS_SC(path)