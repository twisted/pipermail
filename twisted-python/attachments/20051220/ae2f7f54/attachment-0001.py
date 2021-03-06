
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet import reactor, ssl
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword

from pbecho_ssl import DefinedError

def success(message):
    print "Message received:",message
    # reactor.stop()

def failure(error):
    t = error.trap(DefinedError)
    print "error received:", t
    reactor.stop()

def connected(perspective):
    perspective.callRemote('echo', "hello world").addCallbacks(success, failure)
    perspective.callRemote('error').addCallbacks(success, failure)
    print "connected."

factory = pb.PBClientFactory()
reactor.connectSSL("localhost", pb.portno, factory, ssl.ClientContextFactory())
factory.login(
    UsernamePassword("guest", "guest")
).addCallbacks(
    connected, failure
)

reactor.run()
