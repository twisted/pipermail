#!/usr/bin/env python

import sys
from twisted.internet import reactor
from twisted.python import log, failure
from tdefer import TDeferred, logDeferredHistory, succeed

def gen(x):
    D = TDeferred()
    if x:
        reactor.callLater(2, D.callback, x)
    else:
        reactor.callLater(2, D.errback, Exception("one failed!"))
    return D

def ok(result, msg, color='red'):
    print "ok called with %r" % result
    raise Exception("ok raises")

def ok2(result):
    print "ok2 called with %r" % result

def d(result):
    print "d called"
    D = TDeferred()
    D.addCallback(d2)
    # Uncomment the next line to log the history of the deferred D
    # in the middle of running (and printing) the deferred chain
    # started by our original call to gen.
    # D.addCallback(logDeferredHistory, D)
    reactor.callLater(2, D.callback, 33)
    return D

def d2(result):
    return 45
    
def nok(failure):
    print "nok called"
    return d(1)

def stop(x):
    print 'stop received %r' % x
    if isinstance(x, failure.Failure):
        print x.getTraceback()
    reactor.callLater(0, reactor.stop)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    x = gen(True)
    log.err('orig deferred is %r' % x)
    x.addBoth(logDeferredHistory, x)
    x.addCallback(d)
    x.addBoth(logDeferredHistory, x)
    x.addCallback(ok, 'hello', color='black')
    x.addErrback(nok)
    x.addCallback(ok2)
    x.addBoth(logDeferredHistory, x)
    x.addBoth(stop)
    reactor.run()
