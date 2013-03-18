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

# 3rd party imports
import pywintypes
from win32file import CreateFile, GENERIC_WRITE, FILE_SHARE_READ, OPEN_EXISTING
from win32file import WriteFile, CloseHandle

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY
from anagogic.backup.watch import get_watched_directories, add_watch_directory

if __name__ == '__main__':
    dir_to_watch = sys.argv[1]
    pipe = get_reg_value('HKLM', APP_REG_KEY, 'namedpipe')
    watched_dirs = get_watched_directories()
    if dir_to_watch not in watched_dirs:
        add_watch_directory(dir_to_watch)
    try:
        handle = CreateFile(pipe, GENERIC_WRITE, FILE_SHARE_READ, None,
                            OPEN_EXISTING, 0, None)
        WriteFile(handle, 'refreshdirectories')
        CloseHandle(handle)
    except pywintypes.error:
        # The named pipe wasn't ready which should indicate that the service
        # isn't started.  We can ignore this since the watch list will be
        # loaded when the service starts
        pass


