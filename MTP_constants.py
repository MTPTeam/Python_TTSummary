

# All constants live here



#WEEKDAYKEY  = {'120':'Mon-Thu','64':'Mon','32':'Tue','16':'Wed','8':'Thu','4':'Fri','2':'Sat','1':'Sun'}

#WEEKDAYKEY_NON_ABBR = {'120': 'Monday-Thursday','64': 'Monday','32': 'Tuesday','16': 'Wednesday','8': 'Thursday','4': 'Friday','2': 'Saturday','1': 'Sunday'}


#weekdaykey_dict2 = {'120':'M-Th', '4':'Fri', '2':'Sat', '1':'Sun'}



# add variants of names here - to reference - WEEKDAY_KEYS_MASTER.get('120')[0]



WEEKDAY_KEYS_MASTER = {
    '120': {'short': 'Mon-Thu', 'long': 'Monday-Thursday', 'alias': 'M-Th'},
    '64':  {'short': 'Mon',     'long': 'Monday',          'alias': 'M'},
    '32':  {'short': 'Tue',     'long': 'Tuesday',         'alias': 'T'},
    '16':  {'short': 'Wed',     'long': 'Wednesday',       'alias': 'W'},
    '8':   {'short': 'Thu',     'long': 'Thursday',        'alias': 'R'},
    '4':   {'short': 'Fri',     'long': 'Friday',          'alias': 'F'},
    '2':   {'short': 'Sat',     'long': 'Saturday',        'alias': 'S'},
    '1':   {'short': 'Sun',     'long': 'Sunday',          'alias': 'U'},
}

ID_TO_SHORT = {k: v['short'] for k, v in WEEKDAY_KEYS_MASTER.items()}
ID_TO_LONG  = {k: v['long'] for k, v in WEEKDAY_KEYS_MASTER.items()}
ID_TO_ALIAS = {k: v['alias'] for k, v in WEEKDAY_KEYS_MASTER.items()}

# Universal Reverse Map (maps ANY name/alias back to the ID)
NAME_TO_ID = {}
for uid, info in WEEKDAY_KEYS_MASTER.items():
    for val in info.values():
        NAME_TO_ID[val.lower()] = uid




