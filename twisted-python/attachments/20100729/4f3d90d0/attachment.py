#!/usr/bin/python

from twisted.internet.stdio import StandardIO
from twisted.internet.interfaces import IHalfCloseableProtocol
from twisted.internet import protocol, reactor
from zope.interface import implements
import sys

class StdioProtocol(protocol.Protocol):
    implements(IHalfCloseableProtocol)

    def __init__(self):
        pass

    # IBaseProtocol
    def connectionMade(self):
        pass

    # IProtocol
    def dataReceived(self, data):
        sys.stderr.write("dataReceived: '%s'\n" %(data))

    def connectionLost(self, reason):
        # some error happened to stdio, like exception in my code
        from twisted.internet.error import ConnectionDone
        if isinstance(reason.value, ConnectionDone):
            sys.stderr.write("ConnectionDone (clean)\n")
        else:
            sys.stderr.write("StdioProtocol.connectionLost('%s')" % (reason))
        reactor.callLater(0, reactor.stop)

    # IHalfCloseableProtocol
    def writeConnectionLost(self, reason=SystemExit("output pipe is broken")):
        # no more writing is possible, pipe is broken, output is closed
        # This is the end.
        sys.stderr.write("writeConnectionLost(%s)" %(reason))
        self.transport.loseConnection()

    def readConnectionLost(self, reason=EOFError("input is done")):
        # EOF on stdin, congratulations, no more tasks will arrive!
        sys.stderr.write("\nreadConnectionLost(%s)\n\n" %(reason))

p = StdioProtocol()
t = StandardIO(p)

reactor.run()
sys.stderr.write("OK\n")
