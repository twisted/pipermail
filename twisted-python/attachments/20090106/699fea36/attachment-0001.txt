#! /usr/bin/python

import sys
from twisted.spread import pb
from twisted.internet import reactor, defer
from twisted.cred import credentials

class AuthError(pb.Error):
    pass

class Client(pb.Referenceable):

    @defer.inlineCallbacks
    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8000, factory)

        try:
            perspective = yield factory.login(credentials.UsernamePassword("user", "passX"), client=self)
            print "connected to server"
            self.appServer = yield perspective.callRemote("getAppServer")
            yield self.appServer.callRemote("echo", "Test message")
        except:
            print 'Login Failed:',
            print sys.exc_info()[0]

        reactor.stop()


Client().connect()
reactor.run()