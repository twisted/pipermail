#! /usr/bin/env python

import sys
from py.magic import greenlet

def monkeypatch():
    """monkeypatch py.test.item.Function.execute"""
    import py.__.test.item
    
    def myexecute(self, target, *args):
        res = gr_twisted.switch(lambda: target(*args))
        if res:
            res.raiseException()
        
    py.__.test.item.Function.execute = myexecute

def start_twisted_logging():
    class Logger(object):
        """late-bound sys.stdout"""
        def write(self, msg):
            sys.stdout.write(msg)

        def flush(self):
            sys.stdout.flush()
            # sys.stdout will be changed by py.test later.

    import twisted.python.log
    twisted.python.log.startLogging(Logger(), setStdout=0)

def run_twisted():
    """greenlet: run twisted mainloop"""
    from twisted.internet import reactor, defer
    from twisted.python import log, failure
    failure.Failure.cleanFailure = lambda *args: None # make twisted copy traceback...
    start_twisted_logging()
    
    def doit(val):
        res = gr_tests.switch(val)
        if res is None:
            reactor.stop()
            return
            
        def done(res):
            reactor.callLater(0.0, doit, None)

        def err(res):
            reactor.callLater(0.0, doit, res)
            
        defer.maybeDeferred(res).addCallback(done).addErrback(err)
        
    reactor.callLater(0.0, doit, None)
    reactor.run()



gr_twisted = greenlet(run_twisted)
gr_tests = greenlet.getcurrent()

def main():
    monkeypatch()
    import py.test.cmdline
    gr_twisted.switch()
    try:
        py.test.cmdline.main()
    finally:
        gr_twisted.switch(None)
    
if __name__=='__main__':
    main()
