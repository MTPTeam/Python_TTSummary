from prometheus_client import Summary
import xlsxwriter
import re
import os
import sys
import time
import shutil
import numpy as np
from datetime import datetime
import xml.etree.ElementTree as ET

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import gui 
from utils import timetrim, csl
from xml_parser import parse_rsx, TrainInfo, sort_days, sort_units, normalise_days, resolve_DoO
from xml_processor import build_singletrip_col, find_runs_without_stable, init_store, build_weeklists_into_store, merge_out_in_per_day_test
from MTP_constants import YARDS, SORT_ORDER_WEEK, NON_STABLE_LOCATIONS, WEEKDAY_KEYS_MASTER
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
            Summary.write(row, 6+col, unit, font_dict.get(unit)[1])
            col += 1            
        
        def startofdayunitcount(daylist):
            """ 
            Finds the minimum number of units stabled at each location at the start of the day
            Could be other, unused units
            """
            
            qtmptest = [100]
            ngrtest = [100]
            ngretest = [100]
            imutest = [100]
            emutest = [100]
            deptest = [100]
            hybtest = [100]
            smutest = [100]
            qmutest = [100]
            
            qtmpcount = 0
            ngrcount = 0
            ngrecount = 0
            imucount = 0
            emucount = 0
            depcount = 0
            hybcount = 0
            smucount = 0
            qmucount = 0
            
            for x in daylist:
                if x[2] == 'REP':
                    qtmptest.append(qtmptest[qtmpcount] + x[8])
                    qtmpcount += 1
                if x[2] == 'NGR':
                    ngrtest.append(ngrtest[ngrcount] + x[8])
                    ngrcount += 1
                if x[2] == 'NGRE':
                    ngretest.append(ngretest[ngrecount] + x[8])
                    ngrecount += 1
                if x[2] == 'IMU100':
                    imutest.append(imutest[imucount] + x[8])
                    imucount += 1
                if x[2] == 'EMU':
                    emutest.append(emutest[emucount] + x[8])
                    emucount += 1
                if x[2] == 'DEPT':
                    deptest.append(deptest[depcount] + x[8])
                    depcount += 1
                if x[2] == 'HYBRID':
                    hybtest.append(hybtest[hybcount] + x[8])
                    hybcount += 1
                if x[2] == 'SMU':
                    smutest.append(smutest[smucount] + x[8])
                    smucount += 1
                if x[2] == 'QMU':
                    qmutest.append(qmutest[qmucount] + x[8])
                    qmucount += 1
            
            t_qtmp = float(100-min(qtmptest))
            t_ngr = float(100-min(ngrtest))
            t_ngre = float(100-min(ngretest))
            t_imu = float(100-min(imutest))
            t_emu = float(100-min(emutest))
            t_dep = float(100-min(deptest))
            t_hyb = float(100-min(hybtest))
            t_smu = float(100-min(smutest))
            t_qmu = float(100-min(qmutest))
            
            t_all =  t_qtmp + t_ngr + t_ngre + t_imu + t_emu + t_dep + t_hyb + t_smu + t_qmu
            type_dict = {'REP':t_qtmp, 'NGR':t_ngr, 'NGRE':t_ngre, 'IMU100':t_imu, 'EMU':t_emu, 'DEPT':t_dep, 'HYBRID':t_hyb, 'SMU':t_smu, 'QMU': t_qmu}
            
            return [t_all]+[type_dict.get(uu) for uu in u_list]
        
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
                        if j == 9:
                            sheet.write(idx,j,cell,font_dict.get(entry[2])[3])
                        else:
                            sheet.write(idx,j,cell,font_dict.get(entry[2])[0])
                    # sheet.write_row(idx,0,entry+stablechange,font_dict.get(entry[2])[0])
                    if entry[5] in NON_STABLE_LOCATIONS:
                        sheet.write(idx,5,entry[5],font_dict.get(entry[2])[2])
                    if entry[6] in NON_STABLE_LOCATIONS:
                        sheet.write(idx,6,entry[6],font_dict.get(entry[2])[2])
                        
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
        
        # Formatting
        qtmp = workbook.add_format({'align':'center','bg_color':'#FFB7B7'})
        imu  = workbook.add_format({'align':'center','bg_color':'#FDE9D9'})
        emu  = workbook.add_format({'align':'center','bg_color':'#DAEEF3'})
        ngr  = workbook.add_format({'align':'center','bg_color':'#E4DFEC'})
        ngre = workbook.add_format({'align':'center','bg_color':'#FFFF93'})
        smu  = workbook.add_format({'align':'center','bg_color':'#F2DCDB'})
        dept = workbook.add_format({'align':'center','bg_color':'#EBF1DE'})
        qmu = workbook.add_format({'align':'center','bg_color':"#B7FFDB"})
        
        qtmpbold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#FFB7B7','bottom':1})
        imubold  = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#FDE9D9','bottom':1})
        emubold  = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#DAEEF3','bottom':1})
        ngrbold  = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#E4DFEC','bottom':1})
        ngrebold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#FFFF93','bottom':1})
        smubold  = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#F2DCDB','bottom':1})
        deptbold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#EBF1DE','bottom':1})
        qmubold = workbook.add_format({'align':'center','bg_color':'#B7FFDB','bold':True,'bottom':1})
        
        qtmpboldred = workbook.add_format({'align':'center','bg_color':'#FFB7B7','font_color':'#CC194C', 'bold':True})
        imuboldred  = workbook.add_format({'align':'center','bg_color':'#FDE9D9','font_color':'#CC194C', 'bold':True})
        emuboldred  = workbook.add_format({'align':'center','bg_color':'#DAEEF3','font_color':'#CC194C', 'bold':True})
        ngrboldred  = workbook.add_format({'align':'center','bg_color':'#E4DFEC','font_color':'#CC194C', 'bold':True})
        ngreboldred = workbook.add_format({'align':'center','bg_color':'#FFFF93','font_color':'#CC194C', 'bold':True})
        smuboldred  = workbook.add_format({'align':'center','bg_color':'#F2DCDB','font_color':'#CC194C', 'bold':True})
        deptboldred = workbook.add_format({'align':'center','bg_color':'#EBF1DE','font_color':'#CC194C', 'bold':True})
        qmuboldred = workbook.add_format({'align':'center','bg_color':'#EBF1DE','font_color':'#CC194C', 'bold':True})
        
        qtmpborder = workbook.add_format({'align':'center','bg_color':'#FFB7B7','left':1,'right':1})
        imuborder  = workbook.add_format({'align':'center','bg_color':'#FDE9D9','left':1,'right':1})
        emuborder  = workbook.add_format({'align':'center','bg_color':'#DAEEF3','left':1,'right':1})
        ngrborder  = workbook.add_format({'align':'center','bg_color':'#E4DFEC','left':1,'right':1})
        ngreborder = workbook.add_format({'align':'center','bg_color':'#FFFF93','left':1,'right':1})
        smuborder  = workbook.add_format({'align':'center','bg_color':'#F2DCDB','left':1,'right':1})
        deptborder = workbook.add_format({'align':'center','bg_color':'#EBF1DE','left':1,'right':1})
        qmuborder = workbook.add_format({'align':'center','bg_color':'#EBF1DE','left':1,'right':1})

        
        font_dict = {
            'QMU':    [qmu, qmubold, qmuboldred, qmuborder],
            'REP':    [qtmp,qtmpbold,qtmpboldred,qtmpborder],
            'NGR':    [ngr,ngrbold,ngrboldred,ngrborder],
            'NGRE':   [ngre,ngrebold,ngreboldred,ngreborder],
            'IMU100': [imu,imubold,imuboldred,imuborder],
            'EMU':    [emu,emubold,emuboldred,emuborder],
            'HYBRID': [emu,emubold,emuboldred,emuborder],
            'SMU':    [smu,smubold,smuboldred,smuborder],
            'DEPT':   [dept,deptbold,deptboldred,deptborder]
            }
        
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
        
        
        headers = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Dep/Arr',
                   'Δ (6car)','Count'] + u_list
        
    
        
        # Create a list of legimate stabling options in order to flag any runs that do not end at one of these locations
        
        acceptable_stables = [code 
                            for v in YARDS.values() 
                            for code in v['yards']]

                
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
        #########################################################################################
        #########################################################################################
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
            font = font_dict.get(uu)[1]
            Summary.write(1,row,uu,font)
            row += 3 + n
            Summary.write(1,row,uu,font)
            row += 2 + n
            Summary.write(1,row,uu,font)
        
        stable_capacities = {yard: meta['capacity'] for yard, meta in YARDS.items()}


        stables_dict = {}

        for yard_name in YARDS:
            merged = [merge_out_in_per_day_test(store[yard_name][code]['out'], store[yard_name][code]['in']) for code in SORT_ORDER_WEEK]
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

            monday, tuesday, wednesday, thursday, monthu, friday, saturday, sunday = v

            mon_total, mon_bkdwn = endofdayunitcount(monday)
            tue_total, tue_bkdwn = endofdayunitcount(tuesday)
            wed_total, wed_bkdwn = endofdayunitcount(wednesday)
            thu_total, thu_bkdwn = endofdayunitcount(thursday)
            mth_total, mth_bkdwn = endofdayunitcount(monthu)
            fri_total, fri_bkdwn = endofdayunitcount(friday)
            sat_total, sat_bkdwn = endofdayunitcount(saturday)
            sun_total, sun_bkdwn = endofdayunitcount(sunday)
            
            mon_os_total, mon_os_bkdwn = overnightstabling(monday)
            tue_os_total, tue_os_bkdwn = overnightstabling(tuesday)
            wed_os_total, wed_os_bkdwn = overnightstabling(wednesday)
            thu_os_total, thu_os_bkdwn = overnightstabling(thursday)
            mth_os_total, mth_os_bkdwn = overnightstabling(monthu)
            fri_os_total, fri_os_bkdwn = overnightstabling(friday)
            sat_os_total, sat_os_bkdwn = overnightstabling(saturday)
            sun_os_total, sun_os_bkdwn = overnightstabling(sunday)
        
            
            mon_ip_total, mon_ip_bkdwn = interpeakstabling(monday)
            tue_ip_total, tue_ip_bkdwn = interpeakstabling(tuesday)
            wed_ip_total, wed_ip_bkdwn = interpeakstabling(wednesday)
            thu_ip_total, thu_ip_bkdwn = interpeakstabling(thursday)
            mth_ip_total, mth_ip_bkdwn = interpeakstabling(monthu)
            fri_ip_total, fri_ip_bkdwn = interpeakstabling(friday)
            sat_ip_total, sat_ip_bkdwn = interpeakstabling(saturday)
            sun_ip_total, sun_ip_bkdwn = interpeakstabling(sunday)

            #Use a red font if the total is unbalanced at a stabling location at any point during the week
            unbalanced_totals = any([mon_total,tue_total,wed_total,thu_total,mth_total,fri_total,sat_total,sun_total])
            totals_font = boldborderred if unbalanced_totals else boldborder
            
            # Highlight any stabling location if any unit is unbalanced at any point during the week
            breakdown_list = [mon_bkdwn,tue_bkdwn,wed_bkdwn,thu_bkdwn,mth_bkdwn,fri_bkdwn,sat_bkdwn,sun_bkdwn]
            unbalanced_subtotals = any([any(x) for x in breakdown_list]                 )
            stablefont = boldleftvc_unbalanced if unbalanced_subtotals else boldleftvc


            if ndays == 1:
                Summary.write(firstrow,3+n,None)
                Summary.write(firstrow,6+2*n,None)
            else:
                Summary.merge_range(firstrow,3+n,lastrow,3+n,None)
                Summary.merge_range(firstrow,6+2*n,lastrow,6+2*n,None)


            if ndays == 1:
                Summary.write(firstrow, 0,   k,                        stablefont)
                Summary.write(firstrow, 4+n, stable_capacities.get(k), boldcentervc14  )
            else:
                Summary.merge_range(firstrow,0,   lastrow, 0,   k,                        stablefont)
                Summary.merge_range(firstrow,4+n, lastrow, 4+n, stable_capacities.get(k), boldcentervc14)  
                
            # Write days
            # Old: [weekdaykey_dict.get(d) for d in d_list]
            Summary.write_column(firstrow, 1, [WEEKDAY_KEYS_MASTER.get(d, {}).get('short') for d in d_list])


            summary_dict = {
                '64':  (monday,    mon_total,mon_bkdwn,mon_os_total,mon_os_bkdwn,mon_ip_total,mon_ip_bkdwn),
                '32':  (tuesday,   tue_total,tue_bkdwn,tue_os_total,tue_os_bkdwn,tue_ip_total,tue_ip_bkdwn),
                '16':  (wednesday, wed_total,wed_bkdwn,wed_os_total,wed_os_bkdwn,wed_ip_total,wed_ip_bkdwn), 
                '8':   (thursday,  thu_total,thu_bkdwn,thu_os_total,thu_os_bkdwn,thu_ip_total,thu_ip_bkdwn),
                '120': (monthu,    mth_total,mth_bkdwn,mth_os_total,mth_os_bkdwn,mth_ip_total,mth_ip_bkdwn),
                '4':   (friday,    fri_total,fri_bkdwn,fri_os_total,fri_os_bkdwn,fri_ip_total,fri_ip_bkdwn),
                '2':   (saturday,  sat_total,sat_bkdwn,sat_os_total,sat_os_bkdwn,sat_ip_total,sat_ip_bkdwn),
                '1':   (sunday,    sun_total,sun_bkdwn,sun_os_total,sun_os_bkdwn,sun_ip_total,sun_ip_bkdwn)
               }


            row_ptr = firstrow # local pointer so we don't clobber firstrow used above
            yard_days_present = [d for d, info in summary_dict.items() if info[0] is not None]

            for DoW, summary_info in summary_dict.items():
                day_obj, total, breakdown, os_total, os_breakdown, ip_total, ip_breakdown = summary_info

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
        
        steps_col = [
            '1. Determine the location where each Run starts and finishes.',
            '2. By Unit type by Day, count the number of Runs that start or finish at each location.',
            '3. Find where start and finish counts do not match over the day.',
            '4. Find where start and finish counts do not match over the week.'
            ]
        

        singletrip_col = build_singletrip_col(d_list, run_dict)
        runs_without_stable = find_runs_without_stable(run_dict, acceptable_stables)
        
        Info.write_column('A1',info_col,boldright)
        Info.write_column('B1',info_col2)
        Info.write_column('A7',steps_col,boldleft)
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
        
        # Manly.activate()    
        # Caboolture.activate()
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
    path = gui.select_file(

    caption="Select RSX file",
    directory="",
    filter_str="RSX Files (*.rsx);;All Files (*.*)")

    TTS_SC(path)