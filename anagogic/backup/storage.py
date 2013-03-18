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
from dropbox import session, client, rest

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY, set_reg_value


__all__ = [
    'get_session',
    'get_client',
    'is_dropbox_authenticated',
    'get_access_token',
    'get_request_token',
    'get_account_info',
    'get_auth_url',
    'save_access_token',
    'get_app_folder',
    'app_folder_exists',
    'create_app_folder',
    'dbox_munge_path',
]

# Dropbox Info
APP_STORAGE_REG_KEY = APP_REG_KEY + r'\Dropbox'
ACCESS_TYPE = 'dropbox'
APP_FOLDER = 'Anagogic Backup'


def get_session():
    APP_KEY = get_reg_value('HKLM',APP_STORAGE_REG_KEY, 'app_key')
    APP_SECRET = get_reg_value('HKLM',APP_STORAGE_REG_KEY, 'app_secret')
    return session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)


def get_client(access_token, sess=None):
    if not sess:
        sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return client.DropboxClient(sess)


def is_dropbox_authenticated(sess):
    """ Checks to see if the application is already attached and authorized to
    a dropbox account

    """

    access_token = get_access_token()
    authenticated = False
    if access_token.key and access_token.secret:
        try:
            client = get_client(access_token, sess=sess)
            info = client.account_info()
            authenticated = True
        except:
            pass
    return authenticated


def get_access_token():
    """ Return the Dropbox access token stored in the registry

    """

    access_key = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'access_key')
    access_secret = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'access_secret')
    return session.OAuthToken(access_key, access_secret)


def get_request_token():
    """ Return the Dropbox request token stored in the registry

    """

    request_key = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'request_key')
    request_secret = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'request_secret')
    return session.OAuthToken(request_key, request_secret)


def get_account_info(sess=None):
    access_token = get_access_token()
    client = get_client(access_token, sess=sess)
    return client.account_info()


def get_auth_url(sess=None, host='127.0.0.1'):
    """ Returns the URL for authorizing the application

    """
    if not sess:
        sess = get_session()
    request_token = sess.obtain_request_token()
    callback = "http://%s/authorize" % (host)
    url = sess.build_authorize_url(request_token, oauth_callback=callback)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'request_key', request_token.key)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'request_secret', request_token.secret)
    return url

def save_access_token(access_token):
    """ Save the access token received from Dropbox

    """
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'access_key', access_token.key)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'access_secret', access_token.secret)


def get_app_folder():
    """ Return the path of the "App folder".

     By default the "App folder" is "Anaogic Backup"

    """
    return get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'appfolder',
                            default=APP_FOLDER)


def app_folder_exists(sess):
    """ Return whether the "App folder" exists in the linked users' dropbox

     By default, the "App folder" is "Anagogic Backup".  This can be changed
     via the web interface or by setting HLKM\Anagogic\Dropbox\appfolder

    """

    exists = False
    access_token = get_access_token()
    app_folder = get_app_folder()
    client = get_client(access_token, sess=sess)
    try:
        client.metadata(app_folder)
        exists = True
    except rest.ErrorResponse, e:
        if e.status in [304, 406]:
            exists = True
        elif e.status == 400:
            log.error('Error when checking for existence of '
                                       'app folder: %s\nError message:\n\n%s'
                                       % (app_folder, e.error_msg))
            raise e
        elif e.status == 404:
            exits = False
    return exists


def create_app_folder(sess):
    """ Create "App folder" in the linked users' dropbox

    By default, the folder created is "Anagogic Backup".  This can be changed
    via the web interface or by setting HKLM\Anagogic\Dropbox\appfolder

    """

    client = get_client(get_access_token(), sess)
    app_folder = get_app_folder()
    try:
        client.file_create_folder(app_folder)
    except rest.ErrorResponse, e:
        if e.status == 400:
            log.errror('Unable to create app folder: %s\nError Message:\n\n%s'
                       % (app_folder, e.error_msg))
            raise e
        elif e.status == 403:
            # Directory already exists.  That's OK for our purpose
            pass


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

    app_folder = get_app_folder()
    dbox_absolute_path = app_folder + '/' + \
                         path.replace(':\\', '_Drive/'
                         ).replace('\\', '/')
    return dbox_absolute_path

