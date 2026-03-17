import xlsxwriter
import re
import os
import sys
import time
import shutil
import numpy as np
from datetime import datetime
import xml.etree.ElementTree as ET

import gui 
from utils import timetrim, csl
from xml_parser import parse_rsx, TrainInfo, sort_days, sort_units, normalise_days, resolve_DoO
from xml_processor import build_singletrip_col, find_runs_without_stable, init_store, build_weeklists_into_store, merge_out_in_per_day
from ExcelWriter import build_excel_formats
from MTP_constants import YARDS, SORT_ORDER_WEEK, NON_STABLE_LOCATIONS, WEEKDAY_KEYS_MASTER, SORT_ORDER_UNIT, STEPS_COL
import traceback
import logging
from collections import defaultdict

OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True 
OpenWorkbook = True

def TTS_SC(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

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
                print(f' - 2 trains running on {MTP_constants.weekday_short(day)} with train number {tn} - ')
        

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
            
        
        def summary_writerow(r,c,data):
            """ Writes a list of data into a row, with zero values appearing in a grey font """
            
            for i,x in enumerate(data):
                if x:
                    Summary.write(r,c+i,x,centered)
                else:
                    Summary.write(r,c+i,x,greyedouttext)
                    
        def summary_writetotals(day):
            """ Writes overnight stabling figures for each unit type and a total for every day """
            
            nonlocal row
            i = d_list.index(day)
            Summary.write(row+1, 4+n, WEEKDAY_KEYS_MASTER.get(day, {}).get('short'))
            Summary.write(      row+1, 5+n,   totals_col[i],      boldcenter)
            Summary.write_row(  row+1, 6+n,   daylist_dict.get(day),        centered)
            row += 1
        
        def summary_totalheaders(unit):
            """ Writes overnight stabling headers for each unit type """
            
            nonlocal col
            Summary.write(row, 6+col, unit, formats[unit]["bold"])
            col += 1            
        
        def startofdayunitcount(daylist):
            """ 
            Finds the minimum number of units stabled at each location at the start of the day
            Could be other, unused units
            If SORT_ORDER_UNIT is updated then this function will update automatically and calculate new unit types if needed 
            """
            
            # adjust these if the row layout changes
            UNIT_IDX = 2   # where the unit type string lives, e.g NGR, EMU
            DELTA_IDX = 8  # where the +1/-1 (or other delta) lives

            # init running totals and min prefix per unit from the list,
            # so everything is present even if a unit never appears in the daylist.
            running = {u: 0 for u in SORT_ORDER_UNIT}
            min_prefix = {u: 0 for u in SORT_ORDER_UNIT}

            # Walk the day's events and track its running sum and its minimum per unit
            for row in (daylist or []):
                unit = row[UNIT_IDX]
                delta = row[DELTA_IDX]

                # If a unit appears that's not in SORT_ORDER_UNIT, init on the fly (so if new traintypes are added to SORT_ORDER_UNIT this will propagate through to this function)
                if unit not in running:
                    running[unit] = 0
                    min_prefix[unit] = 0

                running[unit] += float(delta)
                if running[unit] < min_prefix[unit]:
                    min_prefix[unit] = running[unit]

            # The number required at start of day for each unit is -min_prefix (never negative)
            per_unit_dict = {u: float(max(0.0, -min_prefix.get(u, 0.0))) for u in SORT_ORDER_UNIT}

            # Produce output aligned to u_list (matches Summary writing order)
            per_unit_aligned = [per_unit_dict.get(u, 0.0) for u in u_list]

            total_required = float(sum(per_unit_aligned))
            return [total_required] + per_unit_aligned

        
        def endofdayunitcount(daylist):
            """ 
            Finds the end of day balance between units at the start of the day and units at the end of the day
            An output of zero means the stabling location is balanced for that day
            """
            
            startcount = startofdayunitcount(daylist)
            stablechange = np.array(startcount)
            
            
            for entry in daylist:
                if entry[2] == 'NGR' or entry[2] == 'NGRE':
                    threecarscalar = 1
                else:
                    threecarscalar = 2 if entry[3] == 6 else 1
        
                if entry[8] < 0:
                    stablechange -= np.array(change_matrix.get(entry[2]))*threecarscalar
                    
                else:
                    stablechange += np.array(change_matrix.get(entry[2]))*threecarscalar
                 
                    
            total = stablechange[0]-startcount[0]
            breakdown  = list(stablechange[1:]-np.array(startcount[1:]))
            
            return total,breakdown
        
        def overnightstabling(daylist):
            """ 
            Finds the number of units back in each location at the end of the day
            Uses the startofdayunitcount function as a startpoint, minimum required units for that day
            Could be other, unused units which never left
            """
            
            startcount = startofdayunitcount(daylist)
            stablechange = np.array(startcount)
            
            for entry in daylist:
                if entry[2] == 'NGR' or entry[2] == 'NGRE':
                    threecarscalar = 1
                else:
                    threecarscalar = 2 if entry[3] == 6 else 1
        
                if entry[8] < 0:
                    stablechange -= np.array(change_matrix.get(entry[2]))*threecarscalar
                else:
                    stablechange += np.array(change_matrix.get(entry[2]))*threecarscalar
            
            
            
            if max(stablechange[0],startcount[0]) == stablechange[0]:
                return stablechange[0],stablechange[1:]
            else:
                return startcount[0],startcount[1:]
                    
                    
        def interpeakstabling(daylist):
            """ 
            Finds the maximum number of trains stabled at each location during interpeak
            Returns the total and the unit breakdown at that point in time
            """
            
            ip_tracker = []
            prepeak = True
            ip = startofdayunitcount(daylist)[0]
            for t,x in enumerate(daylist):
                
                if len(x[7]) == 4:
                    x[7] = '0' + x[7]
                    
                  
                ip += x[8]
                if '09:00:00' < x[7] < '15:30:00':
                    
                    
                    while prepeak == True:
                        ip_tracker.append((daylist[t-1][7],ip-daylist[t][8]))
                        
                        prepeak = False
                    
                    ip_tracker.append((x[7],ip))
            
            if ip_tracker:
                traincount = [x[1] for x in ip_tracker]
                output_total = max(traincount)
                idx = traincount.index(output_total)
                max_oclock = ip_tracker[idx][0]
            else:
                output_total = 0
                
            unit_subtotals = []
            for u in u_list:
                unit_ip = startofdayunitcount(daylist)[1:][u_list.index(u)]
                for x in daylist:
                    try: 
                        max_oclock
                        
                        if x[2] == u:
                            unit_ip += x[8]
                        if x[7] == max_oclock:
                            break
                    except:
                        break
                if output_total == 0:
                    unit_ip = 0
                unit_subtotals.append(unit_ip)    

            return output_total,unit_subtotals
        
    
        
        def write_day(sheet,daylist,row):
            """ Prints each run to the workbook and updates the unit count, printing the subsequent balance of all units """
            
            startcount = startofdayunitcount(daylist)
            if daylist:
                sheet.write_column( row,0,['Start of Day Unit Count','End of Day Unit Count'], size14)
                sheet.write(        row,9, startcount[0],      tborder)
                sheet.write_row(    row,10,startcount[1:],     border)
                row += 2
                stablechange = np.array(startcount)
                for idx,entry in enumerate(daylist, row):
                    unit = entry[2]
                    cars = entry[3]
                    
                    if unit == 'NGR' or unit == 'NGRE':
                        threecarscalar = 1
                    else:
                        threecarscalar = 2 if cars == 6 else 1

                    if unit == "QMU":
                        print("that is why")
                    
    
                    if entry[8] < 0:

                        stablechange -= np.array(change_matrix.get(entry[2]))*threecarscalar
                        
                    else:
                        stablechange += np.array(change_matrix.get(entry[2]))*threecarscalar
                    
                    stablechange = list(stablechange)
                    for j,cell in enumerate(entry+stablechange):
                        sheet.write(idx, j, cell, formats[entry[2]]["normal"])
                       
                    # sheet.write_row(idx,0,entry+stablechange,font_dict.get(entry[2])[0])
                    if entry[5] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, 5, entry[5], formats[entry[2]]["boldred"])
                    if entry[6] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, 6, entry[6], formats[entry[2]]["boldred"])
                        
                sheet.write(        row-1,9,  stablechange[0],      tborder)
                sheet.write_row(    row-1,10, stablechange[1:],     border)
                
                row += len(daylist)
                total      = stablechange[0]-startcount[0]
                breakdown  = stablechange[1:]-np.array(startcount[1:])
                unbalanced = any([total]+breakdown)
                if unbalanced:
                    sheet.write(        row,9,  total,      rborder)
                    sheet.write_row(    row,10, breakdown,  rborder)
                    sheet.set_tab_color('#CC194C')
                else:
                    sheet.write(        row,9,  total,      tborder)
                    sheet.write_row(    row,10, breakdown,  border)
                    
                sheet.write(            row,0,  'Daily Difference', size14)
                # startrow += len(daylist) + 5
            
        def write_sheet(sheet,mon,tue,wed,thu,mth,fri,sat,sun):
            """ Populates the sheet with runs and totals for the whole week """
            
            sheet.merge_range('A1:N1',f'{sheet.get_name()} stabling balance - {filename}', title)
            sheet.write_row(    1,0,headers,header)
        
            firstrow = 2
            for d in [mon,tue,wed,thu,mth,fri,sat,sun]:
                write_day(sheet,d,firstrow)
                firstrow += len(d) + 5*bool(d)
        
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
        
        # Write the column headers for unit types
        for i,uu in enumerate(u_list):
            row = 3+i
            font = formats[uu]["bold"]
            Summary.write(1,row,uu,font)
            row += 3 + n
            Summary.write(1,row,uu,font)
            row += 2 + n
            Summary.write(1,row,uu,font)
        
        stable_capacities = {yard: meta['capacity'] for yard, meta in YARDS.items()}


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
        for i,(k,v) in enumerate(stables_dict.items()):
            firstrow = 2+(ndays+2)*i
            lastrow = firstrow + ndays - 1
            if i != 0:
                Summary.write_row(firstrow-1,0, list((3*n+8)*' '),bottom)
            Summary.write_row(    lastrow+1, 0, list((3*n+8)*' '),top)

            days = dict(zip(SORT_ORDER_WEEK, v))

            summary_dict = {}

            for dow, day in days.items():
                total, bkdwn       = endofdayunitcount(day)
                os_total, os_bkdwn = overnightstabling(day)
                ip_total, ip_bkdwn = interpeakstabling(day)

                summary_dict[dow] = (day, total, bkdwn, os_total, os_bkdwn, ip_total, ip_bkdwn)


            #Use a red font if the total is unbalanced at a stabling location at any point during the week
            unbalanced_totals = any(summary_dict[d][1] for d in summary_dict)
            totals_font = boldborderred if unbalanced_totals else boldborder
            
            # Highlight any stabling location if any unit is unbalanced at any point during the week
            #breakdown_list = [mon_bkdwn,tue_bkdwn,wed_bkdwn,thu_bkdwn,mth_bkdwn,fri_bkdwn,sat_bkdwn,sun_bkdwn]
            unbalanced_subtotals = any(any(summary_dict[d][2]) for d in summary_dict)
            stablefont = boldleftvc_unbalanced if unbalanced_subtotals else boldleftvc

            if ndays == 1:
                Summary.write(firstrow,3+n,None)
                Summary.write(firstrow,6+2*n,None)
                Summary.write(firstrow, 0,   k,                        stablefont)
                Summary.write(firstrow, 4+n, stable_capacities.get(k), boldcentervc14  )
            else:
                Summary.merge_range(firstrow,3+n,lastrow,3+n,None)
                Summary.merge_range(firstrow,6+2*n,lastrow,6+2*n,None)
                Summary.merge_range(firstrow,0,   lastrow, 0,   k,                        stablefont)
                Summary.merge_range(firstrow,4+n, lastrow, 4+n, stable_capacities.get(k), boldcentervc14)  

                
            # Write days
            # Old: [weekdaykey_dict.get(d) for d in d_list]
            Summary.write_column(firstrow,1,[WEEKDAY_KEYS_MASTER.get(d, {}).get('short') for d in d_list])

            row_ptr = firstrow # local pointer so we don't clobber firstrow used above
            #yard_days_present = [d for d, info in summary_dict.items() if info[0] is not None]
            d_list_s = [str(d) for d in d_list]

            for DoW in SORT_ORDER_WEEK:
                #day_obj, total, breakdown, os_total, os_breakdown, ip_total, ip_breakdown = summary_info

                if DoW not in d_list_s:
                        continue
                
                day_obj, total, breakdown, os_total, os_breakdown, ip_total, ip_breakdown = summary_dict[DoW]

                # Render row if the day exists (unchanged)
                if day_obj is not None:
                    Summary.write(row_ptr, 2, total, totals_font)
                    summary_writerow(row_ptr, 3, breakdown)
                    Summary.write(row_ptr, 5 + n, os_total, boldborder)
                    summary_writerow(row_ptr, 6 + n, os_breakdown)
                    Summary.write(row_ptr, 7 + 2 * n, ip_total, boldborder)
                    summary_writerow(row_ptr, 8 + 2 * n, ip_breakdown)

                    if ip_total > os_total:
                        Summary.write(row_ptr, 7 + 2 * n, ip_total, interpeak_flag)

                # Accumulate only if day exists AND breakdown has elements
                has_day = day_obj is not None
                has_os = (
                    os_breakdown is not None and
                    ((os_breakdown.size > 0) if isinstance(os_breakdown, np.ndarray) else len(os_breakdown) > 0)
                )
                if has_day and has_os:
                    for unit, cnt in zip(u_list, os_breakdown):
                        overnight_totals[unit][DoW] += int(cnt)  # int() in case cnt is a numpy scalar

                if DoW in d_list and day_obj is not None:
                    row_ptr += 1


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
            summary_totalheaders(unit)     
        for day in d_list:
            summary_writetotals(day)
        
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
                shutil.copy(filename_xlsx, mypath) 
            else:
                if OpenWorkbook:
                    gui.open_file_crossplatform(filename_xlsx)
                    print('\nOpening workbook')

        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            gui.show_info('Stabling Count Report','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
    
if __name__ == "__main__":
    path = gui.select_file(caption="Select RSX file", directory="", filter_str="RSX Files (*.rsx);;All Files (*.*)")
    TTS_SC(path)