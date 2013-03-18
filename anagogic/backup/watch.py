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
from swiftclient import ClientException

__author__ = 'John Hampton <pacopablo@pacopablo.com>'


__all__ = [
    'watch_directories',
    'unwatch_directory',
    'unwatch_directories',
    'process_directory_changes',
    'get_watched_directory_info',
    'get_watched_directories',
    'pending_changes',
    'set_pending_changes',
    'get_dirs_pending_changes',
    'add_watch_directory',
    'set_directory_change_time',
    'sync_dir',
    'set_upload_in_progress',
    'clear_upload_in_progress',
    'upload_in_progress',
    'enough_time_elapsed',
]

__culprit__ = 'anagogic.backup.watch'
# Stdlib imports
import os
import datetime
import json
from time import strftime

# 3rd party imports
import win32con
import pywintypes
from win32api import FindFirstChangeNotification, FindNextChangeNotification
from win32api import FindCloseChangeNotification
from win32file import CreateFile, GENERIC_WRITE, FILE_SHARE_READ, OPEN_EXISTING
from win32file import WriteFile, CloseHandle





# Local imports
from anagogic.backup.util import get_reg_key_items, APP_REG_KEY, get_reg_value
from anagogic.backup.util import set_reg_value, get_file_stats, del_reg_value
from anagogic.backup.storage import get_session, get_container
from anagogic.backup.storage import dbox_munge_path

APP_DIR_REG_KEY = APP_REG_KEY + r'\Directories'

# Directory change events / filters
STATES = {
    0: 'FILE_NOTIFY_CHANGE_FILE_NAME',
    1: 'FILE_NOTIFY_CHANGE_DIR_NAME',
    3: 'FILE_NOTIFY_CHANGE_SIZE',
    4: 'FILE_NOTIFY_CHANGE_LAST_WRITE',
    }

ALL_STATES = [
    win32con.FILE_NOTIFY_CHANGE_FILE_NAME,
    win32con.FILE_NOTIFY_CHANGE_DIR_NAME,
    win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES,
    win32con.FILE_NOTIFY_CHANGE_SIZE,
    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
    win32con.FILE_NOTIFY_CHANGE_SECURITY,
    ]

STATES_LEN = len(ALL_STATES)
HASHES = '/Hashes/'

# Indexes into REG_MULTI_SZ values for watched directory entries
DIR_ADDED_TIMESTAMP = 0
DIR_LAST_SYNC_TIMESTAMP = 1
DIR_PENDING_CHANGES = 2
DIR_UPLOAD_IN_PROGRESS = 3

def get_watched_directories():
    """ Return a list of directories that need to be watched
    """
    global APP_DIR_REG_KEY

    dirs = [p[0] for p in get_reg_key_items('HKLM', APP_DIR_REG_KEY)]
    return dirs


def get_watched_directory_info(dir):
    """ Return the added and last change times for the directory

    """

    added = changed = ''
    pending = inprogress = False
    tstamps = get_reg_value('HKLM', APP_DIR_REG_KEY, dir)
    num_entries = len(tstamps)
    if num_entries > DIR_ADDED_TIMESTAMP:
        added = tstamps[DIR_ADDED_TIMESTAMP]
    if num_entries > DIR_LAST_SYNC_TIMESTAMP:
        changed = tstamps[DIR_LAST_SYNC_TIMESTAMP]
        if changed == 'None':
            changed = ''
    if num_entries > DIR_PENDING_CHANGES:
        pending = tstamps[DIR_PENDING_CHANGES].lower() == 'true'
    if num_entries > DIR_UPLOAD_IN_PROGRESS:
        inprogress = tstamps[DIR_UPLOAD_IN_PROGRESS].lower() == 'true'
    return (added.strip(), changed.strip(), pending, inprogress)

def set_upload_in_progress(dir):
    """ Sets the upload in progress flag for the given directory
    """

    data = get_reg_value('HKLM', APP_DIR_REG_KEY, dir)
    data[DIR_UPLOAD_IN_PROGRESS] = 'true'
    set_reg_value('HKLM', APP_DIR_REG_KEY, dir, data)


def clear_upload_in_progress(dir):
    """ Clear the upload in progress flag for the given directory
    """

    data = get_reg_value('HKLM', APP_DIR_REG_KEY, dir)
    data[DIR_UPLOAD_IN_PROGRESS] = 'false'
    set_reg_value('HKLM', APP_DIR_REG_KEY, dir, data)


def upload_in_progress(dir):
    """ Returns whether an upload is in progress
    """
    data = get_reg_value('HKLM', APP_DIR_REG_KEY, dir)
    return data[DIR_UPLOAD_IN_PROGRESS].lower() == 'true'


def enough_time_elapsed(changed):
    """ Returns whether or not enough time has elapsed since the last backup

    Pass in the last changed time as retrieved from get_watched_directory_info()
    """
    elapsed = True
    if changed:
        ctime = datetime.datetime.strptime(changed, '%d %b %Y %H:%M')
        elapsed = ((datetime.datetime.now() - datetime.timedelta(minutes=1)) > ctime)
    return elapsed


def pending_changes(dir):
    """ Return whether there are pending changes to be synced for the given dir

    """

    pending = get_reg_value('HKLM', APP_DIR_REG_KEY, dir)
    if len(pending) > DIR_PENDING_CHANGES:
        return pending[DIR_PENDING_CHANGES] == 'true'
    else:
        return False


def set_pending_changes(dir, pending=True):
    """ Mark the directory for pending changes

    By default the directory is marked stating that pending changes are waiting.
    If pending=False, then the pending changes flag is removed

    """

    added, changed, _, inprogress = get_watched_directory_info(dir)
    set_reg_value('HKLM', APP_DIR_REG_KEY, dir,
                    [added, changed, str(pending).lower(),
                     str(inprogress).lower()])


def get_dirs_pending_changes():
    """ Return a list of all the watched directories that have pending changes

    """

    pending_change_list = []
    for d in get_watched_directories():
        if pending_changes(d):
            pending_change_list.append(d)
        continue
    return pending_change_list


def set_directory_change_time(dir):
    """ Sets the last change time for the given directory

    """

    if dir in get_watched_directories():
        added, changed, _, inprogress = get_watched_directory_info(dir)
        pending = pending_changes(dir)
        set_reg_value('HKLM', APP_DIR_REG_KEY, dir,
                      [added, strftime('%d %b %Y %H:%M'), 'false',
                       str(inprogress).lower()])


def add_watch_directory(path):
    """ Add the give n path to the list of directories to watch

    This only stores the info regarding the directory in the registry.  It does
    not start watching the directory.

    """
    absolute_path = os.path.abspath(path)
    tstamp = strftime('%d %b %Y')
    set_reg_value('HKLM', APP_DIR_REG_KEY, absolute_path,
                  [tstamp, 'None', 'true', 'false'])


def watch_directories():
    """ Set 'FindChangeNotification' handles on directories

     Directories to be watched are found in the registry
    """

    handles = list()
    watch_paths = get_watched_directories()
    for path in watch_paths:
        for state in ALL_STATES:
            handles.append(FindFirstChangeNotification(path, 1, state))
    return handles


def unwatch_directory(directory):
    """ Remove the given directory from those being monitored for changes.

    """
    del_reg_value('HKLM', APP_DIR_REG_KEY, directory)
    log.debug('unwatch_directory(%s)' % directory)
    try:
        pipe = get_reg_value('HKLM', APP_REG_KEY, 'namedpipe')
        handle = CreateFile(pipe, GENERIC_WRITE, FILE_SHARE_READ, None,
            OPEN_EXISTING, 0, None)
        WriteFile(handle, 'refreshdirectories')
        CloseHandle(handle)
    except pywintypes.error:
        log.error('Error when calling the namedpipe with the refreshdirectories '
                  'command', culprit=__culprit__)
        pass


def unwatch_directories(handles):
    """ Remove 'FindChangeNotification' handles from the watched directories
    """

    for h in handles:
        FindCloseChangeNotification(h)


def process_directory_changes(handle, pos):
    """ Process the directory that changed
    """

    FindNextChangeNotification(handle)
    state = STATES.get(pos % STATES_LEN, -1)
    if state < 0:
        pass
    else:
        watched_dirs = get_watched_directories()
        changed_dir = watched_dirs[pos / STATES_LEN]
        added, changed, _, _ = get_watched_directory_info(changed_dir)
        log.info('Processing change for %s' % changed_dir, culprit=__culprit__)
        if not upload_in_progress(changed_dir):
            if enough_time_elapsed(changed):
                log.info('Sufficient elapsed time.  Sync dir', culprit=__culprit__)
                set_upload_in_progress(changed_dir)
                sync_dir(changed_dir)
                clear_upload_in_progress(changed_dir)
            else:
                set_pending_changes(changed_dir)
        else:
            log.info('Backup in progress for %s' % changed_dir, culprit=__culprit__)
    pass


def sync_dir(dir, sess=None):
    """ Sync the given directory to Dropbox

    """

    start = datetime.datetime.now()
    backup_data = {}
    uploaded_file_list = []
    deleted_file_list = []
    try:
        if not sess:
            sess = get_session()
        log.info('got session')
        container = get_container()
        hash_path = HASHES + dir[3:].replace("\\", '_')
        log.info('created hash_path')
        try:
            log.info('getting hash from %s' % hash_path)
            manifest = json.loads(sess.get_object(container, hash_path)[1])
            log.info('retrieved manifest')
        except ClientException, e:
            log.warning('Error getting manifest:\n   Status: %d\n   Message: %s'
                        % (e.http_status, e.message), culprit=__culprit__)
            if e.http_status == 404:
                # The manifest didn't exist on swift.  This means we need to seed
                # the directory.  We can do so by starting with an empty manifest
                log.evtlog.info('Swift: manifest doesn\'t exist.  Create a blank one')
                manifest = {}
            elif e.http_status == 400:
                log.error('Error loading manifest for %s\nError message:\n\n%s'
                          % (dir, e.message), culprit=__culprit__)
                return
        files_changed = False
        visited_files = []
        for root, dirs, files in os.walk(dir):
            for f in files:
                absolute_path = os.path.join(root, f)
                dbox_absolute_path = dbox_munge_path(absolute_path)
                visited_files.append(absolute_path)
                file_info = manifest.get(absolute_path, None)
                file_stats = get_file_stats(absolute_path)
                if (not file_info) or\
                   (file_info['filesize'] <> file_stats['filesize'] or\
                    file_info['filemtime'] <> file_stats['filemtime'] or\
                    file_info['filehash'] <> file_stats['filehash']):
                    # File is either new or has been updated.  Either way, we
                    # need to upload the file to dropbox and update the manifest
                    manifest[absolute_path] = file_stats
                    uploaded_file_list.append(absolute_path)
                    sess.put_object(container, dbox_absolute_path, open(absolute_path, 'rb').read())
                    files_changed = True
                continue
            continue
        backup_data['uploaded_files'] = '\n' + '\n'.join(uploaded_file_list)
        deleted_files = set(manifest.keys()).difference(set(visited_files))
        for f in deleted_files:
            sess.delete_object(container, dbox_munge_path(f))
            files_changed = True
            del manifest[f]
            deleted_file_list.append(absolute_path)
            continue
        backup_data['deleted_files'] = '\n' + '\n'.join(deleted_file_list)
        if files_changed:
            sess.put_object(container, hash_path, json.dumps(manifest))
        set_directory_change_time(dir)
        end = datetime.datetime.now()
        backup_data['duration'] = str(end - start)
        backup_data['start'] = start.strftime('%H:%M:%S')
        backup_data['end'] = end.strftime('%H:%M:%S')
        if files_changed:
            log.sentry.info('Backup complete', culprit=__culprit__, extra=backup_data)
    except ClientException, e:
        log.error('Dropbox error: %s' % e.message, culprit=__culprit__)
    except Exception, e:
        log.error('Error', exc_info=True, culprit=__culprit__)
