from twisted.spread import pb
from twisted.internet import reactor
from twisted.python import util

import e

def _printError(f):
    print "f.type: ", f.type
    print "repr(f.value): ", repr(f.value)
    print "type(f.value)", type(f.value)
    print "dir(f.value)", dir(f.value)
    print "f.value.getMsg(): ", f.value.getMsg()

factory = pb.PBClientFactory()
reactor.connectTCP("localhost", 8789, factory)
d = factory.getRootObject()
d.addCallback(lambda object: object.callRemote("echo", "hello network"))
d.addCallback(lambda echo: 'server echoed: '+echo)
d.addErrback(_printError)
d.addCallback(util.println)
d.addCallback(lambda _: reactor.stop())
reactor.run()

