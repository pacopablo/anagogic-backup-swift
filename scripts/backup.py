# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

# This file is only needed if not running from the exe
# Testing has all been done from the py2exe'd package.  There may be somethings
# that don't work properly when run "by hand".  Specifically, all of the
# registry entries will need to be configured.

__author__ = 'John Hampton <pacopablo@pacopablo.com>'

# Stdlib imports

# 3rd party imports
import win32serviceutil

# Local imports
from anagogic.backup.service import AnagogicBackupService


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AnagogicBackupService)