import xlsxwriter # LT change
import re
import os
import sys
import time
import shutil
from datetime import datetime
import xml.etree.ElementTree as ET

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import traceback
import logging


OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True








weekdaykey_dict  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}

wkdk_rename = {
    ('120',):    'Mon-Thu',
    ('120','64'):'Mon',
    ('120','32'):'Tue',
    ('120','16'):'Wed',
    ('120','8'): 'Thu',
    ('4',):      'Fri',
    ('2',):      'Sat',
    ('1',):      'Sun'
    }  



# To be displayed in red font if a run starts or finishes at one of these non-stable locations
nonstables = ['IPS','MNY','CAB','NBR','GYN','RS','BHI']


headers1 = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Start Time', '# Sets','# SetsByUnit']
headers2 = ['Run','Day','Unit','Cars','Trips','Origin','Dest','Finish Time', '# Sets','# SetsByUnit']







def TTS_SB(path, mypath = None):

    copyfile = '\\'.join(path.split('/')[0:-1]) != mypath and mypath is not None

    try:

        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]    
        
        if __name__ == "__main__":
            print(filename,'\n')
       
        tree = ET.parse(filename)
        root = tree.getroot()
        
        filename = filename[:-4]
        filename_xlsx = f'StablingBalance-{filename}.xlsx'
        workbook = xlsxwriter.Workbook(filename_xlsx)
        
        
        
        
        
        ### Check for duplicate train numbers before executing the script
        ### Print warning for user if duplicates exist
        ### Print out all duplicates
        weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
        tn_list = []
        tn_doubles = []
        for train in root.iter('train'):
            tn  = train.attrib['number']; day = train[0][0][0].attrib['weekdayKey']
            if (tn,day) in tn_list: tn_doubles.append((tn,day))
            tn_list.append((tn,day))
                
        if tn_doubles:
            print('           Error: Duplicate train numbers')
            for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit() 
        
        
        start_time = time.time()
        
        runs_without_stable = []
        
        
        
        
        # Run an initial loop through the rsx to find:
        # - a list of days
        # - a list of units
        u_list = []
        d_list = []
        for train in root.iter('train'):
            tn  = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries = [x for x in train.iter('entry')]
            origin = entries[0].attrib
            destin = entries[-1].attrib
            unit   = origin['trainTypeId'].split('-',1)[1]
            if unit not in u_list:
                u_list.append(unit)
            if WeekdayKey not in d_list:
                d_list.append(WeekdayKey)
                
                
        # Sort the day and unit lists
        # Remove mon-thu (120) if individual mon,tue,wed,thu days exist within the rsx
        SORT_ORDER_WEEK = ['64','32','16','8','120','4','2','1'] 
        SORT_ORDER_UNIT = ['REP','NGR', 'NGRE','IMU100','EMU','SMU','HYBRID', 'ICE', 'DEPT']
        d_list.sort(key=SORT_ORDER_WEEK.index)
        u_list.sort(key=SORT_ORDER_UNIT.index)
        weekdays = set(d_list).intersection({'8','16','32','64'})
        if weekdays and '120' in d_list:
            d_list.remove('120')
        ndays = len(d_list)
        n     = len(u_list)
        # print('days: ',d_list)
        # print('units:',u_list)
            
        
        
        # Run a second loop through the rsx to create:
        # - a dictionary using (run,weekdaykey) as a unique key, build the run infomation
        run_dict = {}
        for train in root.iter('train'):
            tn         = train.attrib['number']
            WeekdayKey = train[0][0][0].attrib['weekdayKey']
            entries    = [x for x in train.iter('entry')]
            origin     = entries[0].attrib
            destin     = entries[-1].attrib
            traintype  = origin['trainTypeId']
            unit       = origin['trainTypeId'].split('-',1)[1]
            lineID     = train.attrib['lineID']
            run        = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
            oID        = origin['stationID']
            dID        = destin['stationID']
            odep       = origin['departure']
            ddep       = destin['departure']
            cars       = int(re.findall(r'\d+', traintype)[0])
            
            if not run_dict.get((run,WeekdayKey)):
                trips = 1
                run_dict[(run,WeekdayKey)] = [unit,cars,trips,oID,dID,odep,ddep,[tn]]
            else:
                run_dict[(run,WeekdayKey)][2] += 1
                run_dict[(run,WeekdayKey)][4] = dID
                run_dict[(run,WeekdayKey)][6] = ddep
                run_dict[(run,WeekdayKey)][-1].append(tn) 
        
        
        def timetrim(timestring):
            """ Format converter from hh:mm:ss to [h]:mm """
            
            if type(timestring) == list:
                timestring = timestring[0]
            if timestring is None or timestring.isalpha() or ':' not in timestring:
                pass
                
            
            elif timestring[0] == '0':
                timestring = timestring[1:-3]
            else: timestring = timestring[:-3]
            return timestring
        
        
        def csl(string):
            """ Returns all unique elements separated by commas """
            
            output = []
            for x in string:
                if x not in output:
                    output.append(x)
            return ','.join(output)
        
        
        def writecell_unbalanced(r,c,value,unbalancedfont,balancedfont):
            """ If cell does not equal zero, assign a cell format to highlight inbalance """
            
            if value != 0:
                Summary.write(r,c,value,unbalancedfont)
            else:
                Summary.write(r,c,value,balancedfont)
                
                
        def write_runs(sheet,daylist,r,c):
            """ 
            Writes either the runs coming out of or the runs coming in to the stabling yard
            Must be called twice for each day to compare unit and total balances
            """
            
            if daylist:
                
                # Write runs using individual unittype cell formatting
                for idx,line in enumerate(daylist,r):
                    sheet.write_row(idx,c,line,font_dict.get(line[2])[0])
                    
                    # Use red font if run ends at a station not a stabling yard
                    if line[5] in nonstables:
                        sheet.write(idx,c+5,line[5],font_dict.get(line[2])[4])
                    if line[6] in nonstables:
                        sheet.write(idx,c+6,line[6],font_dict.get(line[2])[4])
             
        
        def write_unit_totals(sheet, sum_of_units, n_units, r, c, font):
            """ 
            Used in write_day function, writes the last column in both in and out blocks,
            If only one entry of a unit type, will skip the merge-range step as this will error
            """
            if n_units == 1:
                sheet.write(r, c, sum_of_units, font)
            else:
                sheet.merge_range(r, c, r+n_units-1, c, sum_of_units, font)    
            
            
        
        
        def build_daylists(daylist_out,daylist_in, wkdk, stable):
            """ 
            From the list of all runs, 
            narrows down runs that either start or end at a particular stabling location, 
            for that particular day of operation,
            and appends that run to the associated in or out list,
            depending on whether the run is starting at the stable or ending there
            """
            
            DoO = wkdk_rename.get(wkdk)
            for k,v in run_dict.items():
                
                
                
                run       = k[0]
                D_o_run   = k[1]
                
                unit      = v[0]
                cars      = v[1]
                trips     = v[2]
                start_sID = v[3]
                end_sID   = v[4]
                start_t   = v[5]
                finish_t  = v[6]
                
                
                if unit == 'NGR':
                    delta = 1
                else:
                    delta = 2 if cars == 6 else 1
                # delta = 2 if cars == 6 else 1
                
                
                
                if D_o_run in wkdk:
                    if start_sID in stable:
                        daylist_out.append([ run, DoO, unit, cars, trips, start_sID, end_sID, start_t, delta ])
                    
                    if end_sID in stable:
                        daylist_in.append([ run, DoO, unit, cars, trips, start_sID, end_sID, finish_t, delta ])
        
                        
            daylist_out.sort(key=lambda val: val[7])
            daylist_in.sort(key=lambda val: val[7])
            daylist_out.sort(key=lambda val: {x:SORT_ORDER_UNIT.index(x) for x in SORT_ORDER_UNIT}[val[2]])
            daylist_in.sort(key=lambda val: {x:SORT_ORDER_UNIT.index(x) for x in SORT_ORDER_UNIT}[val[2]])
            
            for x in daylist_out: x[7] = timetrim(x[7])
            for x in daylist_in: x[7] = timetrim(x[7])
            
            
        def build_weeklists(mon_out,tue_out,wed_out,thu_out,mth_out,fri_out,sat_out,sun_out,   mon_in,tue_in,wed_in,thu_in,mth_in,fri_in,sat_in,sun_in,    stableoptions):
            """ Runs the build_daylists function for a full week """
            
            if weekdays:
                build_daylists(mon_out, mon_in, ('120','64'),stableoptions) 
                build_daylists(tue_out, tue_in, ('120','32'),stableoptions) 
                build_daylists(wed_out, wed_in, ('120','16'),stableoptions) 
                build_daylists(thu_out, thu_in, ('120','8'),stableoptions) 
            else: build_daylists(mth_out, mth_in, ('120',),stableoptions)  
            build_daylists(fri_out, fri_in, ('4',),stableoptions)
            build_daylists(sat_out, sat_in, ('2',),stableoptions)
            build_daylists(sun_out, sun_in, ('1',),stableoptions)    
            
        
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
                
                n_unit_out   = BD_out[ttype][0] if BD_out.get(ttype) else 1
                sum_unit_out = BD_out[ttype][1] if BD_out.get(ttype) else 0
                
                n_unit_in    = BD_in[ttype][0]  if BD_in.get(ttype) else 1
                sum_unit_in  = BD_in[ttype][1]  if BD_in.get(ttype) else 0
                
                
                
                BDogt = BD_out.get(ttype)
                BDigt = BD_in.get(ttype)
                if BDogt != BDigt:
                    font = font_dict.get(ttype)[3]
                    if BDogt:
                        write_unit_totals(sheet, sum_unit_out, n_unit_out, out_row, widecol1,  font)
                        out_row += n_unit_out
                    if BDigt:
                        write_unit_totals(sheet, sum_unit_in, n_unit_in, in_row, widecol2, font)
                        in_row += n_unit_in
                    
                else:
                    font = font_dict.get(ttype)[2]
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
            
        
        
        
        
                
        
        
        
        
        
        # Formatting
        #########################################################################################
        #########################################################################################
        qtmp = workbook.add_format({'align':'center','bg_color':'#FFB7B7'})
        ngr  = workbook.add_format({'align':'center','bg_color':'#E4DFEC'})
        ngre = workbook.add_format({'align':'center','bg_color':'#FFFF93'})
        imu  = workbook.add_format({'align':'center','bg_color':'#FDE9D9'})
        emu  = workbook.add_format({'align':'center','bg_color':'#DAEEF3'})
        smu  = workbook.add_format({'align':'center','bg_color':'#F2DCDB'})
        dept = workbook.add_format({'align':'center','bg_color':'#EBF1DE'})
        
        # qtmpred = workbook.add_format({'align':'center','bg_color':'#FFB7B7','font_color':'#CC194C'})
        # ngrred  = workbook.add_format({'align':'center','bg_color':'#E4DFEC','font_color':'#CC194C'})
        # imured  = workbook.add_format({'align':'center','bg_color':'#FDE9D9','font_color':'#CC194C'})
        # emured  = workbook.add_format({'align':'center','bg_color':'#DAEEF3','font_color':'#CC194C'})
        # smured  = workbook.add_format({'align':'center','bg_color':'#F2DCDB','font_color':'#CC194C'})
        # deptred = workbook.add_format({'align':'center','bg_color':'#EBF1DE','font_color':'#CC194C'})
        
        qtmpbold = workbook.add_format({'align':'center','bg_color':'#FFB7B7','bold':True,'bottom':1})
        ngrbold  = workbook.add_format({'align':'center','bg_color':'#E4DFEC','bold':True,'bottom':1})
        ngrebold = workbook.add_format({'align':'center','bg_color':'#FFFF93','bold':True,'bottom':1})
        imubold  = workbook.add_format({'align':'center','bg_color':'#FDE9D9','bold':True,'bottom':1})
        emubold  = workbook.add_format({'align':'center','bg_color':'#DAEEF3','bold':True,'bottom':1})
        smubold  = workbook.add_format({'align':'center','bg_color':'#F2DCDB','bold':True,'bottom':1})
        deptbold = workbook.add_format({'align':'center','bg_color':'#EBF1DE','bold':True,'bottom':1})
        
        qtmpbig = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FFB7B7','font_size':16})
        ngrbig  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#E4DFEC','font_size':16})
        ngrebig = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FFFF93','font_size':16})
        imubig  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FDE9D9','font_size':16})
        emubig  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#DAEEF3','font_size':16})
        smubig  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#F2DCDB','font_size':16})
        deptbig = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#EBF1DE','font_size':16})
        
        qtmpbigred = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FFB7B7','font_color':'#CC194C','font_size':16})
        ngrbigred  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#E4DFEC','font_color':'#CC194C','font_size':16})
        ngrebigred = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FFFF93','font_color':'#CC194C','font_size':16})
        imubigred  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#FDE9D9','font_color':'#CC194C','font_size':16})
        emubigred  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#DAEEF3','font_color':'#CC194C','font_size':16})
        smubigred  = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#F2DCDB','font_color':'#CC194C','font_size':16})
        deptbigred = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'#EBF1DE','font_color':'#CC194C','font_size':16})
        
        qtmpboldred = workbook.add_format({'align':'center','bg_color':'#FFB7B7','font_color':'#CC194C', 'bold':True})
        ngrboldred  = workbook.add_format({'align':'center','bg_color':'#E4DFEC','font_color':'#CC194C', 'bold':True})
        ngreboldred = workbook.add_format({'align':'center','bg_color':'#FFFF93','font_color':'#CC194C', 'bold':True})
        imuboldred  = workbook.add_format({'align':'center','bg_color':'#FDE9D9','font_color':'#CC194C', 'bold':True})
        emuboldred  = workbook.add_format({'align':'center','bg_color':'#DAEEF3','font_color':'#CC194C', 'bold':True})
        smuboldred  = workbook.add_format({'align':'center','bg_color':'#F2DCDB','font_color':'#CC194C', 'bold':True})
        deptboldred = workbook.add_format({'align':'center','bg_color':'#EBF1DE','font_color':'#CC194C', 'bold':True})
        
        
        # size16vc = workbook.add_format({'font_size':16,'align':'center','valign':'vcenter'})
        
        
        font_dict = {
            'REP':    [qtmp,qtmpbold,qtmpbig,qtmpbigred,qtmpboldred],
            'NGR':    [ngr,ngrbold,ngrbig,ngrbigred,ngrboldred],
            'NGRE':   [ngre,ngrebold,ngrebig,ngrebigred,ngreboldred],
            'IMU100': [imu,imubold,imubig,imubigred,imuboldred],
            'EMU':    [emu,emubold,emubig,emubigred,emuboldred],
            'HYBRID': [emu,emubold,emubig,emubigred,emuboldred],
            'SMU':    [smu,smubold,smubig,smubigred,smuboldred],
            'DEPT':   [dept,deptbold,deptbig,deptbigred,deptboldred]
            }
        
        title                   = workbook.add_format({'bold':True,'align':'center'})
        header                  = workbook.add_format({'bold':True,'align':'center','bg_color':'#CCCCCC'})
        # size14                  = workbook.add_format({'font_size':16})
        size16                  = workbook.add_format({'font_size':16})
        
        boldleft                = workbook.add_format({'bold':True,'align':'left'})
        # boldcenter              = workbook.add_format({'bold':True,'align':'center'})
        boldright               = workbook.add_format({'bold':True,'align':'right'})
        # greyedouttext           = workbook.add_format({'align':'center','font_color':'#666666'})
        centered                = workbook.add_format({'align':'center'})
        redcentered             = workbook.add_format({'align':'center','font_color':'#CC194C'})
        redboldleft             = workbook.add_format({'bold':True,'align':'left','font_color':'#CC194C'})
        redleft                 = workbook.add_format({'align':'left','font_color':'#CC194C'})
        
        leftborder              = workbook.add_format({'left':1,'align':'center'})
        boldbottomleftborder    = workbook.add_format({'left':1,'bottom':1,'align':'center','bold':True})
        # leftborderred           = workbook.add_format({'left':1,'align':'center','font_color':'#CC194C'})
        leftborder_unbalanced   = workbook.add_format({'left':1,'align':'center','bg_color':'#CCB233'})
        
        topleftborder           = workbook.add_format({'top':1,'left':1,'align':'center'})
        # topleftborderredfont    = workbook.add_format({'top':1,'left':1,'align':'center','font_color':'#CC194C'})
        topleftborderredbg      = workbook.add_format({'top':1,'left':1,'align':'center','font_color':'#FFFFFF','bg_color':'#CC194C'})
        
        topborder               = workbook.add_format({'top':1,'align':'center'})
        topborder_unbalanced    = workbook.add_format({'top':1,'align':'center','font_color':'#FFFFFF','bg_color':'#CC194C'})
        boldtopborder           = workbook.add_format({'top':1, 'bold':True,'align':'center'})
        
        
        boldleftvc              = workbook.add_format({'bold':True,'align':'left','valign':'vcenter'})
        boldleftvc_unbalanced_b = workbook.add_format({'bold':True,'align':'left','valign':'vcenter','bg_color':'#CCB233'})
        boldleftvc_unbalanced_r = workbook.add_format({'bold':True,'align':'left','valign':'vcenter','bg_color':'#CC194C'}) 
        # boldcentervc14          = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':14})
        
        # border                  = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','font_size':14})
        border16                = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','font_size':16})
        # tborder                 = workbook.add_format({'border':2, 'border_color':'#000000', 'align':'center','font_size':14})
        # rborder                 = workbook.add_format({'border':1, 'border_color':'#CC194C', 'align':'center','font_size':14,'font_color':'#CC194C'})
        rborder16               = workbook.add_format({'border':1, 'border_color':'#CC194C', 'align':'center','font_size':16,'font_color':'#CC194C'})
        
        # boldborder              = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','bold':True})
        # boldborderred           = workbook.add_format({'border':1, 'border_color':'#000000', 'align':'center','bold':True,'font_color':'#FF0000'})
        
        
        top                     = workbook.add_format({'top':1})
        bottom                  = workbook.add_format({'bottom':1})
        
        
        
        
        
        
        wfeoptions  = ['WFE','WFW','FEE']
        ipssoptions = ['IPSS','IPS']
        rdksoptions = ['RDKS']
        robsoptions = ['ROBS']
        mnyoptions  = ['MNY']
        bnhsoptions = ['BNHS']
        etsoptions  = ['ETB','ETF','ETS','MWS','RS','BHI']
        ynoptions   = ['YN','MNS']
        mesoptions  = ['MES']
        petsoptions = ['PETS']
        kprsoptions = ['KPRS']
        caewoptions = ['CAE','CAW','CAB']
        emhsoptions = ['EMHS']
        wobsoptions = ['WOBS']
        nbroptions  = ['NBR']
        gynoptions  = ['GYN']
        bqysoptions = ['BQYS']
        cpmoptions  = ['CPM']
        ormsoptions = ['ORMS']
        bwhsoptions = ['BWHS']
        
        
        
        # Create a list of acceptable locations to end a run
        acceptable_stables = []
        s_yards = [wfeoptions,ipssoptions,rdksoptions,robsoptions,mnyoptions,bnhsoptions,etsoptions,ynoptions,mesoptions,petsoptions,kprsoptions,caewoptions,emhsoptions,wobsoptions,nbroptions,gynoptions,bqysoptions,cpmoptions,ormsoptions,bwhsoptions]
        for x in s_yards:
                for y in x: acceptable_stables.append(y)
        acceptable_stables.remove('RS')
        acceptable_stables.remove('BHI')
        
        
        # Initialise in and out lists for each day, for each stabling yard
        # Will be filled with runs on that particular day, starting or ending at that particular stabling location
        wfe_mon_out = []; wfe_mon_in = []; 
        wfe_tue_out = []; wfe_tue_in = []; 
        wfe_wed_out = []; wfe_wed_in = []; 
        wfe_thu_out = []; wfe_thu_in = []; 
        wfe_mth_out = []; wfe_mth_in = []; 
        wfe_fri_out = []; wfe_fri_in = []; 
        wfe_sat_out = []; wfe_sat_in = []; 
        wfe_sun_out = []; wfe_sun_in = []; 
        
        ipss_mon_out = []; ipss_mon_in = []; 
        ipss_tue_out = []; ipss_tue_in = []; 
        ipss_wed_out = []; ipss_wed_in = []; 
        ipss_thu_out = []; ipss_thu_in = []; 
        ipss_mth_out = []; ipss_mth_in = []; 
        ipss_fri_out = []; ipss_fri_in = []; 
        ipss_sat_out = []; ipss_sat_in = []; 
        ipss_sun_out = []; ipss_sun_in = []; 
        
        rdks_mon_out = []; rdks_mon_in = []; 
        rdks_tue_out = []; rdks_tue_in = []; 
        rdks_wed_out = []; rdks_wed_in = []; 
        rdks_thu_out = []; rdks_thu_in = []; 
        rdks_mth_out = []; rdks_mth_in = []; 
        rdks_fri_out = []; rdks_fri_in = []; 
        rdks_sat_out = []; rdks_sat_in = []; 
        rdks_sun_out = []; rdks_sun_in = []; 
        
        robs_mon_out = []; robs_mon_in = []; 
        robs_tue_out = []; robs_tue_in = []; 
        robs_wed_out = []; robs_wed_in = []; 
        robs_thu_out = []; robs_thu_in = []; 
        robs_mth_out = []; robs_mth_in = []; 
        robs_fri_out = []; robs_fri_in = []; 
        robs_sat_out = []; robs_sat_in = []; 
        robs_sun_out = []; robs_sun_in = []; 
        
        mny_mon_out = []; mny_mon_in = []; 
        mny_tue_out = []; mny_tue_in = []; 
        mny_wed_out = []; mny_wed_in = [];
        mny_thu_out = []; mny_thu_in = []; 
        mny_mth_out = []; mny_mth_in = []; 
        mny_fri_out = []; mny_fri_in = []; 
        mny_sat_out = []; mny_sat_in = []; 
        mny_sun_out = []; mny_sun_in = []; 
        
        bnhs_mon_out = []; bnhs_mon_in = []; 
        bnhs_tue_out = []; bnhs_tue_in = []; 
        bnhs_wed_out = []; bnhs_wed_in = []; 
        bnhs_thu_out = []; bnhs_thu_in = []; 
        bnhs_mth_out = []; bnhs_mth_in = []; 
        bnhs_fri_out = []; bnhs_fri_in = []; 
        bnhs_sat_out = []; bnhs_sat_in = []; 
        bnhs_sun_out = []; bnhs_sun_in = []; 
        
        ets_mon_out = []; ets_mon_in = []; 
        ets_tue_out = []; ets_tue_in = [];
        ets_wed_out = []; ets_wed_in = [];
        ets_thu_out = []; ets_thu_in = []; 
        ets_mth_out = []; ets_mth_in = []; 
        ets_fri_out = []; ets_fri_in = []; 
        ets_sat_out = []; ets_sat_in = []; 
        ets_sun_out = []; ets_sun_in = []; 
        
        yn_mon_out = []; yn_mon_in = []; 
        yn_tue_out = []; yn_tue_in = []; 
        yn_wed_out = []; yn_wed_in = []; 
        yn_thu_out = []; yn_thu_in = []; 
        yn_mth_out = []; yn_mth_in = []; 
        yn_fri_out = []; yn_fri_in = []; 
        yn_sat_out = []; yn_sat_in = []; 
        yn_sun_out = []; yn_sun_in = [];
        
        mes_mon_out = []; mes_mon_in = []; 
        mes_tue_out = []; mes_tue_in = []; 
        mes_wed_out = []; mes_wed_in = []; 
        mes_thu_out = []; mes_thu_in = []; 
        mes_mth_out = []; mes_mth_in = []; 
        mes_fri_out = []; mes_fri_in = []; 
        mes_sat_out = []; mes_sat_in = []; 
        mes_sun_out = []; mes_sun_in = [];
        
        pets_mon_out = []; pets_mon_in = []; 
        pets_tue_out = []; pets_tue_in = []; 
        pets_wed_out = []; pets_wed_in = []; 
        pets_thu_out = []; pets_thu_in = []; 
        pets_mth_out = []; pets_mth_in = []; 
        pets_fri_out = []; pets_fri_in = []; 
        pets_sat_out = []; pets_sat_in = []; 
        pets_sun_out = []; pets_sun_in = [];
        
        kprs_mon_out = []; kprs_mon_in = []; 
        kprs_tue_out = []; kprs_tue_in = []; 
        kprs_wed_out = []; kprs_wed_in = []; 
        kprs_thu_out = []; kprs_thu_in = []; 
        kprs_mth_out = []; kprs_mth_in = []; 
        kprs_fri_out = []; kprs_fri_in = []; 
        kprs_sat_out = []; kprs_sat_in = []; 
        kprs_sun_out = []; kprs_sun_in = []; 
        
        caew_mon_out = []; caew_mon_in = []; 
        caew_tue_out = []; caew_tue_in = []; 
        caew_wed_out = []; caew_wed_in = []; 
        caew_thu_out = []; caew_thu_in = []; 
        caew_mth_out = []; caew_mth_in = []; 
        caew_fri_out = []; caew_fri_in = []; 
        caew_sat_out = []; caew_sat_in = []; 
        caew_sun_out = []; caew_sun_in = []; 
        
        emhs_mon_out = []; emhs_mon_in = []; 
        emhs_tue_out = []; emhs_tue_in = []; 
        emhs_wed_out = []; emhs_wed_in = []; 
        emhs_thu_out = []; emhs_thu_in = []; 
        emhs_mth_out = []; emhs_mth_in = []; 
        emhs_fri_out = []; emhs_fri_in = []; 
        emhs_sat_out = []; emhs_sat_in = []; 
        emhs_sun_out = []; emhs_sun_in = [];
        
        wobs_mon_out = []; wobs_mon_in = []; 
        wobs_tue_out = []; wobs_tue_in = []; 
        wobs_wed_out = []; wobs_wed_in = []; 
        wobs_thu_out = []; wobs_thu_in = []; 
        wobs_mth_out = []; wobs_mth_in = []; 
        wobs_fri_out = []; wobs_fri_in = []; 
        wobs_sat_out = []; wobs_sat_in = []; 
        wobs_sun_out = []; wobs_sun_in = []; 
        
        nbr_mon_out = []; nbr_mon_in = []; 
        nbr_tue_out = []; nbr_tue_in = []; 
        nbr_wed_out = []; nbr_wed_in = []; 
        nbr_thu_out = []; nbr_thu_in = []; 
        nbr_mth_out = []; nbr_mth_in = []; 
        nbr_fri_out = []; nbr_fri_in = []; 
        nbr_sat_out = []; nbr_sat_in = []; 
        nbr_sun_out = []; nbr_sun_in = []; 
        
        gyn_mon_out = []; gyn_mon_in = []; 
        gyn_tue_out = []; gyn_tue_in = []; 
        gyn_wed_out = []; gyn_wed_in = []; 
        gyn_thu_out = []; gyn_thu_in = []; 
        gyn_mth_out = []; gyn_mth_in = []; 
        gyn_fri_out = []; gyn_fri_in = []; 
        gyn_sat_out = []; gyn_sat_in = []; 
        gyn_sun_out = []; gyn_sun_in = []; 
        
        bqys_mon_out = []; bqys_mon_in = []; 
        bqys_tue_out = []; bqys_tue_in = []; 
        bqys_wed_out = []; bqys_wed_in = []; 
        bqys_thu_out = []; bqys_thu_in = []; 
        bqys_mth_out = []; bqys_mth_in = []; 
        bqys_fri_out = []; bqys_fri_in = []; 
        bqys_sat_out = []; bqys_sat_in = []; 
        bqys_sun_out = []; bqys_sun_in = []; 
        
        cpm_mon_out = []; cpm_mon_in = []; 
        cpm_tue_out = []; cpm_tue_in = []; 
        cpm_wed_out = []; cpm_wed_in = []; 
        cpm_thu_out = []; cpm_thu_in = []; 
        cpm_mth_out = []; cpm_mth_in = []; 
        cpm_fri_out = []; cpm_fri_in = []; 
        cpm_sat_out = []; cpm_sat_in = []; 
        cpm_sun_out = []; cpm_sun_in = [];
        
        orms_mon_out = []; orms_mon_in = []; 
        orms_tue_out = []; orms_tue_in = []; 
        orms_wed_out = []; orms_wed_in = []; 
        orms_thu_out = []; orms_thu_in = []; 
        orms_mth_out = []; orms_mth_in = []; 
        orms_fri_out = []; orms_fri_in = []; 
        orms_sat_out = []; orms_sat_in = []; 
        orms_sun_out = []; orms_sun_in = [];
        
        bwhs_mon_out = []; bwhs_mon_in = []; 
        bwhs_tue_out = []; bwhs_tue_in = []; 
        bwhs_wed_out = []; bwhs_wed_in = []; 
        bwhs_thu_out = []; bwhs_thu_in = []; 
        bwhs_mth_out = []; bwhs_mth_in = []; 
        bwhs_fri_out = []; bwhs_fri_in = []; 
        bwhs_sat_out = []; bwhs_sat_in = []; 
        bwhs_sun_out = []; bwhs_sun_in = [];
        
        
        # Fill the empty lists with runs given it starts or finishes at one of the options
        build_weeklists(wfe_mon_out,wfe_tue_out,wfe_wed_out,wfe_thu_out,wfe_mth_out,wfe_fri_out,wfe_sat_out,wfe_sun_out,           wfe_mon_in,wfe_tue_in,wfe_wed_in,wfe_thu_in,wfe_mth_in,wfe_fri_in,wfe_sat_in,wfe_sun_in,            wfeoptions)
        build_weeklists(ipss_mon_out,ipss_tue_out,ipss_wed_out,ipss_thu_out,ipss_mth_out,ipss_fri_out,ipss_sat_out,ipss_sun_out,   ipss_mon_in,ipss_tue_in,ipss_wed_in,ipss_thu_in,ipss_mth_in,ipss_fri_in,ipss_sat_in,ipss_sun_in,    ipssoptions)
        build_weeklists(rdks_mon_out,rdks_tue_out,rdks_wed_out,rdks_thu_out,rdks_mth_out,rdks_fri_out,rdks_sat_out,rdks_sun_out,   rdks_mon_in,rdks_tue_in,rdks_wed_in,rdks_thu_in,rdks_mth_in,rdks_fri_in,rdks_sat_in,rdks_sun_in,    rdksoptions)
        build_weeklists(robs_mon_out,robs_tue_out,robs_wed_out,robs_thu_out,robs_mth_out,robs_fri_out,robs_sat_out,robs_sun_out,   robs_mon_in,robs_tue_in,robs_wed_in,robs_thu_in,robs_mth_in,robs_fri_in,robs_sat_in,robs_sun_in,    robsoptions)
        build_weeklists(mny_mon_out,mny_tue_out,mny_wed_out,mny_thu_out,mny_mth_out,mny_fri_out,mny_sat_out,mny_sun_out,           mny_mon_in,mny_tue_in,mny_wed_in,mny_thu_in,mny_mth_in,mny_fri_in,mny_sat_in,mny_sun_in,            mnyoptions)
        build_weeklists(bnhs_mon_out,bnhs_tue_out,bnhs_wed_out,bnhs_thu_out,bnhs_mth_out,bnhs_fri_out,bnhs_sat_out,bnhs_sun_out,   bnhs_mon_in,bnhs_tue_in,bnhs_wed_in,bnhs_thu_in,bnhs_mth_in,bnhs_fri_in,bnhs_sat_in,bnhs_sun_in,    bnhsoptions)
        build_weeklists(ets_mon_out,ets_tue_out,ets_wed_out,ets_thu_out,ets_mth_out,ets_fri_out,ets_sat_out,ets_sun_out,           ets_mon_in,ets_tue_in,ets_wed_in,ets_thu_in,ets_mth_in,ets_fri_in,ets_sat_in,ets_sun_in,            etsoptions)
        build_weeklists(yn_mon_out,yn_tue_out,yn_wed_out,yn_thu_out,yn_mth_out,yn_fri_out,yn_sat_out,yn_sun_out,                   yn_mon_in,yn_tue_in,yn_wed_in,yn_thu_in,yn_mth_in,yn_fri_in,yn_sat_in,yn_sun_in,                    ynoptions)
        build_weeklists(mes_mon_out,mes_tue_out,mes_wed_out,mes_thu_out,mes_mth_out,mes_fri_out,mes_sat_out,mes_sun_out,           mes_mon_in,mes_tue_in,mes_wed_in,mes_thu_in,mes_mth_in,mes_fri_in,mes_sat_in,mes_sun_in,            mesoptions)
        build_weeklists(pets_mon_out,pets_tue_out,pets_wed_out,pets_thu_out,pets_mth_out,pets_fri_out,pets_sat_out,pets_sun_out,   pets_mon_in,pets_tue_in,pets_wed_in,pets_thu_in,pets_mth_in,pets_fri_in,pets_sat_in,pets_sun_in,    petsoptions)
        build_weeklists(kprs_mon_out,kprs_tue_out,kprs_wed_out,kprs_thu_out,kprs_mth_out,kprs_fri_out,kprs_sat_out,kprs_sun_out,   kprs_mon_in,kprs_tue_in,kprs_wed_in,kprs_thu_in,kprs_mth_in,kprs_fri_in,kprs_sat_in,kprs_sun_in,    kprsoptions)
        build_weeklists(caew_mon_out,caew_tue_out,caew_wed_out,caew_thu_out,caew_mth_out,caew_fri_out,caew_sat_out,caew_sun_out,   caew_mon_in,caew_tue_in,caew_wed_in,caew_thu_in,caew_mth_in,caew_fri_in,caew_sat_in,caew_sun_in,    caewoptions)
        build_weeklists(emhs_mon_out,emhs_tue_out,emhs_wed_out,emhs_thu_out,emhs_mth_out,emhs_fri_out,emhs_sat_out,emhs_sun_out,   emhs_mon_in,emhs_tue_in,emhs_wed_in,emhs_thu_in,emhs_mth_in,emhs_fri_in,emhs_sat_in,emhs_sun_in,    emhsoptions)
        build_weeklists(wobs_mon_out,wobs_tue_out,wobs_wed_out,wobs_thu_out,wobs_mth_out,wobs_fri_out,wobs_sat_out,wobs_sun_out,   wobs_mon_in,wobs_tue_in,wobs_wed_in,wobs_thu_in,wobs_mth_in,wobs_fri_in,wobs_sat_in,wobs_sun_in,    wobsoptions)
        build_weeklists(nbr_mon_out,nbr_tue_out,nbr_wed_out,nbr_thu_out,nbr_mth_out,nbr_fri_out,nbr_sat_out,nbr_sun_out,           nbr_mon_in,nbr_tue_in,nbr_wed_in,nbr_thu_in,nbr_mth_in,nbr_fri_in,nbr_sat_in,nbr_sun_in,            nbroptions)
        build_weeklists(gyn_mon_out,gyn_tue_out,gyn_wed_out,gyn_thu_out,gyn_mth_out,gyn_fri_out,gyn_sat_out,gyn_sun_out,           gyn_mon_in,gyn_tue_in,gyn_wed_in,gyn_thu_in,gyn_mth_in,gyn_fri_in,gyn_sat_in,gyn_sun_in,            gynoptions)
        build_weeklists(bqys_mon_out,bqys_tue_out,bqys_wed_out,bqys_thu_out,bqys_mth_out,bqys_fri_out,bqys_sat_out,bqys_sun_out,   bqys_mon_in,bqys_tue_in,bqys_wed_in,bqys_thu_in,bqys_mth_in,bqys_fri_in,bqys_sat_in,bqys_sun_in,    bqysoptions)
        build_weeklists(cpm_mon_out,cpm_tue_out,cpm_wed_out,cpm_thu_out,cpm_mth_out,cpm_fri_out,cpm_sat_out,cpm_sun_out,           cpm_mon_in,cpm_tue_in,cpm_wed_in,cpm_thu_in,cpm_mth_in,cpm_fri_in,cpm_sat_in,cpm_sun_in,            cpmoptions)
        build_weeklists(orms_mon_out,orms_tue_out,orms_wed_out,orms_thu_out,orms_mth_out,orms_fri_out,orms_sat_out,orms_sun_out,   orms_mon_in,orms_tue_in,orms_wed_in,orms_thu_in,orms_mth_in,orms_fri_in,orms_sat_in,orms_sun_in,    ormsoptions)
        build_weeklists(bwhs_mon_out,bwhs_tue_out,bwhs_wed_out,bwhs_thu_out,bwhs_mth_out,bwhs_fri_out,bwhs_sat_out,bwhs_sun_out,   bwhs_mon_in,bwhs_tue_in,bwhs_wed_in,bwhs_thu_in,bwhs_mth_in,bwhs_fri_in,bwhs_sat_in,bwhs_sun_in,    bwhsoptions)
        
        # Create blank worksheets for each stabling yard
        Info = workbook.add_worksheet('Info')
        Summary = workbook.add_worksheet('Summary')
        Wulkuraka = workbook.add_worksheet('Wulkuraka')
        Ipswich = workbook.add_worksheet('Ipswich')
        Redbank = workbook.add_worksheet('Redbank')
        Robina = workbook.add_worksheet('Robina')
        Manly = workbook.add_worksheet('Manly')
        Beenleigh = workbook.add_worksheet('Beenleigh')
        MayneWest = workbook.add_worksheet('Mayne West')
        MayneNorth = workbook.add_worksheet('Mayne North')
        MayneEast = workbook.add_worksheet('Mayne East')
        Petrie = workbook.add_worksheet('Petrie')
        KippaRing = workbook.add_worksheet('Kippa-Ring')
        Caboolture = workbook.add_worksheet('Caboolture')
        Elimbah = workbook.add_worksheet('Elimbah')
        Woombye = workbook.add_worksheet('Woombye')
        Nambour = workbook.add_worksheet('Nambour')
        GympieNth = workbook.add_worksheet('Gympie North')
        Banyo = workbook.add_worksheet('Banyo')
        Clapham = workbook.add_worksheet('Clapham')
        Ormeau = workbook.add_worksheet('Ormeau')
        BeerwahSouth = workbook.add_worksheet('Beerwah South')
        
        # Use the lists we've just filled to populate the blank worksheets we've just created
        write_sheet(Wulkuraka,  wfe_mon_out,wfe_tue_out,wfe_wed_out,wfe_thu_out,wfe_mth_out,wfe_fri_out,wfe_sat_out,wfe_sun_out,            wfe_mon_in,wfe_tue_in,wfe_wed_in,wfe_thu_in,wfe_mth_in,wfe_fri_in,wfe_sat_in,wfe_sun_in)
        write_sheet(Ipswich,    ipss_mon_out,ipss_tue_out,ipss_wed_out,ipss_thu_out,ipss_mth_out,ipss_fri_out,ipss_sat_out,ipss_sun_out,    ipss_mon_in,ipss_tue_in,ipss_wed_in,ipss_thu_in,ipss_mth_in,ipss_fri_in,ipss_sat_in,ipss_sun_in)
        write_sheet(Redbank,    rdks_mon_out,rdks_tue_out,rdks_wed_out,rdks_thu_out,rdks_mth_out,rdks_fri_out,rdks_sat_out,rdks_sun_out,    rdks_mon_in,rdks_tue_in,rdks_wed_in,rdks_thu_in,rdks_mth_in,rdks_fri_in,rdks_sat_in,rdks_sun_in)
        write_sheet(Robina,     robs_mon_out,robs_tue_out,robs_wed_out,robs_thu_out,robs_mth_out,robs_fri_out,robs_sat_out,robs_sun_out,    robs_mon_in,robs_tue_in,robs_wed_in,robs_thu_in,robs_mth_in,robs_fri_in,robs_sat_in,robs_sun_in)
        write_sheet(Manly,      mny_mon_out,mny_tue_out,mny_wed_out,mny_thu_out,mny_mth_out,mny_fri_out,mny_sat_out,mny_sun_out,            mny_mon_in,mny_tue_in,mny_wed_in,mny_thu_in,mny_mth_in,mny_fri_in,mny_sat_in,mny_sun_in)
        write_sheet(Beenleigh,  bnhs_mon_out,bnhs_tue_out,bnhs_wed_out,bnhs_thu_out,bnhs_mth_out,bnhs_fri_out,bnhs_sat_out,bnhs_sun_out,    bnhs_mon_in,bnhs_tue_in,bnhs_wed_in,bnhs_thu_in,bnhs_mth_in,bnhs_fri_in,bnhs_sat_in,bnhs_sun_in)
        write_sheet(MayneWest,  ets_mon_out,ets_tue_out,ets_wed_out,ets_thu_out,ets_mth_out,ets_fri_out,ets_sat_out,ets_sun_out,            ets_mon_in,ets_tue_in,ets_wed_in,ets_thu_in,ets_mth_in,ets_fri_in,ets_sat_in,ets_sun_in)
        write_sheet(MayneNorth, yn_mon_out,yn_tue_out,yn_wed_out,yn_thu_out,yn_mth_out,yn_fri_out,yn_sat_out,yn_sun_out,                    yn_mon_in,yn_tue_in,yn_wed_in,yn_thu_in,yn_mth_in,yn_fri_in,yn_sat_in,yn_sun_in)
        write_sheet(MayneEast,  mes_mon_out,mes_tue_out,mes_wed_out,mes_thu_out,mes_mth_out,mes_fri_out,mes_sat_out,mes_sun_out,            mes_mon_in,mes_tue_in,mes_wed_in,mes_thu_in,mes_mth_in,mes_fri_in,mes_sat_in,mes_sun_in)
        write_sheet(Petrie,     pets_mon_out,pets_tue_out,pets_wed_out,pets_thu_out,pets_mth_out,pets_fri_out,pets_sat_out,pets_sun_out,    pets_mon_in,pets_tue_in,pets_wed_in,pets_thu_in,pets_mth_in,pets_fri_in,pets_sat_in,pets_sun_in)
        write_sheet(KippaRing,  kprs_mon_out,kprs_tue_out,kprs_wed_out,kprs_thu_out,kprs_mth_out,kprs_fri_out,kprs_sat_out,kprs_sun_out,    kprs_mon_in,kprs_tue_in,kprs_wed_in,kprs_thu_in,kprs_mth_in,kprs_fri_in,kprs_sat_in,kprs_sun_in)
        write_sheet(Caboolture, caew_mon_out,caew_tue_out,caew_wed_out,caew_thu_out,caew_mth_out,caew_fri_out,caew_sat_out,caew_sun_out,    caew_mon_in,caew_tue_in,caew_wed_in,caew_thu_in,caew_mth_in,caew_fri_in,caew_sat_in,caew_sun_in)
        write_sheet(Elimbah,    emhs_mon_out,emhs_tue_out,emhs_wed_out,emhs_thu_out,emhs_mth_out,emhs_fri_out,emhs_sat_out,emhs_sun_out,    emhs_mon_in,emhs_tue_in,emhs_wed_in,emhs_thu_in,emhs_mth_in,emhs_fri_in,emhs_sat_in,emhs_sun_in)
        write_sheet(Woombye,    wobs_mon_out,wobs_tue_out,wobs_wed_out,wobs_thu_out,wobs_mth_out,wobs_fri_out,wobs_sat_out,wobs_sun_out,    wobs_mon_in,wobs_tue_in,wobs_wed_in,wobs_thu_in,wobs_mth_in,wobs_fri_in,wobs_sat_in,wobs_sun_in)
        write_sheet(Nambour,    nbr_mon_out,nbr_tue_out,nbr_wed_out,nbr_thu_out,nbr_mth_out,nbr_fri_out,nbr_sat_out,nbr_sun_out,            nbr_mon_in,nbr_tue_in,nbr_wed_in,nbr_thu_in,nbr_mth_in,nbr_fri_in,nbr_sat_in,nbr_sun_in)
        write_sheet(GympieNth,  gyn_mon_out,gyn_tue_out,gyn_wed_out,gyn_thu_out,gyn_mth_out,gyn_fri_out,gyn_sat_out,gyn_sun_out,            gyn_mon_in,gyn_tue_in,gyn_wed_in,gyn_thu_in,gyn_mth_in,gyn_fri_in,gyn_sat_in,gyn_sun_in)
        write_sheet(Banyo,      bqys_mon_out,bqys_tue_out,bqys_wed_out,bqys_thu_out,bqys_mth_out,bqys_fri_out,bqys_sat_out,bqys_sun_out,    bqys_mon_in,bqys_tue_in,bqys_wed_in,bqys_thu_in,bqys_mth_in,bqys_fri_in,bqys_sat_in,bqys_sun_in)
        write_sheet(Clapham,    cpm_mon_out,cpm_tue_out,cpm_wed_out,cpm_thu_out,cpm_mth_out,cpm_fri_out,cpm_sat_out,cpm_sun_out,            cpm_mon_in,cpm_tue_in,cpm_wed_in,cpm_thu_in,cpm_mth_in,cpm_fri_in,cpm_sat_in,cpm_sun_in)
        write_sheet(Ormeau,     orms_mon_out,orms_tue_out,orms_wed_out,orms_thu_out,orms_mth_out,orms_fri_out,orms_sat_out,orms_sun_out,    orms_mon_in,orms_tue_in,orms_wed_in,orms_thu_in,orms_mth_in,orms_fri_in,orms_sat_in,orms_sun_in)
        write_sheet(BeerwahSouth,bwhs_mon_out,bwhs_tue_out,bwhs_wed_out,bwhs_thu_out,bwhs_mth_out,bwhs_fri_out,bwhs_sat_out,bwhs_sun_out,   bwhs_mon_in,bwhs_tue_in,bwhs_wed_in,bwhs_thu_in,bwhs_mth_in,bwhs_fri_in,bwhs_sat_in,bwhs_sun_in)
        
        
        
        
        
        # Summary
        #########################################################################################
        #########################################################################################
        
        Summary.write('A1','Daily Difference',boldleft)
        Summary.set_tab_color('#7FE57F')
        Summary.set_column(0,0,15)
        
            
        # monemu = tueemu = wedemu = thuemu = mthemu = friemu = satemu = sunemu = 0
        # monngr = tuengr = wedngr = thungr = mthngr = fringr = satngr = sunngr = 0
        # monimu = tueimu = wedimu = thuimu = mthimu = friimu = satimu = sunimu = 0
        # mondep = tuedep = weddep = thudep = mthdep = fridep = satdep = sundep = 0     
        # monhyb = tuehyb = wedhyb = thuhyb = mthhyb = frihyb = sathyb = sunhyb = 0  
        # monsmu = tuesmu = wedsmu = thusmu = mthsmu = frismu = satsmu = sunsmu = 0 
        
        stables_dict = {
            'Wulkuraka':    (wfe_mon_out,wfe_tue_out,wfe_wed_out,wfe_thu_out,wfe_mth_out,wfe_fri_out,wfe_sat_out,wfe_sun_out,           wfe_mon_in,wfe_tue_in,wfe_wed_in,wfe_thu_in,wfe_mth_in,wfe_fri_in,wfe_sat_in,wfe_sun_in),
            'Ipswich':      (ipss_mon_out,ipss_tue_out,ipss_wed_out,ipss_thu_out,ipss_mth_out,ipss_fri_out,ipss_sat_out,ipss_sun_out,   ipss_mon_in,ipss_tue_in,ipss_wed_in,ipss_thu_in,ipss_mth_in,ipss_fri_in,ipss_sat_in,ipss_sun_in),
            'Redbank':      (rdks_mon_out,rdks_tue_out,rdks_wed_out,rdks_thu_out,rdks_mth_out,rdks_fri_out,rdks_sat_out,rdks_sun_out,   rdks_mon_in,rdks_tue_in,rdks_wed_in,rdks_thu_in,rdks_mth_in,rdks_fri_in,rdks_sat_in,rdks_sun_in),
            'Robina':       (robs_mon_out,robs_tue_out,robs_wed_out,robs_thu_out,robs_mth_out,robs_fri_out,robs_sat_out,robs_sun_out,   robs_mon_in,robs_tue_in,robs_wed_in,robs_thu_in,robs_mth_in,robs_fri_in,robs_sat_in,robs_sun_in),
            'Manly':        (mny_mon_out,mny_tue_out,mny_wed_out,mny_thu_out,mny_mth_out,mny_fri_out,mny_sat_out,mny_sun_out,           mny_mon_in,mny_tue_in,mny_wed_in,mny_thu_in,mny_mth_in,mny_fri_in,mny_sat_in,mny_sun_in),
            'Beenleigh':    (bnhs_mon_out,bnhs_tue_out,bnhs_wed_out,bnhs_thu_out,bnhs_mth_out,bnhs_fri_out,bnhs_sat_out,bnhs_sun_out,   bnhs_mon_in,bnhs_tue_in,bnhs_wed_in,bnhs_thu_in,bnhs_mth_in,bnhs_fri_in,bnhs_sat_in,bnhs_sun_in),
            'Mayne West':   (ets_mon_out,ets_tue_out,ets_wed_out,ets_thu_out,ets_mth_out,ets_fri_out,ets_sat_out,ets_sun_out,           ets_mon_in,ets_tue_in,ets_wed_in,ets_thu_in,ets_mth_in,ets_fri_in,ets_sat_in,ets_sun_in),
            'Mayne North':  (yn_mon_out,yn_tue_out,yn_wed_out,yn_thu_out,yn_mth_out,yn_fri_out,yn_sat_out,yn_sun_out,                   yn_mon_in,yn_tue_in,yn_wed_in,yn_thu_in,yn_mth_in,yn_fri_in,yn_sat_in,yn_sun_in),
            'Mayne East':   (mes_mon_out,mes_tue_out,mes_wed_out,mes_thu_out,mes_mth_out,mes_fri_out,mes_sat_out,mes_sun_out,           mes_mon_in,mes_tue_in,mes_wed_in,mes_thu_in,mes_mth_in,mes_fri_in,mes_sat_in,mes_sun_in),
            'Petrie':       (pets_mon_out,pets_tue_out,pets_wed_out,pets_thu_out,pets_mth_out,pets_fri_out,pets_sat_out,pets_sun_out,   pets_mon_in,pets_tue_in,pets_wed_in,pets_thu_in,pets_mth_in,pets_fri_in,pets_sat_in,pets_sun_in),
            'Kippa-Ring':   (kprs_mon_out,kprs_tue_out,kprs_wed_out,kprs_thu_out,kprs_mth_out,kprs_fri_out,kprs_sat_out,kprs_sun_out,   kprs_mon_in,kprs_tue_in,kprs_wed_in,kprs_thu_in,kprs_mth_in,kprs_fri_in,kprs_sat_in,kprs_sun_in),
            'Caboolture':   (caew_mon_out,caew_tue_out,caew_wed_out,caew_thu_out,caew_mth_out,caew_fri_out,caew_sat_out,caew_sun_out,   caew_mon_in,caew_tue_in,caew_wed_in,caew_thu_in,caew_mth_in,caew_fri_in,caew_sat_in,caew_sun_in),
            'Elimbah':      (emhs_mon_out,emhs_tue_out,emhs_wed_out,emhs_thu_out,emhs_mth_out,emhs_fri_out,emhs_sat_out,emhs_sun_out,   emhs_mon_in,emhs_tue_in,emhs_wed_in,emhs_thu_in,emhs_mth_in,emhs_fri_in,emhs_sat_in,emhs_sun_in),
            'Woombye':      (wobs_mon_out,wobs_tue_out,wobs_wed_out,wobs_thu_out,wobs_mth_out,wobs_fri_out,wobs_sat_out,wobs_sun_out,   wobs_mon_in,wobs_tue_in,wobs_wed_in,wobs_thu_in,wobs_mth_in,wobs_fri_in,wobs_sat_in,wobs_sun_in),
            'Nambour':      (nbr_mon_out,nbr_tue_out,nbr_wed_out,nbr_thu_out,nbr_mth_out,nbr_fri_out,nbr_sat_out,nbr_sun_out,           nbr_mon_in,nbr_tue_in,nbr_wed_in,nbr_thu_in,nbr_mth_in,nbr_fri_in,nbr_sat_in,nbr_sun_in),
            'Gympie North': (gyn_mon_out,gyn_tue_out,gyn_wed_out,gyn_thu_out,gyn_mth_out,gyn_fri_out,gyn_sat_out,gyn_sun_out,           gyn_mon_in,gyn_tue_in,gyn_wed_in,gyn_thu_in,gyn_mth_in,gyn_fri_in,gyn_sat_in,gyn_sun_in),
            'Banyo':        (bqys_mon_out,bqys_tue_out,bqys_wed_out,bqys_thu_out,bqys_mth_out,bqys_fri_out,bqys_sat_out,bqys_sun_out,   bqys_mon_in,bqys_tue_in,bqys_wed_in,bqys_thu_in,bqys_mth_in,bqys_fri_in,bqys_sat_in,bqys_sun_in),
            'Clapham':      (cpm_mon_out,cpm_tue_out,cpm_wed_out,cpm_thu_out,cpm_mth_out,cpm_fri_out,cpm_sat_out,cpm_sun_out,           cpm_mon_in,cpm_tue_in,cpm_wed_in,cpm_thu_in,cpm_mth_in,cpm_fri_in,cpm_sat_in,cpm_sun_in),
            'Ormeau':       (orms_mon_out,orms_tue_out,orms_wed_out,orms_thu_out,orms_mth_out,orms_fri_out,orms_sat_out,orms_sun_out,   orms_mon_in,orms_tue_in,orms_wed_in,orms_thu_in,orms_mth_in,orms_fri_in,orms_sat_in,orms_sun_in),
            'Beerwah South':(bwhs_mon_out,bwhs_tue_out,bwhs_wed_out,bwhs_thu_out,bwhs_mth_out,bwhs_fri_out,bwhs_sat_out,bwhs_sun_out,   bwhs_mon_in,bwhs_tue_in,bwhs_wed_in,bwhs_thu_in,bwhs_mth_in,bwhs_fri_in,bwhs_sat_in,bwhs_sun_in),
                }
        
        sheet_dict = {
            'Wulkuraka':    Wulkuraka,
            'Ipswich':      Ipswich,
            'Redbank':      Redbank,
            'Robina':       Robina,
            'Manly':        Manly,
            'Beenleigh':    Beenleigh,
            'Mayne West':   MayneWest,
            'Mayne North':  MayneNorth,
            'Mayne East':   MayneEast,
            'Petrie':       Petrie,
            'Kippa-Ring':   KippaRing,
            'Caboolture':   Caboolture,
            'Elimbah':      Elimbah,
            'Woombye':      Woombye,
            'Nambour':      Nambour,
            'Gympie North': GympieNth,
            'Banyo':        Banyo,
            'Clapham':      Clapham,
            'Ormeau':       Ormeau,
            'Beerwah South': BeerwahSouth,
                }
        
        
        for i,(k,v) in enumerate(stables_dict.items()):
            srow = i*(ndays+3) + 2
            erow = srow + ndays
            day_out_of_balance = False
            
            Summary.write_row(srow-1,0,list((n+3)*' '),bottom)
            Summary.write_row(erow+1,0,list((n+3)*' '),top)
            Summary.write(1,2+n,'Total',boldbottomleftborder)
            
            Summary.write_column(srow,1,[weekdaykey_dict.get(d) for d in d_list],centered)
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
                Summary.write(1,col,ttype,font_dict.get(ttype)[1])
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
                writecell_unbalanced(erow,col,weekly_balance,topborder_unbalanced,topborder)
                weekly_totals_list.append(weekly_balance)
            
            # Write totals column
            for r,day in enumerate(d_list,srow):
                daily_total = sum([x[8] for x in d_dict.get(day)[1]]) - sum([x[8] for x in d_dict.get(day)[0]])
                writecell_unbalanced(r, 2+n, daily_total, leftborder_unbalanced, leftborder)
        
            # Write totals total        
            writecell_unbalanced(erow, 2+n, total_total, topleftborderredbg, topleftborder)
            
        
            
            if any(weekly_totals_list):
                Summary.merge_range(srow,0,erow,0,k,boldleftvc_unbalanced_r)
                sheet_dict.get(k).set_tab_color('#CC194C')
            elif day_out_of_balance:
                Summary.merge_range(srow,0,erow,0,k,boldleftvc_unbalanced_b)
                sheet_dict.get(k).set_tab_color('#CCB233')
            else:
                Summary.merge_range(srow,0,erow,0,k,boldleftvc)
        
        
            
        
        
        
        
        
        # Info
        #########################################################################################
        #########################################################################################
        
        info_col  = ['Timetable Name:','Timetable Id:','Report Date:','Report Type:']
        info_col2 = [filename,'',datetime.now().strftime("%d-%b-%Y %H:%M"),'Stabling balance by run']
        Info.set_column(0,0,15)
        
        steps_col = [
            '1. Determine the location where each Run starts and finishes.',
            '2. By Unit type by Day, count the number of Runs that start or finish at each location.',
            '3. Find where start and finish counts do not match over the day.',
            '4. Find where start and finish counts do not match over the week.'
            ]
        
        
        
        
        #Initialise single trip lists for info sheet
        mon_st = []; tue_st = []; wed_st = []; thu_st = []
        mth_st = []; fri_st = []; sat_st = []; sun_st = []
        singletrip_dict = {('64','120'):mon_st, ('32','120'):tue_st, ('16','120'):wed_st, ('8','120'):thu_st, ('120',):mth_st, '4':fri_st, '2':sat_st, '1':sun_st}
        runs_without_stable = []
        
        for i,(k,v) in enumerate(singletrip_dict.items()):
            for key,run in run_dict.items():
                
                runID   = key[0]
                DoO     = key[1]
                
                
                trips   = run[2]
                run_oID = run[3]
                run_dID = run[4]
                
                if DoO in k:
                    if trips == 1:
                        v.append(runID)
                    if run_oID not in acceptable_stables or run_dID not in acceptable_stables:
                        runs_without_stable.append([runID,DoO,run_oID,run_dID])         
             
        singletrip_col = []
        
        if '64' in d_list:
            singletrip_col.append(f'{len(set(mon_st))} Runs with only a single trip on Monday: {csl(mon_st)}')
        if '32' in d_list:
            singletrip_col.append(f'{len(set(tue_st))} Runs with only a single trip on Tuesday: {csl(tue_st)}')
        if '16' in d_list:
            singletrip_col.append(f'{len(set(wed_st))} Runs with only a single trip on Wednesday: {csl(wed_st)}')
        if '8' in d_list:
            singletrip_col.append(f'{len(set(thu_st))} Runs with only a single trip on Thursday: {csl(thu_st)}')
        if '120' in d_list:
            singletrip_col.append(f'{len(set(mth_st))} Runs with only a single trip on school nights: {csl(mth_st)}')
        if '4' in d_list:
            singletrip_col.append(f'{len(set(fri_st))} Runs with only a single trip on Friday: {csl(fri_st)}')
        if '2' in d_list:
            singletrip_col.append(f'{len(set(sat_st))} Runs with only a single trip on Saturday: {csl(sat_st)}')
        if '1' in d_list:
            singletrip_col.append(f'{len(set(sun_st))} Runs with only a single trip on Sunday: {csl(sun_st)}')
            
            
        Info.write_column('A1',info_col,boldright)
        Info.write_column('B1',info_col2)
        Info.write_column('A7',steps_col,boldleft)
        Info.write_column('A13',singletrip_col,boldleft)
        
        
        if runs_without_stable:
            Info.write(13+ndays,0,f'{len(runs_without_stable)} Runs not starting or ending at an adequate stabling location:',  redboldleft)
            Info.set_tab_color('#CC194C')
            for row,run in enumerate(runs_without_stable,14+ndays):
                runID     = run[0]
                DoO       = weekdaykey_dict.get(run[1])
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
                    os.startfile(rf'{filename_xlsx}')
                    print('\nOpening workbook') 
        
        # if CreateWorkbook:
        #     workbook.close()
        #     print('Creating workbook')  
        #     if OpenWorkbook and __name__ == "__main__":
        #         os.startfile(rf'{filename_xlsx}')
        #         print('\nOpening workbook')   
        #     else:
        #         if copyfile:
        #             shutil.copy(filename_xlsx, mypath) 
                
        
        
        
        if ProcessDoneMessagebox and __name__ == "__main__":
            print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('Public Timetable','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
            
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_SB(path)           