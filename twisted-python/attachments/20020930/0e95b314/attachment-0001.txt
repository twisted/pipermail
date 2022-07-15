#!/usr/bin/env python

""" Example showing how to use Policies to control connections for a
    ServerFactory.
"""


from twisted.internet import reactor
from twisted.internet.interfaces import IFactoryPolicy
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic  import LineReceiver


class OneConnectionPolicy:

    """ Create a policy that only allows one connection at a time """

    __implements__ = (IFactoryPolicy,)
    numConns = 0

    def verify(self, addr):
        if self.numConns >= 1: return 0
        else:
            self.numConns += 1
            return 1

class MyProto(LineReceiver):
    """ Protocol to test the policy """

    def __init__(self): pass

    def connectionMade(self):
        LineReceiver.connectionMade(self)
        print "A connection got through!"

    def lineReceived(self, line): print line

    def connectionLost(self, reason):
        for policy in self.factory.policies:
            policy.numConns -= 1

if __name__ == '__main__':
    ServerFactory.protocol = MyProto
    fac = ServerFactory()
    fac.addPolicy(OneConnectionPolicy()) # add the policy
    reactor.listenTCP(8080, fac)
    reactor.run()
