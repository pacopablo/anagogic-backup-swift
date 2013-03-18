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

from _winreg import OpenKey, HKEY_LOCAL_MACHINE
from _winreg import KEY_WRITE, CloseKey, SetValueEx, REG_SZ

APP_REG_KEY = r'Software\Anagogic\Backup\Swift'
key = OpenKey(HKEY_LOCAL_MACHINE, APP_REG_KEY, 0, KEY_WRITE)
SetValueEx(key, 'key', 0, REG_SZ, r'testing')
SetValueEx(key, 'account', 0, REG_SZ, r'test')
SetValueEx(key, 'password', 0, REG_SZ, r'tester')
SetValueEx(key, 'auth_url', 0, REG_SZ, r'http://192.168.52.2:8080/auth/v1.0/')
SetValueEx(key, 'container', 0, REG_SZ, r'Anagogic Backup')

CloseKey(key)
