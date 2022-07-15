#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.spread import pb
from tx_fake_connector import FDSocketFakeConnector, FDUNIXStreamSocket
import socket
import os
import sys

sock0, sock1 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
pid = os.fork()
if pid: # parent
    # run a server side of PB protocol
    # when done() method is invoked - close connection after assuring all previous messages have
    # been delivered.
    del sock1
    # this is just a senseless Root object, only to test PB is working.
    class test(pb.Root):
        def remote_test(self, arg):
            print "p:test: %s" % (arg)
            return 1
        
        def remote_done(self, arg):
            print "p:done()"
            def invoked(_=None):
                reactor.callLater(0, c.transport.loseConnection)
                reactor.callLater(0, reactor.stop)
            arg.callRemote("").addBoth(invoked)
            return "done() returns nothing"

    # you create/receive your server factory as usual
    factory = pb.PBServerFactory(test())
    # note the patching that is required to server PB factory to work with a Connector, that is ugly.
    factory.startedConnecting = lambda x=None: None
    factory.clientConnectionFailed = lambda x=None, y=None: y
    factory.clientConnectionLost = lambda x=None, y=None: None
    # actually, you may prefer subclassing, but that is still ugly.
    
    c = FDSocketFakeConnector(sock0, factory, reactor, FDUNIXStreamSocket)
    c.connect()
    # that's it
    
    sys.stdout.write("p: connected...\n")
    
else:  # child
    # run client PB instance, inform server when we are done, wait for an acknowledge of that.
    del sock0
    root = None

    # use it like that
    f = pb.PBClientFactory()
    c = FDSocketFakeConnector(sock1, f, reactor, FDUNIXStreamSocket)
    d = c.connect()
    # other code is as usual, just another example of a PB client...

    sys.stdout.write("c: connected..., d= %r, c = %r\n" % (d,c))
    d = f.getRootObject()
    def _gotRoot(obj):
        global root
        root = obj
        sys.stderr.write("[%d]: root = %r\n" %(os.getpid(), root))
        return obj
    def _noRoot(f):
        sys.stderr.write("[%d]: failed to get root: %s\n" %(os.getpid(), f))
        reactor.stop()
        return f
    class noop(pb.Referenceable):
        # do nothing, just to be able to receive a message and then return a None value.
        def remote_(self, _=None):
            return None
    d.addCallbacks(_gotRoot, _noRoot)
    d.addCallback(lambda obj: obj.callRemote("test", "argument"))
    d.addCallbacks(lambda ret: "returned: "+str(ret), lambda f: 'failure:' + str(f))
    d.addCallback(lambda msg="NOMSGPROVIDED": sys.stdout.write("c:Answer1: %s\n" % (msg)) or root and root.callRemote("done", noop()))
    d.addBoth(lambda val="NONE": sys.stdout.write("c:Answer2: %s\n" %(val)) or reactor.callLater(0, reactor.stop))

reactor.run()
