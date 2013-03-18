# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
__author__ = 'John Hampton <pacopablo@pacopablo.com>'

# Stdlib imports

# 3rd party imports
from raven import Client

# Local imports
from anagogic.backup.util import get_reg_value, APP_REG_KEY

__all__ = [
    'log',
]


LOG_TYPES = [
    'error',
    'warning',
    'critical',
    'info',
    'debug',
]

class EvtlogLogging(object):
    _name = 'evtlog'

    def error(self, message, **kwargs):
        import servicemanager
        servicemanager.LogErrorMsg(message + str(kwargs))

    def warning(self, message, **kwargs):
        import servicemanager
        servicemanager.LogWarningMsg(message + str(kwargs))

    def debug(self, message, **kwargs):
        import servicemanager
        servicemanager.LogInfoMsg(message + str(kwargs))

    def info(self, message, **kwargs):
        import servicemanager
        servicemanager.LogInfoMsg(message + str(kwargs))

    def critical(self, message, **kwargs):
        import servicemanager
        servicemanager.LogErrorMsg(message + str(kwargs))


class SentryLogging(object):
    _name = 'sentry'

    def __init__(self):
        import servicemanager

        dsn = get_reg_value('HKLM', APP_REG_KEY, 'sentry_dsn')
        # Need to do some error catching so that SentryLogging is disabled if,
        # for some reason the dsn is invalid.
        if not dsn:
            servicemanager.LogErrorMsg('Sentry DSN was not specified.  Logging'
                                       ' to sentry will be disabled')
            self.error = self.warning = self.info = self.critical = \
            self.debug = self.nulloutput
        else:
            sitename = get_reg_value('HKLM', APP_REG_KEY, 'sentry_site')
            self.raven = Client(dsn, site=sitename)


    def nulloutput(self, message, **kwargs):
        """ noop for when a Sentry DSN is not provided """
        pass

    def _send_message(self, message, level='debug', **kwargs):
        """ Send a log message to the sentry server.

        This method should be called by other methods which should set the level
        accordingly.
        """
        d = {
            'level': level if level in LOG_TYPES else 'error',
            'culprit': 'anagogic.backup',
            'logger': 'anagogic.backup',
            }
        d.update(kwargs.get('data', dict()))
        culprit = kwargs.get('culprit', None)
        if culprit:
            d['culprit'] = culprit
            del kwargs['culprit']
        logger = kwargs.get('logger', None)
        if logger:
            d['logger'] = logger
            del kwargs['logger']

        exc_info = kwargs.get('exc_info', False)
        extra = kwargs.get('extra', dict())
        extra['message'] = message
        kwargs['extra'] = extra
        kwargs['data'] = d

        if exc_info:
            self.raven.captureException(exc_info=True, data=d, extra=extra)
        else:
            self.raven.captureMessage(message, **kwargs)

    def error(self, message, **kwargs):
        """ Send an error message to given Sentry server.

        If ``exc_info=True`` send a traceback along with message

        """
        self._send_message(message, level='error', **kwargs)

    def warning(self, message, **kwargs):
        self._send_message(message, level='warning', **kwargs)
        pass

    def critical(self, message, **kwargs):
        self._send_message(message, level='critical', **kwargs)
        pass

    def info(self, message, **kwargs):
        self._send_message(message, level='info', **kwargs)
        pass

    def debug(self, message, **kwargs):
        self._send_message(message, level='debug', **kwargs)
        pass


class Log(object):
    """ Log messages to the event log or sentry

    """

    def __init__(self, loggers):

        self.loggers = dict()
        if loggers:
            for l in loggers:
                self.loggers[l._name] = l()
                setattr(self, l._name, self.loggers[l._name])
                continue
        pass

#    def __getattr__(self, item):
#        if item in LOG_TYPES:
#            fn = getattr(self, item)
#        elif item in self.loggers.keys():
#            fn = self.loggers[item]
#        return fn

    def log_message(self, logtype, message, **kwargs):
        for l in self.loggers.values():
            method = getattr(l, logtype, None)
            if method:
                method(message, **kwargs)
            continue

    def error(self, message, **kwargs):
        """ Log an error """
        self.log_message('error', message, **kwargs)
        pass

    def info(self, message, **kwargs):
        """ Log an info message """
        self.log_message('info', message, **kwargs)
        pass

    def warning(self, message, **kwargs):
        """ Log a warning message """
        self.log_message('warning', message, **kwargs)
        pass

    def debug(self, message, **kwargs):
        """ Log a debug message """
        self.log_message('debug', message, **kwargs)
        pass

    def critical(self, message, **kwargs):
        """ Log a critical message """
        self.log_message('critical', message, **kwargs)
        pass

loggers = (SentryLogging, EvtlogLogging)
log = Log(loggers)