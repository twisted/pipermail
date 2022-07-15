#!/usr/bin/env python

import sys
from getpass import getpass
from twisted.python import log
from twisted.conch.ssh import connection, transport, userauth, keys, \
        forwarding, channel
from twisted.conch.ssh.common import NS
from twisted.internet import defer, protocol, reactor
from twisted.web import server, xmlrpc
from twisted.web.xmlrpc import Proxy


conn = None


def connect(user, host, port=22):
    return reactor.connectTCP(host, port, Factory(user, Transport))


class Factory(protocol.ClientFactory):
    def __init__(self, user, protocol):
        self.user = user
        self.protocol = protocol

    def buildProtocol(self, addr):
        p = self.protocol(self.user)
        p.factory = self
        return p


class Transport(transport.SSHClientTransport):
    def __init__(self, user):
        self.user = user

    def verifyHostKey(self, pubkey, fingerprint):
        return defer.succeed(1)

    def connectionSecure(self):
        self.requestService(UserAuth(self.user, Connection()))


class UserAuth(userauth.SSHUserAuthClient):
    def getPassword(self, prompt=None):
        return defer.succeed(getpass("password: "))


class Connection(connection.SSHConnection):
    def __init__(self, *args, **kwargs):
        connection.SSHConnection.__init__(self, *args, **kwargs)
        self.forwarding_sockets = []

    def serviceStarted(self):
        # Create a tunnel from 12345 to 54321
        self.forward_port(12345, 54321)
        # Do something through the tunnel
        p = Proxy('http://localhost:12345/')    # passing through the tunnel,
                                                # triggers the KeyError
        #p = Proxy('http://localhost:54321/')   # not using the tunnel, works
        print "ping...",
        d = p.callRemote("ping")
        def stop_ok(response):
            print response
            conn.disconnect()
            reactor.stop()
        def stop_error(error):
            print "error", error
            conn.disconnect()
            reactor.stop()
        d.addCallback(stop_ok)
        d.addErrback(stop_error)

    def serviceStopped(self):
        # Stop forwarding sockets
        for socket in self.forwarding_sockets:
            socket.stopListening()

    def forward_port(self, local_port, remote_port):
        print "forwarding %d => %d" % (local_port, remote_port)
        socket = reactor.listenTCP(local_port, 
                forwarding.SSHListenForwardingFactory(self, 
                    ("localhost", remote_port), 
                    forwarding.SSHListenClientForwardingChannel))
        self.forwarding_sockets.append(socket)


class DummyServer(xmlrpc.XMLRPC):
    def xmlrpc_ping(self):
        return "pong"


if __name__ == "__main__":    
    if len(sys.argv) != 2:
        print "usage: test.py user"
        sys.exit(1)
    #log.startLogging(sys.stdout)    

    # If the server is not running, stop_error() errback is triggered and we 
    # have the KeyError when passing through the tunnel
    #reactor.listenTCP(54321, server.Site(DummyServer()))

    conn = connect(sys.argv[1], "localhost")
    reactor.run()
