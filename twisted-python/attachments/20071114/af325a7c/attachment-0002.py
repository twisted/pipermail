import datetime
import os

from twisted.spread.pb import PBServerFactory, PBClientFactory, Broker
from twisted.spread.flavors import Root
from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol


def now():
    return datetime.datetime.now().isoformat()

class ExampleRoot(Root):
    def remote_testmethod(self, data):
        print "%s remote testmethod called" % now()
        return 2 * data

class MyBroker(Broker):
    def connectionReady(self):
        print "%s Connection ready on %s" % (now(), self.factory)
        Broker.connectionReady(self)

    def connectionLost(self, reason):
        print "%s client connection lost" % now()
        reactor.stop()

PBServerFactory.protocol = MyBroker
server = PBServerFactory(ExampleRoot())
port = reactor.listenTCP(10000, server)

clientProgram = """
import datetime
from twisted.spread.pb import PBServerFactory, PBClientFactory, Broker
from twisted.spread.flavors import Root
from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol

class MyBroker(Broker):
    def connectionReady(self):
        print "%s Connection ready on %s" % (now(), self.factory)
        Broker.connectionReady(self)

def now():
    return datetime.datetime.now().isoformat()

print "%s Starting Client!" % now()

def gotRootObject(rootobj):
    print "%s pb client got root object" % now()
    return rootobj.callRemote("testmethod", 4)

def gotMethodResult(result):
    print "%s pb client got method result" % now()
    assert result == 8
    reactor.stop()

PBClientFactory.protocol = MyBroker
client = PBClientFactory()
connector = reactor.connectTCP("127.0.0.1", 10000, client)
client.getRootObject().addCallback(gotRootObject).addCallback(gotMethodResult)
reactor.run()
"""

def startClientProcess():
    print "%s spawning client" % now()
    t = reactor.spawnProcess(ProcessProtocol(), "/usr/bin/python2.5",
            ["python2.5", "-c", clientProgram], childFDs = {0:0, 1:1, 2:2})


reactor.callLater(1, startClientProcess)
reactor.run()






