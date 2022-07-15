#! /usr/bin/python

from twisted.internet.app import Application
from twisted.internet import reactor
from twisted.spread import pb
import cache_classes

class Receiver(pb.Root):
    def remote_takePond(self, pond):
        self.pond = pond
        print "got pond:", pond # a DuckPondCache
        print "-"*70
        print "%x" %id(self.pond)
        print self.pond.__dict__
        print "-"*70
        print "%x" %id(self.pond.duck)
        print self.pond.duck.__dict__
        print "-"*70
        
    def remote_shutdown(self):
        reactor.stop()


app = Application("copy_receiver")
app.listenTCP(8800, pb.BrokerFactory(Receiver()))
app.run(save=0)
