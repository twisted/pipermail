#! /usr/bin/python

from twisted.spread import pb
from twisted.internet import reactor, defer
from twisted.cred import credentials
from twisted.python.failure import Failure

class AuthError(pb.Error):
    pass

class Client(pb.Referenceable):

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8000, factory)

        d = factory.login(credentials.UsernamePassword("user", "passX"), client=self)
        d.addCallbacks(self.cb_connected, self.eb_failed)

    def cb_connected(self, perspective):
        print "connected to server"
        return perspective.callRemote("getAppServer").addCallback(self.cb_gotAppServer)

    def eb_failed(self, failure):
        print 'Login failed:', failure.type

    def cb_gotAppServer(self, appServer):

        self.appServer = appServer
        return self.appServer.callRemote("echo", "Test message").addCallback(self.cb_stopReactor)

    def cb_stopReactor(self, ignore):
        reactor.stop()


Client().connect()
reactor.run()
