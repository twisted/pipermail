#!/usr/bin/python
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor, defer, task, threads
import sys, signal, time

class EchoClient(Protocol):
    
    def __init__(self):
        pass
    
    def connectionMade(self):
        reactor.callLater(0, self.__myCallback, 0)
        timer = task.LoopingCall(self.transport.write, "LoopingCall")
        timer.start(4)

    def dataReceived(self, data):
        print "Received : %s" % data
        threads.deferToThread(self.__myLoop)
    
    def __myCallback(self, cnt):
        self.transport.write(str(cnt))
        d = defer.Deferred()
        reactor.callLater(2, d.callback, cnt+1)
        d.addCallback(self.__myCallback)
    
    def __myLoop(self):
        while True:
            self.transport.write("Thread")
            time.sleep(1)

class EchoClientFactory(ClientFactory):
    protocol = EchoClient
    
    def __init__(self):
        if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
            signal.signal(signal.SIGINT, self._sigHandler)
        signal.signal(signal.SIGTERM, self._sigHandler)
        
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, self._sigHandler)
    
    def _sigHandler(self, signum, frame):
        print "Received %d signal" % signum

        if(signum == signal.SIGINT or signum == signal.SIGTERM):
            print "toto"
            reactor.callLater(0, reactor.stop)
#            reactor.callFromThread(reactor.stop)
#            reactor.stop()
#            import sys
#            sys.exit(0)
            
        # Catch Ctrl-Break in windows
        elif(hasattr(signal, "SIGBREAK") and signum == signal.SIGBREAK):
            print "titi"
            reactor.callLater(0, reactor.stop)
#            reactor.callFromThread(reactor.stop)
#            reactor.stop()
#            import sys
#            sys.exit(0)
    
    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()

def main():
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', 8000, factory)
    reactor.run()

if __name__ == '__main__':
    main()
