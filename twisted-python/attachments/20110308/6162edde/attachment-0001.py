import time
from twisted.internet.protocol import ClientCreator, BaseProtocol
from twisted.internet import defer

SYNC = "*"
PROMPT = ">"

class SyncProtocol(BaseProtocol):

    def __init__(self, number, progress_cb=None):
        self.deferred = defer.Deferred()
        self.total = number
        self.number = 0
        if progress_cb is not None:
            self.progress = progress_cb

    def progress(self, frac):
        pass

    def check(self):
        return self.deferred

    def dataReceived(self, data):
        for octet in data:
            if data != PROMPT:
                self.sessionError(Exception("Non-prompt character"))
                break
            else:
                self.number += 1
                self.progress(float(self.number) / self.total)
            
            if self.number >= self.total:
                self.sessionComplete()
                break
            
            self.transport.write(SYNC)
      
    def connectionMade(self):
        print "Connection made!"
        self.start = time.time()
        self.progress(0.)
        self.transport.write(SYNC)

    def sessionComplete(self):
        self.finishSession()
        self.deferred.callback(self.end - self.start)

    def sessionError(self, err):
        self.finishSession()
        self.deferred.errback(err)

    def finishSession(self):
        self.end = time.time()
        self.transport.loseConnection()
    
    def connectionLost(self, reason):
        pass

class ProgressPrinter(object):
    
    inc = 0.1
    
    def __init__(self):
        self.milestone = 0
        
    def __call__(self, frac):
        if frac > self.milestone:
            print "Progress: %.2f" % frac
            self.milestone += self.inc

def print_error(failure):
    print failure.getErrorMessage()
    return failure

def print_time(duration):
    print "Time: %f" % duration

def go(reac):
    print "Using reactor: %s" % type(reac).__name__
    prc = ClientCreator(reac, SyncProtocol, 1000, ProgressPrinter())
    d = prc.connectTCP("localhost", 31415)
    d.addCallback(lambda prot: prot.check())
    d.addCallback(print_time)
    d.addErrback(print_error)
    d.addBoth(lambda _: reac.stop())

# In Windows: socat TCP4-LISTEN:31415 /dev/com4,raw,echo=0,b57600
# In Linux: socat TCP4-LISTEN:31415 /dev/ttyUSB0,raw,echo=0,b57600

if __name__ == "__main__":
    # from twisted.internet import gtk2reactor
    # gtk2reactor.install()
    from twisted.internet import reactor
    reactor.callWhenRunning(go, reactor)
    reactor.run()