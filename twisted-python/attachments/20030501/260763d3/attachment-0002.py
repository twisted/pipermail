#!/usr/bin/python
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

from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet.app import Application
from twisted.internet import reactor, tcp, ssl
import sys

class myContext(ssl.ClientContextFactory):
    isClient = 1
    def getContext(self):
        return ssl.SSL.Context(ssl.SSL.TLSv1_METHOD)

x = myContext()

class EchoClient(Protocol):
    end="Bye-bye!"
    def connectionMade(self):
        self.transport.write("I am sending this in the clear\n")
        self.transport.write("And why should I not?\n")
        self.transport.write("STARTTLS;\n")

    def dataReceived(self, data):
     	for i in data.split("\n"):
            try:
                command, other = i.split(";", 1)
            except:
                command = ""
                other = i
            if command==self.end:
                self.transport.loseConnection()
            elif command=="READY":
                self.transport.startTLS(x)
                self.transport.write("Spooks cannot see me now.\n")
            else:
                print i

class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

factory = EchoClientFactory()
reactor.connectTCP('localhost', 8000, factory)
reactor.run()
