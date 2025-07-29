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

import traceback
import logging




OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True 
OpenWorkbook = True







weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}

wkdk_rename = {
    ('120','64'):'Mon',
    ('120','32'):'Tue',
    ('120','16'):'Wed',
    ('120','8'): 'Thu',
    ('120',):'Mon-Thu',
    ('4',):'Fri',
    ('2',):'Sat',
    ('1',):'Sun'
    }   














def TTS_SC(path, mypath = None):

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
        filename_xlsx = f'StablingCount-{filename}.xlsx'
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
        SORT_ORDER_UNIT = ['NGR', 'IMU100','EMU','SMU','HYBRID', 'ICE', 'DEPT']
        d_list.sort(key=SORT_ORDER_WEEK.index)
        u_list.sort(key=SORT_ORDER_UNIT.index)
        weekdays = set(d_list).intersection({'8','16','32','64'})
        if weekdays and '120' in d_list:
            d_list.remove('120')
        ndays = len(d_list)
        n     = len(u_list)
        # print('days: ',d_list)
        # print('units:',u_list,'\n')
        
        
        # Create an identity matrix using unit types
        # This will be used to update the row representing the number of units in a stabling location, using element-wise addition
        # A ones column is appended for the total
        change_matrix = {}
        for i,unittype in enumerate(u_list):
            change_matrix[unittype] = [1] + list(np.zeros((n,)))
            change_matrix[unittype][i+1] = 1
            
          
            
          
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
            
            
            cars = int(re.findall(r'\d+', traintype)[0])
            
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
            Summary.write(      row, 4+n,   weekdaykey_dict.get(day))
            Summary.write(      row, 5+n,   totals_col[i],      boldcenter)
            Summary.write_row(  row, 6+n,   daylist_dict.get(day),        centered)
            row += 1
                    
        
        def startofdayunitcount(daylist):
            """ 
            Finds the minimum number of units stabled at each location at the start of the day
            Could be other, unused units
            """
            
            emutest = [100]
            ngrtest = [100]
            imutest = [100]
            icetest = [100]
            deptest = [100]
            hybtest = [100]
            smutest = [100]
        
            emucount = 0
            ngrcount = 0
            imucount = 0
            icecount = 0
            depcount = 0
            hybcount = 0
            smucount = 0
            
            for x in daylist:
                if x[2] == 'NGR':
                    ngrtest.append(ngrtest[ngrcount] + x[8])
                    ngrcount += 1
                if x[2] == 'EMU':
                    emutest.append(emutest[emucount] + x[8])
                    emucount += 1
                if x[2] == 'IMU100':
                    imutest.append(imutest[imucount] + x[8])
                    imucount += 1
                if x[2] == 'ICE':
                    icetest.append(icetest[icecount] + x[8])
                    icecount += 1
                if x[2] == 'DEPT':
                    deptest.append(deptest[depcount] + x[8])
                    depcount += 1
                if x[2] == 'HYBRID':
                    hybtest.append(hybtest[hybcount] + x[8])
                    hybcount += 1
                if x[2] == 'SMU':
                    smutest.append(smutest[smucount] + x[8])
                    smucount += 1
            
            t_emu = float(100-min(emutest))
            t_ngr = float(100-min(ngrtest))
            t_imu = float(100-min(imutest))
            t_ice = float(100-min(icetest))
            t_dep = float(100-min(deptest))
            t_hyb = float(100-min(hybtest))
            t_smu = float(100-min(smutest))
            
            t_all = t_emu + t_ngr + t_imu + t_ice + t_dep + t_hyb + t_smu
            type_dict = {'IMU100':t_imu, 'EMU':t_emu, 'NGR':t_ngr, 'ICE':t_ice, 'DEPT':t_dep, 'HYBRID':t_hyb, 'SMU':t_smu}
            
            return [t_all]+[type_dict.get(uu) for uu in u_list]
        
        def endofdayunitcount(daylist):
            """ 
            Finds the end of day balance between units at the start of the day and units at the end of the day
            An output of zero means the stabling location is balanced for that day
            """
            
            startcount = startofdayunitcount(daylist)
            stablechange = np.array(startcount)
            
            for entry in daylist:
                if entry[2] == 'NGR':
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
                if entry[2] == 'NGR':
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
        
        
        
        def build_daylist(daylist, wkdk, stable):
            """ 
            From the list of all runs, 
            narrows down runs that either start or end at a particular stabling location, 
            for that particular day of operation,
            and appends that run to the associated list
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
                
                
                # delta = 1 if v[1] == 6 else 0.5
                if D_o_run in wkdk:
                    if start_sID in stable:
                        daylist.append([ run, DoO, unit, cars, trips, start_sID, end_sID, start_t, -delta])
             
                    if end_sID in stable:
                        daylist.append([ run, DoO, unit, cars, trips, start_sID, end_sID, finish_t, delta])
        
            
            daylist.sort(key=lambda val: val[7])
            for x in daylist: x[7] = timetrim(x[7])
            
        
        
        def build_weeklists(mon,tue,wed,thu,mth,fri,sat,sun,stableoptions):
            """ Runs the build_daylist function for a full week """
            
            if weekdays:
                build_daylist(mon, ('120','64'),  stableoptions) 
                build_daylist(tue, ('120','32'),  stableoptions) 
                build_daylist(wed, ('120','16'),  stableoptions) 
                build_daylist(thu, ('120','8'),   stableoptions) 
            else:
                build_daylist(mth, ('120',),       stableoptions)  
            build_daylist(fri, ('4',),         stableoptions)
            build_daylist(sat, ('2',),         stableoptions)
            build_daylist(sun, ('1',),         stableoptions)
            
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
                    
                    if unit == 'NGR':
                        threecarscalar = 1
                    else:
                        threecarscalar = 2 if cars == 6 else 1
                    
    
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
                    if entry[5] in nonstables:
                        sheet.write(idx,5,entry[5],font_dict.get(entry[2])[2])
                    if entry[6] in nonstables:
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
        #########################################################################################
        #########################################################################################
        imu = workbook.add_format({'align':'center','bg_color':'#FDE9D9'})
        emu = workbook.add_format({'align':'center','bg_color':'#DAEEF3'})
        ngr = workbook.add_format({'align':'center','bg_color':'#E4DFEC'})
        ice = workbook.add_format({'align':'center','bg_color':'#EBF1DE'})
        smu = workbook.add_format({'align':'center','bg_color':'#F2DCDB'})
        
        imubold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#FDE9D9','bottom':1})
        emubold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#DAEEF3','bottom':1})
        ngrbold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#E4DFEC','bottom':1})
        icebold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#EBF1DE','bottom':1})
        smubold = workbook.add_format({'align':'center', 'bold':True,'bg_color':'#F2DCDB','bottom':1})
        
        imuboldred = workbook.add_format({'align':'center','bg_color':'#FDE9D9','font_color':'#CC194C', 'bold':True})
        emuboldred = workbook.add_format({'align':'center','bg_color':'#DAEEF3','font_color':'#CC194C', 'bold':True})
        ngrboldred = workbook.add_format({'align':'center','bg_color':'#E4DFEC','font_color':'#CC194C', 'bold':True})
        iceboldred = workbook.add_format({'align':'center','bg_color':'#EBF1DE','font_color':'#CC194C', 'bold':True})
        smuboldred = workbook.add_format({'align':'center','bg_color':'#F2DCDB','font_color':'#CC194C', 'bold':True})
        
        imuborder = workbook.add_format({'align':'center','bg_color':'#FDE9D9','left':1,'right':1})
        emuborder = workbook.add_format({'align':'center','bg_color':'#DAEEF3','left':1,'right':1})
        ngrborder = workbook.add_format({'align':'center','bg_color':'#E4DFEC','left':1,'right':1})
        iceborder = workbook.add_format({'align':'center','bg_color':'#EBF1DE','left':1,'right':1})
        smuborder = workbook.add_format({'align':'center','bg_color':'#F2DCDB','left':1,'right':1})
        
        font_dict = {
            'IMU100': [imu,imubold,imuboldred,imuborder],
            'EMU':    [ice,icebold,iceboldred,iceborder],
            'NGR':    [ngr,ngrbold,ngrboldred,ngrborder],
            'ICE':    [ice,icebold,iceboldred,iceborder],
            'DEPT':   [ice,icebold,iceboldred,iceborder],
            'HYBRID': [emu,emubold,emuboldred,emuborder],
            'SMU':    [smu,smubold,smuboldred,smuborder]
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
        
        
        
        # Outline stabling locations
        wfeoptions  = ['WFE','WFW']
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
        
        # To be displayed in red font if a run starts or finishes at one of these non-stable locations
        nonstables = ['IPS','MNY','CAB','NBR','GYN','RS','BHI']
        
        # Create a list of legimate stabling options in order to flag any runs that do not end at one of these locations
        acceptable_stables = []
        s_yards = [wfeoptions,ipssoptions,rdksoptions,robsoptions,mnyoptions,bnhsoptions,etsoptions,ynoptions,petsoptions,kprsoptions,caewoptions,emhsoptions,wobsoptions,nbroptions,gynoptions,bqysoptions]
        for x in s_yards:
                for y in x: acceptable_stables.append(y)
        acceptable_stables.remove('RS')
        acceptable_stables.remove('BHI')
        
        # Initialise a list for each day, for each stabling yard
        # Will be filled with runs on that particular day, starting or ending at that particular stabling location
        wfe_mon = []
        wfe_tue = []
        wfe_wed = []
        wfe_thu = []
        wfe_mth = []
        wfe_fri = []
        wfe_sat = []
        wfe_sun = []
        
        ipss_mon = []
        ipss_tue = []
        ipss_wed = []
        ipss_thu = []
        ipss_mth = []
        ipss_fri = []
        ipss_sat = []
        ipss_sun = []
        
        rdks_mon = []
        rdks_tue = []
        rdks_wed = []
        rdks_thu = []
        rdks_mth = []
        rdks_fri = []
        rdks_sat = []
        rdks_sun = []
        
        robs_mon = []
        robs_tue = []
        robs_wed = []
        robs_thu = []
        robs_mth = []
        robs_fri = []
        robs_sat = []
        robs_sun = []
        
        mny_mon = []
        mny_tue = []
        mny_wed = []
        mny_thu = []
        mny_mth = []
        mny_fri = []
        mny_sat = []
        mny_sun = []
        
        bnhs_mon = []
        bnhs_tue = []
        bnhs_wed = []
        bnhs_thu = []
        bnhs_mth = []
        bnhs_fri = []
        bnhs_sat = []
        bnhs_sun = []
        
        ets_mon = []
        ets_tue = []
        ets_wed = []
        ets_thu = []
        ets_mth = []
        ets_fri = []
        ets_sat = []
        ets_sun = []
        
        yn_mon = []
        yn_tue = []
        yn_wed = []
        yn_thu = []
        yn_mth = []
        yn_fri = []
        yn_sat = []
        yn_sun = []
        
        mes_mon = []
        mes_tue = []
        mes_wed = []
        mes_thu = []
        mes_mth = []
        mes_fri = []
        mes_sat = []
        mes_sun = []
        
        pets_mon = []
        pets_tue = []
        pets_wed = []
        pets_thu = []
        pets_mth = []
        pets_fri = []
        pets_sat = []
        pets_sun = []
        
        kprs_mon = []
        kprs_tue = []
        kprs_wed = []
        kprs_thu = []
        kprs_mth = []
        kprs_fri = []
        kprs_sat = []
        kprs_sun = []
        
        caew_mon = []
        caew_tue = []
        caew_wed = []
        caew_thu = []
        caew_mth = []
        caew_fri = []
        caew_sat = []
        caew_sun = []
        
        emhs_mon = []
        emhs_tue = []
        emhs_wed = []
        emhs_thu = []
        emhs_mth = []
        emhs_fri = []
        emhs_sat = []
        emhs_sun = []
        
        wobs_mon = []
        wobs_tue = []
        wobs_wed = []
        wobs_thu = []
        wobs_mth = []
        wobs_fri = []
        wobs_sat = []
        wobs_sun = []
        
        nbr_mon = []
        nbr_tue = []
        nbr_wed = []
        nbr_thu = []
        nbr_mth = []
        nbr_fri = []
        nbr_sat = []
        nbr_sun = []
        
        gyn_mon = []
        gyn_tue = []
        gyn_wed = []
        gyn_thu = []
        gyn_mth = []
        gyn_fri = []
        gyn_sat = []
        gyn_sun = []
        
        bqys_mon = []
        bqys_tue = []
        bqys_wed = []
        bqys_thu = []
        bqys_mth = []
        bqys_fri = []
        bqys_sat = []
        bqys_sun = []
        
        cpm_mon = []
        cpm_tue = []
        cpm_wed = []
        cpm_thu = []
        cpm_mth = []
        cpm_fri = []
        cpm_sat = []
        cpm_sun = []
        
        
        
        
        
        
        
        
        # Fill the empty lists with runs given it starts or finishes at one of the options
        build_weeklists(wfe_mon,wfe_tue,wfe_wed,wfe_thu,wfe_mth,wfe_fri,wfe_sat,wfe_sun,           wfeoptions)
        build_weeklists(ipss_mon,ipss_tue,ipss_wed,ipss_thu,ipss_mth,ipss_fri,ipss_sat,ipss_sun,   ipssoptions)
        build_weeklists(rdks_mon,rdks_tue,rdks_wed,rdks_thu,rdks_mth,rdks_fri,rdks_sat,rdks_sun,   rdksoptions)
        build_weeklists(robs_mon,robs_tue,robs_wed,robs_thu,robs_mth,robs_fri,robs_sat,robs_sun,   robsoptions)
        build_weeklists(mny_mon,mny_tue,mny_wed,mny_thu,mny_mth,mny_fri,mny_sat,mny_sun,           mnyoptions)
        build_weeklists(bnhs_mon,bnhs_tue,bnhs_wed,bnhs_thu,bnhs_mth,bnhs_fri,bnhs_sat,bnhs_sun,   bnhsoptions)
        build_weeklists(ets_mon,ets_tue,ets_wed,ets_thu,ets_mth,ets_fri,ets_sat,ets_sun,           etsoptions)
        build_weeklists(yn_mon,yn_tue,yn_wed,yn_thu,yn_mth,yn_fri,yn_sat,yn_sun,                   ynoptions)
        build_weeklists(mes_mon,mes_tue,mes_wed,mes_thu,mes_mth,mes_fri,mes_sat,mes_sun,           mesoptions)
        build_weeklists(pets_mon,pets_tue,pets_wed,pets_thu,pets_mth,pets_fri,pets_sat,pets_sun,   petsoptions)
        build_weeklists(kprs_mon,kprs_tue,kprs_wed,kprs_thu,kprs_mth,kprs_fri,kprs_sat,kprs_sun,   kprsoptions)
        build_weeklists(caew_mon,caew_tue,caew_wed,caew_thu,caew_mth,caew_fri,caew_sat,caew_sun,   caewoptions)
        build_weeklists(emhs_mon,emhs_tue,emhs_wed,emhs_thu,emhs_mth,emhs_fri,emhs_sat,emhs_sun,   emhsoptions)
        build_weeklists(wobs_mon,wobs_tue,wobs_wed,wobs_thu,wobs_mth,wobs_fri,wobs_sat,wobs_sun,   wobsoptions)
        build_weeklists(nbr_mon,nbr_tue,nbr_wed,nbr_thu,nbr_mth,nbr_fri,nbr_sat,nbr_sun,           nbroptions)
        build_weeklists(gyn_mon,gyn_tue,gyn_wed,gyn_thu,gyn_mth,gyn_fri,gyn_sat,gyn_sun,           gynoptions)
        build_weeklists(bqys_mon,bqys_tue,bqys_wed,bqys_thu,bqys_mth,bqys_fri,bqys_sat,bqys_sun,   bqysoptions)
        build_weeklists(cpm_mon,cpm_tue,cpm_wed,cpm_thu,cpm_mth,cpm_fri,cpm_sat,cpm_sun,           cpmoptions)
        
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
        
        
        # Use the lists we've just filled to populate the blank worksheets we've just created
        write_sheet(Wulkuraka,    wfe_mon,wfe_tue,wfe_wed,wfe_thu,wfe_mth,wfe_fri,wfe_sat,wfe_sun) 
        write_sheet(Ipswich,      ipss_mon,ipss_tue,ipss_wed,ipss_thu,ipss_mth,ipss_fri,ipss_sat,ipss_sun) 
        write_sheet(Redbank,      rdks_mon,rdks_tue,rdks_wed,rdks_thu,rdks_mth,rdks_fri,rdks_sat,rdks_sun) 
        write_sheet(Robina,       robs_mon,robs_tue,robs_wed,robs_thu,robs_mth,robs_fri,robs_sat,robs_sun) 
        write_sheet(Manly,        mny_mon,mny_tue,mny_wed,mny_thu,mny_mth,mny_fri,mny_sat,mny_sun) 
        write_sheet(Beenleigh,    bnhs_mon,bnhs_tue,bnhs_wed,bnhs_thu,bnhs_mth,bnhs_fri,bnhs_sat,bnhs_sun) 
        write_sheet(MayneWest,    ets_mon,ets_tue,ets_wed,ets_thu,ets_mth,ets_fri,ets_sat,ets_sun) 
        write_sheet(MayneNorth,   yn_mon,yn_tue,yn_wed,yn_thu,yn_mth,yn_fri,yn_sat,yn_sun) 
        write_sheet(MayneEast,    mes_mon,mes_tue,mes_wed,mes_thu,mes_mth,mes_fri,mes_sat,mes_sun) 
        write_sheet(Petrie,       pets_mon,pets_tue,pets_wed,pets_thu,pets_mth,pets_fri,pets_sat,pets_sun) 
        write_sheet(KippaRing,    kprs_mon,kprs_tue,kprs_wed,kprs_thu,kprs_mth,kprs_fri,kprs_sat,kprs_sun) 
        write_sheet(Caboolture,   caew_mon,caew_tue,caew_wed,caew_thu,caew_mth,caew_fri,caew_sat,caew_sun) 
        write_sheet(Elimbah,      emhs_mon,emhs_tue,emhs_wed,emhs_thu,emhs_mth,emhs_fri,emhs_sat,emhs_sun) 
        write_sheet(Woombye,      wobs_mon,wobs_tue,wobs_wed,wobs_thu,wobs_mth,wobs_fri,wobs_sat,wobs_sun) 
        write_sheet(Nambour,      nbr_mon,nbr_tue,nbr_wed,nbr_thu,nbr_mth,nbr_fri,nbr_sat,nbr_sun) 
        write_sheet(GympieNth,    gyn_mon,gyn_tue,gyn_wed,gyn_thu,gyn_mth,gyn_fri,gyn_sat,gyn_sun) 
        write_sheet(Banyo,        bqys_mon,bqys_tue,bqys_wed,bqys_thu,bqys_mth,bqys_fri,bqys_sat,bqys_sun) 
        write_sheet(Clapham,      cpm_mon,cpm_tue,cpm_wed,cpm_thu,cpm_mth,cpm_fri,cpm_sat,cpm_sun) 
        
        
        
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
        
        stable_capacities = {
            'Wulkuraka':    11,
            'Ipswich':      7,
            'Redbank':      6,
            'Robina':       11,
            'Manly':        3,
            'Beenleigh':    8,
            'Mayne West':   '/',
            'Mayne North':  '/',
            'Mayne East':   '/',
            'Petrie':       1,
            'Kippa-Ring':   10,
            'Caboolture':   9,
            'Elimbah':      8,
            'Woombye':      4,
            'Nambour':      3,
            'Gympie North': 1,
            'Banyo':        4,
            'Clapham':      '/'
                }
        
        stables_dict = {
            'Wulkuraka':    (wfe_mon,wfe_tue,wfe_wed,wfe_thu,wfe_mth,wfe_fri,wfe_sat,wfe_sun),
            'Ipswich':      (ipss_mon,ipss_tue,ipss_wed,ipss_thu,ipss_mth,ipss_fri,ipss_sat,ipss_sun),
            'Redbank':      (rdks_mon,rdks_tue,rdks_wed,rdks_thu,rdks_mth,rdks_fri,rdks_sat,rdks_sun),
            'Robina':       (robs_mon,robs_tue,robs_wed,robs_thu,robs_mth,robs_fri,robs_sat,robs_sun),
            'Manly':        (mny_mon,mny_tue,mny_wed,mny_thu,mny_mth,mny_fri,mny_sat,mny_sun),
            'Beenleigh':    (bnhs_mon,bnhs_tue,bnhs_wed,bnhs_thu,bnhs_mth,bnhs_fri,bnhs_sat,bnhs_sun),
            'Mayne West':   (ets_mon,ets_tue,ets_wed,ets_thu,ets_mth,ets_fri,ets_sat,ets_sun),
            'Mayne North':  (yn_mon,yn_tue,yn_wed,yn_thu,yn_mth,yn_fri,yn_sat,yn_sun),
            'Mayne East':   (mes_mon,mes_tue,mes_wed,mes_thu,mes_mth,mes_fri,mes_sat,mes_sun),
            'Petrie':       (pets_mon,pets_tue,pets_wed,pets_thu,pets_mth,pets_fri,pets_sat,pets_sun),
            'Kippa-Ring':   (kprs_mon,kprs_tue,kprs_wed,kprs_thu,kprs_mth,kprs_fri,kprs_sat,kprs_sun),
            'Caboolture':   (caew_mon,caew_tue,caew_wed,caew_thu,caew_mth,caew_fri,caew_sat,caew_sun),
            'Elimbah':      (emhs_mon,emhs_tue,emhs_wed,emhs_thu,emhs_mth,emhs_fri,emhs_sat,emhs_sun),
            'Woombye':      (wobs_mon,wobs_tue,wobs_wed,wobs_thu,wobs_mth,wobs_fri,wobs_sat,wobs_sun),
            'Nambour':      (nbr_mon,nbr_tue,nbr_wed,nbr_thu,nbr_mth,nbr_fri,nbr_sat,nbr_sun),
            'Gympie North': (gyn_mon,gyn_tue,gyn_wed,gyn_thu,gyn_mth,gyn_fri,gyn_sat,gyn_sun),
            'Banyo':        (bqys_mon,bqys_tue,bqys_wed,bqys_thu,bqys_mth,bqys_fri,bqys_sat,bqys_sun),
            'Clapham':      (cpm_mon,cpm_tue,cpm_wed,cpm_thu,cpm_mth,cpm_fri,cpm_sat,cpm_sun)
                }
        
        
        
        
        
        
        # Initialise overnight stabling variables to calculate totals for each unit type for each day
        monemu = tueemu = wedemu = thuemu = mthemu = friemu = satemu = sunemu = 0
        monngr = tuengr = wedngr = thungr = mthngr = fringr = satngr = sunngr = 0
        monimu = tueimu = wedimu = thuimu = mthimu = friimu = satimu = sunimu = 0
        monice = tueice = wedice = thuice = mthice = friice = satice = sunice = 0  
        mondep = tuedep = weddep = thudep = mthdep = fridep = satdep = sundep = 0     
        monhyb = tuehyb = wedhyb = thuhyb = mthhyb = frihyb = sathyb = sunhyb = 0  
        monsmu = tuesmu = wedsmu = thusmu = mthsmu = frismu = satsmu = sunsmu = 0       
        
        
        # Loop through all stabling locations and write totals and unit subtotals to worksheet
        # Add unit subtotals for all days and write under 'total overnight stabling'
        for i,(k,v) in enumerate(stables_dict.items()):
            firstrow = 2+(ndays+2)*i
            lastrow = firstrow + ndays - 1
            if i != 0:
                Summary.write_row(firstrow-1,0, list((3*n+8)*' '),bottom)
            Summary.write_row(    lastrow+1, 0, list((3*n+8)*' '),top)
            
            if ndays == 1:
                Summary.write(firstrow,3+n,None)
                Summary.write(firstrow,6+2*n,None)
            else:
                Summary.merge_range(firstrow,3+n,lastrow,3+n,None)
                Summary.merge_range(firstrow,6+2*n,lastrow,6+2*n,None)
        
            
            # Assign the daylists to variables for each stabling yard
            monday    = v[0]
            tuesday   = v[1]
            wednesday = v[2]
            thursday  = v[3]
            monthu    = v[4]
            friday    = v[5]
            saturday  = v[6]
            sunday    = v[7]
            
            # Use our functions to assign a day total and a day subtotal vector to variables
        
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
        
            # Write the name and capacity for each stabling location
            if ndays == 1:
                Summary.write(firstrow, 0,   k,                        stablefont)
                Summary.write(firstrow, 4+n, stable_capacities.get(k), boldcentervc14  )
            else:
                Summary.merge_range(firstrow,0,   lastrow, 0,   k,                        stablefont)
                Summary.merge_range(firstrow,4+n, lastrow, 4+n, stable_capacities.get(k), boldcentervc14)  
                
            # Write days
            Summary.write_column(firstrow,1,  [weekdaykey_dict.get(d) for d in d_list])
           
            
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
            
           
            for DoW,summary_info in summary_dict.items():
                day,total,breakdown,os_total,os_breakdown,ip_total,ip_breakdown = summary_info
                if summary_info[0]:
                    # print(k,firstrow,DoW)
                    Summary.write(   firstrow,2,        total,          totals_font )
                    summary_writerow(firstrow,3,        breakdown                   )
                    Summary.write(   firstrow,5+n,      os_total,       boldborder  )
                    summary_writerow(firstrow,6+n,      os_breakdown                )
                    Summary.write(   firstrow,7+2*n,    ip_total,       boldborder  )
                    summary_writerow(firstrow,8+2*n,    ip_breakdown                )
                    
                    if ip_total > os_total:
                        Summary.write(   firstrow,7+2*n,    ip_total,       interpeak_flag  )
                
                
                if DoW in d_list:  
                    firstrow += 1
        
            # Improve this method of summation for total overnight stabling
            ##########################################################################################
            ##########################################################################################
            ##########################################################################################
            
            if 'EMU' in u_list:
                emuidx = u_list.index('EMU')
                monemu += mon_os_bkdwn[emuidx]
                tueemu += tue_os_bkdwn[emuidx]
                wedemu += wed_os_bkdwn[emuidx]
                thuemu += thu_os_bkdwn[emuidx]
                mthemu += mth_os_bkdwn[emuidx]
                friemu += fri_os_bkdwn[emuidx]
                satemu += sat_os_bkdwn[emuidx]
                sunemu += sun_os_bkdwn[emuidx]
            
            if 'NGR' in u_list:
                ngridx = u_list.index('NGR')
                monngr += mon_os_bkdwn[ngridx]
                tuengr += tue_os_bkdwn[ngridx]
                wedngr += wed_os_bkdwn[ngridx]
                thungr += thu_os_bkdwn[ngridx]
                mthngr += mth_os_bkdwn[ngridx]
                fringr += fri_os_bkdwn[ngridx]
                satngr += sat_os_bkdwn[ngridx]
                sunngr += sun_os_bkdwn[ngridx]
            
            if 'IMU100' in u_list:
                imuidx = u_list.index('IMU100')
                monimu += mon_os_bkdwn[imuidx]
                tueimu += tue_os_bkdwn[imuidx]
                wedimu += wed_os_bkdwn[imuidx]
                thuimu += thu_os_bkdwn[imuidx]
                mthimu += mth_os_bkdwn[imuidx]
                friimu += fri_os_bkdwn[imuidx]
                satimu += sat_os_bkdwn[imuidx]
                sunimu += sun_os_bkdwn[imuidx]
            
            if 'ICE' in u_list:
                iceidx = u_list.index('ICE')
                monice += mon_os_bkdwn[iceidx]
                tueice += tue_os_bkdwn[iceidx]
                wedice += wed_os_bkdwn[iceidx]
                thuice += thu_os_bkdwn[iceidx]
                mthice += mth_os_bkdwn[iceidx]
                friice += fri_os_bkdwn[iceidx]
                satice += sat_os_bkdwn[iceidx]
                sunice += sun_os_bkdwn[iceidx]
            
            if 'DEPT' in u_list:
                depidx = u_list.index('DEPT')
                mondep += mon_os_bkdwn[depidx]
                tuedep += tue_os_bkdwn[depidx]
                weddep += wed_os_bkdwn[depidx]
                thudep += thu_os_bkdwn[depidx]
                mthdep += mth_os_bkdwn[depidx]
                fridep += fri_os_bkdwn[depidx]
                satdep += sat_os_bkdwn[depidx]
                sundep += sun_os_bkdwn[depidx]
            
            if 'HYBRID' in u_list:
                hybidx = u_list.index('HYBRID')
                monhyb += mon_os_bkdwn[hybidx]
                tuehyb += tue_os_bkdwn[hybidx]
                wedhyb += wed_os_bkdwn[hybidx]
                thuhyb += thu_os_bkdwn[hybidx]
                mthhyb += mth_os_bkdwn[hybidx]
                frihyb += fri_os_bkdwn[hybidx]
                sathyb += sat_os_bkdwn[hybidx]
                sunhyb += sun_os_bkdwn[hybidx]
            
            if 'SMU' in u_list:
                smuidx = u_list.index('SMU')
                monsmu += mon_os_bkdwn[smuidx]
                tuesmu += tue_os_bkdwn[smuidx]
                wedsmu += wed_os_bkdwn[smuidx]
                thusmu += thu_os_bkdwn[smuidx]
                mthsmu += mth_os_bkdwn[smuidx]
                frismu += fri_os_bkdwn[smuidx]
                satsmu += sat_os_bkdwn[smuidx]
                sunsmu += sun_os_bkdwn[smuidx]
        
        
        # Improve this method of summation for total overnight stabling
        ##########################################################################################
        ##########################################################################################
        ##########################################################################################
        
        dailytotals_dict = {
            '120':sum([mthemu,mthngr,mthimu,mthice,mthdep,mthhyb,mthsmu]),
            '64': sum([monemu,monngr,monimu,monice,mondep,monhyb,monsmu]),
            '32': sum([tueemu,tuengr,tueimu,tueice,tuedep,tuehyb,tuesmu]),
            '16': sum([wedemu,wedngr,wedimu,wedice,weddep,wedhyb,wedsmu]),
            '8':  sum([thuemu,thungr,thuimu,thuice,thudep,thuhyb,thusmu]),
            '4':  sum([friemu,fringr,friimu,friice,fridep,frihyb,frismu]),
            '2':  sum([satemu,satngr,satimu,satice,satdep,sathyb,satsmu]),
            '1':  sum([sunemu,sunngr,sunimu,sunice,sundep,sunhyb,sunsmu]) 
            }
        
        type_dict = {
            'IMU100':   [monimu,tueimu,wedimu,thuimu,mthimu,friimu,satimu,sunimu],
            'EMU':      [monemu,tueemu,wedemu,thuemu,mthemu,friemu,satemu,sunemu],
            'NGR':      [monngr,tuengr,wedngr,thungr,mthngr,fringr,satngr,sunngr],
            'ICE':      [monice,tueice,wedice,thuice,mthice,friice,satice,sunice],
            'DEPT':     [mondep,tuedep,weddep,thudep,mthdep,fridep,satdep,sundep],
            'HYBRID':   [monhyb,tuehyb,wedhyb,thuhyb,mthhyb,frihyb,sathyb,sunhyb],
            'SMU':      [monsmu,tuesmu,wedsmu,thusmu,mthsmu,frismu,satsmu,sunsmu]
            }
        
        
        totals_col = []
        for d in d_list:
            totals_col.append(dailytotals_dict.get(d))
        
        monday_list     = []
        tuesday_list    = []
        wednesday_list  = []
        thursday_list   = []
        monthu_list     = []
        friday_list     = []
        saturday_list   = []
        sunday_list     = []
        
        for u in u_list:
            monday_list.append(     type_dict.get(u)[0])
            tuesday_list.append(    type_dict.get(u)[1])
            wednesday_list.append(  type_dict.get(u)[2])
            thursday_list.append(   type_dict.get(u)[3])
            monthu_list.append(     type_dict.get(u)[4])
            friday_list.append(     type_dict.get(u)[5])
            saturday_list.append(   type_dict.get(u)[6])
            sunday_list.append(     type_dict.get(u)[7])
        
        daylist_dict = {'120':monthu_list,'64':monday_list,'32':tuesday_list,'16':wednesday_list,
                        '8':thursday_list,'4':friday_list,'2':saturday_list ,'1':sunday_list}
        
        
        
        
        row = len(stables_dict)*(ndays+2)+2
        endrow = row + ndays - 1 
        if ndays == 1:
            Summary.write(row,n,'Total Overnight Stabling',boldcentervc14)    
        else:
            Summary.merge_range(row,n,endrow,3+n,'Total Overnight Stabling',boldcentervc14)    
        
        for day in d_list:
            summary_writetotals(day)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # Info
        #########################################################################################
        #########################################################################################
        info_col  = ['Timetable Name:','Timetable Id:','Report Date:','Report Type:']
        info_col2 = [filename,'',datetime.now().strftime("%d-%b-%Y %H:%M"),'Stabling count by run']
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
        singletrip_dict = {'64':mon_st, '32':tue_st, '16':wed_st, '8':thu_st, '120':mth_st, '4':fri_st, '2':sat_st, '1':sun_st}
        runs_without_stable = []
        
        for i,(k,v) in enumerate(singletrip_dict.items()):
            for key,run in run_dict.items():
            
                runID   = key[0]
                DoO     = key[1]
                
                trips   = run[2]
                run_oID = run[3]
                run_dID = run[4]
                
                if DoO ==  k:
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
            messagebox.showinfo('Stabling Count Report','Process Done')
            
    
    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            time.sleep(15)
    
if __name__ == "__main__":
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    TTS_SC(path)