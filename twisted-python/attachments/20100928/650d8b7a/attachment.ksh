from datetime import datetime
from twisted.internet.defer import inlineCallbacks, maybeDeferred, fail, Deferred
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

    def __init__(self):
        self.deferred = Deferred()

    def __call__(self):
        del self.connector

def doStuff():
    b = Break()
    reactor.callLater(2,b)
    return b.deferred

@inlineCallbacks
def loop():
    print datetime.now()
    try:
        yield doStuff()
    except Exception,e:
        log.err(None,'Unhandled scheduled exception')
    
looper = task.LoopingCall(loop)
looper.start(1.0)
reactor.run()
