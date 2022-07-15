#! /usr/bin/env python

from twisted.internet import defer, protocol, reactor
from twisted.mail import imap4

class SimpleIMAP4Client(imap4.IMAP4Client):
    def serverGreeting(self, caps):
        self.factory.deferred.callback(self)

class SimpleIMAP4ClientFactory(protocol.ClientFactory):
    protocol = SimpleIMAP4Client

    def __init__(self):
        self.deferred = defer.Deferred()

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

    def clientConnectionLost(self, conn, reason):
        print "conn lost:", reason

@defer.deferredGenerator
def test():
    f = SimpleIMAP4ClientFactory()
    reactor.connectTCP("mail", 143, f)
    w = defer.waitForDeferred(f.deferred)
    yield w
    c = w.getResult()

    w = defer.waitForDeferred(c.login("myname", "XXX"))
    yield w
    w.getResult()

    w = defer.waitForDeferred(c.examine("INBOX.BigFolder"))
    yield w
    w.getResult()

    w = defer.waitForDeferred(c.search(imap4.Query(all=True)))
    yield w
    try:
        r = w.getResult()
        print "search ok", len(r)
    except:
        print "search failed", w.failure

    yield None

def quit(result):
    print "quit called"
    if result:
        print result
    reactor.stop()

d = test()
d.addBoth(quit)

reactor.run()
