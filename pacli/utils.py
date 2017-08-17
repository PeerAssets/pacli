from terminaltables import AsciiTable

def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()

def print_table(title, heading, data):
    " prints a table to the terminal using terminaltables.AsciiTable "
    data = list(data)
    data.insert(0, heading)
    table = AsciiTable(data, title=title)
    print(table.table)


