#!/usr/bin/env python
"""
Server.py: Provides a calculation service across the network"
Taken from Bruce Eckel's "Grokking Twisted"
http://www.artima.com/weblogs/viewpost.jsp?thread=156396
"""

from twisted.spread import pb
from twisted.internet import reactor
import time

PORT = 8000
COUNT = 1

class Calculator(pb.Root):
    def __init__(self, id):
        self.id = id
        print "Calculator", self.id, "running"
    def remote_calculate(self, a, b):
        print "Calculator", self.id, "calculating ..."
        time.sleep(61)
        return a + b, self.id


print "port:", PORT
reactor.listenTCP(PORT, pb.PBServerFactory(Calculator(0)))

reactor.run()
