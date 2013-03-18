# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
from anagogic.backup.log import log

__author__ = 'John Hampton <pacopablo@pacopablo.com>'

# Stdlib imports
from threading import Event

# 3rd party imports
import win32event
import win32serviceutil
import win32service
import pywintypes
from win32file import FILE_FLAG_OVERLAPPED, CloseHandle, ReadFile
from win32pipe import CreateNamedPipe, ConnectNamedPipe, DisconnectNamedPipe
from win32pipe import PIPE_ACCESS_INBOUND, PIPE_TYPE_MESSAGE
from win32pipe import PIPE_UNLIMITED_INSTANCES

# Local imports
from anagogic.backup.util import getTrace, get_reg_value, APP_REG_KEY, set_reg_value
from anagogic.backup.web import AdminWebServerThread
from anagogic.backup.watch import unwatch_directories, watch_directories
from anagogic.backup.watch import process_directory_changes
from anagogic.backup.watch import sync_dir, upload_in_progress
from anagogic.backup.watch import enough_time_elapsed, get_watched_directory_info
from anagogic.backup.watch import get_dirs_pending_changes

__all__ = [
    'AnagogicBackupService',
]

__culprit__ = 'anagogic.service'

class AnagogicBackupService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'anagogicbackup'            # used in "net start/stop"
    _svc_display_name_ = "Anagogic Backup"
    _svc_description_ = "Backup directories to Dropbox"
    _svc_thread_class = AdminWebServerThread

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Looks like py2exe handles redirecting stdout and stderror for us
        #sys.stdout.close()
        #sys.stderr.close()
        #sys.stdout = NullOutput()
        #sys.stderr = NullOutput()
        # Create an event which we will use to wait on.
        # The "service stop" request will set this event.
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        # Event for named pipe operation
        self.overlapped = pywintypes.OVERLAPPED()
        self.overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        # Internal timer
        self.timer = win32event.CreateWaitableTimer(None, 0, None)

        set_reg_value('HKLM', APP_REG_KEY, 'restartneeded', 0)
        # Setup Named pip for IPC
        pipename = get_reg_value('HKLM', APP_REG_KEY, 'namedpipe')
        self.pipe_handle = None
        if not pipename:
            log.error('No named pipe was specified in the registry',
                        culprit=__culprit__)
            self.SvcStop()
        else:
            openmode = PIPE_ACCESS_INBOUND | FILE_FLAG_OVERLAPPED
            pipmode = PIPE_TYPE_MESSAGE
            sa = pywintypes.SECURITY_ATTRIBUTES()
            sa.SetSecurityDescriptorDacl(1, None, 0)
            self.pipe_handle = CreateNamedPipe(pipename, openmode, pipmode,
                                                PIPE_UNLIMITED_INSTANCES, 0, 0,
                                                0, sa)

        # Initialize a list of watched handles
        self.handles = list()
        self.mgmt_handles = list()
        self.mgmt_callbacks = list()


    def SvcStop(self):
        # Before we do anything, tell the SCM we are starting the stop process.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # stop the process if necessary
        self.thread_event.clear()
        self.service_thread.join()

        # And set my event.
        win32event.SetEvent(self.hWaitStop)

        # Clear any watched directories
        unwatch_directories(self.handles[:-2])

        # Close named pipe
        if self.pipe_handle:
            DisconnectNamedPipe(self.pipe_handle)
            CloseHandle(self.pipe_handle)

    # SvcStop only gets triggered when the user explicitly stops (or restarts)
    # the service.  To shut the service down cleanly when Windows is shutting
    # down, we also need to hook SvcShutdown.
    SvcShutdown = SvcStop


    def add_mgmt_event_handler(self, event_handle, event_callback):
        """ Add event handles and call backs to the mgmt_handles and
        mgmt_callbacks lists

        """
        self.mgmt_handles.append(event_handle)
        self.mgmt_callbacks.append(event_callback)


    def SvcDoRun(self):
        import servicemanager

        # log a service started message
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ' (%s)' % self._svc_display_name_))
        try:
            # Spawn off web server
            self.thread_event = Event()
            self.thread_event.set()
            log.info('Before try block to spawn thread')
            try:
                if self._svc_thread_class:
                    log.info('Thread class specified, instantiating now')
                    self.service_thread = self._svc_thread_class(self.thread_event)
                    log.info('Thread instantiated, starting thread')
                    self.service_thread.start()
                    log.info('Thread started')
                else:
                    log.error("No Service thread was provided", culprit=__culprit__)
                    self.SvcStop()
            except Exception, info:
                log.error('Uncaught error in thread', exc_info=True, culprit=__culprit__)
                errmsg = getTrace()
                servicemanager.LogErrorMsg(errmsg)
                self.SvcStop()

            # Start watching directories
            self.mgmt_handles = []

            self.handles = watch_directories()
            self.add_mgmt_event_handler(self.timer, self.process_timer)
            self.add_mgmt_event_handler(self.overlapped.hEvent,
                                        self.process_named_pipe)
            self.add_mgmt_event_handler(self.hWaitStop,
                                        lambda a, b, c: True)
            self.handles.extend(self.mgmt_handles)

            # Set internal timer
            # default to 2 minute period
            timer_period = get_reg_value('HKLM', APP_REG_KEY, 'timer',
                                          default=120000)
            win32event.SetWaitableTimer(self.timer, 0, timer_period, None, None,
                                        False)

            while 1:
                hr = ConnectNamedPipe(self.pipe_handle, self.overlapped)

                rc = win32event.WaitForMultipleObjects(self.handles, 0,
                    win32event.INFINITE)

                if rc == win32event.WAIT_FAILED:
                    log.error('WAIT_FAILED for unknown reason')
                    self.SvcStop()
                    break
                elif rc == win32event.WAIT_TIMEOUT:
                    log.error('WAIT_TIMEOUT: This should NEVER happen')
                    pass
                elif (rc >= win32event.WAIT_OBJECT_0) and \
                     (rc < (len(self.handles) - len(self.mgmt_handles))):
                    process_directory_changes(self.handles[rc], rc)
                else:
                    offset = rc - len(self.handles) + len(self.mgmt_handles)
                    dobreak = self.mgmt_callbacks[offset](rc, self.handles,
                                                          self.mgmt_handles)
                    if dobreak:
                        break
                continue
        except:
            log.error('Uncaught error in main event loop', exc_info=True,
                      culprit='anagogic.service')
            servicemanager.LogErrorMsg(getTrace())

        # log a service stopped message
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, ' (%s) ' % self._svc_display_name_))


    def process_named_pipe(self, rc, handles, mgmt_handles):
        """ Read data from the named pipe and perform the appropriate action

        """
        hr, data = ReadFile(self.pipe_handle, 256)
        if data.strip() == 'refreshdirectories':
            unwatch_directories(self.handles[:-len(mgmt_handles)])
            newhandles = watch_directories()
            newhandles.extend(self.mgmt_handles)
            self.handles = newhandles
            pass
        elif data.strip() == 'restartwebserver':
            #restart webserver
            pass
        DisconnectNamedPipe(self.pipe_handle)
        return False


    def process_timer(self, rc, handles, mgmt_handles):
        dirs_pending = get_dirs_pending_changes()
        if dirs_pending:
            log.info('The following directories have pending changes:\n   %s'
                      % '\n   '.join(dirs_pending), culprit='anagogic.service'
                        )
            for d in dirs_pending:
                if not upload_in_progress(d):
                    _, changed, _, _ = get_watched_directory_info(d)
                    if enough_time_elapsed(changed):
                        sync_dir(d)
                    else:
                        log.info('Not enough time has elapsed since last backup '
                                 'for %s' % d, culprit=__culprit__)
                else:
                    log.info('Backup in progress for %s' % d, culprit=__culprit__)
        return False
