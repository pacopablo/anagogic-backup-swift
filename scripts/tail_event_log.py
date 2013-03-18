# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

""" A very hacky `tail -f` for the Application Event Log

Very simple script to parse through the events in the Application event log
and only show the events with a given source.  By default it only shows events
with a source of "anagogic".  An alternate source can be specified on the
command line.
"""

__author__ = 'John Hampton <pacopablo@pacopablo.com>'

import sys
import time

from win32evtlog import OpenEventLog, CloseEventLog, ReadEventLog, EVENTLOG_FORWARDS_READ, EVENTLOG_SEQUENTIAL_READ
from win32evtlog import EVENTLOG_ERROR_TYPE, EVENTLOG_INFORMATION_TYPE, EVENTLOG_WARNING_TYPE
from win32evtlogutil import SafeFormatMessage

evlog = OpenEventLog(None, 'Application')
flags = EVENTLOG_FORWARDS_READ | EVENTLOG_SEQUENTIAL_READ

TYPES = {
    EVENTLOG_ERROR_TYPE: 'Error',
    EVENTLOG_WARNING_TYPE: 'Warning',
    EVENTLOG_INFORMATION_TYPE: 'Info',
}

if len(sys.argv) > 1:
    source = unicode(sys.argv[1])
else:
    source = u'anagogicbackup'

while 1:
    try:
        records = ReadEventLog(evlog, flags, 0)
        if len(records) == 0:
            time.sleep(0.5)
        for x in records:
            if x.SourceName == source:
                print x.TimeWritten.Format(), '- %-7s - EventID: %d' % (TYPES.get(x.EventType), x.EventID)
                print '\n   ', SafeFormatMessage(x), '\n'
            continue
    except KeyboardInterrupt:
        break

CloseEventLog(evlog)
sys.exit(0)