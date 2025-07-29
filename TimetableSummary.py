import os
import sys
import time
import shutil  

import traceback
import logging

import tkinter as tk
from tkinter.filedialog import askopenfilename
import xml.etree.ElementTree as ET
from TripCount                 import TTS_TC
from PublicTimetable           import TTS_PTT
from WorkingTimetable          import TTS_WTT
from StablingCount             import TTS_SC
from StablingBalance           import TTS_SB
from RunInfo                   import TTS_RI
from HASTUS_Converter          import TTS_H
from TDS_Converter             import TTS_TDS
from VASExtract                import TTS_VAS
from TrainMovements            import TTS_TM
# from TrainMovements_fulloutput import TTS_TMFO
from FirstLast                 import TTS_FL
from SimpleFirstLast           import TTS_SFL

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
    
    rsxselecta = tk.Tk()
    rsxselecta.withdraw() # we don't want a full GUI, so keep the root window from appearing
    rsxselecta.update()
    path = askopenfilename() 
    rsxselecta.destroy()
    
    directory = '\\'.join(path.split('/')[0:-1])
    os.chdir(directory)
    filename = path.split('/')[-1]
    print(filename,'\n')
    
    
    ### Check for duplicate train numbers before executing the script
    ### Print warning for user if duplicates exist
    ### Print out all duplicates
    weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}
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
        for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
        time.sleep(15)
        sys.exit()  
    
    
    
    
    desired_reports = []
    
    count = 0
    cb = tk.Tk()
    cb.title('Choose Reports to Archive')
    cb.geometry("330x360") # w x h (add 30 height for every box)
    
    var1  = tk.IntVar()
    var2  = tk.IntVar()
    var3  = tk.IntVar()
    var4  = tk.IntVar()
    var5  = tk.IntVar()
    var6  = tk.IntVar()
    var7  = tk.IntVar()
    var8  = tk.IntVar()
    var9  = tk.IntVar()
    var10 = tk.IntVar()
    var11 = tk.IntVar()
    var12 = tk.IntVar()
    var13 = tk.IntVar()
            
    
    def Add_SimpleFirstLast():
        Add_Checkbox(var13,'SFL')
    
    def Add_FirstLast():
        Add_Checkbox(var12,'FL')
    
    # def Add_TrainMovementsFull():
    #     Add_Checkbox(var11,'TMFO')
        
    def Add_TrainMovements():
        Add_Checkbox(var10,'TM')
        
    def Add_VAS():
        Add_Checkbox(var9,'VAS')
        
    def Add_TDSjourneyplanner():
        Add_Checkbox(var8,'TDS')
        
    def Add_HASTUS():
        Add_Checkbox(var7,'H')
        
    def Add_RunInfo():
        Add_Checkbox(var6,'RI')
        
    def Add_StablingBalance():
        Add_Checkbox(var5,'SB')
    
    def Add_StablingCount():
        Add_Checkbox(var4,'SC')
            
    def Add_WTT():
        Add_Checkbox(var3,'WTT')
    
    def Add_PTT():
        Add_Checkbox(var2,'PTT')
            
    def Add_TripCount():
        Add_Checkbox(var1,'TC')
          
    
          
            
    
        
    
    checkbox1  = tk.Checkbutton(cb, text='TripCount',                    variable=var1, onvalue=1, offvalue=0, command=Add_TripCount)
    checkbox2  = tk.Checkbutton(cb, text='Public Timetable',             variable=var2, onvalue=1, offvalue=0, command=Add_PTT)
    checkbox3  = tk.Checkbutton(cb, text='Working Timetable',            variable=var3, onvalue=1, offvalue=0, command=Add_WTT)
    checkbox4  = tk.Checkbutton(cb, text='Stabling Count',               variable=var4, onvalue=1, offvalue=0, command=Add_StablingCount)
    checkbox5  = tk.Checkbutton(cb, text='Stabling Balance',             variable=var5, onvalue=1, offvalue=0, command=Add_StablingBalance)
    checkbox6  = tk.Checkbutton(cb, text='Run Info',                     variable=var6, onvalue=1, offvalue=0, command=Add_RunInfo)
    checkbox7  = tk.Checkbutton(cb, text='HASTUS Export',                variable=var7, onvalue=1, offvalue=0, command=Add_HASTUS)
    checkbox8  = tk.Checkbutton(cb, text='TDS // Journey Planner',       variable=var8, onvalue=1, offvalue=0, command=Add_TDSjourneyplanner)
    checkbox9  = tk.Checkbutton(cb, text='VAS Extract',                  variable=var9, onvalue=1, offvalue=0, command=Add_VAS)
    checkbox10 = tk.Checkbutton(cb, text='Train Movement Tables',        variable=var10, onvalue=1, offvalue=0, command=Add_TrainMovements)
    # checkbox11 = tk.Checkbutton(cb, text='TrainMovements (Full Output)', variable=var11, onvalue=1, offvalue=0, command=Add_TrainMovementsFull)
    checkbox12 = tk.Checkbutton(cb, text='First Last',                   variable=var12, onvalue=1, offvalue=0, command=Add_FirstLast)
    checkbox13 = tk.Checkbutton(cb, text='Simple First Last',            variable=var13, onvalue=1, offvalue=0, command=Add_SimpleFirstLast)
    
    checkbox1.pack(anchor  = "w")
    checkbox2.pack(anchor  = "w")
    checkbox3.pack(anchor  = "w")
    checkbox4.pack(anchor  = "w")
    checkbox5.pack(anchor  = "w")
    checkbox6.pack(anchor  = "w")
    checkbox7.pack(anchor  = "w")
    checkbox8.pack(anchor  = "w")
    checkbox9.pack(anchor  = "w")
    checkbox10.pack(anchor = "w")
    # checkbox11.pack(anchor = "w")
    checkbox12.pack(anchor = "w")
    checkbox13.pack(anchor = "w")
    
    def close_window(): 
        cb.quit()
    
    tk.Button(cb,width=20, padx=5, pady=5, text='OK',command=close_window).pack()
    cb.mainloop()
    cb.withdraw()
    
    
    
    
    
    
    
    
    
    
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
        shutil.copy(filename, mypath)  

    
    if ProcessDoneMessagebox:
            print(f'\n(runtime: {time.time()-tts_start_time:.2f}seconds)')
            from tkinter import messagebox
            messagebox.showinfo('TimeTable Summary','Process Done')
except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)



