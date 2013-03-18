__author__ = 'John Hampton <pacopablo@pacopablo.com>'

from distutils.core import setup
import py2exe
import sys

__VERSION__ = '0.9'

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = __VERSION__
        self.company_name = "Anagogic"
        self.copyright = "(c) 2012 Anagogic"
        self.name = "Anagogic Backup"

################################################################
# a NT service, modules is required
myservice = Target(
    # used for the versioninfo resource
    description = "Anagogic Backup",
    # what to build.  For a service, the module name (not the
    # filename) must be specified!
    modules = ["anagogic.backup"],
    cmdline_style='pywin32',
)

setup(
    # The lib directory contains everything except the executables and the python dll.
    # Can include a subdirectory name.
# Is this needed for the service?
#    zipfile = "lib/shared.zip",
    service = [myservice],
    windows = ['scripts/watchdir.py'],
#    options = {'py2exe': {"dll_excludes": ["mswsock.dll", "MSWSOCK.dll"]}},
    options={"py2exe": {
                "includes": [
                    "raven.events",
                    "raven.processors",
                    "raven.handlers.logging",
                    "raven.conf",
                ]
            }},
)
