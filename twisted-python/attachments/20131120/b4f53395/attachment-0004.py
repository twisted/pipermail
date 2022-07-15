#!/usr/bin/env python

from twisted.spread import pb
from twisted.internet import reactor
from twisted.cred import credentials

class Client(pb.Referenceable):

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8800, factory)
        def1 = factory.login(credentials.UsernamePassword("alice", "1234"),
                             client=self)
        def1.addCallback(self.connected)
        reactor.run()

    def connected(self, perspective):
        self.perspective = perspective
        d = perspective.callRemote("getViewable")
        d.addCallback(self.gotViewable)
    
    def gotViewable(self, v):
        v.callRemote("test", "RETURNED FROM")
    
    def remote_takeViewable(self, v):
        v.callRemote("test", "SENT BY")

Client().connect()