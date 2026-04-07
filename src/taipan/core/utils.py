# helper functions live here 

from taipan.constants.days import WEEKDAY_KEYS_MASTER
import re
import pandas as pd
import numpy as np
import colorsys

def _time_key(t):
    """
    Convert various time representations to a numeric key in seconds.
    Supports:
      - ints/floats: hours (can be >24)
      - 'H', 'HH', 'H:MM', 'HH:MM', 'H:MM:SS', 'HH:MM:SS'
      - also handles >24h like '25:14'
    """
    # numeric hours
    if isinstance(t, (int, float)):
        return float(t) * 3600.0

    s = str(t).strip()
    if not s:
        return -1.0  # push empties to the top

    if ":" in s:
        parts = s.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            sec = int(parts[2]) if len(parts) > 2 and parts[2] else 0
            return h * 3600.0 + m * 60.0 + sec
        except Exception:
            # fallback: float hours
            try:
                return float(s) * 3600.0
            except Exception:
                return -1.0
    else:
        # bare hour string or float-like
        try:
            return float(s) * 3600.0
        except Exception:
            return -1.0


def timetrim(timestring):
    """ Format converter from hh:mm:ss to [h]:mm """
    
    if type(timestring) == list:
        timestring = timestring[0]
    if timestring is None or timestring.isalpha() or ':' not in timestring:
        pass
        
    
    #elif timestring[0] == '0':
        #timestring = timestring[1:-3] #comm out for hastus 
    else: timestring = timestring[:-3]
    return timestring


def csl(string):
    """ Returns all unique elements separated by commas """
    
    output = []
    for x in string:
        if x not in output:
            output.append(x)
    return ','.join(output)




def get_weekday_short(weekdaykey):

    weekdaykey = int(weekdaykey)
    if weekdaykey != 0 and (weekdaykey & 120) == weekdaykey:
        return 'Mon-Thu'

    return WEEKDAY_KEYS_MASTER[str(weekdaykey)]['short']


def parseTimeDelta(s):
    if str(s) == 'nan':
        return np.nan
    d = re.match(
        r'((?P<days>\d+) days, )?(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)',
        str(s)).groupdict(0)
    from datetime import timedelta
    return timedelta(**{k: int(v) for k, v in d.items()})

def minutes_to_time_format(chart_obj):
    """Format X axis as HH:MM by using a custom number format on the axis."""
    ax = chart_obj.Axes(1)
    ax.TickLabels.NumberFormat = '[h]:mm'
    ax.MajorUnit = 60    # tick every 60 minutes
    ax.MinimumScale = 0
    ax.MaximumScale = 24 * 60


def timedeltatohhmmss(s):
    s = str(s)
    if s == 'NaT' or s == '': return ''
    parts = s.split()

    if len(parts) == 3:
        days = int(parts[0])
        timestamp = parts[2].split('.')[0]
        h, m, s = map(int, timestamp.split(':'))
        total_hours = (days * 24) + h
        result = f"{total_hours:02}:{m:02}:{s:02}"
    elif len(parts) == 1:
        result = parts[0].split('.')[0]
    else:
        result = s

    return timetrim(result)  # strips :ss consistently
 


def hhmm_to_excel_time(hhmm):
   if not hhmm or pd.isna(hhmm): return np.nan
   return _time_key(hhmm) / 86400.0


def td_to_hhmm(td):
    if pd.isna(td): return None
    total_minutes = int(td.total_seconds() // 60)
    hh, mm = divmod(total_minutes, 60)
    return f"{hh:02d}:{mm:02d}"


def generate_colors(n, saturation=0.65, value=0.85):
    colors = []
    for i in range(n):
        h = i / n
        r, g, b = colorsys.hsv_to_rgb(h, saturation, value)
        rgb = (int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255)
        colors.append(rgb)
    return colors


def hhmm_to_mins(t: str) -> int:
    h, m = t.split(':')
    return int(h) * 60 + int(m)


def mins_to_excel_time(m: int) -> float:
    return m / 1440