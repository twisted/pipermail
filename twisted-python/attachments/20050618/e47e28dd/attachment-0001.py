from twisted.internet import reactor, protocol
from twisted.protocols import basic

class Test(basic.LineReceiver):
    registered = False
    def lineReceived(self, line):
        print 'got a line', repr(line)
        if not self.registered:
            self.registered = True
            self.transport.registerProducer(self, False)

class Client(protocol.Protocol):
    def connectionMade(self):
        self.transport.write('a\r\n')

f = protocol.ServerFactory()
f.protocol = Test
reactor.listenTCP(3456, f)

g = protocol.ClientFactory()
g.protocol = Client
reactor.connectTCP('127.0.0.1', 3456, g)
reactor.run()
