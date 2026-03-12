# helper functions live here 


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

