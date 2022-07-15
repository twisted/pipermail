#! /usr/bin/python

from twisted.spread import pb

class MasterDuck(pb.Cacheable):
    def __init__(self, pond):
        self.pond = pond

    def getStateToCacheAndObserveFor(self, perspective, observer):
        return {"pond" : self.pond}


class SlaveDuck(pb.RemoteCache):
    def setCopyableState(self, state):
        self.__dict__.update(state)

                
class MasterDuckPond(pb.Cacheable):
    def __init__(self):
        self.duck = MasterDuck(self)
        
    def getStateToCacheAndObserveFor(self, perspective, observer):
        return {"duck" : self.duck}


class SlaveDuckPond(pb.RemoteCache):
    def setCopyableState(self, state):
        self.__dict__.update(state)


pb.setUnjellyableForClass(MasterDuckPond, SlaveDuckPond)
pb.setUnjellyableForClass(MasterDuck, SlaveDuck)
