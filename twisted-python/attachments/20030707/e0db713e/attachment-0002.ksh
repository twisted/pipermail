#! /usr/bin/python

from twisted.spread import pb, jelly
from twisted.python import log
from twisted.internet import reactor
from cache_classes import MasterDuckPond

class Sender:
    def __init__(self, pond):
        self.pond = pond

    def phase1(self, remote):
        self.remote = remote
        d = remote.callRemote("takePond", self.pond)
        d.addCallback(self.phase2).addErrback(log.err)
    def phase2(self, dummy):
        d = self.remote.callRemote("shutdown")
        d.addCallback(self.phase3)
    def phase3(self, dummy):
        reactor.stop()

def main():
    master = MasterDuckPond()

    sender = Sender(master)
    deferred = pb.getObjectAt("localhost", 8800, 30)
    deferred.addCallback(sender.phase1)
    reactor.run()

if __name__ == '__main__':
    main()
