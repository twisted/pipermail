#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__copyright__ = 'Copyright(C) CCI.fr SAS, 2005'
__authors__   = 'Olivier GUILLOUX <o.guilloux@cci.fr>'
__credits__   = ''
__version__   = '$Revision: 2822 $'
__date__      = '$Date: 2005-12-19 10:31:28 +0100 (lun, 19 déc 2005) $'
__doc__ = """ Gamin reactor """

# Python
import gamin
import time
import imp

# twisted
from twisted.application import service
from twisted.internet import base

# Local
import configuration

class _Gamin(object):
    """ Encapsulate monitoring tool and manage watching directories

    @ivar _monitor: Monitor
    @type _monitor: C{gamin.WatchMonitor}

    @ivar _directories: watching directories list
    @type _directories: C{list}

    @ivar callback: callback method to be called when an event occur on
                    watching directories
    @type callback: C{ref}

    @ivar _conf: configuration module
    @type _conf: C{ref}
    """

    def __init__(self):
        self._monitor = gamin.WatchMonitor()
        self._directories = []
        self.callback = None
        self._conf = configuration


    def __del__(self):
        """ destroy _monitor """
        del self._monitor

    def addDirectory(self, p_dir):
        """ Add a watching directory to the list """
        self._directories.append(p_dir)
    
    def setCallback(self, p_callback):
        """ Initialize callback method """
        self.callback = p_callback

    def importConfiguration(self, p_moduleName):
        """ Dynamic import of the configuration, the module name must be
        in the python path. """
        m = imp.find_module(p_moduleName)
        module = imp.load_module(p_moduleName, *m)
        self._conf = module
        
    def loadConfiguration(self):
        # Initialize callback
        m = imp.find_module(self._conf.CALLBACK)
        module = imp.load_module(self._conf.CALLBACK, *m)
        self.setCallback(getattr(module, 'getCallback'))
        
        # Initialize directories
        self._directories = self._conf.WATCHING_DIRECTORIES

    def watching(self):
        for dir in self._directories:
            obj = self._monitor.watch_directory(dir, self.callback)
            obj.data = dir

    def stopWatching(self):
        for dir in self._directories:
            self._monitor.stop_watch(dir)

class GaminReactor(base.ReactorBase, _Gamin):

    __name__ = 'pyccifr.exploitation.gaminreactor'

    def __init__(self):
        base.ReactorBase.__init__(self)
        _Gamin.__init__(self)

    def run(self):
        self.running = 1
        try:
            self.loop()
        except KeyboardInterrupt:
            self.stop()

    def loop(self):
        while self.running:
            # run the delayeds
            self.runUntilCurrent()
            timeout = self.timeout()
            if timeout is None:
                timeout = self._conf.SLEEP
            self.doIteration(timeout)

    def doIteration(self, delay):
        result = self._monitor.event_pending()
        time.sleep(delay)
        if result > 0:
            self._monitor.handle_one_event()
            self._monitor.handle_events()   

class GaminService(service.Service):

    def startService(self):
        reactor = GaminReactor()
        reactor.addSystemEventTrigger('before', 'startup', 
            reactor.loadConfiguration
        )
        reactor.addSystemEventTrigger('before', 'startup',
            reactor.watching
        )
        reactor.addSystemEventTrigger('before', 'shutdown',
            reactor.stopWatching
        )
        reactor.run()

# To be used with twistd
application = service.Application(
    'gestionnaireEvenementCollecte',
    uid=505,
    gid=506
)
service = GaminService()
service.setServiceParent(application)
service.startService()


