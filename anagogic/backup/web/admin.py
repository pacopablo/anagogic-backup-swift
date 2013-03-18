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
import os

# 3rd party imports
from bottle import Bottle, request, static_file, view, TEMPLATE_PATH, debug
from bottle import redirect
from dropbox import rest

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY, set_reg_value
from anagogic.backup.storage import get_session, is_dropbox_authenticated
from anagogic.backup.storage import get_account_info, get_auth_url
from anagogic.backup.storage import get_request_token, save_access_token
from anagogic.backup.storage import get_access_token, create_app_folder
from anagogic.backup.storage import app_folder_exists, APP_STORAGE_REG_KEY
from anagogic.backup.watch import get_watched_directories, get_watched_directory_info
from anagogic.backup.watch import unwatch_directory

__all__ = [
    'app',
]

__culprit__ = 'anagogic.backup.web.admin'
htdocs = get_reg_value('HKLM', APP_REG_KEY, 'htdocs')
templates = get_reg_value('HKLM', APP_REG_KEY, 'templates')
TEMPLATE_PATH = [templates]

debug(True)
app = Bottle()

def check_internal_error(fn):
    def wrap_error(*args, **kwargs):
        try:
            set_reg_value('HKLM', APP_REG_KEY, 'internal_error', False)
            fn(*args, **kwargs)
        except rest.ErrorResponse, e:
            log.error('Application auth callback failure', exc_info=True,
                culprit=__culprit__)
            set_reg_value('HKLM', APP_REG_KEY, 'internal_error', True)
            redirect('/index.html')

    return wrap_error


@app.get('/_info_')
def info():
    html = "<html><head><title>Bottle Info</title></head><body>"
    html += "<h1>bottle - template paths</h1><p>"
    for p in TEMPLATE_PATH:
        html += "&nbsp;&nbsp;&nbsp;{} <br>".format(p)
    html += "<h1>os.environ</h1><p>"
    for k, v in os.environ.items():
        html += "{}: {} </br>".format(str(k), str(v))
    html += "</p><h1>wsgi.environ</h1><p>"
    for k, v in request.environ.items():
        html += "{}: {} </br>".format(str(k), str(v))
    html += "</p></body></html>"
    return html

@app.error(404)
def error404(error):
    global htdocs
    return static_file('404.html', root=htdocs)

@app.get('/js/<path:path>')
def serve_js(path):
    global htdocs
    return static_file(path, root=os.path.join(htdocs, 'js'))

@app.get('/img/<path:path>')
def serve_img(path):
    global htdocs
    return static_file(path, root=os.path.join(htdocs, 'img'))

@app.get('/css/<path:path>')
def serve_css(path):
    global htdocs
    return static_file(path, root=os.path.join(htdocs, 'css'))

@app.get('/<path:path>')
def serve_resources(path=''):
    global htdocs
    return static_file(path, root=htdocs)

@app.get('/')
@app.get('/index.html')
@view('index.tpl')
def index():
    global htdocs, templates

    account_info = ''
    auth_url = ''

    try:
        sess = get_session()
        try:
            authenticated = is_dropbox_authenticated(sess)
        except rest.ErrorResponse:
            authenticated = False

        if authenticated:
            account_info = get_account_info(sess)
            if not app_folder_exists(sess):
                create_app_folder(sess)
        else:
            auth_url = get_auth_url(sess, request.environ['HTTP_HOST'])
    except rest.ErrorResponse:
        log.error('Dropbox get_session() error', exc_info=True, culprit=__culprit__)


    watched_data = {
        'dirs': []
    }
    watched_dirs = get_watched_directories()
    for dir in watched_dirs:
        added, changed, _, _ = get_watched_directory_info(dir)
        watched_data['dirs'].append(
            {
                'directory': dir,
                'added': added,
                'changed': changed,
            }
        )
        continue

    restartneeded = get_reg_value('HKLM', APP_REG_KEY, 'restartneeded')
    internal_error = get_reg_value('HKLM', APP_REG_KEY, 'internal_error', False)
    app_key_set = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_key')
    app_key_set = app_key_set and get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_secret')
    data = {
        'template_lookup': [templates,],
        'restartneeded': restartneeded,
        'internalerror': internal_error,
        'dropbox_data': {
            'appkey': app_key_set,
            'linked': authenticated,
            'account': account_info,
            'authorize': auth_url,
        },
        'server_data': {
            'hostname': get_reg_value('HKLM', APP_REG_KEY, 'host'),
            'port': str(get_reg_value('HKLM', APP_REG_KEY, 'port')),
            'appfolder': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'appfolder',
                                        default='Anagogic Backup'),
            'sentrydsn': get_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn'),
            'sentrysite': get_reg_value('HKLM', APP_REG_KEY, 'sentry_site'),
        },
        'watched_data': watched_data,
    }
    return data


@app.get('/authorize')
@check_internal_error
def auth_callback():
    request_token_key = request.query.oauth_token
    if not request_token_key:
        return "Expected a request token key back!"

#    try:
    sess = get_session()
    request_token = get_request_token()
    access_token = sess.obtain_access_token(request_token)
    save_access_token(access_token)
    if not app_folder_exists(sess):
        create_app_folder(sess)
#    except rest.ErrorResponse, e:
#        log.error('Application auth callback failure', exc_info=True,
#                    culprit=__culprit__)
#        set_reg_value('HKLM', APP_REG_KEY, 'internal_error', True)
    redirect('/index.html')


@app.get('/unlink')
@check_internal_error
def unlink_dropbox():
    sess = get_session()
    access_token = get_access_token()
    sess.set_token(access_token.key, access_token.secret)
    sess.unlink()
    access_token.key = ''
    access_token.secret = ''
    save_access_token(access_token)
    redirect('/index.html')


@app.post('/save_settings')
def save_settings():
    port = get_reg_value('HKLM', APP_REG_KEY, 'port', default=4242)
    hostname = get_reg_value('HKLM', APP_REG_KEY, 'hostname', default='127.0.0.1')
    sentrydsn = get_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn')
    sentrysite = get_reg_value('HKLM', APP_REG_KEY, 'sentry_site')
    restartneeded = 0
    data = request.forms.settings_hostname
    if data:
        parts = data.split(':')
        if hostname <> parts[0].strip():
            log.info("--%s-- | --%s--" % (hostname, parts[0].strip()))
            hostname = parts[0].strip()
            restartneeded = 1
        if len(parts) > 1:
            try:
                if port <> int(parts[1].strip()):
                    port = int(parts[1].strip())
                    log.info("--%d-- | --%d--" % (port, int(parts[1].strip())))
                    restartneeded = 1
            except ValueError:
                log.error('Unable to set port to: %s' % parts[1].strip())

    data = request.forms.sentry_dsn if request.forms.sentry_dsn.lower() <> 'none' else None
    if data and (data <> sentrydsn):
        sentrydsn = data
        restartneeded = 1
    data = request.forms.sentry_site if request.forms.sentry_site.lower() <> 'none' else None
    if data and (data <> sentrysite):
        sentrysite = data
        restartneeded = 1
    app_key = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_key')
    if not app_key:
        app_key = request.forms.app_key
    app_secret = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_secret')
    if not app_secret:
        app_secret = request.forms.app_secret
    appfolder = request.forms.settings_appfolder
    set_reg_value('HKLM', APP_REG_KEY, 'hostname', hostname)
    set_reg_value('HKLM', APP_REG_KEY, 'port', port)
    set_reg_value('HKLM', APP_REG_KEY, 'restartneeded', restartneeded)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'appfolder', appfolder)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_key', app_key)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'app_secret', app_secret)
    set_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn', sentrydsn)
    set_reg_value('HKLM', APP_REG_KEY, 'sentry_site', sentrysite)
    redirect('/index.html')


@app.post('/watchdirs')
def watchdirs():
    selected_dirs = request.forms.getlist('watcheddirs')
    for directory in selected_dirs:
        unwatch_directory(directory)
    redirect('/index.html')
