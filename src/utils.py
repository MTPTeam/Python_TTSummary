# helper functions live here 

        
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

