
# Twisted, the Framework of Your Internet
# Copyright (C) 2001 Matthew W. Lefkowitz
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import udp, ssl

### Protocol Implementation

# This is just about the simplest possible protocol

x = ssl.DefaultOpenSSLContextFactory(privateKeyFileName="server.pem",
                                 certificateFileName="server.pem",
                                 sslmethod=ssl.SSL.TLSv1_METHOD)


class Echo(Protocol):
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print data
        try:
            command, other = data.split(";", 1)
        except:
            command = data
            other = ""
        if command == "STARTTLS":
            print "starting TLS"
            self.transport.write("READY;ajshdakjsd\n")
            self.transport.startTLS(x)
        else:
            self.transport.write(data)


### Persistent Application Builder

# This builds a .tap file
class EchoClientFactory(Factory):
    protocol = Echo
    def connectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()

    def connectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()


if __name__ == '__main__':
    # Since this is persistent, it's important to get the module naming right
    # (If we just used Echo, then it would be __main__.Echo when it attempted
    # to unpickle)
    import echoserv_tls
    from twisted.internet.app import Application
    factory = echoserv_tls.EchoClientFactory()
    factory.protocol = echoserv_tls.Echo
    app = Application("echo-tls")
    app.listenTCP(8000,factory)
    app.run(save=0)
