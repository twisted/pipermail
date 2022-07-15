import twisted.spread.pb as pb
import twisted.cred.portal as portal

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.cred import credentials
from zope.interface import implements

import descriptor

class Cacheable(pb.Cacheable):
    """I'm a cacheable object which notifies observers when data is added"""
    def __init__(self, data):
        self.data = data
        self.observers = {}
    
    def add(self, x):
        for p in self.observers:
            self.observers[p].callRemote("add", x)
    
    def getStateToCacheAndObserveFor(self, perspective, observer):
            self.observers[perspective] = observer
            return self.data


class RemoteCache(pb.RemoteCache):
    """I find out about data added to the Cacheable"""
    def __init__(self):
            print("RemoteCache %d.__init__"%(id(self),))
    
    def setCopyableState(self, state):
        print
        print("RemoteCache starting setCopyableState")
        for elem in state:
            self.add(elem)
        print("RemoteCache finished setCopyableState")
        print
    
    def observe_add(self, obj):
        self.add(obj)
    
    @descriptor.TestDescriptor
    def add(self, obj):
        print("RemoteCache %d added %s"%(id(self), obj))


pb.setUnjellyableForClass(Cacheable, RemoteCache)


class Server(object):
    implements(portal.IRealm)
        
    def __init__(self):
        self.thing = Cacheable(['a', 'hello'])
        self.users = set()
    
    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        p = Perspective(avatarID, mind, self)
        self.users.add(p)
        return pb.IPerspective, p, lambda a=p:a.detached()
    
    def start(self):
        for p in self.users:
            p.mind.callRemote("take", self.thing)
    
    def update(self):
        self.thing.add("foobar")


class Perspective(pb.Avatar):
    def __init__(self, name, mind, server):
        self.name = name
        self.mind = mind
        self.server = server
    
    def detached(self):
        self.mind = None
    
    def perspective_start(self):
        self.server.start()
    
    def perspective_update(self):
        self.server.update()


class Client(pb.Referenceable):
    
    def __init__(self, reactor):
            self.reactor = reactor
            print("Client %d"%(id(self),))
    
    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8800, factory)
        def1 = factory.login(credentials.UsernamePassword("alice", "1234"),
                             client=self)
        def1.addCallback(self.connected)
    
    def connected(self, perspective):
        print("CONNECTED")
        self.perspective = perspective
        self.reactor.callLater(1.0, self.start)
    
    def start(self):
        self.perspective.callRemote("start")
    
    def update(self):
        print("Asking server to update")
        self.perspective.callRemote("update")
        self.reactor.callLater(1, self.showId)
    
    def remote_take(self, d):
        self.d = d
        print
        print("Client received RemoteCache: id=%d"%(id(d),))
        print
        self.reactor.callLater(2.0, self.update)
    
    def showId(self):
        print("RemoteCache id=%d"%id(self.d))