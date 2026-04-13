import xml.etree.ElementTree as ET
import os
import re
import sys
import string
import pandas as pd
import xlsxwriter
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import traceback
import logging

ProcessDoneMessagebox = False
ProcessDoneMessagebox = True

def generate_ew(prefixes):
   # helper to generate electric workings for each unit type and day of operation
   # this prevents indexing errors by ensuring that there are always enough electric workings for the number of runs in each unit type and day of operation category
   result = []
   for p in prefixes:
       for c in string.ascii_uppercase:
           result.append(p + c)
   return result

weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
wk_dep_ew  = generate_ew(['Z'])
wk_ngr_ew  = [str(i) for i in range(1, 150)]
wkd_emu_ew = generate_ew(['A','B','C','D','E'])
wkd_imu_ew = generate_ew(['F','G','H'])
fri_imu_ew = generate_ew(['N','U','V','W'])
sat_emu_ew = generate_ew(['I','J'])
sat_imu_ew = generate_ew(['K','L','M'])
sun_emu_ew = generate_ew(['O','P'])
sun_imu_ew = generate_ew(['Q','R'])
#QTMP Electric Workings Allocation...
wk_rep_ew  = []
wkd_rep_ew = []
sat_rep_ew = []
sun_rep_ew = []
# Script needs further modification to facilitate new unit type

try:
   
   Tk().withdraw()
   path = askopenfilename()
   directory = '\\'.join(path.split('/')[0:-1])
   os.chdir(directory)
   filename = path.split('/')[-1]
   print(filename,'\n')
   tree = ET.parse(filename)
   root = tree.getroot()
   filename = filename[:-4]
   filename_rr_rsx = f'{filename} (renamed).rsx'

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
   def reassign_runs(list_of_runs, electric_workings):
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
   reassign_runs(fri_imu, fri_imu_ew)
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
           if line.startswith('        <train'):
               tn = re.findall('number="(.{4,6})"',line)[0]
               run = re.findall(r'lineID=".+~\s(.{1,4})"',line)
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
           elif line.startswith('                  <connection'):
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