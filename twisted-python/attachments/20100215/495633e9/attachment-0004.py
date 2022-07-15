#!/usr/bin/python

from twisted.internet import ssl, reactor
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword

class DefinedError(pb.Error):
    pass

def success(message):
    print "Message received:",message
    reactor.stop()

def failure(error):
    t = error.trap(DefinedError)
    print "error received:", t
    reactor.stop()

def connected(perspective):
    perspective.callRemote('echo', "hello world").addCallbacks(success, failure)
    print "connected."

factory = pb.PBClientFactory()
reactor.connectSSL('localhost', 2323, factory, ssl.ClientContextFactory())
factory.login(UsernamePassword("raq", "diga33")).addCallbacks(connected, failure)
reactor.run()
