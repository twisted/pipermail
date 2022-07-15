from datetime import datetime
from twisted.internet.defer import inlineCallbacks, maybeDeferred, fail, Deferred, succeed
from twisted.internet import task, reactor
from twisted.python import log
from twisted.python.log import PythonLoggingObserver, defaultObserver

import logging

defaultObserver.stop()
logging.basicConfig(level=0,
                    format=(
        "%(asctime)s %(levelname)-8s: %(module)-11s"
        " (%(process)d|%(thread)x): %(message)s"
        ))
observer = PythonLoggingObserver()
observer.start()

class Break:

    called = 0
    
    def __init__(self):
        self.deferred = Deferred()

    def __call__(self):
        self.__class__.called += 1
        print "called ",self.called
        if self.called==3:
            del self.connector
        if self.called==5:
            self.deferred.errback('Break!')
        else:
            self.deferred.callback('happy!')

def doStuff():
    b = Break()
    reactor.callLater(2,b)
    return b.deferred

def loop():
    try:
        doStuff()
    except Exception,e:
        log.err(None,'Unhandled scheduled exception')
    
looper = task.LoopingCall(loop)
looper.start(1.0)
reactor.run()
