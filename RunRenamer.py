import xml.etree.ElementTree as ET
import os
import re
import sys
import pandas as pd
import xlsxwriter
import time

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import traceback
import logging


ProcessDoneMessagebox = False
ProcessDoneMessagebox = True





weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}

wk_dep_ew  = ['ZA','ZB','ZC','ZD','ZE','ZF','ZG','ZH','ZI','ZJ','ZK','ZL','ZM','ZN','ZO','ZP','ZQ','ZR','ZS','ZT','ZU','ZV','ZW','ZX','ZY','ZZ']


wk_ngr_ew  = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26',
              '27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52',
              '53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78',
              '79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','96','97','98','99','100','101','102','103',
              '104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125',
              '126','127','128','129','130','131','132','133','134','135','136','137','138','139','140','141','142','143','144','145','146','147','148','149']



wkd_emu_ew = ['AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ',
              'BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ',
              'CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV','CW','CX','CY','CZ',
              'DA','DB','DC','DD','DE','DF','DG','DH','DI','DJ','DK','DL','DM','DN','DO','DP','DQ','DR','DS','DT','DU','DV','DW','DX','DY','DZ',
              'EA','EB','EC','ED','EE','EF','EG','EH','EI','EJ','EK','EL','EM','EN','EO','EP','EQ','ER','ES','ET','EU','EV','EW','EX','EY','EZ']
wkd_imu_ew = ['FA','FB','FC','FD','FE','FF','FG','FH','FI','FJ','FK','FL','FM','FN','FO','FP','FQ','FR','FS','FT','FU','FV','FW','FX','FY','FZ',
              'GA','GB','GC','GD','GE','GF','GG','GH','GI','GJ','GK','GL','GM','GN','GO','GP','GQ','GR','GS','GT','GU','GV','GW','GX','GY','GZ',
              'HA','HB','HC','HD','HE','HF','HG','HH','HI','HJ','HK','HL','HM','HN','HO','HP','HQ','HR','HS','HT','HU','HV','HW','HX','HY','HZ']



sat_emu_ew = ['IA','IB','IC','ID','IE','IF','IG','IH','II','IJ','IK','IL','IM','IN','IO','IP','IQ','IR','IS','IT','IU','IV','IW','IX','IY','IZ',
              'JA','JB','JC','JD','JE','JF','JG','JH','JI','JJ','JK','JL','JM','JN','JO','JP','JQ','JR','JS','JT','JU','JV','JW','JX','JY','JZ']

sat_imu_ew = ['KA','KB','KC','KD','KE','KF','KG','KH','KI','KJ','KK','KL','KM','KN','KO','KP','KQ','KR','KS','KT','KU','KV','KW','KX','KY','KZ',
              'LA','LB','LC','LD','LE','LF','LG','LH','LI','LJ','LK','LL','LM','LN','LO','LP','LQ','LR','LS','LT','LU','LV','LW','LX','LY','LZ',
              'MA','MB','MC','MD','ME','MF','MG','MH','MI','MJ','MK','ML','MM','MN','MO','MP','MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ']



sun_emu_ew = ['OA','OB','OC','OD','OE','OF','OG','OH','OI','OJ','OK','OL','OM','ON','OO','OP','OQ','OR','OS','OT','OU','OV','OW','OX','OY','OZ',
              'PA','PB','PC','PD','PE','PF','PG','PH','PI','PJ','PK','PL','PM','PN','PO','PP','PQ','PR','PS','PT','PU','PV','PW','PX','PY','PZ']

sun_imu_ew = ['QA','QB','QC','QD','QE','QF','QG','QH','QI','QJ','QK','QL','QM','QN','QO','QP','QQ','QR','QS','QT','QU','QV','QW','QX','QY','QZ',
              'RA','RB','RC','RD','RE','RF','RG','RH','RI','RJ','RK','RL','RM','RN','RO','RP','RQ','RR','RS','RT','RU','RV','RW','RX','RY','RZ']















try:
    
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename() 
    directory = '\\'.join(path.split('/')[0:-1])
    os.chdir(directory)
    filename = path.split('/')[-1]
    print(filename,'\n')
    
    tree = ET.parse(filename)
    root = tree.getroot()
    
    filename = filename[:-4]
    filename_rr_rsx = f'{filename} (renamed).rsx'
    
    
    ### Check for duplicate train numbers before executing the script
    ### Print warning for user if duplicates exist
    ### Print out all duplicates
    
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
    
    d_list = []
    u_list = []
    run_dict = {}
    patterndaydict = {}
    pmp_ew_allocation = []
    pmp_without_amp = []
    gen = (x for x in root.iter('train'))
    for train in gen:
        tn  = train.attrib['number']
        WeekdayKey = train[0][0][0].attrib['weekdayKey']
        entries = [x for x in train.iter('entry')]
        origin = entries[0].attrib
        destin = entries[-1].attrib
        unit   = origin['trainTypeId'].split('-',1)[1]
        lineID = train.attrib['lineID']
        run  = lineID.split('~',1)[1][1:] if '~' in lineID else lineID
        
        pattern = train.attrib['pattern']
        patterndaydict[(tn,pattern)] = WeekdayKey
        
        
        
        
        
        rw_pair = (run,WeekdayKey)
        
        if (run[0].isalpha() and run[-1] == '1') or (run[0].isnumeric() and run[-1] == 'A'):
            amp_ew = ''
            if run[-1] == 'A':
                for i in run:
                    if i.isnumeric():
                        amp_ew += i

                        
            if run[-1] == '1':
                for i in run:
                    if i.isalpha():
                        amp_ew += i
            
            
            amp_pair = (amp_ew,WeekdayKey)
            if amp_pair not in run_dict:
                
                if run_dict.get(amp_pair):
                    pmp_ew_allocation.append(rw_pair)
                    
                else:
                    run_dict[amp_pair] = unit
                    pmp_without_amp.append(rw_pair)
                    print(f'no corresponding {amp_ew} for run {run}')
        
        
        elif rw_pair not in run_dict:
            run_dict[rw_pair] = unit
            
        if WeekdayKey not in d_list:
            d_list.append(WeekdayKey)
            
        if unit not in u_list:
            u_list.append(unit)
    
    
    
    
    
    
    
    
        
    
    
    mth_emu = []
    mth_imu = []
    mth_ngr = []
    
    fri_emu = []
    fri_imu = []
    fri_ngr = []
    
    sat_emu = []
    sat_imu = []
    sat_ngr = []
    
    sun_emu = []
    sun_imu = []
    sun_ngr = []
    
    
    
    mon_dep = []
    tue_dep = []
    wed_dep = []
    thu_dep = []
    mth_dep = []
    fri_dep = []
    sat_dep = []
    sun_dep = []
    
    
    
    for k,v in run_dict.items():

        run = k[0]
        DoO = k[1]
        unittyp = v
        
        
        if DoO == '120': 
            if unittyp in ['EMU','SMU']:
                mth_emu.append((run,DoO))
            if unittyp == 'IMU100':
                mth_imu.append((run,DoO))
            if unittyp == 'NGR':
                mth_ngr.append((run,DoO))
            if unittyp == 'DEPT':
                mth_dep.append((run,DoO))
                
        if DoO == '4':
            if unittyp in ['EMU','SMU']:
                fri_emu.append((run,DoO))
            if unittyp == 'IMU100':
                fri_imu.append((run,DoO))
            if unittyp == 'NGR':
                fri_ngr.append((run,DoO))
            if unittyp == 'DEPT':
                fri_dep.append((run,DoO))
    
        if DoO == '2':
            if unittyp in ['EMU','SMU']:
                sat_emu.append((run,DoO))
            if unittyp == 'IMU100':
                sat_imu.append((run,DoO))
            if unittyp == 'NGR':
                sat_ngr.append((run,DoO))
            if unittyp == 'DEPT':
                sat_dep.append((run,DoO))
    
        if DoO == '1':
            if unittyp in ['EMU','SMU']:
                sun_emu.append((run,DoO))
            if unittyp == 'IMU100':
                sun_imu.append((run,DoO))
            if unittyp == 'NGR':
                sun_ngr.append((run,DoO))
            if unittyp == 'DEPT':
                sun_dep.append((run,DoO))
                
        if DoO == '64':
            mon_dep.append((run,DoO))
        if DoO == '32':
            tue_dep.append((run,DoO))
        if DoO == '16':
            wed_dep.append((run,DoO))
        if DoO == '8':
            thu_dep.append((run,DoO))
                
           
            
         
            
            
    run_renamed_dict = {}       
    
    def reassign_runs(list_of_runs,electric_workings):
    
        for i,x in enumerate(list_of_runs):
            run = x[0]
            DoO = x[1]
            newrun = electric_workings[i]
            
            if run_renamed_dict.get(x):
                print('error')
                print(x)
            
            run_renamed_dict[(run,DoO)] = newrun
    
    reassign_runs(mth_emu, wkd_emu_ew)
    reassign_runs(fri_emu, wkd_emu_ew)
    reassign_runs(sat_emu, sat_emu_ew)
    reassign_runs(sun_emu, sun_emu_ew)
    
    reassign_runs(mth_imu, wkd_imu_ew)
    reassign_runs(fri_imu, wkd_imu_ew)
    reassign_runs(sat_imu, sat_imu_ew)
    reassign_runs(sun_imu, sun_imu_ew)
    
    reassign_runs(mth_ngr, wk_ngr_ew)
    reassign_runs(fri_ngr, wk_ngr_ew)
    reassign_runs(sat_ngr, wk_ngr_ew)
    reassign_runs(sun_ngr, wk_ngr_ew)   
    
    reassign_runs(mon_dep, wk_dep_ew)
    reassign_runs(tue_dep, wk_dep_ew)
    reassign_runs(wed_dep, wk_dep_ew)
    reassign_runs(thu_dep, wk_dep_ew)
    reassign_runs(mth_dep, wk_dep_ew)
    reassign_runs(fri_dep, wk_dep_ew)
    reassign_runs(sat_dep, wk_dep_ew)
    reassign_runs(sun_dep, wk_dep_ew)
    
    o = open(filename_rr_rsx, 'w')
    wl = o.writelines
    
    
    
    with open(path) as f:
        for index, line in enumerate(f):
            if line.startswith('		<train'):
                tn = re.findall('number="(.{4,6})"',line)[0]
                
                run = re.findall('lineID=".+~\s(.{1,4})"',line)
                run = run[0] if run else re.findall('lineID="(.*)"',line)[0]
                
                pattern = re.findall('pattern="([^"]+)"',line)[0]
                DoO = patterndaydict.get((tn,pattern))

                
                
                amp_ew = ''

                
                if run[-1] == 'A':
                    for i in run:
                        if i.isnumeric():
                            amp_ew += i

                            
                elif run[-1] == '1':
                    for i in run:
                        if i.isalpha():
                            amp_ew += i 
                            
                else:
                    amp_ew = run
                
                
                
                if (run,DoO) in pmp_ew_allocation:
                    run_renamed = run_renamed_dict.get((amp_ew,DoO)) + run[-1]
                    
                elif (run,DoO) in pmp_without_amp:
                    run_renamed = run_renamed_dict.get((amp_ew,DoO))
                    
                else:
                    run_renamed = run_renamed_dict.get((run,DoO))

                    

                    
                line = re.sub(f'~ {run}',f'~ {run_renamed}',line)
                line = re.sub(f'"{run}"',f'"{run_renamed}"',line)
                wl(line)
                
            elif line.startswith('					<connection'):
                line = re.sub(f'~ {run}',f'~ {run_renamed}',line)
                line = re.sub(f'"{run}"',f'"{run_renamed}"',line)
                wl(line)
                
            else:
                wl(line)
    
            
            
        
            
    o.close()        
            
            
    print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
        
    if ProcessDoneMessagebox:
        from tkinter import messagebox
        messagebox.showinfo('Run Renamer','Process Done')
        

except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)     