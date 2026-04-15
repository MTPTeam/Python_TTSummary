import os
import sys


import time
import shutil  

import traceback
import logging

import xml.etree.ElementTree as ET
from taipan.gui.base import select_file, select_option, select_checkboxes, show_info
from taipan.reports.TripCount                 import TTS_TC
from taipan.timetables.PublicTimetable           import TTS_PTT
from taipan.timetables.WorkingTimetable          import TTS_WTT
from taipan.stabling.StablingCount             import TTS_SC
from taipan.stabling.StablingBalance           import TTS_SB
from taipan.reports.RunInfo                   import TTS_RI
from taipan.converters.HASTUS_Converter          import TTS_H
from taipan.converters.TDS_Converter             import TTS_TDS
from taipan.reports.VASExtract                import TTS_VAS
from taipan.reports.TrainMovements            import TTS_TM
# from TrainMovements_fulloutput import TTS_TMFO
from taipan.first_last.FirstLast                 import TTS_FL
from taipan.first_last.SimpleFirstLast           import TTS_SFL
from taipan.constants.days import ID_TO_SHORT

from PyQt6.QtWidgets import QApplication
ProcessDoneMessagebox = copyfile  = False
ProcessDoneMessagebox = True




copyfile = True if os.path.basename(__file__) == 'TimetableSummary - Copy.py' else False


name_dict = {
    TTS_TC:   ('TC',   'Trip Count Report'),
    TTS_PTT:  ('PTT',  'Public Timetables'),
    TTS_WTT:  ('WTT',  'Working Timetables'),
    TTS_SC:   ('SC',   'Stabling Count Report'),
    TTS_SB:   ('SB',   'Stabling Balance Report'),
    TTS_RI:   ('RI',   'RunInfo'),
    TTS_H:    ('H',    'HASTUS Export'),
    TTS_TDS:  ('TDS',  'TDS // JourneyPlanner'),
    TTS_VAS:  ('VAS',  'VAS Extract'),
    TTS_TM:   ('TM',   'Train Movements Tables'), 
    # TTS_TMFO: ('TMFO', 'Train Movements Table (Full Output)'),
    TTS_FL:   ('FL',   'FirstLast'),
    TTS_SFL:  ('SFL',  'Simple FirstLast')
    }

def reset_directory():
    global file
    global direct
    file = os.path.realpath(__file__)
    direct = os.path.dirname(file)
    os.chdir(direct)



def new_report(name):
    reset_directory()
    print(f'\n{name} \n\n')

def fin_report():
    print()
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')  

def Add_Checkbox(var,function_abr):
    global count
    if var.get() == 1:
        desired_reports.append(function_abr)
        count += 1
    if var.get() == 0 and count > 0:
        desired_reports.remove(function_abr)
        

def run_report(script):
    short_name,long_name = name_dict.get(script)
    if short_name in desired_reports:
        new_report(long_name)
        script(path,mypath)
        fin_report()        
        






try:


    app = QApplication(sys.argv)

    path = select_file("Select a timetable RSX file")
    if not path:
        print("No file selected. Exiting.")
        sys.exit()

    directory = os.path.dirname(path)
    os.chdir(directory)
    filename = os.path.basename(path)
    print(filename,'\n')
    
    
    ### Check for duplicate train numbers before executing the script
    ### Print warning for user if duplicates exist
    ### Print out all duplicates
    tree = ET.parse(filename)
    root = tree.getroot()
    tn_list = []
    tn_doubles = []
    for train in root.iter('train'):
        tn  = train.attrib['number']
        day = train[0][0][0].attrib['weekdayKey']
        if (tn,day) in tn_list: tn_doubles.append((tn,day))
        tn_list.append((tn,day))
            
    if tn_doubles:
        print('           Error: Duplicate train numbers')
        for tn,day in tn_doubles: print(f' - 2 trains runnnig on {ID_TO_SHORT[day]} with train number {tn} - ')
        time.sleep(15)
        sys.exit()  
    
    
    
    
    report_options = [
        ('TripCount', 'TC'),
        ('Public Timetable', 'PTT'),
        ('Working Timetable', 'WTT'),
        ('Stabling Count', 'SC'),
        ('Stabling Balance', 'SB'),
        ('Run Info', 'RI'),
        ('HASTUS Export', 'H'),
        ('TDS // Journey Planner', 'TDS'),
        ('VAS Extract', 'VAS'),
        ('Train Movement Tables', 'TM'),
        ('First Last', 'FL'),
        ('Simple First Last', 'SFL'),
    ]
    desired_reports = select_checkboxes(
        'Choose Reports to Archive',
        'Select one or more reports to run:',
        report_options,
    )
    if not desired_reports:
        print('No reports selected. Exiting.')
        sys.exit()

    print('Timetable Summary\n')
    
    tts_start_time = time.time()
    
    if copyfile:
        
        mypath = '//Cptprdfps001/ServicePlan/SMTP/02 PROJECTS/WPy64-3740/_TimetableSummary_Repository/'
        refnum_list = [int(x) for x in next(os.walk(mypath))[1]]
        new_refnum = str(      (max(refnum_list) if refnum_list else 11110) + 1     )
        mypath += new_refnum
        if not os.path.exists(mypath):
                os.makedirs(mypath)
        print('New Timetable Reference Number Created')
        print('—————————————————————————————————————————————————————————————————————————————————————————')
        print(mypath)
        print('—————————————————————————————————————————————————————————————————————————————————————————\n')
        print() 
            
        
    
    else:
        mypath = directory
     
    
    
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')
    print('———————————————————————————————————————————————————————————————————————————————————————————————————————————————————')  
  

    
        
    run_report(TTS_TC)
    run_report(TTS_PTT)
    run_report(TTS_WTT)
    run_report(TTS_SC)
    run_report(TTS_SB)
    run_report(TTS_RI)
    run_report(TTS_H)
    run_report(TTS_TDS)
    run_report(TTS_VAS)
    run_report(TTS_TM)
    # run_report(TTS_TMFO)
    run_report(TTS_FL)
    run_report(TTS_SFL)
    
    
    if copyfile:
        print('\nCopying RSX')
        destination = os.path.join(mypath, os.path.basename(filename))
        if os.path.abspath(filename) != os.path.abspath(destination):
            shutil.copy(filename, destination)
        else:
            print('Skipping copy because source and destination are the same file')  

    
    if ProcessDoneMessagebox:
            print(f'\n(runtime: {time.time()-tts_start_time:.2f}seconds)')
            show_info('TimeTable Summary', 'Process Done')
except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)



