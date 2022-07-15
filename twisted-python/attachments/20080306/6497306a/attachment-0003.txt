from twisted.internet import reactor, protocol, defer, threads
from twisted.protocols import basic
import socket
import time


# connection
class ConnectionProtocol(basic.LineReceiver):
    def __init__(self):
        self.deferred = defer.Deferred()

    def connectionMade(self):
        basic.LineReceiver.connectionMade(self)
        
        #reactor.listenTCP(6019 + 1,BasicClientFactory())
        print "connected to : %s" % self.transport.getPeer().host
        print "sending ip address"
        #self.setLineMode()
        self.sendLine(socket.getfqdn().ipaddrs)
        self.deferred = threads.deferToThread(self.ThreadKirim)
        self.deferred.addCallback(self.lineReceived)
        
        #reactor.callFromThread(self.ThreadKirim,1)

    def lineReceived(self,line):
        print line

    def ThreadKirim(self):
        while self.connected == 1:  # infinite loop nya gak berhenti kemungkinan besar disini
            data = raw_input("data to send :")
            self.sendLine(data)
        else :
            break

        
class BasicClientFactory(protocol.ClientFactory):

    protocol = ConnectionProtocol

    def __init__(self):
        self.deferred = defer.Deferred()

    def clientConnectionLost(self, connector, reason):
        print "Lost connection: %s" % reason.getErrorMessage( )
        self.protocol.connected = 0
        reactor.stop( )


    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason.getErrorMessage( )
        reactor.stop( )
# end connection block




host = raw_input("host: ")
port = int(raw_input("port: "))
reactor.connectTCP(host, port, BasicClientFactory())

reactor.run()