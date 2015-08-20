from __future__ import unicode_literals
from unicodedata import east_asian_width


def get_display_width(str_):
    return len(str_) + get_full_width_count(str_)


def get_full_width_count(str_):
    return sum(east_asian_width(c) == 'W' or east_asian_width(c) == 'F'
               for c in str_)
    
    
def resolve_status(c_status, air_status):
    if not c_status:
        return air_status
    else:
        return c_status