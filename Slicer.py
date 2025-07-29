import math
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
import sys
import time

import tkinter as tk
from tkinter.filedialog import askopenfilename

import traceback
import logging

ProcessDoneMessagebox = False
ProcessDoneMessagebox = True




weekdaykey_dict = {'120':'Mon-Thu','64': 'Mon','32': 'Tue','16': 'Wed','8':  'Thu', '4':  'Fri','2':  'Sat','1':  'Sun'}






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
    
    

    
    tree = ET.parse(filename)
    root = tree.getroot()
    
    
    
    ### Check for duplicate train numbers before executing the script
    ### Print warning for user if duplicates exist
    ### Print out all duplicates
    tn_list = []
    tn_doubles = []
    patterndaydict = {}
    for train in root.iter('train'):
        tn  = train.attrib['number']; day = train[0][0][0].attrib['weekdayKey']
        pattern = train.attrib['pattern']
        patterndaydict[(tn,pattern)] = day
        if (tn,day) in tn_list: tn_doubles.append((tn,day))
        tn_list.append((tn,day))
            
    if tn_doubles:
        print('           Error: Duplicate train numbers')
        for tn,day in tn_doubles: print(f' - 2 trains runnnig on {weekdaykey_dict.get(day)} with train number {tn} - ')
        time.sleep(15)
        sys.exit() 

    














    desired_blocks = []
    desired_days = []

    count = 0
    cb = tk.Tk()
    cb.title("Choose RSX Slice")
    tk.Label(cb, text="Blocks can be separated by a comma or added one by one and do not need to be uppercase").pack()
    e = tk.Entry(cb,width=50, font=('Calibri',20))
    e.pack()
    # cb.geometry("300x130")

    day_var1 = tk.IntVar()
    day_var2 = tk.IntVar()
    day_var3 = tk.IntVar()
    day_var4 = tk.IntVar()
    
    def myClick():
        myLabel = tk.Label(cb, text=f'{e.get()} added to slice')
        desired_blocks.extend(e.get().split(','))
        myLabel.pack()
        
    def close_window(): 
        desired_blocks.extend(e.get().split(','))
        cb.quit()

    def Add_MTh():
        global count
        if day_var1.get() == 1:
            desired_days.append("120")
            count += 1
        if day_var1.get() == 0 and count > 0:
            desired_days.remove("120")        

    def Add_Friday():
        global count
        if day_var2.get() == 1:
            desired_days.append("4")
            count += 1
        if day_var2.get() == 0 and count > 0:
            desired_days.remove("4")
        
    def Add_Saturday():
        global count
        if day_var3.get() == 1:
            desired_days.append("2")
            count += 1
        if day_var3.get() == 0 and count > 0:
            desired_days.remove("2")
        
    def Add_Sunday():
        global count
        if day_var4.get() == 1:
            desired_days.append("1")
            count += 1
        if day_var4.get() == 0 and count > 0:
            desired_days.remove("1")
        
    # def close_window(): 
    #     cb.quit()
        

    checkbox1 = tk.Checkbutton(cb, text='Monday-Thursday',variable=day_var1, onvalue=1, offvalue=0, command=Add_MTh)
    checkbox2 = tk.Checkbutton(cb, text='Friday',         variable=day_var2, onvalue=1, offvalue=0, command=Add_Friday)
    checkbox3 = tk.Checkbutton(cb, text='Saturday',       variable=day_var3, onvalue=1, offvalue=0, command=Add_Saturday)
    checkbox4 = tk.Checkbutton(cb, text='Sunday',         variable=day_var4, onvalue=1, offvalue=0, command=Add_Sunday)
    # e = tk.Entry(cb,width=50, font=('Calibri',20))
    # e.pack()
    
    
    checkbox1.pack(anchor = "w")
    checkbox2.pack(anchor = "w")
    checkbox3.pack(anchor = "w")
    checkbox4.pack(anchor = "w")
    
    tk.Button(cb,width=20, padx=5, pady=5, text='Add Slice',command=myClick).pack()
    tk.Button(cb,width=20, padx=5, pady=5, text='Finished',command=close_window).pack()
    cb.mainloop()
    cb.withdraw()
    SORT_ORDER_WEEK = ['120','4','2','1']
    desired_days.sort(key=SORT_ORDER_WEEK.index)


    desired_blocks = map(str.upper,desired_blocks)
    desired_blocks = map(str.strip,desired_blocks)
    desired_blocks = list(set(desired_blocks))
    # desired_blocks.sort(key=int)
    print(desired_blocks)
































    
    
    
    
    # window = tk.Tk()
    # window.title("Choose RSX Slice")
    # tk.Label(window, text="Blocks can be separated by a comma or added one by one and do not need to be uppercase").pack()
    # e = tk.Entry(window,width=50, font=('Calibri',20))
    # e.pack()


    # def myClick():
    #     myLabel = tk.Label(window, text=f'{e.get()} added to slice')
    #     desired_blocks.extend(e.get().split(','))
    #     myLabel.pack()
        
    # def close_window(): 
    #     desired_blocks.extend(e.get().split(','))
    #     window.quit()
        
        
        
    # tk.Button(window,width=20, padx=5, pady=5, text='Add Slice',command=myClick).pack()
    # tk.Button(window,width=20, padx=5, pady=5, text='Finished',command=close_window).pack()

    # window.mainloop()
    # window.withdraw()
    
    # desired_blocks = map(str.upper,desired_blocks)
    # desired_blocks = map(str.strip,desired_blocks)
    # desired_blocks = list(set(desired_blocks))
    # # desired_blocks.sort(key=int)
    # print(desired_blocks)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    start_time = time.time()
    blocks = ', '.join(desired_blocks)
    days   = ', '.join([weekdaykey_dict.get(x)  for x in desired_days])
    filename = filename[:-4]
    filename_sliced = f'{filename} ({days}) and ({blocks}).rsx'
    
    
    o = open(filename_sliced, 'w')
    wl = o.writelines
    
    writeblock = True
    
    with open(path) as f:
        for index, line in enumerate(f):
            
            
            
            if line.startswith('		<train'):
                tn = re.findall('number="(.{4,6})"',line)[0]
                run = re.findall('lineID=".+~\s(.{1,4})"',line)
                run = run[0] if run else re.findall('lineID="(.*)"',line)[0]
                
                pattern = re.findall('pattern="([^"]+)"',line)[0]
                DoO = patterndaydict.get((tn,pattern))
                
                if run in desired_blocks and DoO in desired_days:
                    wl(line)
                    writeblock = True
                else:
                    writeblock = False
            
            elif line.startswith('	</timetable>') or line.startswith('</railsys>'):
                wl(line)
                    
            elif writeblock == True:
                wl(line)
    
    o.close()    
    
    print(f'\nNew RSX Created: {filename_sliced}')

    print(f'\n(runtime: {time.time()-start_time:.2f}seconds)')
    
    if ProcessDoneMessagebox:
        from tkinter import messagebox
        messagebox.showinfo('Slicer','Process Done')

except Exception as e:
    logging.error(traceback.format_exc())
    if ProcessDoneMessagebox:
        time.sleep(15)