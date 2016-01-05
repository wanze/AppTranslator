def to_utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string

def to_ascii(string):
    if isinstance(string, unicode):
        return string.encode('ascii', 'replace')
    return string
