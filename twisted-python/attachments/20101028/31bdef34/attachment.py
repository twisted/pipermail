#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol

state = dict()

def forwardWithProducer(_from, to, streaming=True):
	#def debugPrint(data):
		#print _from.__class__.__name__, "-->", to.__class__.__name__, len(data), repr(data)
		#to.transport.write(data)
	#_from.dataReceived = debugPrint #to.transport.write
	_from.dataReceived = to.transport.write
	to.transport.registerProducer(_from.transport, streaming)

def forward(_from, to):
	#def debugPrint(data):
		#print _from.__class__.__name__, "-->", to.__class__.__name__, len(data), repr(data)
		#to.transport.write(data)
	#_from.dataReceived = debugPrint #to.transport.write
	_from.dataReceived = to.transport.write

def multiforward(_from, to, streaming=True):
	def multi(data):
		to.transport.write(data*100)
		reactor.callLater(1, to.transport.write, data*100)
	_from.dataReceived = multi
	to.transport.registerProducer(_from.transport, streaming)

def loseConnectionWithProducer(proto, onlost=lambda *args: None):
#def loseConnection(proto, onlost=None):
	#print "LOSING CONNECTION", proto
	#if onlost is None:
		#proto.connectionLost = proto.expectedConnectionLost
	#else:
	proto.connectionLost = onlost
	proto.transport.unregisterProducer()
	proto.transport.loseConnection()

def loseConnection(proto, onlost=lambda *args: None):
#def loseConnection(proto, onlost=None):
	#print "LOSING CONNECTION", proto
	#if onlost is None:
		#proto.connectionLost = proto.expectedConnectionLost
	#else:
	proto.connectionLost = onlost
	proto.transport.loseConnection()

def OneStart():
	forwardWithProducer(state["OneA"], state["OneB"])
	forwardWithProducer(state["OneD"], state["OneC"])
	forwardWithProducer(state["OneC"], state["OneD"])
	forwardWithProducer(state["OneE"], state["OneA"])

def TwoStart():
	multiforward(state["TwoB"], state["TwoD"])
	multiforward(state["TwoD"], state["TwoE"])

# one
class OneA(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		reactor.connectTCP("127.0.0.1", 8081, OneBFactory())
		reactor.connectTCP("127.0.0.1", 8084, OneCFactory())
class OneB(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if len(state) == 5:
			OneStart()
class OneC(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if len(state) == 5:
			OneStart()
	def connectionLost(self, reason):
		state["OneE"].connectionLost = lambda *args: loseConnectionWithProducer(state["OneA"])
		loseConnectionWithProducer(state["OneB"])
		loseConnectionWithProducer(state["OneD"])

class OneD(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if len(state) == 5:
			OneStart()
class OneE(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if len(state) == 5:
			OneStart()

# two
class TwoB(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		reactor.connectTCP("127.0.0.1", 8082, TwoDFactory())
		reactor.connectTCP("127.0.0.1", 8083, TwoEFactory())
		#reactor.callLater(5, os.kill, os.getpid(), 9)
		reactor.callLater(8, loseConnectionWithProducer, self)
		#reactor.callLater(5, reactor.crash)
	def connectionLost(self, reason):
		pass
class TwoD(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if "TwoE" in state:
			TwoStart()
	def connectionLost(self, reason):
		loseConnectionWithProducer(state["TwoE"])
class TwoE(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if "TwoD" in state:
			TwoStart()
	def connectionLost(self, reason):
		pass

# three
class ThreeC(Protocol):
	def connectionMade(self):
		#forwardWithProducer(self, self)
		multiforward(self, self)
		reactor.callLater(10, loseConnectionWithProducer, self)
		#reactor.callLater(10, reactor.crash)

# server factories
class OneAFactory(ServerFactory):
	protocol = OneA
class OneDFactory(ServerFactory):
	protocol = OneD
class OneEFactory(ServerFactory):
	protocol = OneE
class TwoBFactory(ServerFactory):
	protocol = TwoB
class ThreeCFactory(ServerFactory):
	protocol = ThreeC

# client factories
class OneBFactory(ClientFactory):
	protocol = OneB
class OneCFactory(ClientFactory):
	protocol = OneC
class TwoDFactory(ClientFactory):
	protocol = TwoD
class TwoEFactory(ClientFactory):
	protocol = TwoE

def main(what):
	if what == "one":
		reactor.listenTCP(8080, OneAFactory())
		reactor.listenTCP(8082, OneDFactory())
		reactor.listenTCP(8083, OneEFactory())
	elif what == "two":
		reactor.listenTCP(8081, TwoBFactory())
	elif what == "three":
		reactor.listenTCP(8084, ThreeCFactory())

if __name__ == "__main__":
	reactor.callWhenRunning(main, sys.argv[1])
	reactor.run()

