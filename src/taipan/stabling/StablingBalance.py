import xlsxwriter # LT change
import re
import os
import sys
import time
import shutil
from datetime import datetime
import xml.etree.ElementTree as ET
import time

from taipan.gui.base import open_file_crossplatform, show_info, select_file
from taipan.stabling.StablingCount import capacity_exceeded
import traceback
import logging

from taipan.constants.locations import YARDS, NON_STABLE_LOCATIONS
from taipan.constants.days import ID_TO_SHORT, SORT_ORDER_WEEK, WEEKDAY_KEYS_MASTER, ID_TO_SHORT
from taipan.constants.trains import SORT_ORDER_UNIT
from taipan.constants.styles import STEPS_COL


from taipan.core.xml_parser import parse_rsx, TrainInfo, sort_days, sort_units, normalise_days
from taipan.core.xml_processor import init_store, build_weeklists_into_store, make_legacy_stables_dict_from_store, write_sheet_from_store, build_singletrip_col, find_runs_without_stable
from taipan.core.ExcelWriter import writecell_unbalanced, write_unit_totals, build_excel_formats, build_generic_formats

from PyQt6.QtWidgets import QApplication

OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True

headers1 = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Start Time', '# Sets','# SetsByUnit']
headers2 = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Finish Time', '# Sets','# SetsByUnit']


def TTS_SB(path, mypath = None):

    
    src_dir = os.path.dirname(path)
    copyfile = (mypath is not None) and (os.path.normpath(src_dir) != os.path.normpath(os.path.dirname(mypath)))

    try:
        
        root, trains, d_list, u_list, run_dict, duplicates = parse_rsx(
        path,
        want_trains=True,
        want_days=True,
        want_units=True,
        want_runs=True,
        want_duplicates=True)
        run_dict = {(run, str(day)): v for (run, day), v in run_dict.items()}
        d_list   = [str(d) for d in d_list]

        if duplicates:
            print("Error - duplicate train numbers")
            for tn, day in duplicates:
                print(f' - 2 trains running on {ID_TO_SHORT.get(day, day)} with train number {tn} - ')

        
        directory = os.path.dirname(path)
        os.chdir(directory)
        filename = os.path.splitext(os.path.basename(path))[0]
        filename_xlsx = f'StablingBalance-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        formats = build_excel_formats(workbook)
        #print(formats)


        d_list = normalise_days(sort_days(d_list), collapse_mon_thu=False)
        u_list = sort_units(u_list)

        ndays = len(d_list)
        n = len(u_list)

        #print(d_list)
        
        start_time = time.time()
        runs_without_stable = []
        store = init_store(YARDS, SORT_ORDER_WEEK)
        #print(store)
        
        
        def write_runs(sheet,daylist,r,c):
            """ 
            Writes either the runs coming out of or the runs coming in to the stabling yard
            Must be called twice for each day to compare unit and total balances
            """
            
            if daylist:
                
                # Write runs using individual unittype cell formatting
                for idx,line in enumerate(daylist,r):
                    sheet.write_row(idx, c, line, formats[line[2]]["normal"])
                    
                    # Use red font if run ends at a station not a stabling yard
                    if line[5] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, c+5, line[5], formats[line[2]]["boldred"])
                    if line[6] in NON_STABLE_LOCATIONS:
                        sheet.write(idx, c+6, line[6], formats[line[2]]["boldred"])
            

        def write_day(sheet, daylist_out, daylist_in, row):
            """ 
            Separated by runs starting at or ending at the stable,
            prints each run to the workbook and updates the unit count, 
            prints the balances in and out for each unit as well as the total balance at the end of the day 
            """
            
            col1 = 0
            col2 = 11
            widecol1 = 9
            widecol2 = 20
            BD_out = {}
            BD_in  = {}
                      
            write_runs(sheet, daylist_out, row, col1)
            write_runs(sheet, daylist_in,  row, col2)
            
            if daylist_out:
                units_in_daylist = [ttype for ttype in u_list if any([x[2]==ttype for x in daylist_out])]
                for ttype in units_in_daylist:
                    count = sum([  1  for x in daylist_out if x[2] == ttype])
                    total = sum([x[8] for x in daylist_out if x[2] == ttype])
                    BD_out[ttype] = count, total
                    
            if daylist_in:
                units_in_daylist = [ttype for ttype in u_list if any([x[2]==ttype for x in daylist_in])]
                for ttype in units_in_daylist:
                    count = sum([  1  for x in daylist_in if x[2] == ttype])
                    total = sum([x[8] for x in daylist_in if x[2] == ttype])
                    BD_in[ttype]  = count, total
            
            
            in_row = out_row = row
            for ttype in u_list:

                #print(ttype)
                
                n_unit_out   = BD_out[ttype][0] if BD_out.get(ttype) else 1
                sum_unit_out = BD_out[ttype][1] if BD_out.get(ttype) else 0
                
                n_unit_in    = BD_in[ttype][0]  if BD_in.get(ttype) else 1
                sum_unit_in  = BD_in[ttype][1]  if BD_in.get(ttype) else 0
                
                
                
                BDogt = BD_out.get(ttype)
                BDigt = BD_in.get(ttype)
                if BDogt != BDigt:
                    font = formats[ttype]["bigred"]
                    if BDogt:
                        write_unit_totals(sheet, sum_unit_out, n_unit_out, out_row, widecol1,  font)
                        out_row += n_unit_out
                    if BDigt:
                        write_unit_totals(sheet, sum_unit_in, n_unit_in, in_row, widecol2, font)
                        in_row += n_unit_in
                    
                else:
                    font = formats[ttype]["big"]
                    if BDogt:
                        write_unit_totals(sheet, sum_unit_out, n_unit_out, out_row, widecol1, font)
                        out_row += n_unit_out
                    if BDigt:
                        write_unit_totals(sheet, sum_unit_in, n_unit_in, in_row, widecol2, font)
                        in_row += n_unit_in
                        
                            
            if daylist_in or daylist_out:
                totals_row =  row + max(len(daylist_out), len(daylist_in))
                sheet.write(totals_row,0,'Total',size16)
                allunits_out = sum([v[1] for k,v in BD_out.items()]) if BD_out else 0
                allunits_in  = sum([v[1] for k,v in BD_in.items()])  if BD_in  else 0
                if BD_out != BD_in:
                    sheet.write(totals_row,widecol1-1,allunits_out,rborder16)
                    sheet.write(totals_row,widecol2-1,allunits_in,rborder16)
                    sheet.set_tab_color('#CCB233')
                else:
                    sheet.write(totals_row,widecol1-1,allunits_out,border16)
                    sheet.write(totals_row,widecol2-1,allunits_in,border16)
            
            
        def write_sheet(sheet, mon_out,tue_out,wed_out,thu_out,mth_out,fri_out,sat_out,sun_out,   mon_in,tue_in,wed_in,thu_in,mth_in,fri_in,sat_in,sun_in):
            """ Populates the sheet with runs and totals for the whole week """
            
            widecol1 = len(headers1) - 1
            widecol2 = len(headers1) + len(headers2)
            sheet.set_column(widecol1,widecol1,11.5)
            sheet.set_column(widecol2,widecol2,11.5)
            sheet.merge_range(0,0,0,widecol2,f'{sheet.get_name()} stabling balance - {filename}', title)
            col1 = 0
            col2 = 11
            sheet.write_row(    1,col1,headers1,header)
            sheet.write_row(    1,col2,headers2,header)
            
            firstrow = 2
            outlists = [mon_out,tue_out,wed_out,thu_out,mth_out,fri_out,sat_out,sun_out]
            inlists  = [mon_in,tue_in,wed_in,thu_in,mth_in,fri_in,sat_in,sun_in]
            for a,b in zip(outlists, inlists):
                write_day(sheet, a,b, firstrow)
                firstrow += max(len(a),len(b)) + 2*bool(a or b)
            
        
        # size16vc = workbook.add_format({'font_size':16,'align':'center','valign':'vcenter'})
    
        
        title                   = workbook.add_format({'bold':True,'align':'center'})
        header                  = workbook.add_format({'bold':True,'align':'center','bg_color':'#CCCCCC'})
        size16                  = workbook.add_format({'font_size':16})
        
        boldleft                = workbook.add_format({'bold':True,'align':'left'})
        boldright               = workbook.add_format({'bold':True,'align':'right'})
        centered                = workbook.add_format({'align':'center'})
        redcentered             = workbook.add_format({'align':'center','font_color':'#CC194C'})
        redboldleft             = workbook.add_format({'bold':True,'align':'left','font_color':'#CC194C'})
        redleft                 = workbook.add_format({'align':'left','font_color':'#CC194C'})
        
        leftborder              = workbook.add_format({'left':1,'align':'center'})
        boldbottomleftborder    = workbook.add_format({'left':1,'bottom':1,'align':'center','bold':True})
        leftborder_unbalanced   = workbook.add_format({'left':1,'align':'center','bg_color':'#CCB233'})
        
        topleftborder           = workbook.add_format({'top':1,'left':1,'align':'center'})
        topleftborderredbg      = workbook.add_format({'top':1,'left':1,'align':'center','font_color':'#FFFFFF','bg_color':'#CC194C'})
        
        topborder               = workbook.add_format({'top':1,'align':'center'})
        topborder_unbalanced    = workbook.add_format({'top':1,'align':'center','font_color':'#FFFFFF','bg_color':'#CC194C'})
        boldtopborder           = workbook.add_format({'top':1, 'bold':True,'align':'center'})
        
        
        boldleftvc              = workbook.add_format({'bold':True,'align':'left','valign':'vcenter'})
        boldleftvc_unbalanced_b = workbook.add_format({'bold':True,'align':'left','valign':'vcenter','bg_color':'#CCB233'})
        boldleftvc_unbalanced_r = workbook.add_format({'bold':True,'align':'left','valign':'vcenter','bg_color':'#CC194C'}) 
        
        border16                = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','font_size':16})
        rborder16               = workbook.add_format({'border':1, 'border_color':'#CC194C', 'align':'center','font_size':16,'font_color':'#CC194C'})
                
        top                     = workbook.add_format({'top':1})
        bottom                  = workbook.add_format({'bottom':1})
        
        # Create Info & Summary before writing to them
        Info    = workbook.add_worksheet('Info')
        Summary = workbook.add_worksheet('Summary')

        acceptable_stables = [code for loc in YARDS.values() for code in loc['yards']]
        for bad in ('RS', 'BHI'):
            if bad in acceptable_stables:
                acceptable_stables.remove(bad)

        # Build store for each yard (unchanged)
        for yard_name, info in YARDS.items():
            build_weeklists_into_store(
                store, yard_name, info['yards'], # Access 'yards' here
                SORT_ORDER_WEEK, d_list, run_dict, count=False
        )

        # Create yard worksheets ONCE (no sheet_dict)
        yard_sheets = [(name, workbook.add_worksheet(name)) for name in YARDS.keys()]


        # Write each yard sheet using your legacy write_sheet via the adapter
        for yard_name, ws in yard_sheets:
            write_sheet_from_store(
                ws, store, yard_name,
                SORT_ORDER_WEEK,
                write_sheet_legacy=write_sheet
            )

        

        # wrong train type in yard 
        for yard_name, ws in yard_sheets:
            meta = YARDS[yard_name]
            if not meta.get('ngr_only') and not meta.get('qr_only'):
                continue
            wrong_type_any_day = False
            for dow in SORT_ORDER_WEEK:
                day_store = store[yard_name].get(dow, {})
                all_runs = day_store.get('out', []) + day_store.get('in', [])
                for run in all_runs:
                    unit = run[2]
                    is_ngr = unit in ('NGR', 'NGRE')
                    if meta.get('ngr_only') and not is_ngr:
                        wrong_type_any_day = True
                        break
                    if meta.get('qr_only') and is_ngr:
                        wrong_type_any_day = True
                        break
                if wrong_type_any_day:
                    break
            if wrong_type_any_day:
                print(f"Warning: {yard_name} has a wrong train type on at least one day")
                ws.set_tab_color('#FF0000')

        
        stables_dict = make_legacy_stables_dict_from_store(store, SORT_ORDER_WEEK)

        #print(stables_dict)

        # Summary
        Summary.write('A1','Daily Difference',boldleft)
        Summary.set_tab_color('#7FE57F')
        Summary.set_column(0,0,15)
        
        
        yard_to_ws = dict(yard_sheets)  # yard_name -> worksheet
        
        for i,(k,v) in enumerate(stables_dict.items()):
            srow = i*(ndays+3) + 2
            erow = srow + ndays
            day_out_of_balance = False
            
            Summary.write_row(srow-1,0,list((n+3)*' '),bottom)
            Summary.write_row(erow+1,0,list((n+3)*' '),top)
            Summary.write(1,2+n,'Total',boldbottomleftborder)
            
            Summary.write_column(srow,1,[WEEKDAY_KEYS_MASTER[d]['short'] for d in d_list],centered)
            Summary.write(erow,1,'Total',boldtopborder)
            
            monday      = (stables_dict.get(k)[0], stables_dict.get(k)[8])
            tuesday     = (stables_dict.get(k)[1], stables_dict.get(k)[9])
            wednesday   = (stables_dict.get(k)[2], stables_dict.get(k)[10])
            thursday    = (stables_dict.get(k)[3], stables_dict.get(k)[11])
            monthu      = (stables_dict.get(k)[4], stables_dict.get(k)[12])
            friday      = (stables_dict.get(k)[5], stables_dict.get(k)[13])
            saturday    = (stables_dict.get(k)[6], stables_dict.get(k)[14])
            sunday      = (stables_dict.get(k)[7], stables_dict.get(k)[15])
            d_dict = {'120':monthu, '64':monday, '32':tuesday, '16':wednesday, '8':thursday, '4':friday, '2':saturday, '1':sunday} 
            
            
            total_total = 0
            weekly_totals_list = []
            for col,ttype in enumerate(u_list,2):
                Summary.write(1, col, ttype, formats[ttype]["bold"])
                for r,day in enumerate(d_list,srow):
                    daily_unit_balance = sum([x[8] for x in d_dict.get(day)[1] if x[2] == ttype]) - sum([x[8] for x in d_dict.get(day)[0] if x[2] == ttype])
                    total_total += daily_unit_balance
                    if any(ttype in t for t in [ [x[2] for x in d_dict.get(day)[1]], [x[2] for x in d_dict.get(day)[0]] ]):
                        if daily_unit_balance != 0:
                            Summary.write(r,col,daily_unit_balance,redcentered)
                        else:
                            Summary.write(r,col,daily_unit_balance,centered)
                    
                daily_balance = [sum([x[8] for x in d_dict.get(day)[1] if x[2] == ttype]) - sum([x[8] for x in d_dict.get(day)[0] if x[2] == ttype]) for day in d_list]
                if any(daily_balance):
                    day_out_of_balance = True
                    
                
                weekly_balance = sum( daily_balance )
                writecell_unbalanced(Summary, erow,col,weekly_balance,topborder_unbalanced,topborder)
                weekly_totals_list.append(weekly_balance)
            
            # Write totals column
            for r,day in enumerate(d_list,srow):
                daily_total = sum([x[8] for x in d_dict.get(day)[1]]) - sum([x[8] for x in d_dict.get(day)[0]])
                writecell_unbalanced(Summary, r, 2+n, daily_total, leftborder_unbalanced, leftborder)
        
            # Write totals total        
            writecell_unbalanced(Summary, erow, 2+n, total_total, topleftborderredbg, topleftborder)
            
    
            if any(weekly_totals_list):
                Summary.merge_range(srow,0,erow,0,k,boldleftvc_unbalanced_r)
                yard_to_ws[k].set_tab_color('#CC194C')
            elif day_out_of_balance:
                Summary.merge_range(srow,0,erow,0,k,boldleftvc_unbalanced_b)
                yard_to_ws[k].set_tab_color('#CCB233')
            else:
                Summary.merge_range(srow,0,erow,0,k,boldleftvc)
        
        # Info
        info_col  = ['Timetable Name:','Timetable Id:','Report Date:','Report Type:']
        info_col2 = [filename,'',datetime.now().strftime("%d-%b-%Y %H:%M"),'Stabling balance by run']
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
                DoO       = ID_TO_SHORT[run[1]]
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

        
        if ProcessDoneMessagebox:
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            show_info('Public Timetable', 'Process Done')
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    start_time = time.perf_counter()
    path = select_file(caption="Select RSX file", directory="",filter_str="RSX Files (*.rsx);;All Files (*.*)")
    end_time = time.perf_counter()
    # Calculate the elapsed time - checking if pyqt is consistently faster than tk (should be)
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.4f} seconds")

    TTS_SB(path)  

