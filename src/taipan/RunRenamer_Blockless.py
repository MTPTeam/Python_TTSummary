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

#May not be long enough for mth + mon,tues,wed,thurs #!!!
mth_dep_ew  = iter(['ZA','ZB','ZC','ZD','ZE','ZF','ZG','ZH','ZI','ZJ','ZK','ZL','ZM','ZN','ZO','ZP','ZQ','ZR','ZS','ZT','ZU','ZV','ZW','ZX','ZY','ZZ'])

fri_dep_ew  = iter(['ZA','ZB','ZC','ZD','ZE','ZF','ZG','ZH','ZI','ZJ','ZK','ZL','ZM','ZN','ZO','ZP','ZQ','ZR','ZS','ZT','ZU','ZV','ZW','ZX','ZY','ZZ'])

sat_dep_ew  = iter(['ZA','ZB','ZC','ZD','ZE','ZF','ZG','ZH','ZI','ZJ','ZK','ZL','ZM','ZN','ZO','ZP','ZQ','ZR','ZS','ZT','ZU','ZV','ZW','ZX','ZY','ZZ'])

sun_dep_ew  = iter(['ZA','ZB','ZC','ZD','ZE','ZF','ZG','ZH','ZI','ZJ','ZK','ZL','ZM','ZN','ZO','ZP','ZQ','ZR','ZS','ZT','ZU','ZV','ZW','ZX','ZY','ZZ'])


mth_ngr_ew  = iter(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26',
                    '27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52',
                    '53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78',
                    '79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','96','97','98','99','100','101','102','103',
                    '104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125',
                    '126','127','128','129','130','131','132','133','134','135','136','137','138','139','140','141','142','143','144','145','146','147','148','149'])

fri_ngr_ew  = iter(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26',
                    '27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52',
                    '53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78',
                    '79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','96','97','98','99','100','101','102','103',
                    '104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125',
                    '126','127','128','129','130','131','132','133','134','135','136','137','138','139','140','141','142','143','144','145','146','147','148','149'])

sat_ngr_ew  = iter(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26',
                    '27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52',
                    '53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78',
                    '79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','96','97','98','99','100','101','102','103',
                    '104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125',
                    '126','127','128','129','130','131','132','133','134','135','136','137','138','139','140','141','142','143','144','145','146','147','148','149'])

sun_ngr_ew  = iter(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26',
                    '27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52',
                    '53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78',
                    '79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','96','97','98','99','100','101','102','103',
                    '104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125',
                    '126','127','128','129','130','131','132','133','134','135','136','137','138','139','140','141','142','143','144','145','146','147','148','149'])


mth_emu_ew = iter(['AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ',
                   'BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ',
                   'CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV','CW','CX','CY','CZ',
                   'DA','DB','DC','DD','DE','DF','DG','DH','DI','DJ','DK','DL','DM','DN','DO','DP','DQ','DR','DS','DT','DU','DV','DW','DX','DY','DZ',
                   'EA','EB','EC','ED','EE','EF','EG','EH','EI','EJ','EK','EL','EM','EN','EO','EP','EQ','ER','ES','ET','EU','EV','EW','EX','EY','EZ'])

fri_emu_ew = iter(['AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ',
                   'BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ',
                   'CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV','CW','CX','CY','CZ',
                   'DA','DB','DC','DD','DE','DF','DG','DH','DI','DJ','DK','DL','DM','DN','DO','DP','DQ','DR','DS','DT','DU','DV','DW','DX','DY','DZ',
                   'EA','EB','EC','ED','EE','EF','EG','EH','EI','EJ','EK','EL','EM','EN','EO','EP','EQ','ER','ES','ET','EU','EV','EW','EX','EY','EZ'])

sat_emu_ew = iter(['IA','IB','IC','ID','IE','IF','IG','IH','II','IJ','IK','IL','IM','IN','IO','IP','IQ','IR','IS','IT','IU','IV','IW','IX','IY','IZ',
                   'JA','JB','JC','JD','JE','JF','JG','JH','JI','JJ','JK','JL','JM','JN','JO','JP','JQ','JR','JS','JT','JU','JV','JW','JX','JY','JZ'])

sun_emu_ew = iter(['OA','OB','OC','OD','OE','OF','OG','OH','OI','OJ','OK','OL','OM','ON','OO','OP','OQ','OR','OS','OT','OU','OV','OW','OX','OY','OZ',
                   'PA','PB','PC','PD','PE','PF','PG','PH','PI','PJ','PK','PL','PM','PN','PO','PP','PQ','PR','PS','PT','PU','PV','PW','PX','PY','PZ'])

mth_imu_ew = iter(['FA','FB','FC','FD','FE','FF','FG','FH','FI','FJ','FK','FL','FM','FN','FO','FP','FQ','FR','FS','FT','FU','FV','FW','FX','FY','FZ',
                   'GA','GB','GC','GD','GE','GF','GG','GH','GI','GJ','GK','GL','GM','GN','GO','GP','GQ','GR','GS','GT','GU','GV','GW','GX','GY','GZ',
                   'HA','HB','HC','HD','HE','HF','HG','HH','HI','HJ','HK','HL','HM','HN','HO','HP','HQ','HR','HS','HT','HU','HV','HW','HX','HY','HZ'])

fri_imu_ew = iter(['FA','FB','FC','FD','FE','FF','FG','FH','FI','FJ','FK','FL','FM','FN','FO','FP','FQ','FR','FS','FT','FU','FV','FW','FX','FY','FZ',
                   'GA','GB','GC','GD','GE','GF','GG','GH','GI','GJ','GK','GL','GM','GN','GO','GP','GQ','GR','GS','GT','GU','GV','GW','GX','GY','GZ',
                   'HA','HB','HC','HD','HE','HF','HG','HH','HI','HJ','HK','HL','HM','HN','HO','HP','HQ','HR','HS','HT','HU','HV','HW','HX','HY','HZ'])

sat_imu_ew = iter(['KA','KB','KC','KD','KE','KF','KG','KH','KI','KJ','KK','KL','KM','KN','KO','KP','KQ','KR','KS','KT','KU','KV','KW','KX','KY','KZ',
                   'LA','LB','LC','LD','LE','LF','LG','LH','LI','LJ','LK','LL','LM','LN','LO','LP','LQ','LR','LS','LT','LU','LV','LW','LX','LY','LZ',
                   'MA','MB','MC','MD','ME','MF','MG','MH','MI','MJ','MK','ML','MM','MN','MO','MP','MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ'])

sun_imu_ew = iter(['QA','QB','QC','QD','QE','QF','QG','QH','QI','QJ','QK','QL','QM','QN','QO','QP','QQ','QR','QS','QT','QU','QV','QW','QX','QY','QZ',
                   'RA','RB','RC','RD','RE','RF','RG','RH','RI','RJ','RK','RL','RM','RN','RO','RP','RQ','RR','RS','RT','RU','RV','RW','RX','RY','RZ'])

#QTMP Electric Workings Allocation...
mth_rep_ew = iter([])
fri_rep_ew = iter([])
sat_rep_ew = iter([])
sun_rep_ew = iter([])
# Script needs further modification to facilitate new unit type










ew_dict = {
    # ('REP','120'):   mth_rep_ew,
    # ('REP','4'):     fri_rep_ew,
    # ('REP','2'):     sat_rep_ew,
    # ('REP','1'):     sun_rep_ew,
    
    ('IMU100','120'):   mth_imu_ew,
    ('IMU100','4'):     fri_imu_ew,
    ('IMU100','2'):     sat_imu_ew,
    ('IMU100','1'):     sun_imu_ew,
    
    ('EMU','120'):  mth_emu_ew,
    ('EMU','4'):    fri_emu_ew,
    ('EMU','2'):    sat_emu_ew,
    ('EMU','1'):    sun_emu_ew,
    
    ('NGR','120'):  mth_ngr_ew,
    ('NGR','4'):    fri_ngr_ew,
    ('NGR','2'):    sat_ngr_ew,
    ('NGR','1'):    sun_ngr_ew,
    
    ('DEPT','120'): mth_dep_ew,
    ('DEPT','4'):   fri_dep_ew,
    ('DEPT','2'):   sat_dep_ew,
    ('DEPT','1'):   sun_dep_ew,
    ('DEPT','64'):  mth_dep_ew,
    ('DEPT','32'):  mth_dep_ew,
    ('DEPT','16'):  mth_dep_ew,
    ('DEPT','8'):   mth_dep_ew,
    }









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
    
    gen = [x for x in root.iter('train')]
    for train in gen:
        tn  = train.attrib['number']
        DoO = train[0][0][0].attrib['weekdayKey']
        entries = [x for x in train.iter('entry')]
        origin = entries[0].attrib
        destin = entries[-1].attrib
        unit   = origin['trainTypeId'].split('-',1)[1]
        
        pattern = train.attrib['pattern']
        patterndaydict[(tn,pattern)] = DoO
        
    
        connection = [x.attrib['trainNumber'] for x in train.iter('connection')]
        if tn == '1R08':
            print(unit)
        
        #First train in run
        if connection:
            connection = connection[0]
        else:
            run = next(ew_dict[(unit,DoO)])
            run_dict[(tn,DoO)] = run
        
        #All subsequent trains in run
        if connection:
            run_dict[(tn,DoO)] = run_dict[(connection,DoO)]
        
        
    
    
    
        if DoO not in d_list:
            d_list.append(DoO)
            
        if unit not in u_list:
            u_list.append(unit)
    
    
    
    
    o = open(filename_rr_rsx, 'w')
    wl = o.writelines
    
    
    
    with open(path) as f:
        for index, line in enumerate(f):
            if line.startswith('		<train'):
                tn = re.findall('number="(.{4,6})"',line)[0]
                pattern = re.findall('pattern="([^"]+)"',line)[0]
                DoO = patterndaydict.get((tn,pattern))
                run_renamed = run_dict[(tn,DoO)]
                
                
                run = re.findall('lineID=".+~\s(.{1,4})"',line)
                if run:
                    run = run[0] if run else re.findall('lineID="(.*)"',line)[0]
                    line = re.sub(f'~ {run}',f'~ {run_renamed}',line)
                    line = re.sub(f'"{run}"',f'"{run_renamed}"',line)
                    
                else:
                    line = line[:-2] + f' lineID="{run_renamed}">\n'
                    run = ''       
                
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
        messagebox.showinfo('Block Creator','Process Done')
        

except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)   