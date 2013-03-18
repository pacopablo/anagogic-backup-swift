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

# 3rd party imports
from swiftclient import Connection, ClientException

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY, set_reg_value


__all__ = [
    'get_session',
    'is_swift_authenticated',
    'get_account_info',
    'get_container',
    'app_container_exists',
    'create_container',
    'dbox_munge_path',
]

# Dropbox Info
APP_STORAGE_REG_KEY = APP_REG_KEY + r'\Swift'
APP_CONTAINER = 'Anagogic Backup'


def get_session():
    SWIFT_USER = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'account')
    SWIFT_PASS = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'password')
    SWIFT_KEY = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'key')
    SWIFT_AUTH_URL = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'auth_url')
    cnx = Connection(SWIFT_AUTH_URL, '%s:%s' % (SWIFT_USER,SWIFT_PASS), SWIFT_KEY)
    cnx.get_auth()
    return cnx

def is_swift_authenticated(sess):
    """ Attempts to create a swift connection.

    """

    try:
        cnx = get_session()
        authenticated = True
    except ClientException:
        authenticated = False
        pass
    return authenticated


def get_account_info(sess=None):
    cnx = get_session()
    return cnx.get_account()


def get_container():
    """ Return the path of the "App folder".

     By default the "App folder" is "Anaogic Backup"

    """
    return get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'container',
                            default=APP_CONTAINER)


def app_container_exists(sess):
    """ Return whether the "App folder" exists in the linked users' dropbox

     By default, the "App folder" is "Anagogic Backup".  This can be changed
     via the web interface or by setting HLKM\Anagogic\Dropbox\appfolder

    """

    exists = False
    app_container = get_container()
    cnx = get_session()
    try:
        info = get_account_info()
        for container in info[1]:
            if container['name'] == app_container:
                exists = True
                break
    except ClientException, e:
        log.error('Error when checking for existence of '
                                   'app container: %s\nError message:\n\n%s'
                                   % (app_container, e.error_msg))
    return exists


def create_container(sess):
    """ Create "App folder" in the linked users' dropbox

    By default, the folder created is "Anagogic Backup".  This can be changed
    via the web interface or by setting HKLM\Anagogic\Dropbox\appfolder

    """

    cnx = get_session()
    app_container = get_container()
    try:
        cnx.file_create_folder(app_container)
    except ClientException, e:
        log.errror('Unable to create app folder: %s\nError Message:\n\n%s'
                   % (app_container, e.error_msg))
        raise e


def dbox_munge_path(path):
    """ Returns the path in a suitable format for Dropbox.

    ``path`` should be an absolute path.

    Dropbox uses unix paths. Paths will be munged by replacing all backslashes
    with forward slashes and the drive moniker (ie; C:) with C_Drive, where 'C'
    corresponds to the drive letter.  Additionally, the APP_FOLDER is prepended
    to the path.

    Example:

    >>> dbox_mung_path('C:\Development\mungepath.py')
    '/Anagogic Backup/C_Drive/Development/mungepath.py'

    >>>

    """

    dbox_absolute_path = '/' + \
                         path.replace(':\\', '_Drive/'
                         ).replace('\\', '/')
    return dbox_absolute_path

