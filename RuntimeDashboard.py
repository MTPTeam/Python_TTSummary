import os
import time
import logging
import traceback
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import math
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from dash import dcc, html, Input, Output, State, dash_table, ctx, no_update
from dash_extensions.enrich import DashProxy, MultiplexerTransform
import plotly.graph_objects as go
import webbrowser
import threading
import socket
import ctypes

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
OpenWorkbook = CreateWorkbook = ProcessDoneMessagebox = False
ProcessDoneMessagebox = True
CreateWorkbook = True
OpenWorkbook = True
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
weekdaykey_dict = {'120': 'Monday-Thursday','64': 'Monday','32': 'Tuesday','16': 'Wednesday','8': 'Thursday','4': 'Friday','2': 'Saturday','1': 'Sunday'}
weekdaykey_dict2 = {'120':'Mon', '4':'Fri', '2':'Sat', '1':'Sun'}
weekdayabr_dict = {'Monday-Thursday':'Mon-Thurs', 'Friday':'Fri', 'Saturday':'Sat', 'Sunday':'Sun'}
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Used for conversion between the name of each location and its abbreviated version
stationmaster = {
    'Fortitude Valley':'BRC',
    'Electric Train South': 'ETS',
    'Elec Train S': 'ETS',
    'Campbell St': 'CAM',
    'Exhibition ':'EXH',
    'Exhibition': 'EXH',
    'Normanby': 'NBY',
    'Roma Street': 'RS',
    'Central': 'BNC',
    'Brunswick Street': 'BRC',
    'Bowen Hills': 'BHI',
    'Mayne': 'MNE',
    'Albion': 'AIN',
    'Wooloowin': 'WWI',
    'Eagle Junction': 'EGJ',
    'Toombul': 'TBU',
    'Nundah': 'NND',
    'Northgate': 'NTG',
    'Bindha': 'BHA',
    'Banyo': 'BQY',
    'Nudgee': 'NUD',
    'Boondall': 'BZL',
    'North Boondall': 'NBD',
    'Deagon': 'DEG',
    'Sandgate': 'SGE',
    'Shorncliffe': 'SHC',
    'Caboolture East Yard': 'CAE',
    'Caboolture': 'CAB',
    'Caboolture North': 'CEN',
    'Elimbah Stabling Yard': 'EMHS',
    'Kippa-Ring Stabling Yard': 'KPRS',
    'Kippa-Ring': 'KPR',
    'Airport Junction': 'AJN',
    'Virginia': 'VGI',
    'Sunshine': 'SSN',
    'Geebung': 'GEB',
    'Zillmere': 'ZLL',
    'Carseldine': 'CDE',
    'Bald Hills': 'BDS',
    'Strathpine': 'SPN',
    'Bray Park': 'BPR',
    'Lawnton': 'LWO',
    'Petrie': 'PET',
    'Dakabin': 'DKB',
    'Narangba': 'NRB',
    'Burpengary': 'BPY',
    'Morayfield': 'MYE',
    'Mayne North Yard': 'YN',
    'Mayne North':'YN',
    'Mayne Yard Arrival': 'YNA',
    'Roma St West Junction': 'RSWJ',
    'South Brisbane': 'SBE',
    'South Bank': 'SBA',
    'Park Road': 'PKR',
    'Dutton Park': 'DUP',
    'Fairfield': 'FFI',
    'Yeronga': 'YRG',
    'Yeerongpilly': 'YLY',
    'Moorooka': 'MQK',
    'Rocklea': 'RKE',
    'Salisbury': 'SLY',
    'Coopers Plains': 'CEP',
    'Banoon': 'BQO',
    'Sunnybank': 'SYK',
    'Altandi': 'ATI',
    'Runcorn': 'RUC',
    'Fruitgrove': 'FTG',
    'Kuraby': 'KRY',
    'Trinder Park': 'TDP',
    'Woodridge': 'WOI',
    'Kingston': 'KGT',
    'Loganlea': 'LGL',
    'Bethania': 'BTI',
    'Edens Landing': 'EDL',
    'Eden\'s Landing': 'EDL',
    'Eden’s Landing': 'EDL',
    'Holmview': 'HVW',
    'Beenleigh': 'BNH',
    'Beenleigh Turnback': 'BNT',
    'Electric Train Flyover': 'ETF',
    'Elec Train Flyover':'ETF',
    'Electric Depot Junction': 'EDJ',
    'Ipswich Stabling':'IPSS',
    'Ipswich Stabling Yard': 'IPSS',
    'Ipswich Stable':'IPSS',
    'Ipswich': 'IPS',
    'Milton': 'MTZ',
    'Auchenflower': 'AHF',
    'Toowong': 'TWG',
    'Taringa': 'TIQ',
    'Indooroopilly': 'IDP',
    'Chelmer': 'CMZ',
    'Graceville': 'GVQ',
    'Sherwood': 'SHW',
    'Corinda': 'CQD',
    'Oxley': 'OXL',
    'Darra': 'DAR',
    'Wacol': 'WAC',
    'Gailes': 'GAI',
    'Goodna': 'GDQ',
    'Redbank': 'RDK',
    'Riverview': 'RVV',
    'Dinmore': 'DIR',
    'Ebbw Vale': 'EBV',
    'Bundamba': 'BDX',
    'Booval': 'BOV',
    'East Ipswich': 'EIP',
    'Rothwell': 'RWL',
    'Mango Hill East': 'MGE',
    'Mango Hill': 'MGH',
    'Murrumba Downs': 'MRD',
    'Kallangur': 'KGR',
    'Richlands': 'RHD',
    'Springfield': 'SFD',
    'Springfield Central': 'SFC',
    'Thomas Street': 'THS',
    'Wulkuraka': 'WUL',
    'Karrabin': 'KRA',
    'Walloon': 'WOQ',
    'Thagoona': 'TAO',
    'Yarrowlea': 'YLE',
    'Rosewood': 'RSW',
    'Buranda': 'BRD',
    'Coorparoo': 'CRO',
    'Norman Park': 'NPR',
    'Morningside': 'MGS',
    'Cannon Hill': 'CNQ',
    'Murarrie': 'MJE',
    'Hemmant': 'HMM',
    'Lindum': 'LDM',
    'Lytton Junction': 'LJN',
    'Wynnum North': 'WYH',
    'Wynnum': 'WNM',
    'Wynnum Central': 'WNC',
    'Manly': 'MNY',
    'Lota': 'LOT',
    'Thorneside': 'TNS',
    'Birkdale': 'BDE',
    'Wellington Point': 'WPT',
    'Ormiston': 'ORO',
    'Cleveland': 'CVN',
    'Elimbah': 'EMH',
    'Beerburrum': 'BEB',
    'Glasshouse Mountains': 'GSS',
    'Beerwah': 'BWH',
    'Landsborough': 'LSH',
    'Mooloolah': 'MOH',
    'Eudlo': 'EUD',
    'Palmwoods': 'PAL',
    'Woombye': 'WOB',
    'Nambour': 'NBR',
    'Mayne Junction': 'MYJ',
    'Windsor': 'WID',
    'Wilston': 'WLQ',
    'Newmarket': 'NWM',
    'Alderley': 'ADY',
    'Enoggera': 'EGG',
    'Gaythorne': 'GAO',
    'Mitchelton': 'MHQ',
    'Oxford Park': 'OXP',
    'Grovely': 'GOQ',
    'Keperra': 'KEP',
    'Ferny Grove': 'FYG',
    'Robina Stabling Yard': 'ROBS',
    'Robina': 'ROB',
    'Varsity Lakes': 'VYS',
    'Caboolture West Yard': 'CAW',
    'International Airport': 'BIT',
    'Domestic Airport': 'BDT',
    'Ormeau': 'ORM',
    'Coomera': 'CXM',
    'Helensvale': 'HLN',
    'Nerang': 'NRG',
    'Beenleigh Stabling Yard': 'BNHS',
    'Beenleigh Stable': 'BNHS',
    'Banyo Stabling Yard': 'BQYS',
    'Wulkuraka Service Centre East': 'WFE',
    'WSC East Entrance': 'FEE',
    'Redbank Stabling Yard': 'RDKS',
    'Redbank Stabling':'RDKS',
    'Roma St Fork': 'RSF',
    'Clayfield': 'CYF',
    'Hendra': 'HDR',
    'Ascot': 'ACO',
    'Doomben': 'DBN',
    'Clapham Yard': 'CPM',
    'Varsity Lakes Turnback': 'VYST',
    'Varsity Lakes TB': 'VYST',
    'Woombye Stabling Yard': 'WOBS',
    'Gympie North': 'GYN',
    'Glanmire': 'GMR',
    'Woondum': 'WOO',
    'Traveston': 'TRA',
    'Cooran': 'COZ',
    'Pomona': 'PMQ',
    'Cooroy': 'COO',
    'Sunrise': 'SSE',
    'Eumundi': 'EUM',
    'North Arm': 'NHR',
    'Yandina': 'YAN',
    'Wulkuraka Service Centre West': 'WFW',
    'WSC West Entrance': 'FWE',
    'Tennyson': 'TNY',
    'Moolabin': 'MBN',
    'Rocklea sidings': 'RKET',
    'Rocklea Sidings': 'RKET',
    'Electric Train Balloon': 'ETB',
    'Elec Train Balloon': 'ETB',
    'Petrie Stabling Yard': 'PETS',
    'Petrie Eastern Sdgs': 'PETS',
    'Mayne East Stabling Yard':'MES',
    'Mayne North Stabling':'MNS',
    'Mayne 2':'MNE2',
    'Ormeau Stabling':'ORMS',
    'Pimpama':'PIA',
    'Hope Island':'HID',
    'Merrimac':'MRC',
    
    'Boggo Road':'BOG',
    'Boggo Road station':'BOG',
    'Albert Street':'ALB',
    'Woolloongabba':'WLG',
    
    'Mayne North Stabling':'MNS',
    'Mayne East':'MES',
    'Mayne East Stabling':'MES',
    'Clapham Yard':'CPM',
    
    'Beerwah Junction': 'BWJ', 
    'Beewah East Junction': 'BEJ', 
    'Aura': 'AUR', 
    'Caloundra Road': 'CRD', 
    'Mayne North Yard Entrance': 'MNYE', 
    'Bowen Hills North Jn': 'BHNJ', 
    'Signal 10 Departure': 'SIG10D', 
    'Kippa-Ring Stable': 'KPRS', 
    'Ormeau Junction': 'ORMJ', 
    'Salisbury Junction': 'SLYJ', 
    'Yeerongpilly Junction': 'YLYJ', 
    'Southern Tunnel Portal': 'STP', 
    'Northern Tunnel Portal': 'NTP', 
    'Land Bridge': 'LBR', 
    'Tunnel Jn': 'ZZZTJN', 
    'Mayne East Junction': 'MEJ', 
    'Clapham Yard Junction': 'CYJ', 
    'Signal 9 Arrival': 'SIG9A', 
    'Mayne East Yard': 'MES', 
    'Fork Timing Point': 'FRK', 
    'Tennyson Branch Junction': 'TNYBCHJ',
  }
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Non-revenue locations for toggling on/off
non_revenue_stations = [
    'RSWJ',
    'RSF',
    'MNE',
    'LJN',
    'ETF',
    'EDJ',
    'YLE',
    'ETS',
    'CAM',
    'EXH',
    'NBY',
    'YNA',
    'YN',
    'MYJ',
    'AJN',
    'IPSS',
    'VYST',
    'CAW',
    'CAE',
    'CEN',
    'BNHS',
    'BNT',
    'EMHS',
    'RKET',
    'WOBS',
    'PETS',
    'KPRS',
    'RDKS',
    'BQYS',
    'ROBS',
    # 'WUL',
    'WFE',
    'FEE',
    'WFW',

    'NTP',
    'STP',
    'SIG9A',
    'SIG10D',
    'ZZZTJN',
    'TNYBCHJ',
    'YLYJ',
    'BHNJ',
    'MEJ',
    'ORMS',
    'MNYE',

    #F3S
    'MNS',
    'MES',
    'MWS',
    'CPM',

    'NHR', #North Arm
    'SSE', #Sunrise
    'WOO', #Woondum
    'GMR', #Glanmire
    
    # 'DUP', #Dutton Park
    # 'RKE', #Rocklea
    
    'BWJ',    #Beerwah Junction
    'BEJ',    #Beewah East Junction
    'MNYE',   #Mayne North Yard Entrance
    'BHNJ',   #Bowen Hills North Jn
    'SIG10D', #Signal 10 Departure
    'KPRS',   #Kippa-Ring Stable
    'ORMJ',   #Ormeau Junction
    'SLYJ',   #Salisbury Junction
    'YLYJ',   #Yeerongpilly Junction
    'STP',    #Southern Tunnel Portal
    'NTP',    #Northern Tunnel Portal
    'LBR',    #Land Bridge
    'ZZZTJN', #Tunnel Jn
    'MEJ',    #Mayne East Junction
    'CYJ',    #Clapham Yard Junction
    'SIG9A',  #Signal 9 Arrival
    'MES',    #Mayne East Yard
    'FRK',    #Fork Timing Point
    'TNYBCHJ',#Tennyson Branch Junction
    ]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
snake_logo = "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAT8AAAGlCAIAAAADOWbZAAAAA3NCSVQICAjb4U/gAAAgAElEQVR4nOydd5wd5XX3zzlPmbl9927RrqRVRSsJCTWaQDTbVBsXbOMS+42Na3DeuCd2II5t3MAYCO523OKWQEIIYGIMBNObaAIk1FDXanu5be7MPM857x9XYJzYjnHwx2+s/X7ms5/dO3N35rl3fnPO85zznAdgmmmmmWaaaaaZZppppplmmmmmmWaaaf5/A//QF/DHDiICHvycf/nDFgAEEDi459lfnt118B8AH9z3n/8zAIDIwXO0XpLnHCm/fCQAoPziFRR5zt/PeZ1/xalaJ2n9YAYBQBRABAGR1o7nXv6z7xKU1g4G+ZVtmOZ/xLR6fw8cvNERSSMRoUYiAEBARBFgL4JAAnjwrhdEFJaWCoVQsPUCOwQhYRQGaUlaAFvPAkEFgMgMAohECCRA3h88Mwi4g9eCgAe1Q8CIKAwibI0AeGntEAEQRAEB8SKth4m0LhlEAFFIGUAlAJ6FBYhQhAnAI6Hgc54QzzyKEEBaDWTxnl0szPCrn0PT/I7oP/QF/LFBpEAZJEVEpDQqjWBIETKgiNLA4J04RAIgES2gEdF5JmAgAC8AKbKTpAnMAM57ARCQlpwACQCAAAAANZFAwqzJAhAhUWBYkFATagJgAABUSjnvAcCAAAiAZ5eYkF0i4h2AeO8AQKN4BvEHFeZbp0MUEU0gIooyTgQRSRttAiRh7wkVC2mlxHsBICWAKEAiYJA8gPcgnHJqOI1ZUgEAAZBpa/wCMG17X0iQjLY51CEqJIUICEQGATyDiHNOOE3BIQkhsYA2GcRQ0AqSVZQmkaKEIJE4CjVmNAQhWautsVplEAgJGFKGlMQwSzOJkyhtJBB7n6RpmqZam9irJIUgyCltGVAQlVIIiOB9ksbNBpHTiglSETbaZKyxShmDmVAba7QCIgAwBIYZBBjQOd+M6nEUc+whijluJhQWsqVyNUpBKQ3s04RdrEAcp4QkoDwzASgbIhmllHeJT2IW1/IixDtOmiD+D/2N/e9mWr0vGIhKBQUdFEEFRKI1CCdps47skBMS0eCCjA7DjDbaeVet15w3UZNFwsDkA6sFk2JBTj31+Nk9pTJMlUyzvURthXw2LCksKG3FcIq1lOuGc+J0tdEYn6hX6lKP07HJqeGhkdHRiaFxPxa78amoNtUUso7BM2hCIq8kzRcyhULQYVVvp+2d1d1ZLreXCm25oJSnUjGbCS2pRBtnsKig6GMQSJVJGunkRKMyXnFTTTtZy258avctdz8yEWvKtCXO+WgSknohxKzxqLSxWpNKkjROXeJN6hF1JnVAxqIGzx7EsHOcVDlugLg/9Pf2v5hpz/kFA0mTzqDOECkFjptVF1fENUrF3PxZ7fN6uub05Of2tXV19VgTVuqVXYMHDuyrPb1rZO/+qYlavTJZY01LFiw8/cUnrF09p+x2QTzuGhXlY4MS10eFyCtOlXOcGu8NBrrb0GGdSIpIey9OxHtIUto9FT+xbffmLcP7R+r79gwOTcW5gObN6+mbUVjaP2PpvJl9pbCQt6E1mhDBMzsQEHbsneOml7qRpvZVRAREHZK3Cgu9YVuOwhkNWXTznZuf3LJjavdIczIWn3YVTd/87pWHdS6cE3b0tBcKhVwQVCeqQ4MTewaaT+4Yfnrf2MBY4iVLipQxIkbQIgABSlITnrbAvyPTtveFApXNmqCdlNUKgeO4NlrOweqlfWeduvL41X2zusNiVkniJEXxoKwxWR1FbmzKPbZp/4NP7rnr/q1P7BxuRGm5s3D80UtPO27BUYf39rareGInNkdD5dkzKZ2yImXIexAWBABCpUVIG6O1BSREpEJocgVtCrU6DwxM7hmoFnO4cEFnoaAIY19puHoCImkSs3fMnjlFYURBRCBOODYE2oMWEdQpqFQXdNuMNCjsHeOf3b3nR1f/fODAOBF0d7atWdz3ohOPWLdm9swum8+IE8epU5wGSIHNJBDuG4nu37j/2ls3PPj4zqGpOgY5m2lzPuNZOIkgrfi4DtMC/p2YVu8LAypjbM4EefSJVdxoTC6Z1/m2V64656zj82HKzbFmdYiTqjiPnhQYBOJUKDBBqUD5PGbath9o/tO1j/zk9k1P7RoBAKvgrFNWvP1PXnTEQuur26k5bCTVEEKaUZgVrDAmz4zwogC1YkAgyAioEkEBCKwthZmS0dpx2owqzeYkcJPAAgcoIiB4MBgkAAzACOBRNZmtToEbmtiD8dSRLS8eb7b/63889oNrb9u0owIA7cVw3fJZbzrrqLNOWmGp0YwnK41x71OInfJOQao4FUC0YaatW5VmNDB3yz2PX/3vT9z54E6HGk07BqVm1ARX93GVk8b0INbvgPpDX8AfBUhKZ4MwQ8AK4rRZPfaImZ/54CtecfIibg5Vh3dyYwTjKS2JBW/QEzgFbFGQm3E8GkVD9WhkRlfhuONWzu2bUxuvjIxXm542P31g49a9xXLb3AVzlUEBSJpsqSBeMcZADIgA9KyGAVvRIjSMhjV54tQltSiqVpNaXZJIezBMKCSIgIDPBq0ObgiITpQNC7GLWXtnVBNzpZ7D900Uv/Ct2772/VsGxmMg6F/Y/Y5zj/vI2049fmkpHt3cHN/ZrA8zN8lz4LwVb8Vp9BpTdpH3jYnxAwj1I4+Ye/Sapa7pNz+1z7PTJnCghBCFmVPgXxVonuY3Mq3eFwAkrWzOZAri4ySq9M9pv/xv37SiPzM5tKUxNagg1sDAnpAEiAmFkBE9oCgG8ogiPq1MTnKcLu+fd9yaxUmzsX94Mkl4YHhq/cOb20rdixctUkr7JPZJbA0CsQACKAAlQAgKgA4qWYgkQLHS0gaBkAABgUIxKIEQSSsn49kcD4DW2wUIUYlDx46CTAr5fMfivaP5i75081U33c8CbfngpKMW/837XvnKFy3N0+TU0BYfjxPGhIxAKKBBEBhQGEmAVGC9sIgnTqvjg+3Z3IlrV/lE7n1km0IU0qiIQYA9eDcdDX6+TKv3BUApo20OVejiekjJFR9/46ol4fjQRnGTRgEhWZMxNs9kUlEpKkc6JUyVOEIBQtEWg4C0q9d8NN6Vdy85aUlnV2lkuJLUmyNVd9/6rZ2F4qrl/T6d0lRXFDGjoHrG8CoUeka9BAAChkkxsVOOVcIq8egFhVEJKEAAbPUzEQBbuVKC2LK9WkCazXw2X4ug3LV4eKrtwsuu/8kdjwUAvTPb3/CKoy565ynLZtrayI7q5B6PEWgQQgZFracCMhM6xIS01xkMsjrIIWpJnWLmZt1qvXrlyu07hrfuOoDKoLYCdDCHhafHn58f0+p9ASAy2mYMqkblwOtOX/GuN62rj+3AZBx9LGDQlPYO+4bkMuVeCgoJIDMLeUZHqEAMsCG0nDJKarHpmsMaKmuPOuzYI5emdT8xWRucaj7xxLbF8zsXL+gGN0ESiWgEhYAAQNLKfHzWgQZBYfKsUqEEKGVMgQBBBEEQEDw+o9Zn3ojPpFuKQdDsBTSoNrEz33/R1f9+31NdeXvimrnve/upb3zpirI/UB/ZhRA5SXRgPSkWQlTggUAEU4/gKFS5TpWfMRUH+4frmUwxoxQmsSFI4rRQKM+dN++G/1jvPIgOAAwBsE/Fp3/ob/J/GdPqfQFAZYwOXbPaYZNPf+i07nyjOT6eZW8ZTDhjPCl++PM33/zwfs7NKLTP6CgVNXjrmqFPjAAJMoMoJURkSMALeh83q6OjM7vKJ52wZmZv+9TExNOD9ebkyEuOX2w4JedAqJUBiSCAjL/ou7a2g0NQJEisFRvNikAREAEjyDNpmnBQw9DStSAAsAuUiliF7T0/vvGxb/7b+sP6Sn/x+mP/6u2nr+kL/cTORnNMyDt2Rmtxgk40kFFamBE9KUFls219kpnz8I70O9es/8aP7+hfMHfhzLJOpgh0nIDndM78voce27Jl95AK8gyhsBPfZDftPD8/ptX7PwYJtDU6jBoTq/t73vnG49LKXnLeiCBqW5z11AG4/Af3b91XueOBp57ePdpeLM6ZNStjNXIziWNBMlalcaQVAAAyAmgQ0koq1YoDXr580aplswvGhxCtXTVbSwQ+RsTnxgsQfzF0BfjcFxABCQmBnrG1rX7ufxLJL/5UCMwpGpuS2rB576xO84E/PflVLzta6oOuOpg0JlkZEVIIxKxEULwiAWDUFAtD2JbtnD9cy/zwJ49f/I2f/vzBbcNVXrm07+jlc11jNE1dmMvVolqps1yJ6Wd3baEgCxiIa6k3nVbv82I6W+N/BhLaAIMQSAPIYXN7S8X8yEhUMFZSbLJCFU7FziOFeUYT3HLXU+vXb/7Qu1/xujOXlbIMMAEu9j4OjZDEIFpEMRtUzBgxxq42Uq83+srdH3zrcezqktRcVFeKgen31CAhZOA4rWljX3fmwnzpaEAztHcTpPWMZgy0sEYQZK/Aa2RtdTWO0IQeSLd1x9S7YUvty9/76U33PA2kw0KuWa0PVRppkE9NRlPE0kSSSmVy6ZL5mUA1nSPLQM848dPifT5Mq/d3BxHRhBBkKciIVwDSN7uURtVAg0FJBDygDfP1eAhAEm+DIN8+o9BRavvUV2/ctW/oz849Zk53R3Nqv/EVSKcIPIiIkIDyDrz4IDBxXC8E0hga18oEoU7iOoEHTfBfzecLRMpeUJQWl0zmsqVobE+Suoy1bFziEqWMIKMwSqogRfZx5JTNpJRR+Q5d7P3pnfs+/5Xrsm3ze2bNrtab3oRQq49XGxGTUtb7WrNR05lc3Ky0Fbu7OjM7R2JrBQERCfG/Tlmc5jfx+3qE/9GDSEpnVZDDMCCtAQRA9c7oFk6NpiSqk7AGMYp8swoiaHJRJemZMe9rX//6eeed991rHvrgp6+5d2Nd5xfawkxPGUYS8oIJUALkBTWJVt5RXCspV6KE4qoVT6CZteDvrctDSsiiMuBTV58wvlHQjlxDOEWlUSNgE6CuKAVgFmAIhNpNbl4kM6/41r3v/9gPjl531k0/vf6kU05tNkXEgmCt1mQXW4MC3lgCdEguE6pyextIiiCARGSIzLMzlaf5bZhW7+8CIikTmqCgdIaIkADRaU2lUo7ZpUkCAprEgOO4agEUIvoUFE1O1g5fuuyrX/va+977nge2Tf35J//hlvWDdZ6hC/O87fA6TNGDitE4o7Nxk622SlA5x3GsvIADYAUStAaYfv3ltbI2DvJbNOc5B4vyXgvrgDLao2aB1CsBTVqEWFDpCDBCw44wwawE3UFp0YFK6YJLr7/su3e9/NVv+NKXvtw7c06zFknC4hJldX0y1uDiaFITAIEw+7QZGgxDo1EQ2FirgsCEOdLBtIB/e6bV+7xBRGVDFeTIhITaKEL0iN652HNKhAyMRASCkhCk5UIWAbJWKXAT4yNTkxNE6vIrrvzQ+94fufD8v/nmd697vKbnqPbDEtPBQcZr76XpnNfKAisUJagQNQgpMgBa+PfpYSIqNMAEQggGQCNaAA0MijQygyTaYCPlSDJQmG07l9y7uf6uC7593Z3b3vmOd33ja1/t6OgEgHq9AgKGRANq8VkDlliYAZQAsheNRECawKdNIjTakAl0MC3g58F0v/f5gYjKZlSQVyo0FHhJ2SVpGmsgBKjXakq1IyoG5cULsHNpW1toNKScGhM2q0ONRl1EkPCzl3yqXG6/7MrLP/H1f9s3UXvbucfP6VzIjb1pNBBo5pRFgBEcAoJqlatgAAD+vWanI0grqiSAnhQKeBQ+GEVOETx57YRQt+lMrwtm/uy+3Z/+8vX7Rirve+/7Pn/JJaQQQFKHUSMSRKspBWhr0wCstE6SlCgAdho0eGHvjFYMksQRokelKTgYBWEXy3Tm83/HtHqfDwetblbpUGnNSUqQ1Ccn2zrbGlMVBKjVqkDEQkAm8ey1ridpvlxsa7N7J1NlMgA0NjEpIgxMCB/+yAeL5bZPfeqib111657BkQve/dJFPb3EiW+OEaRCwAJ8MJOxZY8YwFMrOen31ERhFAeAjCRIrVMDCJMn8MgSQM6pnC7OagY919y68aIrr6tE7vzz3/P5z18ChJ5FEe7Zs3doZASNBUHHPGf+TCbtRAEFwto7zhUytWacRJFPnc3bRuqTRj2XzytlwSIgQAycTgv4v2Hac/5tQESFpLTNKlMklVPGIkqzNuobE8sWzzvn1S/v6GxHwHozAlJEhkGE0ITZ2HGp1N7R0SVOFAEAb9j0lGd23jXThhd+1zvf9slPfW7evAU337HhA5/41r2PD/vMLMz1eNTMTMgIKaITYo/AyIIeJT1Y9Ob30VTwiA5QBPFgQhaJQELokZ1C5akUFPsmmoWv/MOtF156VTWWP33rWy+99PNE6LzzDAAwcGD/2OioCQLngZ2f07fQe0ycE0UOBAADG0ZRGjWiej0OrTpqZX9vSae1SZ/EVhulAhXmlAlQKZj2on890+r970AkE2ibtUHRmLwxRa2y4n0cTZWC+mnHzvm7Sz+2aEGf96kHGZ+oulQbU0ic0wFJmmIcdeczc7o7MU1NJgCgB+67F0SsspayScIi8La3vPHiz13a37/40a0jf/7Jq66+Z3DYzOPCPE8lJSpI44xLNYOA8mgE6VfUgvwVyG/cflODmUjQkITaB5bR+ERDogEJsmhnUNfCbRX94b/7ySXfvTOV8Lx3vfuyyy63NnDOgUsNAADs3PV0ozZps1kQCAEOmzFTeyeQMMWiYm2I0MSJGZqIMLCK/LvecNrH/+LVR87JY2PEJ1VCCGzWZHI2DLU2L8CX+EfKtHp/I4jKZk1YMmG7DYtaZQwSuSiaGpzRJue/+UVf/+LfWEVfvuIr1VodAHburUaRZ9CkxXvHPiWJyVWPmF9SiprVOpj8Q/c9ODI6joggQui9E2Z5/RtefeXffXHRokXDE9EFn/mn717z6JTvzHUvbqYWRAMjMhAgAIGo36Lf+ztLFxhJQINoZEVCwMzeKWMTr02uJ1Ne9NQB+dgXrr3h5xuNDc57+9uvvOLyUrEQO0ZOFXIrknX73fd7DNO4nsS1hbPLfZ0hN6cUMaBHYPYelRmd8pM1Doql/fsHrrv231599snfuvwvzl63JPRV5xpIbDMZG+aUDZGmMwJ/NdOfy28Alc2osKBMQamcoowhakYjPh5Ztbh84Qde/Z53/5+hin/Hn310y45BbUKU1BrzqtNWBtQAXwf2hAqITTaEMPsvNz2OlKWwc3x4dObs3mOPPpIUpBxrrbz3AtDfv2junLn33//A+NjEQw9va9Siw/sXlUt55pTBCyIjEoAS1B6gpeVnL/SFdC9JgFAUCQI6D6nK2ARDk5tFYc/jT9cvvPy6ex7ZGYTZ8972zi98/uJMEDQSCZSkLtXGIOlde/d94IMfjTyGIUSTw2eetPSc0xYl9X3iGoiKRLPYUtf8Ox/bf+NdT4LJBLnC4xue0r7x6rNfdMqx/RkN23fuGxof15m8kGURcel09ZxfybR6fy2otArzZPJa5Ujy2nESDRtdOfvFh130oVeeeeKK8Ynkrz/+xf+4Z5PJFk22DOzSRvXUdcu6y9rHE5pIRAkkZCXX1nn9TY9P1sEGXUmcPL3jqbPOOqOzo4PBAfokbRqtmWXp0qWd5a71Dz08Vals2DIwOFg96qhlbeVCM64zeGxJV4CEuDWl6NlLfSHVq1AsASI6IMfEEZDKzZDMrCd3ND74mR8+tHk/o3rHee/+8pe/GIaWPWjCJE0J0dggcelnLrv8zlvvUrZAXIdm9GevX7F8US5tjBEoYRRW2pZybXO/d81dj24dUPl21JbYb92+Y96M7KpF5bVrFs3pLe3YM7R7YFysJkXCLOyni2/8V6bV+2tRxpLNkQ4MhORcvba/kK+//XUrP/p/X7ZgRtHXou9cfc+V/3CLsjZT7GHIWK0mJ8bn9HYcs2quTyaVMiJaMImTWrmre8eeiUefGCAqaJsZHthVi6prVq3uaO8gVEorBpf6VCuzcuWKMCjce+89zLhpx97R0eqRRy3NZpVLGkq8as3uZ2J67soIL6R6UTSKARCgVNClSkFQVLm+9ZvGP/L5f35yxygAvPjUM7/+ja9kMkFUjxUgIGitrTWp8z/656su/tRn4zQMrWlMDq1cWPrgu07UfjJpJIHpILTNFG1+RiXNfuEb1080BYIi6gyhH5+obdux//gj5wcYLZ1bPvKI+Tt3D+/eNwyKlLWEIp6nh6D/E9Pq/TUQaR0Yk9diNKdRZW97e/ret534zjcfa7muIPP4hv1/+bmrJhPMlTodhKknpZRwMjY6cuYpqwPjAU3iSRlK04Y1uWJ59u13b55qJJlsLgV5dP194xO1+fPmldvLVltqjUUJItCRa1aNjlcfeugRj2rT9r1RvXbKiau0a6CLlDAJeCFUB5dm+C2zqZ4PCkAjOKCU0bMKbL53xyB+8KIfbdo5bmzmyGOPv/yyyw5bONd5J+ys0cooIty378A//cu1n/jExydGq0HYhhyDq77vvFNOPHJOY2qcoCBQ9kwU5ArdC39298arb3oIw6LDAMgAYiGf3bV7YHxq8vSTVrvJvfM6zdGr+3ftHt07MOoFtdUgIH7aAv8S0+r9FSCSNqG2WaMzAUJ9Yu/cLn3h+8547Rl9koxFtZTVzI9e9OMnd0+E5TJgwECAWogA0v0Hhmd2Fo4/avk9D2y/b8P+JUvmBVo3askRy1ZOTkWPbt4VN6qBUcoUH17/wL0PPGqtLhbzbW3tRtlWBVYiPO30F//stvWDw0MCfvPW/bM6w9X9MyGpkU+FwCPiL3vOLygKQCGkQI4RTFjGoPfCi//1nieGTZDLljquv+Ha1cuXAgCRIkVeYHR07M677r34kisvvfhylyaZfAl8Wq8Onn7MYe9/+5kSTYmjYvvcW+7ceuMdj8+YNaejb8nl37h2845hyrWhyYIgEoIgK7999+DCObNXLOxojO7uKuLao5dNTNa3bNmTCmljhWW6A/xcptX7nzmYTRXmtckY4Ghi/+I5+Qvee8brTp9dHd7ZrLv2rmXfu/r+f7hxPeRKKigCILbqVCkERAXpwP6RV51+8o+uX3/FDx+a39e1ctFCSTmOo9Wr+3cPDG7deUC8gBiV6RzYs+PGm27ctGljkrqx8fGxsfFKZWpwZGTvvoEndww8+dD6bE43GtHE0ODrzzxGuzpw05N4QqDfXxiUBBEoBUoZVK44887793/xRw8qG8YqV+ruOe2kY/fu27dt+9M79uzc8tSWO++958c/vuozF1/+8AP3ZEpdRhvXGE+albm9uU988Ny+solr1VJ55hNbRz58yVXXP7zfJeJM+L1rfh6J1ZkicyulFBAIdRCn8caNu9Yeu6yUYR9NdLUFa49ePjrReGrzQAqstRYWma5f9wzTuVa/REu62uZIZxi4XhtfOq9wyQXnrDs8U9v3lI6g3L343g1DX736DihkyLYJWISUwAuBoGEdZNs6t+7afff6vSeffPxPH9138XfvWdjeffKxC0Ynd+dL9OH3nDDVaN6zfqjZbOpcQB2lJEn+45bb/uOWm4J8Z2/PjK7usrh0z77B0UodAk2BRTWZy3Ug5gCMEDCJI2+YfvNEhd8ZQRZwCA6AQZQ1hT27d8fMmWwmgWBobPxlL39NoZBPUm8DPT4+DnEDQGO2kO3osZriyhRK0tuT+8j/PXXV4QWemgxs2Gyab1x954Tod7z5jPvuufOBLbvG66nKlhMPCgWFCUSEjM5QUNo7Onbxt2+94qOvag9wamygowx/+2dnCpsf/+xR1GQzNo2EvZ/uA8O07f0lkJTNqiCvgxwiNybH5vXaT33k3LXL2qoDG1USF3N9dT/jry67euO+MSkUWOUIDAEjeiFkJFaKnaekOToy/pbzXr3y8N5rf7p+0+N7Z3UWFi+bPTq+u62UW7VseVqX3YODlaiKirPZICx0MOUFw/HR6sCeAwODI1HC+bYCoieiuFr50DtfuWZh2dWGBZqemAmUKJJfWtCztT3fBv+qrVUj1iMKixEslbsX3HrHY5MpUa6gTFYlNmkCU6YRMYSFTLknWypq8Eq5RnUi5+IjFs/+6/ee+uLjezEdU0jadP7DP9//xWvuefd551z0yQt+/KN/2rJ7MmzvZjRIWgsTMwoBKhRgBhXqpzbubOssLV3US0kFompg1KmnHLtrf2XrrkGjjNIKBHjaAk+r91kQUdksBAXAMAgxqYz0FtVnP/SyU4/qiQa3WnGC+bB7+TeufegHN2/QQY7CkkMrSApEsZAoBhJUApgxtHXn3u72zFtffTy69J/vfvK+DbsW98+b1dFh07Td0kuOXtxZMlMTlerkJPs08YxhCCajsyVlsh3lHqAwlcBYqg7uObq//JdvPyXjRiQeR3GCQEDkLSB5FCEBQAKlfStCK4Je4JfrPP/y1lr3t1XD/dnDUJ6tnPPs2r4KQDXjeN68uUNjlQc3bAdlweQCkwFUYAI0QWADSBuS1qU5qbjWWbDnHr30ove++rhluja5UWd1A7q+9uP1n/z2Tccs7vvaZR/Z8NjWb33/33ShHAuS0gSiWbSggPFgBdBBikEujZMNjz15zJpV83o748o4cWJVfPIpazdtH9zy9EBojLbaM0+70NPqBWhJN8josCQ6B8Bxbawcwif+4pyzT5oVDW/TrqkpUIW+jUP+r794bUNMkCtzqoUI0Btmw0hCAOQBUKFRBN49vWnjkUtmvepVZ9Wrtdsf2nznvZsCMvNnzzHo0FfWHbNszYolBG58op7EUVSvpM06EXDakKSOAM6RclPIjU+89/RjFuXjid0krbJPiEIkmhGYWNAjkPakWKG03FAWREB6xh7/l+2Zwu3ynOJY+JyfHkCAABCBFXhEWbq0/7Z7nzwwWtU2w77JPkqbNQVNH01INJpV8Zyu3PFrFr779ae841Un9LbF1dqgzRV3D/LX//HxL33/jhX987702ff3dAUX/M0Vm/aM2l3EZLQAACAASURBVHxbrLUKA04SA6gAGcgpJegFPZgAtIoq9a2bd5x6wpqejkIcTSbxZDFvjzn6qI1b9u/ZfUAbRUazZ+ZD2n+eVi8Akg6yKsyrIItKI9dVXDn/T894x2vWNka3Ka6LkJhCUJ7/uW/c+MDGA2EuL2AUWYRYS2LZGWZEYEShVs9UMkoNj45PTtbXrV156jGLIZ3YsPXAzXdv2z44lu/oCgsdqE17V2HtUUuOXD6rMwdtFsoFndcuxCZIPVDsJalXRk85Zu6fv+kk1RyVuKLECwqTSKuaJLKQa61OrwRJQBAYWxWv6DdkU+KzRhgBEOiZ+umtspICwiiCAigE4NMUADtn9FUSumv9VqNEcaOUlXKOu4vS1x0sm58/+0VL3/yaE9762hOOWDLb66kJTiag6+5HK1/46h3X3bzppccefuUn/uzoE/q/8JXvfu/ae8NCe0qKlfbOGyRiAPRM3itH4DRS6gWVCUO1d99IXvsTj10KHKeu2Yzjrs6uI5b1r398594DYybQqEgO7RjwIa9eJLJZFRRUkCWtJa0mlbHXnbn6o+86w09sV8lIElcpLJV6Ft1w5/bLv3cHmQzYNmFNAIixglSzgChA4pa7CoiMCAYQn96zP0A+YfX8446ZM6esx2rJbQ/vvv2+jU2vTJiNm1PZwPd1mNPWzj/zhEVnres/cc2Co1f2r1t35MT4+OatT8/uzFx24bm9xdTXhjTHBCwgQiLISgTQM4IgoiAJEoigeEJGgv8mE/qgelsrL6AIIiOwIAO11kICAWjVmtWEIMJAixb1P/bU7i07D/TNyL//nee+9sw1Z62b85ZXHPGmly4/cXVv/6xCY2o8TRv7q9H6bWPf+9cN3/7+rYOT6Z+cvOxzf3HO4qWzbl//6AWX/GM1VRDmHCrQGhxaZcmDgAh5oRR8asEIkvOoFKFEWzbvOaK/d+G87jSuuqiWRtUF82b39c2+99Ht45W6NlopYoZDVsGHtnoRyWYpKGibVSYgjhoTwyv7ey/+8DklGVbJEKaTHjBsnzNYz//VJVfvn0xA5UxYAiFkB5gCCoAWNIyKCQQEEEWImXRYZMH1Dz62etncmSV1xOGzjzt2QUcp3Lp74mf3bL7zwa1bt+956YmL3NR+ntpn45GSSWd3t69as7p33tx/v/ne4ZHxC999xlknL0qmdmNaUeLw4Ky9VkV18QKirGdFpImZgAWBiRgVtrT3azlomVtrGB1cvQwQAF1r/AtEAFvWmMCLd8y+1F5edFjvPQ/trEbJqSeseOMrj5tVbOT8ADT2SVyJqlMi8vTu2iV/f+e3f3zf9i0DJ6yc9cE/PeX8N6ztmmG37h686Es3Pbp1NGzrYZXROkBB9AQeUbQgAjGj0yLigHQAOvCMmVBVKvUDA8Mnr1uWNUCuon2tUastPnyJDXP3PbIj5jQwWoBY5NDM4jik1Ys6UGHeBDmlLUqS1sd7SubzH339slkG6/t8bQjQB8VuLPR96ccP3nDbkzpXpqDMQj5NA00eHCN5DJkCjyjglfLMjpCIhWzRxXEq6fqHH1u9clFnSZW0W7dy3qpF3cMj9e17h57aPXXuqf1dWdHNKeubabNer0We7AWf/ta1t2w+/zUrPvD2U6eGtkI8piFRzwiMEQSFQZHN2mx7o8nGBuzSltfMSIwan1kc8Ne1GwBR4BeVKVExaB0WPAUeCCAVQGl52OwViUsTBll02NxirnDrfdtuv+O+U1Z1BjJOzVFJalqkEfnyjFkf+ez119+7d2lf+WNve/H737T2yP5silMVUp/56o1X/fvj2excMe2oNKepYpdRGj2iGAFATd4nobHA4DwyKA9KgLIhb981tmRh15KFvRJPZlScpI2Uec2RKwbHqo8/tRuRlLYsAHIoxoEPZfWi0oGyWSKj0XNzApLG+99y8jkn9Udj25SvgnimIGifs20IP37l9bWUdLYT0YCIIvDshITReAw9GQBPGClu1idHO0uZNI5ZUABtLjs0NrV9976Tj17SZeN0dN+C2d0nHLVUQVwu5c46oV+5WgAOfMqCNtdWjfi7//LA2pXzPvn+MyAZj6sHlDTBp4RaQAkQAHgQMflYigMjcVvXzCROCZkwAWRBxWBA+DdN35dWmZuWdMkLKptVmfZqExouUEor3xQAAAUMhkAToLCINOLGihX9BHbP3qG1S4tzunOQNsC51KEOSuzV7Q/vKOZzl//lK19+3Bw/sbPRmPD57qtu3fyVH94numxthweFyFbiQJpJfdIQojJeFCKBiAgAIpICICSNSiOwpLWBgeEzX3JczjAkU84nSdoMs8ERyxY++tjOPfsnUSkyGqS1pOmhZYEPXfUiIiljgpAUSVr1SfX0Y/o/dv7LTGMfR2NI3GSSsM22z7viO3fe8dCufHkmS6CASBjQsxIiBNKM2gOSREYq9dHR1Ytnveqlp2x+6qnK1JTNl6LE5Tvbd27dOzAwsu7ope15MzF8oKM9s3bVgtOOn5fRXvlIfEpaidKNlHWYWbG443UvPyqnmhMju0PDLm1o0gi21bsGFCHIl+f+6Nqnvn3NQ8cdf3SotfhIYQTgGYjB/He2F+CZ0BAAMlgKS4Wu2V/74R0/+fmWNSsWlmzKzAIKkAhac3ydAAMBs6xevuTwWZm5M3NGmhpaBwaMlsLs/J7iGWtnL5/XltQONKJqvnvxTx8Y+dsrfjIR53WYtxa8Z+TE14cPn98urlGtTAEiKJukLrRWABwigBAACXkGEUUU79lf6V8w5/DDZvp4UpMgurg+1dPVNbtr5l33b5uoRzabZdIoJN4fUqsxHMrqJdKBtgGhS5vVGW2ZKy584+xMrTm23SjXFIxVNmyfvWl37VNfvNGprLLt4EmDEKZC7AkUAgl6USis3GQ0PnrsktmXfuwtb37d2Y9teHLztj2gQ5MJnfM2ozZu3js81Tx8+aJiXtdGdmagHhqJKsNWi6CPfaozGQ/s0sasnrJrTEaVMaMcgjOahEHEAhoAAGRGle/u/8F1m//lnl3p+PjLzjghiceR6wipAAnbVu/41zb8F0PSyKLI5DOF7qf31T50xe0Pbp58w9lHz8hFznlGA6IQBMQpBCBy7JvNulVuwaysloaP66o1+EXogJM06pvV1lPU1cmBphLo7Htsr//Lz1yzZwjyxV6ymiEihGZ1OBckV3763Ycv6tmwcfvoxGS+VGKPiJCIOI0IrMUrQRZEMsoY15gaHp18yQmrMjphH1mVYlpLG80Vy1ZN1dwDT+5KkcAECjRIKwh8qAj4kK2tgUpZY0NA8BynSfKmV528fEFXNLbXcKwQvCjWuaBt5j9e/9B4w9tsyXnSqLQ4JR6AD4Zt2Clx5OuNysSSOV2XX/jaY/pLMLX9/HPXtbVl40aFuKl9qlQ27O69+mdPXvr9u6q6PZsPMR3B+v4MVJLmmJCjrKkljWZSydjEVfeoZMTq1KWR5xSQGLSIAlEgGoVIVOzs3NltiujWB3cNjafZQgcDAbeK1XHLCX2moBz8skN5cFAZBVrBJjTZMNd+1Y2PDVSSJfPKpbYO8QpFIWBr+JwRmVrleNgo56o7amPbyE1oTNg7EfY+VegUNqoT+xoj+wNjG0FhzHb97Vevf3q4Wix0ZFQoThySYJzGlbNfdMTxa2a9/U/WffS9L+3uyNSqI0o5AnEAHlrxLiHxBgEBhGyhvf3hTXtvumtT2N4nJuvS1EKqosn6yJ7zXvvidasX+mYEXrTOqDCvTAB4qNzVh6jtVcqaoKh1FkgkrS2b2/7pD7wcJrcHaQ29eDGedLa9a+sgXvqNmyMmNiWgwECqJAbynsAhIRrxSOTq4wfm9RQv++tzjl2UqQ9vq43un9/X/dDGHZt3j2mDSgfOG5GMMeFjG7Z0lfRxRx8e1Ua8ayhLHtEBeAZEtBolTSx5rcS5ptJARjVihyoAtCBEQooVOqV0e7bU+W+3PjJUTQr58KhlC1Tc0MDiAbRlEERkAdSKRbwwICICgVciAsTSmhtAHrO2POeJffXLfnDnyET93DNXveyYw6g2BZ6FGCgFiplSRu9BBJFAtLh8NlOr1oIwFAEW0MY6n3qfhlpbJJVpt92LL//OXddctyFX7jRhIWpGxmoPLp4a6Z9ZuPTDr5kZTA5sf/y4o44wNnjwkc31RqxJK2NFgBgNGBTwPkblgJJsLlurN/bsPnDGi47M5QR8hVKv2Dov5Z627lndtz2wtRl5rQtIFkhE+BCZinQoqhdJaZvTqmBUmLo6pNWL/vLsFXOVn9hlhcVZUVlWutw764rv3fXzB57WhQ4Misys0JMkgOJJObTCBOLjxnh7Tl38kdecsjLvJ572zfHUu1JHV1MVb737yYS9sgXBLEEYCnBc27fnwEtOPTaT1z6tegDQAXswyjKLIkOklA7jONWkCJQXIhUAkgASMAErESXgkmjOgvl7hwe37hp5dNOe+Z16+fxOJXHqUtGGGRVZARIvKITSGmEGZEBAT4YFdSspIyhWsfyxL99w96N7Vh/W/tG3ntSbS1xzUrAVD3OADEQAisRgq2IOBY0mF9o6oihWxgCiMBMSofZeBFSmo++pve6iL1zf8KhzZQdIhgS9S5oqqX3uQ688ZXlnfe8T2k36qL5i1QovZv1j25hdGGRQFHpCNIwClJCKAdI4YdCFkaGh3s7imlVzfDJJiRgIAFyTp+b3zz0w0tywYQ9iDrUCUgIiwiB//EPQh4qP8SyIRDZDNiRrCH1cm1h35MLTTlxdGx8EcV6cJ/akwlLnjn0TP7n5wSCTtUEGAcA7oFZAlQQ0glLcjGtDIcR/9efnnH78IlcdjxtVx+hVGGFYLM8IswEIoULnIwYHmoqF3NOD0fW3PB4W+oAKIAEyGVCG0aIBDtB2RNAG4SzwHehKymW1U5pZSQzY8LqWmFoS1Dzua0RPfuS9LzrvtcvK7cHjTz7MMuVclZQHcEYZSbwVFXid8boAYYYDTBSyYTYsgEqEPIAzhjdu2rR1x9Dxq2Z/8gMvXTSvXIkGomAssRUmh2y0z9m4ZJOSdhnjQvDGY1ssWY850llERSAKmMSrVvc4aIPS7O9fffd4pRHmS6RCEAUCAJgkydy+zlPPPn0yiqpJnbkWNQ5wc+A9bzvzdS9fp1ytWRtF8EqRZ/aCgppFgShEE5iQTPGq6++ZqiFjjtGQVt6lSVTxzcpbXnX8jI6AfV0g9cRiLYUZVOb3Wrb+/wcONdtLFGQozKMNNaqkMZFV9c989PW9RSe1A4E0ETjxypt855wF3/zRbTfdOxBmyx6tkBJgJG5lMrRGdCQak7h6/ptPe+e5J/DEdj+1DznxlLUd8+qqfMU3b9ywcdBmC7H3ylhSpBAUMnG058D4S19ybEcW4yhSXgIkdJ5AmaBw+4OD3hS7evskiUU8glfABE5JisStcq0MbExSb1Yy+cLaY5ccs7i0dllvd95wGiPahMmQaEnEexSVyRSQjM1kU/ZOHGjw4BBZQQrgnYjOZNasnPvGc47rn9PeGNujVC2mCIAUW82BdlazPjj/gZxHDeEMMoWbf/ZYuS2bMYTiERiASTygbpu98r6N45/+0g3eWgzbHGsCatV0Z+8tNVYvP6yrzViqej/F5OpR3bnkxScdu2PnwKbNe1mR0RZRCeDB7joSiEIxGSODI6NH9PcuP6yPm3VJY2Mw8UkqNKOnb3wyeuDxp3UQpAQ6DAFIGMS7P24LfGjZXtQWTQ51SEoJR1Fz4uxTlqxbNS8a3WMxJXROnNcUtHfuG4tvuH2bUoFwAB7FO1ToQBwhIyEApFGjOnnmiYe/509OxsouP7nPQhJm8irbodv6rvzODTfc8qgNOrK5dkUKiT0nqfhYtMoUN+8a+9F1D6hsV7bQBWDAeSVeg5RKhcc2jl/293fuHo9tZ9GFlCpx5BCEgMgrcpZcVkmeYh2kGI+OJSNjqxf2HjZzRlyNyQXobABZn9TIxByg6eod16UbHh147EBDd83GYs5RLJQIpCIO0YGv9RSTYxfnuu1Uc3Sb8WMhAbkc+Syx0swaU8QmqzihJNYeC9li95x/vWXrv/z7dlI5a7MorQFsYlBhoVzx+Su+c9N404vJKlsQeeYGEwxsdmQsvfBvv7x5zyQWepzNoSbiupvaW5KRT55/2ur+Lo6rnFYRPSGIKBYjolt3qbFZx/TPNz4ScSko9Dik1McZq119IiNTf3rOulldmaQ+YVAQCClAm0ET/HEXcz+UbC8qsjkwBW0yGpO4NtqWgcsveE1n2OD6iJFIK049QNBW6Dnsn2589KobnwjynaDyyhgvXlAEPBKSAPo4qoyvWdxx8Ydf2ZVtuomd1tc0acyUqTTvm1fd87Uf3mazXSwZJ0AaAcGzCGOYyRGqxLut2/YtWzRzaf/camUCJTYkiU9TUKuPWXrVrZvveWjz/IUdHT1lE4ZJ7FgQQSErFEWiiMkAGspEtSRngubUZFqvGWRD2jMSaTIsxlL7gr1R21euuuvi793/8LYDHbNm983tDSygMPu0NTlQgXJxLGnMjckMNgOIXOxRCkZIS4rQBBV57ZpKOJMzbTMw2331Tzd/84f3fug9Zx2xsD2OqigsRA50tr0nLM360o/u/d61D4bFImQ64hQVaZJWehgAqYwNhwZHNzy59agjj+joKLq4IakLlY6rjdndM8ozZj7w6NaJqUpoAwYjRK3RNgQiQaUV+2TPvsF1a5bN6S2m8QRwE5gV6WajPqOnZ7Ih9z+yDRWCCoECZkGfiE/+iFM4DiH1ojIU5MnmFWEAjfrUxGtOXf62V6yoj+wyECtInXdeWc6UY9316S9eNzhZ15kORsviEaQVQhXvjUqT6kQ5pz77oVccf0TH1P7NJqmQeAqKVJp380ODH7/i2hisDspAWUEW9CJCpAmV8yIANjDjY6ObN+9fe9yqUjFjFCRJA0hix/lycd1R82++c+c1Nz/eMWNOT/esTLaNMZDW/Y+CmLBvgKB3aAx511QQa+WEOIGENeiMDfO9TZr1yE7/ub+/7epbtjYjGBhpPLhht3e6t6unvb1NUDErFgVACgh9apGJHQEDagIiSgQiVk1nxP8/9t402pKrOBP9IvbemXmGe+58b81zaS7NpQkJxCQECINAYIwxbZvGjfHw7LbduF+3/Z6fJ2hYNsZ4attgbDyjBgkbCYEkhEZAs1SDVKpJpaq6decz57B3xPuRp4QwUG4vwH5cv1hnVdWqe2pV7p35ZcSO+OKLuEL16drEafOd4b/41EN/8Il73v2WnT/wmnObSyc09NmwmGpuhhtrTr/5zr2/9pHPtr2Jh6fS4IgdkxotSEWJlNjCOWMOHVvYf+C5F7/osoozVHgulAl5Wmw7+/Qc9pHHn1FfwEZge7KHkUhYmchQr9NNLL/sRef4fJ41MzAEFvFg3Xr66Xfc++SJ+VZSHSoCMwmFTP5/9K4MI2PZVk1U06JP2XIjxq//whumqx3fWyJfQEWJJKrS0PSXdy189JMPwA2LHVJSQmAoiEFGJGffztrdn/ihV/7gdef25p5GfzGi4NUmk1uPtCs/8//8zZGFNB4aga0GLZNDoWygJzVGCSTEklTp2aPLDz+x/4rLLxoergHiJQRImhZTk6MvveLsLz/W+eO/uXd+IR8dnRwen4rrwzaywkWhPXYS2HnDQh6mIKPewFtHtSFba2hce25h+FN3Hv213/n7h3YfJTM8NT5FpAuLrXseOnToqZn66HRldKQ6vMpTlV01dlURAoyyCyZWYqWgHBA7qje4PonqmmBWPfRE89d++x9v/sKun3rbzh+74aKlheMsPcAHdlSZqEyedvNde9/7gZtmOzo0OhmoImSsYRZPWjCkTHsbikRMFLt9h2ekoBdffrEJhYGIhELyLOQXX3Tm/n0zu5466iKjxgnR801UAaIucsxHDx+59uXnjTWCz1okjuCYpPC9devXtzvZvQ8eZOtgIhAgXsVrWLHVo39H6GW25GLnquR7vfbC9S/f8SNvvrhYflbzlAQgCsQSVeqTGz7y5/c89OQMx9PiLKgwKqwEGGJrTejMzV505sSv/vybkjDTmT1QjxgCqoz7yrr3/+ntdz64PxmZSCqj/TxXQyAhCIFZLKkhRVlEJRcl1eGDh07sfurwadu2rV49JsEzFD5PW8sTw8PXXH1Zc37prz731dvv37PY7FFcixrjca2hxtVHp1Eb1ajCURxVqvHQOCoTmZ0oojVHFvnWLz39oT9/4GM339frFRWDMzcM/fR/umHT2vH5E3PI0j0zrc/ds/fQiSVbnzLVKZhqFFfjuBZVhmx1FMkoJ42oWjPVCVTWtMPEbKf+8K7lv7np4d/5o3+YW+7+6k9e/yNv2tFcONpvn6hGQkywNaqvvvPhmV/64N8fWcqGR8eMq+XCxjpASDOjAaRCrGQ0CIMRVZh0777D52zbuHXtuIaul34wwRfdeuK2bd76wKP7ZxaWbVKVkvMMMBAAb9gEbi/Pr19b3Xn+6qy/jBARHJEnSn2Rbt56xi23P7HUzjiqESugKkGCX6nu998Resk44yJnIi3SinR+5ee+b3qoSJePW1VmSyAPqoyMz/fcb374M30dQjQeOIC8VWVlkA0iIe+a0P+Vn7/h7PUmXTzEWcuy+sCN6W23fPnI+/7n56gyFFdGxRuyHMiXTfukhtWyMiBEBTj1Ghe+UavV9h888tjjB9eumdq6cRWppzx16n2/PVQ3L7l02/hw9MTB5Vvveeq2Lz6y+5mFo7Ppcsf0w/Byxu3cpMEt98yJJXd4Ibr70RN/9w9P/uXND/3lTY8fmFlWxobpxrWXbPg/f+yK73vRuqvOXzUxXm/n6PbyhXZ/38Glz97x2MFjrZn57mIz7Wemk6EboqUiWuyZE4u876h+dU/r1rsO3fj5vX/w8dvvfvTo+adPfuBnX/X6V5wxP/OU5ksWuTGIknrcmL7l/oPvfd+NRxazZGzS2kruA0ykTKTeiGcEQjmJycSRS9NeXBvJ85xIDx86dN72qbWrhrLQghPHvr24cNZZZ6up3/3g07kXdokQE4iVlAHH7CG+1+8vX3fNOez75VUQeaK+ZOnU6o1H5vP7Hz1gXALnAK9BEPxKbT9ayRm5rzNmGw+ZeMix63fmXnXh+J+974fz5lNFbzFWZ8koih785NbzPvHZZ37mV//BNqY0HgFUQx5ZoqAi0FB0W7Ovv/rM3/2/b0B7b2jOwHdtbG11Vddte8d7P3HvrmPVqUnyzmhNIAVnZcKGYSAGYFKBKUBZIRXvhxh51fSW5p6bGnb/5cde9rY3XEzLB6U/l3aaJqrGQ5PDExu/snvu72594nP37t9/bBFAzDQ9MTY2rrWKcUz9TrHcxHImC82WDwrAENZPD19w1urXv/SsV126dggL7cXj7Gq2sWExG73t/v2fvfPJJ58+cnS+6QEA1YobrSQjCdWGDAxETK9Nc53+YqsTFADWTjWu27npJ3/4stM21+eO7QtpE2qipGEq46kM33jLIx/8+JeONjE8NV1QlUWIwC5Ji4JVHAmpAAhsBMZACSbAsgL5QmfpxLuuv+C/vedVofMMh0XWnKiWDG3qhqlf/vBn/uYLTyYj097WVMmKiGRiDXOi/QXtzP7FR37osm1VXZi3wTP73HeIMLR6x/756ht+/PcWUlB91AtJloV+KxTpv92T9120fx++l5ijionqNoohfd9f+sV3XXPOBivdGRU1EpkAIKPYuZEtH/nzB3Yd7NjqiJiuDZbEwZJXD2Ts243Iv/+//ODaer9oHnYQJUUtTlZt++tb9//ZjV+xwyMaAaQUYggTCZTopNQbSAZj/NRCmQ2IITCVarzUbN/70D6IbNu+eWi0qiQaxKdp1m5tWz/xisvOPGfLdOyogC1CmF1uH5/tHTneO3Sse3Q+Xeik3X7Gxo43oi1rJl52yZafeutFP/2WneduHvLdeZ91VdQZl7bbQzZccfa6ay47a/OqYUtFAIJqL5dmN51rZ0cX0qNz6bH53ly718vyasVtXD161dmb3vsfX/Tut+0cq/u5o/vUdyyjOjwVkjXHs+nf/cSDv/knd7ZSMzQ6bqO6SoACYPG+HLxLRCCjZAZd/yQKQAMBZOMiL3YfOLrzwnO2rx3lzgmjEsho3h+pxtu3bLrtnl29QgIiE8VS9COrhkIegomrvdbiyNDISy89x2bzXLShCGqVTV6EjRvWP/XMzEN7jrikIpQIEYKXkP8bP4HfHft3oedM1pGtcZQwU562d5y25vxzNvp0KWQZEwOipEJI6sPPPrf48O4jSTSkYCh59ZF1RSGAUZ+3280f/eFXnLl9pDP7ZAQBUQDXa2OLLfmrT94JU41svSi148iDDAZdeC+8FB3oWpAAKcAEBlVGRyezztJv/8mX9uw7/p4ffOkF28+x8ZFOc6HfXZ4/lkfJ8EsuXnvheRueOd574JGnnti/cOzoieVWv58GY1CNefXk8Mj4xDmb6hfu2Hra5qmI5jrLBzs9NhRZN+YRyJlKlUXz4/O7lPmNr1n3spdMPfLM7INPzu0/2puZazZbvU7bG3DFaVKh0YnRbesaV1+8+bwz1o7Vpds83lqeiRzF9fHCNto89uCuxQ997OZ7HnnWxrVKbURdLRcVlVIlnkqonlzw10xZ6aSWFrjeGGnNt2/8x3tffsH1nquQVAphzvu9xdO2nfX9r7v0w397T1aERmVNKiAyIp7JqZKJanc/sGf2LTunrRMiEs9slCnP+ml3+S1vuvrGL+0t8pSSOsiQdeyt+OJf63H717OVj15iw65iooTYqu/m/e6rr3rJ2vGhbO6QiifnAC+CwK5eHfvy/c8em2lSXGHrCs2JfQHPcFa51elu3zT19hsu7Tb3RdJOXJQVubIz0ehtn3t6z4HlSmU1NOEAsAfCqcXSqTwAwwAuqFXUh0crPm3edNe+Q4eWf+j1l1/3Rwxc0AAAIABJREFU4smp8XVRtdvvNvvdhezZZlytnzXdOPu67YWevjiXpr08zQsyEsc0OtYYH60Zkl67mXcPNPNmdWTYh+pyK9q1a+arj+6r1eKLdqw/56yp2kQifnFuYU+lMnTlOSNX7pgUqTWbRbNV9Dqi4mxUNOoyNhwlCSD9LD00f6xLZKq1RhzXUlSeeA6fuu2eT9/6xImlfjI0GlVH1VR8QAiFYacq9AJhgBcqTimgRIAhLdUBKHIVY93nv7Rr3+GXbB6a8v1ZzbocSdpb1vbxt7/5RTd/6ZHdB+aLfs25ui88yDoXedGhsZFnnj364OMHXnfFqrzfhO8bQ6yIDeZPHLvo7AvP3zp1757jLmmwidTGbBMJYeXxrlZ+5Ew24coQ2Qpb+N5SI5Zf/qnrx+Ne0T7m2CuXElAqrpaMrP+dv7hr/3N9dUNkI3YUqFBlhzhtLUq++F9/4tqrLhzLm884n2omShwPj2d28td//4v7j3Uq1VVKMZ2UaFToKdMKgREAAgzUqnGFh3HVSpQcmll64KE9B547EddGxqbXVmojSaUSWQp5L+sthXSRsuaQoam6WzNuxhtar2QU2v32/PLinGNTSWqFGT7RqnzxqzN/edMjf/z3X731wWN3PXr03gefeW4uDVxrjExX4gZpVPTTrLXMWbPO/ckhWTWK8ZFiou5Hozz059P2jM9bAd5W6nFtKjcTzxxNb7nv8Pv+5Iu33vN0KrbaGHPVca+RF1IVQ8oEfL0wwD/RiyNiBp8UteSgGjtdbnXGY7ry8vOzbrMemRBy0aKQfNX6tcut7gMPHmZjjK0FZetsUAbYoOi1W0lEr7x6h8+a6ns8KMZ7Y+zU1LrZZrjzy3tt5MhUAAOoilfx362H7N/IVjp6idlVKa7ARExZtjR3zeXb3/6aC6l3PEZfpAAIkAClymiHJt/3e7e0MrK1Ua8ax1EuPWZO1LWbR3duHf4/3vWKKBykYtaJauE8cWN6071PLP7Ox+8ytkFuBDCAACIcUMqtfqvrQqnfaJSMEotCQMEY2MgmFXH2yX2zX3hg/+59sznX4GquMpLUh6u1IbC1LoJSlqfdrJsWaSAIR+xGTLwq09G9Bzqfe+D4H37ivr/49MNf2TvT1uGhkVVx0mil/OATh790/5Hd+xbSfKg2tCFyI9Wk7piJfaFpgZ7nFATxhkwU14YpafQx1A6jjx5IP3nbnj/6q7v/+tZdJzqhPjwWVYZtPFKUMnaqjsVxQChOyt2dXOYLDcDJAzCVG2DIGqDfmT2x/Lprr4o117wl6k2EwqfEsnHzpnvv3dfqZkIxmZiZfCFRVBHJLeUzx46/9tpLhxIykjnWUmmeiTu9YsPWrTfe8kC3n0eVelCjIhoKlZUWPK/0yJmYrAMbthzyFKovu/TMCnXyrBWkILIiAPnAVKmO3PvIwePNnJLRglQJWZq7yMEXmi9HyP7Dm9+0agj95XkuMpUYTC6pianf9Lnb08C1xpgXsQgs7GECFyC1p6gyKkPdyT5yIVJhLaCeApxwVIu50uz1Pnvfwc/e98zpG0Yu3HH62VuGz9q+bmqsMTKURBxshawzufe9vCiyaLGFg4eXvvrE4fvuf2L3sXlFFNVqlem6uLhPVjWKkqReHVlud269/8it9+05Y/305edu3rFt/Kytk6ONemPYVIaiQr0GZ6ia+tBeyA4fPb734Oyju2fvevjpxRaDuDK0eihJFKTK4oMDVD1BSD2LN0S5liLvJ7f/hTTjwRSHUoJaFQrizHO1MbTnxPLdDx1+44tW5fOzREZCbiiE9vz6iZF3vvWy937wFua+mMgHMFvJCzKJiaozi90HHj/0hqs2aW9e8gxETBApNG+vW7vpygs2/a8797qiS1QlLveZVpjsxgpHrzEmYuvBxiDN0umx+CU7N0tvnkM/DwWZiJUCvEuSqD58z0OP5p6iqBpYWEuAMWnoZ82zNk5ec+WZ6B5yuWe1CusVIyPjB44273n4qE1GM8C6Ar4gsaQDfeV/7uq4PAgSBRCYNJAoCSCFWk4mIqtaHdXQe+pY86lnv+wiO1pPVo0nmzdOjzTier1WSSqdbm9hqXn8ufnZZT063+728nplYnh0fYg5GPUcPPUEAJkczkYuGR1lHUp7C3tPtPb+4wMxYWK4UouS1auiyVUTZcN9t9NfXGrNL6Zzy51mLy88uNIYWzXdFwuKRPqEQADgyz0iCA2Ou3TqaI6eF44jKpVc2cRshpian7z13ldf9mbnnA9eJbAGk/fTuWPXXXXWR//ugaeOttXFRFHZzwRlMRWAvvTlp6990Wl1W0XeC0SsQhQQuja0r7n6ktvu35f1W6YasyGvWGHQxcpGL4HYWDbMQaVIpdc/Z+e6zesne0cOxiZkgiAcUxQkNdb1Mn30qRnhqrATCkRgTxC20Ha/95brXzE1HDozyzY4KHsYZUsmenzPsWOzzWR0S0cKlY5jy1JlMNSATknQIxYAEBAIUmooQwkwQtaS8Vnf97JKPfI+qo1OAQXBL6ed2cOdJ470NE/xNQaCtc4YG9tkZLheDaq5lcAeUCicAFBASD1UBEyWoqFapVFjkazXm80KaRdPz/bx+DLgwALJQICLa5V6dbgKdrDJcqsj3icjw8oKVYZCBaRSzk4CKxgMCJ/KxZGAFDqInL1ItVrt9/vVoeqDu549Mrt49vTQwmKfyUVA3u7GlWjdVOXN1170y394W5WDR4AyQRVMroZK8vCu460eRlzN62JQVsCqh6T99uLFZ01NjFQWeyokvawo1fJXGHxXMnrBxGwUYikEEYTiFS+70KdNzbswHswCq4EBZuv2H108eOi4iUeFjFIBVYIxHHWb3emR+JVXbg/ZnPEFS6QKZZBzAeb+h/dnHihAVSbxKIQQE4wq0bdWVyIghCLPMlWJIuOsA1iVGUbVMBmCoLcwNTJMlB5dWvR5ZJxzSRIN1eIGVIXK2DOABQwjIIUoUzBeGEEDCZFaK4bFUCkRT0HICxUUSAW5qLWxqdUpCQwmKKsiiLdeYmUyHCLyloR9lvZbi86Gyena/PKJEA8x2xKCg8UQQ1mJfBCf9q0xzrlv1ppHgNDzoxpIICi89wH1pLY8N/vAw0+d/brNZGP1GUET45wP/cX561526cdufujZpZapjIAMVBRGyZqkfnRmbu/Tx7ecN1zABYWSsirB91oLGzdsOvv0jZ+7e28yEpxBvuKgi5Xe36tQaAAztOjXqvaqi88suossXrwnkGEOwcOYqDa653BzvuUjVzFQhgdUYINo0Utfe/WOjZO2uzwTUGJewcbFldmOvev+Pc5WrSEtApELxJ5FEYwylIVAEKPBiJIw1AmsBs+SFr2FiaR35vqqzZuUd0iCqlEkhIS9ocKnvbkff/c73v/+X7/mZS9aP1m3od9fXuy1Wnk/Lzz5EAepCdWFaoESVUNsQarqgYIVLMaI5RBxiEyI2cckjsUYIRaOKIk48QVCANgFUCAWw4iIjM09idi8n3VbS8vzx/L+wpqp2hte+9IPfvA3tm5anWcdoFASJSixklNYEdG0F9qLmybMEPd9v80epFaUpDwOKLO4MhUwKARDrOFQ5HGcBDhRc98TRzohqsRVKjwLorjWyzNftNaMRde99CKf9kKR06Ae5TXkzJx78+CThymqGEPMZTOJUbBK4dC7+uJ1AcqQf1Yf93vUVrTvBQAYA0vSXl684tIt60YUS0tWtSQBiRSWpTBOKlP3PPygRxQjYu2z5qJJQJJlTcPF9125vZotpyHNjZIJIU0NV+L62CPP0r55X6vWQCHkBKoX8MEqq7fCnjiYYIN3IqRRrlZcRUI/hs9b85ecufrtrz9v5/k7PvyxW2794q5+Hnzk1BiGGs2NZADOu/DC1732tW+64YZ//MfP3v75zz/44FePHZ85Prco4Lg+Yl1cejcBiDWUSqhkKZykiGgILIEHPlIHapJWRQN5YrKGVHJVskSqqgopU0u9PC+aicGa6ZGxsdU7d17yildc84Y3vM4Y88f/8892P3WQKjHDiBqBZYVkfd9bHDL5S8/d8hPvet1XHnnmI5+4PU8NV4aDIyExSiyGJRYmNUExSDpbeAWp14CYktG7H9k/m75+TehUQh65uCeQJMp80/SPvvkVp//Fp7/YzjOJhwOR0dxprgwM1R/ZczDVFzkLFCnIBTglQ6x5emLnuRuqjoIWhu2KpASvcPSqlpouAapnbl2XGA0+o/JVTAoVsuSSaqtbPPrkswQmgqqwludR8b3Wjk3jO87YmHUOWUMCFOIjS4X48cbwrr17ARVReG/YSSAwKQSqz4/WLAfhKqyyAan6LrS3YWrkfb/4AxecXgHsL/3M60X1ptsf92RBxoOGEvZ9D+Cpp/dde02RxPGb3nj9m954/f79+7/81QfvuPNL+/cf+PKDjygbNicV2IjpBeM8B0YDWdgX+h3FIPdbisYSDSYeDa5WkXaap23ZvGXj2rPOPuvqq1+ybcvm007bXv7bZqszP78AVIAKBAQYkry3XEF37XT88ovP/M/vfP36TWM7d6xvdbofv/HeLMudGy7KeUkcBJlSOClSe3J3BjMUECXxiUW/98Dcms0uiqIiFB7EzoS8T1lry9qtO7aMP/B0u/C5iRw8oJpElX7WfXLf7Mx8e0tcDb4jUCVWQNRnvfbGNWu3rak9/lynOtRYiYHzSkcvCEQ25F0AF5y7NoRUgsgAUQAQVK2rnFjqHp/vM1shKTUnWAHN0F98xYtfOTZW6x9JA3klkSIzkQvBuKTy8GP7RJSt8SDrbB4KKj0cBkQNowBswQbqAkilj9Ahaf/aL/7Uju1jM889CNDk6tP/r5+/4eCRhfv3HKtUK4UYgRECgHvvve+n3vPjqhpCsNZu3bp169atb3vr9zc7/fPOPe/ofCepVEqf+W3KvzzPqQgh+G7r537+Z9/5jh944ReyPI+jaN8z+47PzMA0VOoKTygQmuSbb7n+ymsu33zl+ettWDz29N76yKqff9fLjs0dv+kLu2zEzo4EGKGgtgs136oGbqwB8PSBI688+xzNbNFPTRyrBmO0SNujU/Laay69+4mbyFXVVX2hzrngNYoqy6353fueO+2SSektlRk6AggSfDE2XLvggu2PHXzY531aefWilX7uBQGqPut3R2runO1ri34T5IXKUX9gEi+SVBoHDp7o9VJbiVCyCdQwVIo2M6665AxkTUEexANiWaFi42Spkx48vgw2ZJ0CKoNo9flx1qwwQlDryeVsYWC0l7WX33H9pddcvnH5uceRzcXoHD/06LpxftfbX1oz4ntNy+JDIBsBtO/pp/PCi4qI5HmeZXkRBEAcRUwIeS6qRGTMt0u50ZMmqkCeRBRCEFUvPs/TEApmAvDss88uLzeNiRRWYYkkay9tXT32iz/+plddsZl6BzsndlXCUrq4j/NDv/ST1+7YvirvtLhQEqdE3viSxPLN7xQxwI/teU5dJRdVBpgIsFCEXtpbePHObVOjVfhMgye2BBu8Rq4muX718eeCqStbDIIeNVAtUg3ZJTs2x5Epslx1pRGtsMLRqwQVDWmeZ+smh9dNNazmBAGVvQLKECJUaiN7n1nqp2qiSFkVzHAQzXrNresnzt027tO2aiAmJsTOAsounplvzy8uwxqBUUUIgQajvUojEhghBQc1wvC+21k6ceEZ0z96w4uz+acr1KqQUN6rI1t+bv/l560/c/OIpH1HVtSBIorqMydmDj37HJOxzhHIWFM6yeeOHUv7fQAD0cXvnPAaEwPYd+CAiABlWBtEBujd/dQeleCcgHLhAsjyPDt/+9pR21k6tCssHx8ynvKeydv50uHN0/zeH7t2KLah13HsRFkGRbJvbkQM45462OxkqtZQxD4EJtJQOAo+XdwwnVxy1kbJU4i31gZPlhIVC2OfeGa54yO28cnnWYnUF72i17r43M2jjaoUvnxFfac26v8jtqLRWw7JMwHA2aePxtRnSYlUicEMIiAQkw/m8EyuKIfmBVVmRAhBs/65WyZXDydZd4mIFFBRCR4BzlXn28XcYp9sEsDGWDYnGYCDIzVBStIRBVVm9dlypPlP/tBL1o1If+lQ1lmkAEqLKITQXp6qJTvPO9eKcFDWSDSKasMLsyfuu//+EIKKEhMzOcMA8iwNQYwxBFJV+bZbz5/nMjIzgOWFJVVVKBG5yBrjQBRUb73lc17FRhmZnnIWkFrgwjOmXNGNfFZllkxisjGR8emJQ/tedcVZr7/6IsmXrGYQgkSA0W+wr11DUl3u9E4sNJN6PYCISRSkZCSknUWHzisv38xaMHnvs/KnCjZJ9elDR2aahXEVIS6DH6bgWHuthS3rptavGgXAxCcZVyvHVtp6/okRAsMDOGP7hhipFF1Ay9k8ICVSG0XdvszNL4FYmGAUyqGAZQLk5Vds42xZi74Pno2FKoODlzhunJj3aQ62bjC5Hs+P1XxBh42IQq2DRRo6rSsvWHf1zu2+OwtJnXNQZ01EQclnnHUvO3NdbGyR9hSssCaKAezatcsHP6AJn/QcwftBNg4gou+gS9GTl43BBG4GbBAYMsdnTuzZ/RRZS5qp5spBEFxizjl9S95tWUIQgq0Ug8QRU5H3lo7/6PdftWF1o7P4rCNBbklPlWdhW5lbaB093oRxJfEbYlAWmeDT7vyLLz19rOGC7ysb1ZLlQi5Ojs31DxxdZpcoGQAMIQlGA0JKobfz7DVExDay1p2iCP+9aCtqMd9gSqTBC4DtG6Yp9DjkBFGUg0GUVNiYNMPxmTmO4lCO/GEDYSmEgIt3nJa25lgDERGZAUMqwMX1w8daqkpsBaXY+CBZQhhMAKNB8lNIi7y7YDnc8JpLphuc9RasYyEb4BTMECO57y1ddP7WoUYlz7qgAiRsLSj+whfu6HS6ZeCKkt4EqMp3VaipfB2QDpTQy4fkjjvu6nbbSbVhFCQEWFXDxo6OjuRZ30W2lxcpqDDsiVUtq/Y6x07fEl17zY4kya32jUnEf8vnTRWRreSFHjneMcYQs6hRdYBVsEJ93tq4Kj73tKkiSxWhPBcxyLpIgKcPzbKNaOB7VTUYFpKsSNs7LzzLMMNYE9c5SlYSgFfOSr7RynJIluU1h9Vjcci6JEWJrLKQQlC2Js10dnY5ihIBggQGM5tut7d90+hkw0nWJag1Li8Ck5WgkasoR7NzS6rQMgJXIiU6WSjSk38BgBni+3lr+cLT17z6qh3p0nH1KdikQQNzKYZnKM+z5bWrGmsmqkpekSoV3ntXH97zxGNHjx5TVWZ+fjy8cbYUhP8ukRDK57usJSngrAFwx513+twDxmjMGqskopEKoiRyjvpp21SjPry3CExBGarBN7Ps0BtfvaVapbS3yMp8Kha0WhMBdnaxyWyNKVNQVtUCBkSh6KFo7rz4LPaZigeBiUUEbAE8tX8/W0fEJRWESQ1EijTk3W3rpuqxUTXsqjaurCQAr5BlfCtT0TyX1auGx8diSKlORkqiJASCRs5Vlvt+oRNAzDCWjKiK+qLo7DzvtHqVmQRSEFREQByUTJyA3MJiU2kwzP5kzFy69EHbkECFDFsm9RC98sKzxuqm35ozqiEoKFKxYBbyagqxgRI7Nl6xhh0Jh0xFk1oDCHfdfW8QgYpq2QYAZx0bIxrwT8NmOvn5tsxahzIZpoM8XKeX7t29G65uKCaNGRGpJUqyLHzy07fbyhiiuhAZC7ZUyvApedas3547c/vwuWdMp/1+OXtloA30zT7lLyfmFgtxRIYQCEGIBExg8QXDn3faVCWC0aBEaoyHDxLgzN79JwJXiI0RYYWCAwwkcMhWj7kNa4a8L8haY6sc1dmuEACvhDV8K1NAyQKYnBwdrhkEDyQKI+RBnsWyr8M0Zjv9gpSYIzGJxj4UHl2CXHL6KjL9fuiCg4bCMBchcBT3vaiNl5c7SsbCkMqAQgwojMBAUbYoEFvxZEmNxblnjGlvyYXUQUnZUFWKiGA8QuHIjU/deu8Tew4uqSQVGFdkziVqEsDceOMne72+90Fk4GpjFxvnggoRQigGFSOlr33+hQB+PmulKgCGhxqDflwKqgWAxx55ZPeTT7K1bKMy2rcaDEdRZfgP//a+LzzSSkbPNtywXlGoKqkBGTVg9NWl7uWXn+uYFF1BcQr0BuSwbqbZy+2wqInIE3U9+1L2xgkVvdbObas3jQ+brJur9A28UYG4uHZ8Qdt5ZNlF4lm1QBJsnYgpbw65bOOaKfG9oIFsbG3dxkNsou/sw/ZvYisZvVCQiQEzPVqv12IJwRh7Mi8coERqiVy72ythwR4ahBjKvlGzZ2yZLPKeR06kgAy6U5mCBg1SeK9fc3RykqVBAxYvlC1LUBFfFFlk7MZ101L0iYRJAJCKIS2yTMhyZaSZug/94WeenelXR6Y7vcIlFe99UOXq+JOPP7bvmf3WOWtdCAJgZHTEOUvMIoEI/J1OpY6MDA+qUAo2BOCuu+9KsxTkICIkCq9UKGs0NNLS+Fd+/+bnlsRWxxRGg7IKMJifRl58Pz9z22nWsGjGdKpQn0jAyIoQyAJM6gGvFMrmIFZ0253VYyObV42FtKcaCgCGjGFr4n5azC52RYkkAAp2RQCRkSxt1NzGVSMcRNRD2XBkOCH+pn0U32O2otELBBFA1q8eipzL8wwyyKoCgxjTWGouL6kqwAoo1Br2RT46OrJpw7oiTUkVpDRgd7CGQCDxRfDFP1Wc+3ojQNQbA+8lMXZqajIvcoFXFdVAyJzpk0FAdWTqzM99cd9XHjuRNMYyMaY+3BeoBkaIqtXFhbnbb78jhOCDuCgCMDxUs0zwOQBjrIh8p9LOKgpgZGR4wGdUJnLdbu/jH//zAlG1VheIaOHZB/IFhZQpGhp6fP+Rj/zVLT2u2foEkWVVo8IaCAVzkWedNWtHa4kJMpjf9q13jKCapmkIgZlPksgGFCkmyrM+Wz7ztNUehSUxogzDbIm5n6aLS60oSsgwUDb/KxNnWU5E27aMsQFCoJJOwwQ2K0AOeUWjl6C+AHTtmmFfZKHI9Wu6ZKoQkEbWtVqtMi2k5Xx5aN7pjFTcUM0Fn5OCBQQiYiISFcMEElF/6rsfxBMrG4WGOCIXGZEcKqpBERQZo8fOmerUTDP+65seFeNcdaxQ69kENjaOmaASwNVPfepTaZZpWYBSAKjUhrRIjTHM7L0vF/vtmwQPoFKtEEFUS7B9+ubPHDl82DqrKsQkDIEIfCDJiIuoWm3UPnbTQ59/8Eg8ugkmgZZtv56RW/KQPLEyNloLPtdTptmICaq9Xj8Ebwyrfr2wH8EwdZvz5593hjGGpOBSe0gZxGmaL7V6Jq6B+ST3m0jJgDrt5qYN0y4yCAUh8EBu7NSqgd8btqLRCxJ4EE9OjPo8s8ZwyboABrLKCM7aPM2A8n1MClHxCMW66TiJAA1lA/1gBhlUVZnBJIZVVU7BnCWCMSwiQX2tTtayaClrWLKYQ0BeqK2Nb73ptt2PPHWiUhstvAK+yHqGxUAQfOSMq9UfuP++Rx59Iorc8/md0884y5AQIKJawuzb975EviiAqNEYRM5EFEL40z/9k6wI1Wo1hEKVghoiIi3gU9UQKKHKeObpt/74cwdm1FUmlB3IEBGrQHNnxKofHm74Ij/1TAMVgMh7r6L/NCFHENHIuU57aeuGVUOx8UXPoJwzA2YKirm5vqgJUB1oABDAsbO97vL6tZNJEpMUBgKS57Nk3+u2ktFLAESYaXy0Acl5oAKBsvNHSQGBqA8BgwY6KiNDsJ2aHmUOEnItBZhUVUiFSBUq3qfVSkyQkzIv9I10xTL2EylPbURMIoNvl35SYOqja44u0Z9/5itZ4OrQSOgtWWm50LRFm3ymUjBRpVKF4vd+7w/anS5AhRcAl19+mbEmL3Li8v/+thzJACeqkufrN67bsGE9Uakeh1tuvfW+e+4zlYaQGXxHyUHRbUZ5m7rLCL7QJBme3L1/6ROffsjUVtnKmKcY5ESVSAkhiS2pQsKpT+hBgnWRtVaB4P3XbamCQBo8swzXdf2ahvqMNJTTg41jACfmciXHxoAVJFBiZahK3p8Yq9WTiHxgiIQC+O4WzP/VbEWjt6x5ECqxVV8ghK8vr4iWPXSqOEmxQKm4BBmuV7ToqQbg+ba6k0+0ijVoDNdIT/UOFymdolFB8FAhgJ8v6ngBRY3a+MY/+Zs7Ht19tNIYKbKO7y+cs2X0lS86PbQXNO86JgKMNbY2csst//DY47uYtJQ7P/uM05hKRARm/nZcCRGVXEvvPYJfv3bd2jWry1efD+HDH/5IHuAqVYCYCKSRM6Hfol77uivOumDDiLTnQ5FX6lPG1T/x6bv3HGqa2nSGSibGC6uSilrDKuGfk7hGGajHSWwMszHM/MJVMZF4j5BVE1k1NQzxJEJaihAxgNnlXhFYiQQSJJSNKPCBtIhdMT3miERDUBko1546jP+esBWNXmYiJSCKjEoBCfz8DSMoBCi7QYGT7pi4dMBhYmyYfEoqA/kXBUp6NHGQIBpGR0fplOkiCeUQdwMyhZd+P2cqx8AzKYm6pLH6yQPLN37+MZPUbRSn3YVGIj/7ztf993ffMFlP0m67xHoQqTdGWsuLH/v4x7MsN4YBDDcaxrlS2oqIvh1HUnItjTHBe2h/1apVcRwFUSZ8/gt3fOXLX0ZcARs2hogIoqHXay+95OIN7/+vP/gb/+Vtq6uB82ZRpEltpNWTj/7tHZ1QtdUJj9jG1RDKSRXKIIiezBp+iysB+SxtDA0x8TeeS8tqmM97SUKrJkZD4UmVSlYmAQZzyy1RZmO0JMLKoFBgSBz7NatGNQRCYCbRk/Ie3+O2otFLSgRHVEkiRVAofWOV4AXuU6nsFhcAqybH4TNoIFU+WRpSDYZZfFHk6aqpCSI5JWwYMKrsItft+aXFZWsclKFGlYkTV5n4hy/uOjp2snU6AAAgAElEQVTftUmlCGmaZW+7/rJXXLLhnDXJa150ZpEX3uc+eBERwCRjH//Yxx5+9LFyAes3bdqwaVuRpcaYb7NLQUSMMURlYC8X7LyMma2hXj/90Ic+1O6mLqmUI5gUECn6veXp8cp73/3a6Xj+JecO//gPvjgK7ZC3YHm4Ubn59l2P7j1hquOVxmQWiMmqQgpREcY/G+ErQj46OsrMvvDP35bB70QMklAYDpNjDSKQCisrGAS2aLU6xBaWlISMIWLSsrnEE/npqQkJvsxhq18ROauVjd4yKLag2FoVxWDEAb6uT1sH8sM0mNPOpARgqF4VCQwAJIBCCUGDJ2JRUgmb1404S+ILaJnEpJM64yULE2wYUBJ15FKvJxZb5BxxmQkz9ZFVs83w6dseiqpD6uK0n66fGv6Rt1zVndnrm8/+hzdcNjZcydIuQYgMwNX6UCiy973//cdnZgCsXTV14QXnUpFqCCL+26lcqmocx1maMgDYV1/7CmstgI9/4q9uu+12qjSiKIao+ADVokg167zz+y+76IyR1rMPd48+8c63vviVV5+T95aYPbmoX9DvfvTz7cyJqZFJwExQ74sgYowjOtmKhcFt+Dp2mALA1MS4NariiYiUoIYG5auSfh0IfnK8HhtSKW9oUCVi1+31Rcl7UVECeCAEoCSBgl+zepKIJUAHWY5TZRy/V2wlo1dFRVSYRKmsIJT5XlYFqJypC6GKiwFCgCEL4fKeG+eUQEoBJicOCEZ7joJXhCgOId88GcYaRvMOISgM4EitVTJQJlVGMJ44c+KdRt7L00cXQ+LY9Zj6UTQUNTbefPeex/fNJpUhzQt02z/x9pesqvQpO9Za3n/G9rHXXX2OZG1jRNkqRUzcaIx+5tP/6yO//0f9NANwzo6zjUHIewwhDWWDxCnZEM/vywtZWSAmEWFS9b0NW7ZuWr+GiPY89fRvffADNkosGyNslUgUIlmredVFG95+3eXF3HOVopMvHYkx/57/+NqRmuNQMOKoMXTnY4duv28/R5NsqoCAvNcsiMAlAVao9MFUUsNPfoiJqfAAtq4dodBi6RoRoxFrYiRiEiVRIkIB3187WYsio4CYvpgUAkal0+t49UatgUNQURESYdEgWhTjIxUleDUCEgSVsAISVysZveWpNCjyUGpdlGkmAZSUSQ1AofDVWo0IEgRCpCj5TElsgUFqQ4mUhFEYCkUIyq7Xa6+fqKyeGCbJLbMqVE3pxbl0v0SF5kKeNViOg+CJp4+JiwTeMLmovtCWG299xEW2SHtZc+GCM9bccM1F6M5x3kw7i+Jb7/mhl66drPe7y0RBVVU5ipM4rv72h37r9rvuBvADP/C2WqNG8HYwtw/A//5R7ms+j4nzNI2iuOgvf/9b3zIyMtLtdn/pl395//4DSa3uXFJ4Dw2ViPudhWrs33nDFWuGTNZuShEshdbMgR2bG69++Xn9VjMEmGSM2PzdZ+7OQlIIgwwZKnyeFbkxTkFcRjllsFKOLjkZuYQ8b1Tslg3DIe8QctZAakgtwGWNQIkAj1AM1RIiqxBlDyoIRGqK4IMIgUlYRRUqFECqIAkSWwYBZAlWJQzykd/jtpLRW4ZaQdUXgYyBKsosFg3kFRXIfD48OkzEQUVUVCV4T0DsDFRfMHWOAFJVIiZor9MeGx3bum5aRVT9yZMnAVySeYyqBoBdIQpryFT27nuu2fFk6oLYxfVnDs/ufub4UKOumhLyN75m51g1p7xp1TtjZo8fO23jxBuvvZhCHnqLoeh7YkT1qDrWb7d/6b//t4OHDm9ct/a8887v9/qiqs9PCqJ/qdQGiUiSJEuzJ+LayOuuu06B3/v9P7jx7/620hiHrXFSVWu97zP1fdq65oozXn7JaUsLRwtVb5wSqL+c5ItvffXOWsLeFyaKa42Rh3Y9++jugzYeCZSwTTqdtN/uWwJrYBWjymV7X6nhrlbBSpRm3TWrJtevmS6ynMgoMaAnSwOA6PP+2rkYX591GMwHVlEVkaAvkNoDoFDnHA3Edl6oi/e9bSsZvTh5/7wPhuzA94LkawqKWgQ/PDJCxgwKCIqS0OGL8EJpyMFP2DhnIZ7U51nvkgs3MoIUmSEVES6jZjALWNWwVbK5qhqOhhrPHDr6zME5l0wUWuG4ds9Xn+6mDLZ5ka+bdK+88vT+0oEEbek3Y+soFO25Z37khit3bFud9Vtkgoe0+4WtNKrDax998Cu/9uu/ubS0/J9/9ueGqkmeZmVxpeRzfpPS86m3iLnb7ajvX375FZdfvvO2L9zxm7/xmzaqu3g4CAk7GKoNmdbywrZ1jZ98x8vjfDbvnIDhYCIRcaHr5w+dv2Viw+qx1Oe9zLukknrc8sVHk8ZqT3XhyvxS2m4XlmFUWJWgpASwomwWHrxQ1WenrR8db1RCkZUpiFILWiFUdl2W5XZVa+03iTLoa+0WL0Ro+SdrGBjMTzqZ+/ietxWO3jKS9UEGChjEg26DAdVZob5er7JhYiWIEsqWnV6/OEmzVZRt/qAgSgT1vhK71tLc5ReeW40jkswZDb4YhIJa6tEpE3shslaIyJhWWx7fO69uIqqv6WvyhXseZU7AlaIIOy86a+1UYqXLvhcxEILjULSPr2pkP/GOV47Wk7Qz58gnlWrmxca1qLb6ox/9s/f9jw9efvnlr3v99SH4EAbeV6h84v/390cJKHJfHWr8+Lv/0yOPPfkLv/DeTrs3NLoq86rsAiSEXtZrUfDvfMvl525phNazFesFUoDZWkfBZK3xqt22bsTnXozzcHEl+eK9u5+bz7g6WVBtoYOegMvXmz5/OCcFl533gEAKwF96/oaYC6tBQlCCkgQul8OqpvScwQ9erHiBgqeqMhGTKWX6ym++oPdwAFk9WbJaEa53ZaOXYIwloqIIQYjIlLGWkgogrKpBpahXKGZvGMQQDcwEwnKnS1xSAjHwDAQFpAiGQOqLfnvz6sbZmyYl67P2nS3JlFTqKhHAQqpgZq8i7GCj+x86mJuJ2vjmvUeX9x3rGtcIYqEyNb1KtCjyXAMiG6kElZylW7SOvf5l29/0qvMiSU3oBcl9UUiQSrWRVIf/x/t+/QMf+MD3veH6yakpkYDynK8aoP+SfAypapBw2YtfNjk1+Z73/PT/y957Rll2XXd+O5xz732xclfnbnQAutHIOTdyMJgpUiRFkRzRNkWLQw1lizO2tEbjWbK05DHHooYKQ4qmyAFFigEkmAACIBsAkboROqDROVbnyi/ecM7Z2x9eNQAGSPbSjEcseK/68OrDq3rv3bvfOWfv/f/9d+3cWa8PoyKoYGS868RUtKbb99605lffdIV0T0g2S1ooeFEAMqDEJiLmKC4RM9sogE3KtRMTnWe3HuDKIke1mVTgNYPTZz9SnEMYaCDwwacEcNVFayWdZhAA9SKCqugBpNds73EzQggi2vsLPf5Wb6bNWIt4dgjjNaWAV94ovJLu8yXmdfb2Ogw+dLoZAodXq4yoc9wIVZfWKzA8kIh3KgEB0RhQHJ9qBLSv6U8iABChgjCROKe+sNK899YLrPiQN42FoF56xttnn8KqAKIayEZcqj6/89TEDNq+ZY9tOdjqpGyqigYMjZ06pbaGtu6hUgQKKsyC4EM64xsnPvquK65at6TbnnZ5I0p6kCeNS+WBBSv+93/3qS9/9ZsjC0YBQc4uQT/reP3/IOIk7nQ6v/O7/+r5Z56uDi70gF5DFJORNArN1uTkRWtGfuuDN/bZTtE+oyggwTIwqvPobT0eXP7ivtObdxzBqJTlubIhk6QCz790PNNqVF108OhpYPRnmZJnC80QJCB6Ah+RzzqNC1b1rVtRC+mszzPLFggCi1LoQXoASEQA0BgTXrmWvTFUAFGNo+jVw+9rsrS3jRYRhLlJtXkT8zp7AUU1iJ+amopLJQVA6kGSzrqDgKKktZgWL1zg0jaoRyIlA6Bjx09DXAGYG/9X7AHc5+onjAqhcN2JN9+8bmigVKRdCSmgCCogvko2BGEIgCqKUbk20+6+uOuUo4Fnth9TjhkRlEyp/Ny2PVteOl4aWlvggMOSEgCLkuZpyzdOrhiAT374zoW1RNOmgRw5EIq1sfNYHVz8nQe+c/DwYeT4NcKZfyB58eciiZMXNj/z8q495cFhZMY4BkYNmebT0p3ti/iTH7ln3fKBztSxULQdGQHm4Cl4LyYaWtkwo//+i4+OjTfYWCJEQOSYTLRl+6HpNtja6PPbDnhh4dgrCaL2WuioIg7Vk+YoqRbpHTdc2J94lhyDZ2RAVBRBFexZ1yCAIoK1ttPtBO9fqzdUlVK5dPbQq3h2B/RKZznP3StrMsyPU+98z17oQUCPHD1to5jYAP2UPyWhquuWDCxbshiCJwRRCYrAds+hk2RLwHSWETl3J2Bvc6yBNfj25KpFlWsuXilevO8SqSAIgiAHRARlDaSeICigYuICPfLkrr1j03uOHIUoZoQQfFytT0y6v/riw6cbUXlolXCFjHWhYBsjBEmniumjd1278mO/dkPFSLc1TSguOBdEkYNC39ACm5RVBebat6L4/2aCV+fmnEcWLomTEhvbY8F7FQYPRZe9/9gHbrnl6jVFc0LzRmQ5x8QjU/Am+MiWkuFzvvbY3m//eAeX+kxUYURX5C5Atdr38pHJ2Y5mPjp0so3GeLCCpse0CwgCggyKjiDP243E0o1Xrg1ZIxRtayiEHkNHAcLcJTi7Tyai2ZlZ59xrXb5VpFqtESEiIfzsTBcCdtNM51D582f9ne/ZiwgAYyc6vU4jiD9rEt3DqWpwRWxh+ZJhY0CCEwUfAErJkdNpo+OQ7dl7CF/NXFAEZVApWsE13vPWq0qRBe9UfE/YGkB6c71zxrxzmDquVga27tr/5At7GkUgG1PPyxLi0uDg45sPfeZvvpdCPaqNOlFEyF2I4wS8iyWbPXHog79yy/vedm2MIes2UZ2qGMORMcF5l3smmhMx9tZePFuwOSukePVBb31+leCMEkKpXG41m1FkESkqlQNh8Ln6btrs/Mpdl/7me+/yrUnyKYgrnPNAqsoAhqPqwKKntp349F8/6G3ClUFRIgACFQUTJwKw7+jEywdOtrPUJmUB1LMzJdSzKmYOwSP4buo2nLfi0ovWFnkzuIwIfQiE/Nomdm8GHRSQYKaZOUXCV/iyAhpKSQkUBBXmxtt7wiQERELOC6dz0CD5qfnYX+aY79kLAAATzVycsaBGM4QCgEStogrljqy47oblSSXCwqfBsKqNOW400gNj01SuqGUfkMCCkgIEFuHQ61Ii+U7r5DWXrrlyw3LNCuMLVlXUAA5YAgQB9GBAicWzBqd4uhW+vWlb0D4Fyq0Do+SwFg+QqX35wR2f/+5zWbzQxkNlLgUXFBgh8RlIa8a2Tvzuh+54710Xl0LbSAdCEUJAxYhMRGxUGITAEwakAKhKPTSc9oq8r3kAgiTIAgggqIERXJrGSeKDEtksy4O01bclbb3p2nN+/yNvhdkxP3NS0o4IkuEYWoQZJBU7fM6eM9H/+mcPHTwya5JBAGQoGII1TIQeDFD02AsHv7dpZydHpJJFEQyCwhriEOKAHCIKiXcaBN5+92W1OJeijQRBAdAAGBImQFRQVFFQISXUiE63ctAYtUISIWAAB1D0l0qE0gm5MJGiCSRKgU0ARIy6aW/f7RDC2a/jX/qY39mrhoQApmeanbaLbEToCb0qKRhAEQwebbc1e9HagVIpJvSARGiTuDY9037xpZNUqlBkjbGgPfQGCYogKPa0epplDQqzH/vQrfUSYdFlDSDKhp0UgKpK0steFYIgbFJbf27XmISIrc3JI6sV1JTK5cFuiP74c9/73DefxspKGy+slqp5LhxVFRl8N5s5VA0nfv+jd77rzovJpT5kiuolBOnNBAIoEACiEioCkTKBITWk5uwDJmBUQ0qovRZY7ySICuCcB2Qf1LC61iRkrRsvX/+Hv/u+AdOSxlisHcJCkbwP6p0pVbU2unvC/KtPfe+pFw+VBxZGtkYSGB2IAwmgIkBJ/6KnX9z/wINPctwnQUGcgu8ZZBtRkp7hgUnTsGZJ9R13XJzPHA8+J0OCiCYWJVQmIZzbOwgoAWJAPD3dALUIMapFxQACoCMlm8TkKXgEVCZBRPKEnjiy5dnZFFVBPZLMh8QFgPmdvYgA4AFhYnpmqtmxpWpQ6rVsewBXUGCVvNtZtmh0yVANVEiCKpKJke2OfaeCmBCQgFQcgBD29n1zdRdWEyN3Gqdvvm7tzVev6nZmGFxwGsQGYcCfZRebOFIFVxRBQmxjI9TbQgaEwDbpHyio9O8++8hffW3LdBgt1RbFpVogynxXTM42nZ45zDTzyY+/+d7bLrGUpZ0p0bQQlyMWHHuMPMSgEYbICBvPJrAJxnpjvTHBmmBsMDawCWLEswZUVOQ8CMQRRcb7lKjoTp4uF+4dGy//w0/8yuI+ak4eMtQBSEULIA1isbISKmuOTFf+4P/8zuPb9vUPj5CtAhD2YJqvOVVGUdScnT51+lRcqnBv1KnX+FEOyAIEGFzR8nn63rdtXNiHeWf2lZq5/NzOlghQgzFxlsnE6fEA4axtFPVG3frLaA1YZhUhUkQlg0E9ELCNTp+ZOHtThHljxj2fs7cXkcXJ6e5Us4Co6sEAEIEyKCqoEiOAczHKdZcuCVnO6okwy7RvYGjz1j3NDiVxvxchFJACxJPOzTILAogpUeS7E2lr38c+fNOSkZLP2zEbEDa20oNgvBIiQkjW8Nx4r1cTmIQFORAWIIFMeXDA2eQPP/foH3/ux7uPe1NbjuVhrPSJpdQ3mJp560gZxv/ok2/9Z++4etmgyVsTKm3EQlADRgIxaEwSowKhR/CIYe4HAkIACIiewTMIKgiiR8QoKly3yGfBtUNncs3iysd/9bpP/U/vXFJqtcd3x9BE6AAFVSaqVAdWJgMXbd7j/8Uf3v+j549Wh0aC7RM0iEQ4Z4r2yltWFSBTrvcXhZsrwouSIAB7ZGEIoVsUnQ1rRt9510WhcxJ85ywnQX/eNAwJkDWOaq0Wnjg2aQ0LigIKsARFgJGRUpa1VBz2dL0UBJ2CkLFpHo6MnUZjkIyCIArgP9b86Z9C/GPNI/9JByIbYy13snDrNRvWLK0WRVt7LFgABDWI4oTZKllMhn/wo21qSgIxsYGQnRmfvPGyFecuHy46bVZnIAD2yKQ97RkataHIbeQy1zhnzTnew+PP7GFTEjQ2jnyRm9cgv197LxKRhEDK2IO4ECiDDwXa2Ngycf+LO4/s2Lm3VB8aXrTMJpFSQHSEDl2GWZZouOG6y1cuHz5+6OTM7FRwBaggGUQiJVJQ9IGckgqqkCiJkiqJUhAKiqhESiS9lkzoSt6KQtf44uoNi37/o3e/5/Z1iR/PGkcMtoLrAGKghOIRihbkOPLw5lN/9Bff2nbgjKkPadSvisHl6HNGgV5F8Ozq2xP9A1IIAQCMMT3FniIBsWIouuPg2r/3sbdef35/OrHXYvEzrWr8mbKySlRdcHym9B+/ukVNglFfICDwzmWxFh959/ULBn0optEHEibEgC4gmLiew8Cnv/x0O1cTlVQleOd9MQ80RvM5exGR2UaxzbLignMXXXnBCs1bEHI8O43EaDQoEgpxpT7y0GPbp5o5mrKNEw3Ou6xu9aZrLgx5m3wnMgAI0pODAwKoBdZQIBeAaZrml1581d79Zw4cPYMIXgQB+LU3H+Ic5RSAiECAwfTETkIC6FQzVa8a2WjARPUjpyZ+/OzOIyemhxcuXbJ8GZNaVCxc5ITSTPOZS85beMPl54jI9HSz3Wil3TYEFxtmhAJ9IBTiABSABDkgCaISCKECEPUoUbnPW649U+Vw/vKRD7zp0v/xQzdftqqWTe7uto4TZs6laEsYDXBpqcbLdh9sf+Ohlz/1+e8cGe9Uh0YhrqiIZI2KKfrKnKdtRQAyrzZZEYmoyPMojntKChFBJAVCJnGtvD298fJz/peP3oOtw5hPkor89A35U9mL4kUqg6uf2zPzjUe2U1SBuCIIGgpfdPoS+q1fu6Eed3zWMADgSVGVvFom29dMK5/91pY8MBI5V3iXS3D/H9yB/6VjXmcvINmILee5qyfw1nuuz5pnQDKGAKC99k9sbBAvxEOjS57cOrbv8IQt1woXoiTyRXv8TONNt11dKyNKV3yKgNIjZgAACKgwo4BTDcFDElfXnbf+8c27Wp02ErGJfr6wedayQHsGpEIcEBE9SqdCrmyk6BYgCsgmSTKM9u479uKO/crlxYuXVMuVCGMKhgU4tLuN08sWjVx/5bpzVy0yHIEURdoR183zzEsIQipEEKPa4AmEELinKApFKkU36zZde6o/8uuXDr/rrov/5X93x5tvPCcuJtPmWOGmbcl6ZbW18sBKKC071Sh9/7G9n/nCg99/8uVMo2r/EESx94XvTC2t66+/beM733z7/v17JmYayIn+9HGMiHou4QAAqkwMhN511DXKGP70D96/csCl00cs5EFU8fVNBjGAiSuD677wjWeee/kYletiIlAwEELWGqnFH3vP1UZmXNYyyKgsGoSDIEel0cMnivu+/7zHGIi8y8Vl86NjNK+zF9GYyNhIkbrt7vvffovkU+y7DI4QAIwI9mwQihAGRxafnuw8seVAUq4JGmImksmpyeWLF1xx8eqiO46+y8gCBsAoKmAACoqgwCQRCIPq8uWL6gPDT23ZWWSFsbH+XOHq1dcGqgS9qSwC15k8de/Gy+69/YpjBw82JscRgxqycY1NaWJi9olnd+8/esZGfYuWrIrLQxxVRZyitrtdCW718pE7brrwmktXLVs0ElGeZR3JUtfJXZpaEXY5ZCkWWcjbknc173DeqJliyVD1inMXvOfuC/+H99/0jtvOHyxlzYmjIZtxPodSpcCKrS+O+tccnaSnd0z8+X969Iv3PznThXLfQFyuBETnukVzav3i0sffc/0H3n7TzXfeeGLs5BPPbgdTfq3JCP70vDETBw3EQNDNm40Pv/OqD73zqpmj28uROFcoGnh9eyGvPq4P57jkT7/wo1OzOVVqHgBEE8Ki01izsPThd1xVdE6LzyxGKgwoypIHHVqw9qnnjj3wxC61ZQkuFJnKfBD3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"


def hide_console_window():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception as e:
        logging.error(f"Failed to hide console window: {e}")

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def runtime_dashboard(path, mypath=None):
    try:
        directory = '\\'.join(path.split('/')[0:-1])
        os.chdir(directory)
        filename = path.split('/')[-1]
        
        if __name__ == "__main__":
            print("File chosen:", filename,'\n')
            
        tree = ET.parse(filename)
        root = tree.getroot()


        # CHECK FOR DUPLICATE TRAIN NUMBERS
        tn_list = []
        tn_doubles = []
        for train in root.iter('train'):
            tn = train.attrib['number']
            day = train[0][0][0].attrib['weekdayKey']
            if (tn, day) in tn_list:
                tn_doubles.append((tn, day))
            tn_list.append((tn, day))

        if tn_doubles:
            print('Error: Duplicate train numbers')
            for tn, day in tn_doubles:
                print(f' - 2 trains running on {weekdaykey_dict.get(day)} with train number {tn} - ')
            time.sleep(15)
            sys.exit()
        
        # Convert HH:MM:SS to seconds, accounting for times beyond 23:59:59
        def time_to_seconds(time_str):
            hours, minutes, seconds = map(int, time_str.split(":"))
            return hours * 3600 + minutes * 60 + seconds

        # PARSE THE RSX FOR DATAFRAME
        def rsx_to_df(root):
            services = []
            revtrains = [train for train in root.iter('train') if 'Empty' not in train[1][0].attrib['trainTypeId']]
            for train in revtrains:
                tn = train.attrib['number']
                weekday_key = train[0][0][0].attrib['weekdayKey']
                day = weekdaykey_dict.get(weekday_key, "Unknown")
                day2 = weekdaykey_dict2.get(weekday_key, "Unknown")
                entries = list(train.iter('entry'))
                line = entries[0].attrib.get('zuggattung', 'Unknown')
                
                for i in range(len(entries) - 1):
                    origin          = stationmaster.get(entries[i].attrib['stationName'], 'Unknown')
                    LONGorigin      = entries[i].attrib['stationName']
                    destination     = stationmaster.get(entries[i+1].attrib['stationName'], 'Unknown')
                    LONGdestination = entries[i+1].attrib['stationName']
                    platform_start  = entries[i].attrib.get('trackID', 'N/A')
                    platform_end    = entries[i+1].attrib.get('trackID', 'N/A')
                    
                    dep_1 = time_to_seconds(entries[i].attrib['departure'])
                    dep_2 = time_to_seconds(entries[i+1].attrib['departure'])

                    
                    if entries[i+1].attrib.get('stopTime'):
                        stop_type = "stop"
                        stop_time = int(entries[i+1].attrib['stopTime'])
                        runtime = dep_2 - dep_1 - stop_time
                    else:
                        stop_type = "exp"
                        runtime = dep_2 - dep_1
                    
                    services.append({
                        "Service": tn,
                        "Day": day,
                        "Day2": day2,
                        "Origin": origin,
                        "LOrigin": LONGorigin,
                        "Destination": destination,
                        "LDestination": LONGdestination,
                        "Runtime": runtime,
                        "P-Start": platform_start,
                        "P-End": platform_end,
                        "Type": stop_type,
                        "Line": line
                    })

            # FEED TO DATA FRAME AND SUMMARISE FOR USER
            df = pd.DataFrame(services)
            
            # REVENUE LOCATIONS ONLY
            revloc_services = []
            skipped_runtime = 0
            pending_origin = None # Stores origin info in the event we pass a non-revenue location
            pending_dest = None
            for train in revtrains:
                tn = train.attrib['number']
                weekday_key = train[0][0][0].attrib['weekdayKey']
                day = weekdaykey_dict.get(weekday_key, "Unknown")
                day2 = weekdaykey_dict2.get(weekday_key, "Unknown")
                entries = list(train.iter('entry'))
                line = entries[0].attrib.get('zuggattung', 'Unknown')
                
                for i in range(len(entries) - 1):
                    origin          = stationmaster.get(entries[i].attrib['stationName'], 'Unknown')
                    LONGorigin      = entries[i].attrib['stationName']
                    destination     = stationmaster.get(entries[i+1].attrib['stationName'], 'Unknown')
                    LONGdestination = entries[i+1].attrib['stationName']
                    platform_start  = entries[i].attrib.get('trackID', 'N/A')
                    platform_end    = entries[i+1].attrib.get('trackID', 'N/A')
                    
                    dep_1 = time_to_seconds(entries[i].attrib['departure'])
                    dep_2 = time_to_seconds(entries[i+1].attrib['departure'])

                    
                    if entries[i+1].attrib.get('stopTime'):
                        stop_type = "stop"
                        stop_time = int(entries[i+1].attrib['stopTime'])
                        runtime = dep_2 - dep_1 - stop_time
                    else:
                        stop_type = "exp"
                        runtime = dep_2 - dep_1
                        
                    origin_is_rev = origin not in non_revenue_stations
                    dest_is_rev = destination not in non_revenue_stations
                    
                    if origin_is_rev and not dest_is_rev and not (i+1 == len(entries)-1): 
                        pending_origin = {
                            "Service": tn,
                            "Day": day,
                            "Day2": day2,
                            "Origin": origin,
                            "LOrigin": LONGorigin,
                            "P-Start": platform_start,
                            "Line": line
                        }
                        skipped_runtime += runtime
                        continue
                    elif pending_origin and (not origin_is_rev and dest_is_rev):
                        pending_dest = {
                            "Destination": destination,
                            "LDestination": LONGdestination,
                            "P-End": platform_end,
                            "Type": stop_type,
                            }
                    elif pending_origin and (not origin_is_rev and not dest_is_rev):
                        if i+1 == len(entries)-1:
                            pending_origin = None
                            skipped_runtime = 0
                            continue
                        else:
                            skipped_runtime += runtime
                            continue
                    
                    
                    total_runtime = runtime + skipped_runtime
                    skipped_runtime = 0
                    
                    if pending_origin and pending_dest:
                        service_details = {
                            **pending_origin,
                            **pending_dest,
                            "Runtime": total_runtime
                            }
                        revloc_services.append(service_details)
                        pending_origin = None
                        pending_dest = None
                    else:
                       revloc_services.append({
                        "Service": tn,
                        "Day": day,
                        "Day2": day2,
                        "Origin": origin,
                        "LOrigin": LONGorigin,
                        "Destination": destination,
                        "LDestination": LONGdestination,
                        "Runtime": runtime,
                        "P-Start": platform_start,
                        "P-End": platform_end,
                        "Type": stop_type,
                        "Line": line
                    })                     

            # FEED TO DATA FRAME AND SUMMARISE FOR USER
            df_rev = pd.DataFrame(revloc_services)
            
            unknown_lines_df = df[df["Line"] == "Unknown"]
            if not unknown_lines_df.empty:
                missing_services = unknown_lines_df["Service"].unique().tolist()
                missing_days     = unknown_lines_df["Day"].unique().tolist()
                
            return df, df_rev, {
                "summary": [
                    f"File chosen: {filename}",
                    f"Revenue services identified: {len(revtrains)}",
                    f"Total station-to-station trips identified: {len(services)}",
                    f"Days covered: {', '.join(df['Day'].unique())}"
                ],
                "warning": (
                    "WARNING!" '\n'f"Line allocation missing for services: {missing_services} on {missing_days}"
                    if not unknown_lines_df.empty else None
                )
            }

        data, rev_data, dashboard_messages = rsx_to_df(root)
        
        # RUN THE DASHBOARD
        try:
            port = get_free_port()
        except Exception as e:
            print("Failed to get a free port:", e)
            sys.exit(5)
            
        app = DashProxy(__name__, transforms=[MultiplexerTransform()])
        
        # Dashboard Layout
        app.title = "TAIPAN Runtime Dashboard"
        app.layout = html.Div(id="dashboard-contatiner", style={"position":"relative"}, children=[
            html.Div([
            dcc.Store(id="esc-store", data={"last_cell": None,"clear": False}),
            dcc.Store(id="distinct-table-height", data="29.75vh"),
            dcc.Store(id="details-table-height", data="55.75vh"),
                # Centered Title and Subheading
                html.Div([
                    html.Div([
                        # Left snake icon
                        html.Img(src= snake_logo, style={"height": "100px", "marginRight": "10px"}),
                
                        html.H1("TAIPAN Runtime Dashboard", style={
                            "color": "#e63946",
                            "textAlign": "center",
                            "fontSize": "40px",
                            "marginBottom": "10px",
                            "flex": "1"
                        }),
                
                        # Right snake icon
                        html.Img(src= snake_logo, style={"height": "100px", "marginLeft": "10px"})
                    ], style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "space-between",
                        "paddingLeft": "10px",
                        "paddingRight": "10px"
                    }),
                
                    html.H3("Analyse each services' runtime on a station-to-station level by line, day and the number of unique runtimes.", style={
                        "color": "#e63946",
                        "textAlign": "center",
                        "fontSize": "20px",
                        "marginBottom": "15px",
                        "marginTop": "0px"
                    }),
                ]),  
                
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "5px",
                        "paddingLeft": "10px",
                        "paddingRight": "10px"
                    },
                    children=[
                        # Left: Reset Selection Button
                        html.Div([
                            html.Button("⟲", id="clear-selection-btn", n_clicks=0, title="Clear cell selection", style={
                                "backgroundColor": "#e63946",
                                "color": "white",
                                "border": "none",
                                "padding": "6px 10px",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "22px"
                            }),
                        ], style={"flex": "1", "display": "flex", "justifyContent": "flex-start"}),
                
                        # Center: Dropdowns
                        html.Div([
                            html.Div([
                                html.Label("Runtime Type", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#e63946", "fontSize":"16px"}),
                                dcc.Dropdown(
                                    options=[{"label": "Working", "value": "Working"}, {"label": "Public", "value": "Public"}],
                                    value="Working",
                                    id="runtime-type",
                                    style={"color": "black", "width": "250px"}
                                ),
                            ]),
                            html.Div([
                                html.Label("Line", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#e63946", "fontSize":"16px"}),
                                dcc.Dropdown(
                                    options=[{"label": line, "value": line} for line in sorted(data['Line'].unique())],
                                    multi=True,
                                    id="origin-line",
                                    placeholder="Select line(s)...",
                                    style={"color": "black", "width": "250px"}
                                ),
                            ]),
                            html.Div([
                                html.Label("Reference Station (from or to)", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#e63946", "fontSize":"16px"}),
                                dcc.Dropdown(
                                    options=[{"label": REFstat, "value": REFstat} for REFstat in sorted(set(data['LOrigin'].unique())|set(data['LOrigin'].unique()))],
                                    multi=True,
                                    id="reference-station",
                                    placeholder="Select reference station(s)...",
                                    style={"color": "black", "width": "250px"}
                                ),
                            ]),
                            html.Div([ #!!!
                                html.Label("Revenue Locations Only?", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#e63946", "fontSize":"16px"}),
                                dcc.Dropdown(
                                    options=[{"label": "Yes", "value": "Revenue Locations"}, {"label": "No", "value": "All Locations"}],
                                    value="All Locations",
                                    id="location-type",
                                    style={"color": "black", "width": "250px"}
                                ),
                            ])
                        ], style={"flex": "2", "display": "flex", "gap": "20px", "justifyContent": "center"}),
                        
                        # Right: Warning & Info Icons
                        html.Div([
                            html.Button("⚠️", id="warning-btn", title=dashboard_messages["warning"], style={
                                "backgroundColor": "#FFEA00",
                                "color": "white",
                                "border": "none",
                                "padding": "5px 7px",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "22px"
                            }) if dashboard_messages["warning"] else None,
            
                            html.Button("ℹ️", id="info-btn", title="\n".join(dashboard_messages["summary"]), style={
                                "backgroundColor": "#e63946",
                                "color": "white",
                                "border": "none",
                                "padding": "5px 7px",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "22px"
                            })
                        ], style={"flex": "1", "display": "flex", "justifyContent": "flex-end", "gap": "5px"})
                    ]
                ),
        
                # Main layout continues
                dcc.Loading(type="circle", fullscreen=False, children=html.Div([
                html.Div(style={"display": "flex", "flexWrap": "wrap", "height": "100vh", "overflow": "hidden"}, children=[
                    html.Div(style={"flex": "1", "minWidth": "300px", "paddingRight": "8px", "display": "flex", "flexDirection": "column", "gap": "10px", "marginTop": "18px"}, children=[
                        html.Div(style={"backgroundColor": "#2c2c2c", "padding": "10px", "borderRadius": "8px", "boxShadow": "0 2px 6px rgba(0,0,0,0.3)"
                                        }, children=[
                            html.H3("No. of Unique Run Times", style={"marginTop": "0px","marginBottom": "1vh", "color": "#e63946"}),
                            dash_table.DataTable(
                                id="distinct-table",
                                columns=[
                                    {"name": ["Station", "From"], "id": "Origin"},
                                    {"name": ["Station", "To"], "id": "Destination"},
                                    {"name": ["Day", "Mon"], "id": "Monday-Thursday"},
                                    {"name": ["Day", "Fri"], "id": "Friday"},
                                    {"name": ["Day", "Sat"], "id": "Saturday"},
                                    {"name": ["Day", "Sun"], "id": "Sunday"},
                                ],
                                merge_duplicate_headers=True,
                                page_size = 200,
                                data=[],
                                tooltip_data=[],
                                tooltip_delay=800,
                                tooltip_duration=None,
                                css=[
                                    {"selector": "td:hover", "rule": "background-color: rgba(255, 105, 180, 0.2) !important;"}, # Cell highlight
                                    {"selector": "tr:hover", "rule": "background-color: rgba(255, 105, 180, 0.01) !important;"} # Row highight
                                    ],
                                sort_action="native",
                                sort_mode="multi",
                                style_table={"height": "29.75vh", "overflowY": "auto", "overflowX": "auto"},
                                style_header={"backgroundColor": "#2c2c2c", "fontWeight": "bold", "fontSize": "14px", "color": "#e63946"},
                                style_cell={"backgroundColor": "#2c2c2c", "color": "white", "textAlign": "center", "border": "1px solid #444", "minWidth": "10vh", "width": "50%"}, 
                            )
                        ]),           
                        
                        html.Div(style={"backgroundColor": "#2c2c2c", "padding": "10px", "borderRadius": "8px", "boxShadow": "0 2px 6px rgba(0,0,0,0.3)"
                                        }, children=[
                            html.H3("Service Details", style={"marginTop": "0px", "marginBottom": "1vh", "color": "#e63946"}),
                            dash_table.DataTable(
                                id="details-table",
                                columns=[
                                    {"name": "Day", "id": "Day"},
                                    {"name": "Line", "id": "Line"},
                                    {"name": "Train", "id": "Service"},
                                    {"name": "From", "id": "Origin"},
                                    {"name": "To", "id": "Destination"},
                                    {"name": "Type", "id": "Type"},
                                    {"name": "P-Start", "id": "P-Start"},
                                    {"name": "P-End", "id": "P-End"},
                                    {"name": "Runtime", "id": "Runtime", "type": "numeric"},
                                ],
                                page_size = 100,
                                data=[],
                                cell_selectable=False,                                
                                sort_action="native",
                                sort_mode="multi",
                                filter_action="native",
                                css=[
                                        {"selector": ".dash-filter input", "rule": "color: #e63946 !important; background-color: #2c2c2c !important; border: 1px solid #444; font-style: italic;"},
                                        {"selector": ".dash-filter input::placeholder", "rule": "color: #888 !important; font-style: italic;"},
                                    ],
                                style_table={"height": "55.75vh", "overflowY": "auto", "overflowX": "auto"},
                                style_header={"backgroundColor": "#2c2c2c", "fontWeight": "bold", "fontSize": "14px", "color": "#e63946"},
                                style_cell={"backgroundColor": "#2c2c2c", "color": "white", "textAlign": "center", "border": "1px solid #444", "whiteSpace": "normal", "height": "auto", "minWidth": "7.5vh", "width": "100%"}
                            )
                        ])
                    ]),
                    html.Div(style={"backgroundColor": "#2c2c2c", "padding": "10px", "borderRadius": "8px", "boxShadow": "0 2px 6px rgba(0,0,0,0.3)", "marginTop": "18px", "height": "95.5vh"
                                    }, children=[
                        html.H3("Runtime Distribution by Day", style={"marginBottom": "6px", "marginTop": "0px","color": "#e63946"}),
                        html.Div(id="runtime-graphs", style={
                            "width": "60vw",
                            "height": "95vh",
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "space-around",
                            "alignItems": "stretch",
                            "overflow": "hidden"
                        })
                    ])
                ])
            ]))
        ], style={"backgroundColor": "#000000", "color": "#e63946", "fontFamily": "Roboto Mono", "padding": "10px", "margin":"-8px",  "height": "auto", "overflowY": "auto"}),#"height":"125vh"})"minHeight": "100vh",
        html.Div(id="custom-tooltip", style={
                    "position": "absolute",
                    "top": "10px",
                    "right": "10px",
                    "zIndex": "1000",
                    "backgroundColor": "#333",
                    "color": "white",
                    "padding": "8px",
                    "borderRadius": "6px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                    "display": "none",
                    "maxWidth": "300px",
                    "fontSize": "13px"
                })
            ])
                                            
                                        
        @app.callback(
            Output("distinct-table", "data"),
            Output("distinct-table", "tooltip_data"),
            Output("distinct-table", "style_data_conditional"),
            Output("details-table", "data"),
            Output("runtime-graphs", "children"),
            Output("distinct-table", "active_cell"),
            Output("distinct-table", "selected_cells"),
            Output("distinct-table-height", "data"),
            Output("details-table-height", "data"),
            Input("runtime-type", "value"),
            Input("origin-line", "value"),
            Input("reference-station", "value"),
            Input("location-type", "value"),
            Input("distinct-table", "active_cell"),
            Input("clear-selection-btn", "n_clicks"),
            State("distinct-table", "derived_virtual_data"),
            State("distinct-table", "page_current"),
            State("distinct-table", "page_size")
        )
        def update_dashboard(runtime_type, selected_lines, reference_stations, location_type, active_cell, clear_clicks, derived_virtual_data, page_current, page_size):
            if ctx.triggered_id == "clear-selection-btn":
                active_cell = None
                
            page_current = page_current or 0
            page_size = page_size or 20
            
            if location_type == "Revenue Locations":
                df = rev_data.copy()
                df = df[~df["Origin"].isin(non_revenue_stations) & ~df["Destination"].isin(non_revenue_stations)]
            else:
                df = data.copy()
            
            if runtime_type == "Public":
                df["Runtime"] = (df["Runtime"] // 60)
            
            if selected_lines:
                df = df[df["Line"].isin(selected_lines)]
        
            if reference_stations:
                df = df[df["LOrigin"].isin(reference_stations) | df["LDestination"].isin(reference_stations)]
                
            
                
            pivot = df.groupby(["Origin", "Destination", "Day", "LOrigin", "LDestination"]).agg({"Runtime": "nunique"}).reset_index()
            pivot_table = pivot.pivot_table(index=["Origin", "Destination", "LOrigin", "LDestination"], columns="Day", values="Runtime", fill_value=0).reset_index()
        
            for col in ["Monday-Thursday", "Friday", "Saturday", "Sunday"]:
                if col not in pivot_table.columns:
                    pivot_table[col] = 0
        
            # Tooltip generation
            tooltip = []
            day_columns = ["Monday-Thursday", "Friday", "Saturday", "Sunday"]
            for row in pivot_table.to_dict("records"):
                row_tooltips = {}
                for col in day_columns:
                    row_tooltips[col] = {
                        "type": "markdown",
                        "value": f"**Day**: {col}\n\n**Origin**: {row['LOrigin']}\n\n**Destination**: {row['LDestination']}\n\n**Unique Runtimes**: {int(row.get(col, 0))}"
                    }
                tooltip.append(row_tooltips)
        
            # Highlights based on unique run numbers
            colour_styles = []
            for col in day_columns:
                colour_styles.extend([
                    {"if": {"column_id": col, "filter_query": f"{{{col}}} >= 2 && {{{col}}} <= 3"},
                     "backgroundColor": "rgba(255, 255, 0, 0.4)", "color": "white", "border": "2px solid #cccc00"},
                    {"if": {"column_id": col, "filter_query": f"{{{col}}} >= 4 && {{{col}}} <= 5"},
                     "backgroundColor": "rgba(255, 165, 0, 0.4)", "color": "white", "border": "2px solid #cc8400"},
                    {"if": {"column_id": col, "filter_query": f"{{{col}}} >= 6"},
                     "backgroundColor": "rgba(255, 0, 0, 0.4)", "color": "white", "border": "2px solid #990000"}
                ])
        
            # Static styling
            non_selectable_columns = ["Origin", "Destination"]
            static_styles = [
                {
                    "if": {"column_id": col},
                    "pointerEvents": "none",
                    "backgroundColor": "#2c2c2c"
                } for col in non_selectable_columns
            ]
        
            # Dynamic styling and filtering
            highlight_style = []
            if active_cell and active_cell["column_id"] in day_columns:
                true_index = page_current * page_size + active_cell["row"]
                if true_index < len(derived_virtual_data):
                    row = derived_virtual_data[true_index]
                    col = active_cell["column_id"]
                    df = df[
                        (df["Origin"] == row["Origin"]) &
                        (df["Destination"] == row["Destination"]) &
                        (df["Day"] == col)
                    ]
        
                    highlight_style = [{
                        "if": {
                            "row_index": active_cell["row"],
                            "column_id": active_cell["column_id"]
                        },
                        "backgroundColor": "#444444",
                        "color": "white",
                        "fontWeight": "bold"
                    }]
        
            style_data_conditional = static_styles + highlight_style + colour_styles
            details = df.to_dict("records")
        
            # Graph generation
            day_colours = {
                "Monday-Thursday": "#0070C0",
                "Friday": "#C00000",
                "Saturday": "#92D050",
                "Sunday": "#F37021"
            }
        
            graph_components = []
            graph_ids = ["graph-mon-thurs", "graph-friday", "graph-saturday", "graph-sunday"]
            day_order = ["Monday-Thursday", "Friday", "Saturday", "Sunday"]
        
            def get_dtick(max_count):
                if max_count <= 10:
                    return 1
                raw_tick = max_count / 10
                magnitude = 10 ** math.floor(math.log10(raw_tick))
                nice_tick = math.ceil(raw_tick / magnitude) * magnitude
                return nice_tick
        
            for i, day in enumerate(day_order):
                day_df = df[df["Day"] == day]
                if day_df.empty:
                    continue
                runtime_counts = day_df["Runtime"].value_counts().sort_index()
                max_count = runtime_counts.max()
                dtick = get_dtick(max_count)
        
                fig = go.Figure(data=[
                    go.Bar(
                        x=runtime_counts.index,
                        y=runtime_counts.values,
                        marker=dict(color=day_colours[day], line=dict(width=0)),
                        width=[1] * len(runtime_counts),
                        hovertemplate="Runtime: %{x}<br>Count: %{y}<extra></extra>"
                    )
                ])
        
                fig.update_layout(
                    title=dict(text=day, font=dict(size=18), x=0.5, xanchor='center'),
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    font_color="white",
                    title_font_color=day_colours[day],
                    margin=dict(l=10, r=10, t=40, b=15),
                    yaxis=dict(title=dict(text="Count", font=dict(size=12), standoff=1), dtick=dtick, tickfont=dict(size=10), automargin=True),
                    xaxis=dict(title=dict(text="Runtime", font=dict(size=12), standoff=1), tickangle=-45, tickfont=dict(size=10), automargin=True)
                )
        
                graph_components.append(
                    html.Div([
                        dcc.Graph(id=graph_ids[i], figure=fig, style={"height": "100%", "width": "100%"})
                    ], style={
                        "backgroundColor": "#808080",
                        "padding": "3px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                        "flex": "1",
                        "margin": "3px",
                        "height": "93%",
                        "minWidth": "0",
                        "maxWidth": "90%"
                    })
                )
        
            num_graphs = len(graph_components)
            if num_graphs == 1:
                graphs = [
                    html.Div([
                        html.Div([graph_components[0]], style={
                            "borderRadius": "8px",
                            "width": "100%",
                            "maxWidth": "1000px",
                            "margin": "0 auto",
                            "height": "100%"
                        })
                    ], style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "stretch",
                        "height": "90%",
                        "width": "93%",
                        "marginTop": "10px",
                        "marginLeft": "auto",
                        "marginRight": "0"
                    })
                ]
            else:
                graphs = [
                    html.Div(graph_components[:2], style={
                        "borderRadius": "8px",
                        "display": "flex",
                        "flexWrap": "wrap",
                        "height": "50%",
                        "width": "100%",
                        "marginBottom": "2px"
                    }),
                    html.Div(graph_components[2:], style={
                        "borderRadius": "8px",
                        "display": "flex",
                        "flexWrap": "wrap",
                        "height": "50%",
                        "width": "100%",
                        "marginTop": "1px"
                    })
                ]
                
            # Generates each table height dynamically
            distinct_page_size = 200
            num_rows1 = len(pivot_table)
            height1 = "26vh" if num_rows1 > distinct_page_size else "29.75vh"
        
            details_page_size = 100
            num_rows2 = len(details)
            if height1 == "26vh":
                height2 = "51.875vh" if num_rows2 > details_page_size else "55.625vh"
            else:
                height2 = "51.925vh" if num_rows2 > details_page_size else "55.75vh"
        
            return pivot_table.to_dict("records"), tooltip, style_data_conditional, details, graphs, active_cell, [], height1, height2

        # Allows tooltips for all pages
        @app.callback(
            Output("custom-tooltip", "children"),
            Output("custom-tooltip", "style"),
            Input("distinct-table", "active_cell"),
            State("distinct-table", "derived_virtual_data"),
            State("distinct-table", "page_current"),
            State("distinct-table", "page_size")
        )
        def show_custom_tooltip(active_cell, derived_virtual_data, page_current, page_size):
            if not active_cell or not derived_virtual_data:
                return "", {"display": "none"}
            
            page_current = page_current or 0
            page_size = page_size or 20
        
            true_index = page_current * page_size + active_cell["row"]
            if true_index >= len(derived_virtual_data):
                return "", {"display": "none"}
        
            row = derived_virtual_data[true_index]
            col = active_cell["column_id"]
        
            if col not in ["Monday-Thursday", "Friday", "Saturday", "Sunday"]:
                return "", {"display": "none"}
        
            tooltip_text = [
                html.Strong("Day:"), f" {col}", html.Br(),
                html.Strong("From:"), f" {row['LOrigin']}", html.Br(),
                html.Strong("To:"), f" {row['LDestination']}", html.Br(),
                html.Strong("Unique Runtimes:"), f" {int(row.get(col, 0))}"
            ]
        
            style = {
                "position": "absolute",
                "top": "225px",
                "right": "5px",
                "zIndex": "1000",
                "backgroundColor": "#e63946",
                "color": "white",
                "padding": "8px",
                "borderRadius": "6px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                "display": "block",
                "maxWidth": "300px",
                "fontSize": "13px"
            }
        
            return tooltip_text, style


        # Adjusts height of distinct table dynamically
        @app.callback(
            Output("distinct-table", "style_table"),
            Input("distinct-table-height", "data")
            )
        def apply_table_height(height1):
            return {
                "height": height1,
                "overflowY": "auto",
                "overflowX": "auto"
                }
        
        # Adjusts height of details table dynamically
        @app.callback(
            Output("details-table", "style_table"),
            Input("details-table-height", "data")
            )
        def apply_table_height(height2):
            return {
                "height": height2,
                "overflowY": "auto",
                "overflowX": "auto"
                }
        
        # Updates graphs based on filtered data
        @app.callback(
            Output("runtime-graphs", "children"),
            Input("details-table", "derived_virtual_data")
        )
        def update_graphs_from_filtered_details(filtered_details):
            
            if not filtered_details or len(filtered_details) == len(data):
                return no_update

            df = pd.DataFrame(filtered_details)
        
            day_colours = {
                "Monday-Thursday": "#0070C0",
                "Friday": "#C00000",
                "Saturday": "#92D050",
                "Sunday": "#F37021"
            }
        
            graph_components = []
            graph_ids = ["graph-mon-thurs", "graph-friday", "graph-saturday", "graph-sunday"]
            day_order = ["Monday-Thursday", "Friday", "Saturday", "Sunday"]
        
            def get_dtick(max_count):
                if max_count <= 10:
                    return 1
                raw_tick = max_count / 10
                magnitude = 10 ** math.floor(math.log10(raw_tick))
                nice_tick = math.ceil(raw_tick / magnitude) * magnitude
                return nice_tick
        
            for i, day in enumerate(day_order):
                day_df = df[df["Day"] == day]
                if day_df.empty:
                    continue
                runtime_counts = day_df["Runtime"].value_counts().sort_index()
                max_count = runtime_counts.max()
                dtick = get_dtick(max_count)
        
                fig = go.Figure(data=[
                    go.Bar(
                        x=runtime_counts.index,
                        y=runtime_counts.values,
                        marker=dict(color=day_colours[day], line=dict(width=0)),
                        width=[1] * len(runtime_counts),
                        hovertemplate="Runtime: %{x}<br>Count: %{y}<extra></extra>"
                    )
                ])
        
                fig.update_layout(
                    title=dict(text=day, font=dict(size=18), x=0.5, xanchor='center'),
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    font_color="white",
                    title_font_color=day_colours[day],
                    margin=dict(l=10, r=10, t=40, b=15),
                    yaxis=dict(title=dict(text="Count", font=dict(size=12), standoff=1), dtick=dtick, tickfont=dict(size=10), automargin=True),
                    xaxis=dict(title=dict(text="Runtime", font=dict(size=12), standoff=1), tickangle=-45, tickfont=dict(size=10), automargin=True)
                )
        
                graph_components.append(
                    html.Div([
                        dcc.Graph(id=graph_ids[i], figure=fig, style={"height": "100%", "width": "100%"})
                    ], style={
                        "backgroundColor": "#808080",
                        "padding": "3px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                        "flex": "1",
                        "margin": "3px",
                        "height": "93%",
                        "minWidth": "0",
                        "maxWidth": "90%"
                    })
                )
        
            if len(graph_components) == 1:
                return [
                    html.Div([
                        html.Div([graph_components[0]], style={
                            "borderRadius": "8px",
                            "width": "100%",
                            "maxWidth": "1000px",
                            "margin": "0 auto",
                            "height": "100%"
                        })
                    ], style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "stretch",
                        "height": "90%",
                        "width": "93%",
                        "marginTop": "10px",
                        "marginLeft": "auto",
                        "marginRight": "0"
                    })
                ]
            else:
                return [
                    html.Div(graph_components[:2], style={
                        "borderRadius": "8px",
                        "display": "flex",
                        "flexWrap": "wrap",
                        "height": "50%",
                        "width": "100%",
                        "marginBottom": "2px"
                    }),
                    html.Div(graph_components[2:], style={
                        "borderRadius": "8px",
                        "display": "flex",
                        "flexWrap": "wrap",
                        "height": "50%",
                        "width": "100%",
                        "marginTop": "1px"
                    })
                ]


        def open_browser(port):
            webbrowser.open_new(f"http://127.0.0.1:{port}/")
        
        # Launches dashboard and closes CMD window - if there is failure to launch, CMD stays open for error logging
        def launch_dashboard():
            try:
                threading.Timer(1, lambda: open_browser(port)).start()
                print("Dashboard launching successfully.")
                time.sleep(2)
                hide_console_window()  # Hide the window ONLY if/once the app is running
                app.run(port=port, debug=False)
            except Exception as e:
                logging.error(traceback.format_exc())
                print("Dashboard failed to launch.")
                time.sleep(10)
                sys.exit(1)
        
        launch_dashboard()

    except Exception as e:
        logging.error(traceback.format_exc())
        if ProcessDoneMessagebox:
            print("Dashboard failed to launch.")
            time.sleep(10)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    root.attributes('-topmost', True)  # Ensure dialogs stay on top
    path = askopenfilename(title="Select your RSX", parent=root)
    if path:
        runtime_dashboard(path)
    else:
        messagebox.showinfo('Runtime Dashboard', 'No file selected.', parent=root)
        time.sleep(10)
    root.destroy()
