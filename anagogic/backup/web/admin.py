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
import urllib

# 3rd party imports
from bottle import Bottle, request, static_file, view, TEMPLATE_PATH, debug
from bottle import redirect, response
from swiftclient import ClientException, quote

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY, set_reg_value
from anagogic.backup.storage import get_session
from anagogic.backup.storage import create_container, get_container
from anagogic.backup.storage import app_container_exists, APP_STORAGE_REG_KEY
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

    try:
        sess = get_session()
        if not app_container_exists(sess):
            create_container(sess)
    except ClientException, e:
        log.error('Swift get_session() error: %s' % e.message, exc_info=True, culprit=__culprit__)

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
    data = {
        'template_lookup': [templates,],
        'restartneeded': restartneeded,
        'internalerror': internal_error,
        'server_data': {
            'hostname': get_reg_value('HKLM', APP_REG_KEY, 'host'),
            'port': str(get_reg_value('HKLM', APP_REG_KEY, 'port')),
            'container': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'appfolder',
                                        default='Anagogic Backup'),
            'swift_account': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'account'),
            'swift_password': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'password'),
            'swift_key': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'key'),
            'swift_auth_url': get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'auth_url'),
            'sentrydsn': get_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn'),
            'sentrysite': get_reg_value('HKLM', APP_REG_KEY, 'sentry_site'),
        },
        'watched_data': watched_data,
    }
    return data


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
    swift_key = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'key')
    if not swift_key:
        swift_key = request.forms.settings_swift_key
    swift_password = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'password')
    if not swift_password:
        swift_password = request.forms.settings_swift_password
    swift_account = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'account')
    if not swift_account:
        swift_account = request.forms.settings_swift_account
    swift_auth_url = get_reg_value('HKLM', APP_STORAGE_REG_KEY, 'auth_url')
    if not swift_auth_url:
        swift_auth_url = request.forms.settings_swift_auth_url
    container = request.forms.settings_container
    set_reg_value('HKLM', APP_REG_KEY, 'hostname', hostname)
    set_reg_value('HKLM', APP_REG_KEY, 'port', port)
    set_reg_value('HKLM', APP_REG_KEY, 'restartneeded', restartneeded)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'container', container)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'key', swift_key)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'password', swift_password)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'account', swift_account)
    set_reg_value('HKLM', APP_STORAGE_REG_KEY, 'auth_url', swift_auth_url)
    set_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn', sentrydsn)
    set_reg_value('HKLM', APP_REG_KEY, 'sentry_site', sentrysite)
    redirect('/index.html')


@app.post('/watchdirs')
def watchdirs():
    selected_dirs = request.forms.getlist('watcheddirs')
    for directory in selected_dirs:
        unwatch_directory(directory)
    redirect('/index.html')


@app.get('/browse.html')
@view('browse.tpl')
def browse():
    global htdocs, templates

    cnx = get_session()
    container_info = cnx.get_container(get_container())
    restartneeded = get_reg_value('HKLM', APP_REG_KEY, 'restartneeded')
    internal_error = get_reg_value('HKLM', APP_REG_KEY, 'internal_error', False)
    file_data = {
        'template_lookup': [templates,],
        'restartneeded': restartneeded,
        'internalerror': internal_error,
        'dirs': []
    }
    for files in container_info[1]:
        file_data['dirs'].append(
            {
                'path': files['name'],
                'path_encoded': quote(files['name'], safe='').lstrip('/'),
                'changed': files['last_modified'],
                'size': files['bytes']
            }
        )
        continue
    return file_data

@app.get('/view')
def view_object():
    path = request.query.path
    cnx = get_session()
    container = get_container()
    log.debug('path: %s' % path)
    object_data = cnx.get_object(container, urllib.unquote(path))
    response.content_type = object_data[0]['content-type']
    response.content_length = object_data[0]['content-length']
    response.content_disposition = 'Content-Disposition: attachment; filename="%s"' % urllib.unquote(path)
    return object_data[1]