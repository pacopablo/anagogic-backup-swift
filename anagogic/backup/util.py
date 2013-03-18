# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
__author__ = 'John Hampton <pacopablo@pacopablo.com>'

# Stdlib imports
import sys
import traceback
import os
import hashlib
from stat import ST_SIZE, ST_MTIME

# 3rd party imports
from _winreg import OpenKey, EnumKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ
from _winreg import HKEY_CLASSES_ROOT, HKEY_CURRENT_USER, HKEY_DYN_DATA
from _winreg import HKEY_USERS, HKEY_PERFORMANCE_DATA, HKEY_CURRENT_CONFIG
from _winreg import QueryValue, KEY_WRITE, CloseKey, CreateKey, SetValueEx
from _winreg import SetValue, REG_DWORD, REG_MULTI_SZ, REG_SZ, EnumValue
from _winreg import DeleteValue


ROOTS = {
    'HKLM' : HKEY_LOCAL_MACHINE,
    'HKCU' : HKEY_CURRENT_USER,
    'HKDD' : HKEY_DYN_DATA,
    'HKU'  : HKEY_USERS,
    'HKCC' : HKEY_CURRENT_CONFIG,
    'HKPD' : HKEY_PERFORMANCE_DATA,
    'HKCR' : HKEY_CLASSES_ROOT,
}

APP_REG_KEY = r'Software\Anagogic\Backup'

__all__ = [
    'getTrace',
    'NullOutput',
    'set_reg_value',
    'get_reg_value',
    'del_reg_value',
    'get_reg_key_items',
    'APP_REG_KEY',
    'get_file_stats'
]

def getTrace():
    """ retrieve and format an exception into a nice message
    """
    msg = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1],
        sys.exc_info()[2])
    msg = ''.join(msg)
    msg = msg.split('\012')
    msg = ''.join(msg)
    msg += '\n'
    return msg

class NullOutput:
    """A stdout / stderr replacement that discards everything."""

    def noop(self, *args, **kw):
        pass
    write = writelines = close = seek = flush = truncate = noop

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration

    def isatty(self):
        return False

    def tell(self):
        return 0

    def read(self, *args, **kw):
        return ''

    readline = read

    def readlines(self, *args, **kw):
        return []

def get_reg_value(root='HKLM', key='', name=None, default=None):
    """ Return the value of the specified key

    Returns None on error.  To get the key default value, the value parameter
    should be None
    """

    try:
        key = OpenKey(ROOTS[root], key, 0, KEY_READ)
        if name:
            val = QueryValueEx(key, name)
        else:
            val = QueryValue(key, None)
        CloseKey(key)
    except WindowsError:
        val = (default,)

    return val[0]


def get_reg_data_type(data):
    """ Return the proper data type for the registry

    list() = REG_MULTI_SZ  # List values must be strings
    str() = REG_SZ
    int() =  REG_DWORD

    """
    #TODO: add binary data type

    data_type = None
    if isinstance(data, list):
        data_type = REG_MULTI_SZ
        for x in data:
            if not isinstance(x, basestring):
                data_type = None
                break
    elif isinstance(data, basestring):
        data_type = REG_SZ
    elif isinstance(data, int):
        data_type = REG_DWORD

    return data_type


def set_reg_value(root='HKLM', key='', name=None, value=None):
    """ Set the registry value

    If value is None, the default key value is set
    """

    data_type = get_reg_data_type(value)
    if not data_type:
        return
    try:
        k = OpenKey(ROOTS[root], key, 0, KEY_WRITE)
    except WindowsError:
        k = CreateKey(ROOTS[root], key)

    if name:
        SetValueEx(k, name, 0, data_type, value)
    else:
        SetValue(k, '', data_type, value)
    CloseKey(k)


def del_reg_value(root='HKLM', key='', name=None):
    """ Remove the value specified by 'name' from the given key
    """

    try:
        k = OpenKey(ROOTS[root], key, 0, KEY_WRITE)
        if name:
            DeleteValue(k, name)
    except WindowsError:
        pass


def get_reg_key_items(root='HKLM', key=''):
    """ Return a list of tuples containing (name, value) pairs

    The default value for the key is not returned
    """

    items = []
    try:
        key = OpenKey(ROOTS[root], key, 0, KEY_READ)
        i = 0
        while 1:
            name = EnumValue(key, i)
            value = QueryValueEx(key, name[0])
            items.append((name[0], value[0]))
            i += 1
            continue
    except WindowsError:
        CloseKey(key)

    return items


def get_file_stats(path):
    """ Returns the filesize and has of the file contents of path.

    Path should be and absolute path

    """
    statinfo = os.stat(path)
    filehash = hashlib.sha1(open(path, 'rb').read()).hexdigest()
    filestats = {
        'filesize': statinfo[ST_SIZE],
        'filehash': filehash,
        'filemtime': statinfo[ST_MTIME],
    }
    return filestats


