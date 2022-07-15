#!/usr/bin/python2.3
"""
A trivial test problem to illustrate the problems we're having
with _Dereference objects cropping up in the wrong places.
"""
from twisted.spread import pb
from twisted.internet import reactor

#++++++++++++++++++++++++++++++++++++++++++++++++++#
# Here are the data classes
#++++++++++++++++++++++++++++++++++++++++++++++++++#

class Alpha(pb.Cacheable):
    def __init__(self):
	self.b = []
	self.c = []
	self.observers = []

    def getStateToCacheAndObserveFor(self, perspective, observer):
	self.observers.append(observer)
	d = self.__dict__.copy()
	del d['observers']
	return d

    def stoppedObserving(self, perspective, observer):
	self.observers.remove(observer)

    def addBravo(self, name):
	bravo = Bravo(name)
	self.b.append(bravo)
	return bravo

    def addCharlie(self, bravo_one, bravo_two):
	charlie = Charlie(bravo_one, bravo_two)
	self.c.append(charlie)
	return charlie

class Bravo (pb.Cacheable):
    def __init__(self, name):
	self.name = name
#	self.connexions = {}
	self.connexions = []
	self.observers = []

    def connect(self,other,charlie):
#	self.connexions[other.name] = charlie
	self.connexions.append(charlie)

    def getStateToCacheAndObserveFor(self, perspective, observer):
	self.observers.append(observer)
	d = self.__dict__.copy()
	del d['observers']
	return d

    def stoppedObserving(self, perspective, observer):
	self.observers.remove(observer)

class Charlie (pb.Cacheable):
    def __init__(self, bravo_one, bravo_two):
	self.one = bravo_one
	self.two = bravo_two
	bravo_one.connect(bravo_two, self)
	bravo_two.connect(bravo_one, self)
	self.observers = []

    def getStateToCacheAndObserveFor(self, perspective, observer):
	self.observers.append(observer)
	d = self.__dict__.copy()
	del d['observers']
	return d

    def stoppedObserving(self, perspective, observer):
	self.observers.remove(observer)

# remote caches
class Cache(pb.RemoteCache):
    def setCopyableState(self, state):
	self.__dict__.update(state)

class RemoteAlpha (Cache):
    pass

class RemoteBravo (Cache):
    def __str__(self):
	return "Bravo(%s)" % (str(self.name))
    pass

class RemoteCharlie (Cache):
    def __str__(self):
	return "Charlie(%s,%s)" % (str(self.one), str(self.two))
    pass

cacheMap = (
    (Alpha, RemoteAlpha),
    (Bravo, RemoteBravo),
    (Charlie, RemoteCharlie),
)
for x in cacheMap: pb.setUnjellyableForClass(*x)

#++++++++++++++++++++++++++++++++++++++++++++++++++#
# Here are server classes
#++++++++++++++++++++++++++++++++++++++++++++++++++#

class AlphaMaker (pb.Root):
    def __init__(self):
	self.alpha = Alpha()
	bravos = [self.alpha.addBravo(x) for x in range(3)]
	charlies = [self.alpha.addCharlie(bravos[x], bravos[x+1]) for x in range(2)]

    def remote_getalpha(self):
	return self.alpha

class Server:
    def run(self):
	self.port = reactor.listenTCP(12001, pb.PBServerFactory(AlphaMaker()))
	print "server running..."
	reactor.run()

#++++++++++++++++++++++++++++++++++++++++++++++++++#
# Here are client classes
#++++++++++++++++++++++++++++++++++++++++++++++++++#

class Client:
    def __init__(self):
	self.makerRef = None
	self.alpha = None

    def run(self):
	factory = pb.PBClientFactory()
	reactor.connectTCP("localhost", 12001, factory)
	factory.getRootObject().addCallbacks(self.gotmaker, self.error)
	reactor.run()

    def error(self, obj):
	print "error:",str(obj)
	reactor.stop()

    def gotmaker(self, obj):
	print "got maker:",obj
	self.makerRef = obj
	self.makerRef.callRemote("getalpha").addCallbacks(self.gotalpha, self.error)
    
    def gotalpha(self, obj):
	print "got alpha:",obj
	self.alpha = obj
	print "--------------------------------------------------\nbravos:"
	for b in self.alpha.b:
	    print b, b.connexions
	print "--------------------------------------------------\ncharlies:"
	for c in self.alpha.c:
	    print c
	reactor.stop()

#++++++++++++++++++++++++++++++++++++++++++++++++++#
# Here is program flow
#++++++++++++++++++++++++++++++++++++++++++++++++++#

import sys

if len(sys.argv) < 2 or sys.argv[1] not in ('client','server'):
    print >>sys.stderr, "must specify either client or server on command line"
    sys.exit()

if sys.argv[1] == 'client':
    Client().run()
elif sys.argv[1] == 'server':
    Server().run()
