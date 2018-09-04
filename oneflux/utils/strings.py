'''
oneflux.utils.strings

For license information:
see LICENSE file or headers in oneflux.__init__.py

String parsing utilities

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2015-04-04
'''
import os
import sys
import logging

_log = logging.getLogger(__name__)

def num(s):
    """
    Returns a number (integer or float) if string 's' is a numeric and 'None' if not.
    's' MUST be a string.
    
    :param s: string with number
    :type s: str
    :rtype: int or float or None
    """
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None

def my_int(s):
    """
    Returns an integer if string 's' is integer and 'None' if not.
    's' MUST be a string.
    
    :param s: string with number
    :type s: str
    :rtype: int or None
    """
    try:
        return int(s)
    except ValueError:
        return None

def my_float(s):
    """
    Returns a float if string 's' is float and 'None' if not.
    's' MUST be a string.
    
    :param s: string with number
    :type s: str
    :rtype: float or None
    """
    try:
        return float(s)
    except ValueError:
        return None

def is_int(s):
    """
    Returns True if string 's' is integer and False if not.
    's' MUST be a string.
    
    :param s: string with number
    :type s: str
    :rtype: bool
    """
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    """
    Returns True if string 's' is float and False if not.
    's' MUST be a string.
    
    :param s: string with number
    :type s: str
    :rtype: bool
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def longest_substring(str_list):
    """
    Finds longest substring among list of strings
    
    :param str_list: strings to be searched
    :type str_list: list (of str)
    :rtype: str
    """

    lstr = ''
    if (len(str_list) > 1) and (len(str_list[0]) > 0):
        for i in range(len(str_list[0])):
            for j in range(len(str_list[0]) - i + 1):
                if (j > len(lstr)) and all(str_list[0][i:i + j] in entry for entry in str_list):
                    lstr = str_list[0][i:i + j]
    lstr = 'a' + lstr # avoid stripping beginning of line
    return lstr.strip('1234567890_- \t\n\r\'"')[1:] # removes digits at the end of line


if __name__ == '__main__':

    _log.critical(msg="Error: cannot be executed directly")
    sys.exit(-1)
