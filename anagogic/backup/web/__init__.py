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


__all__ = [
    'AdminWebServerThread',
]

# Stdlib imports
import select
from threading import Thread

# 3rd part imports
from bottle import ServerAdapter, run as bottle_run

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY
from anagogic.backup.web.admin import app

__bottle_app__ = app


class WSGIRefHandleOneServer(ServerAdapter):
    """ Bottle request handler that tries not to block
    """

    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        handler_class = WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            handler_class = QuietHandler
        srv = make_server(self.host, self.port, handler, handler_class=handler_class)
        log.evtlog.info("Bound to %s:%s" % (self.host or '0.0.0.0', self.port))
        srv_wait = srv.fileno()
        # The default  .serve_forever() call blocks waiting for requests.
        # This causes the side effect of only shutting down the service if a
        # request is handled.
        #
        # To fix this, we use the one-request-at-a-time ".handle_request"
        # method.  Instead of sitting polling, we use select to sleep for a
        # second and still be able to handle the request.
        while self.options['notifyEvent'].isSet():
            ready = select.select([srv_wait], [], [], 1)
            if srv_wait in ready[0]:
                srv.handle_request()
            continue


class AdminWebServerThread(Thread):
    """ Bottle web server thread
    """
    def __init__(self, eventNotifyObj):
        """ Initializes the thread with a signal used for stopping the thread
        """
        Thread.__init__(self)
        self.notifyEvent = eventNotifyObj

    def run ( self ):

        try:
            port = get_reg_value(key=APP_REG_KEY, name='port')
            host = get_reg_value(key=APP_REG_KEY, name='host')
            bottle_run(__bottle_app__, host=host, port=port,
                        server=WSGIRefHandleOneServer, reloader=False,
                        quiet=True, notifyEvent=self.notifyEvent)
        except:
            log.error('Error in WebServerThread', exc_info=True)
