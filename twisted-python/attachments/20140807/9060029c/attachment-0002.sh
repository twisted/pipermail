#! /usr/bin/python
from twisted.spread import pb
from example import Library
from twisted.internet import reactor
def open_library(port=7999):
    print 'open_library:', port
    reactor.listenTCP(port, pb.PBServerFactory(Library()))    
reactor.callWhenRunning(open_library)
reactor.run() 

