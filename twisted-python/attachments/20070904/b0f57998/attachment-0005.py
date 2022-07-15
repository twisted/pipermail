from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.threads import deferToThread

from socket import gethostname
import time

class Foo(object):
    def slow_count(self, number, callback = None):
        for num in xrange(1, number + 1):
            time.sleep(0.1)
            print 'Counted to %s. (On the way to %s)' % (num, number)
            if callback and (num % 10 == 0) :
                callback(num, number)
                print "Called callback with %s, %s" % (num, number)
        return "Counted to %s on '%s'" % (number, gethostname())

class FooServerProxy(pb.Referenceable):
    def __init__(self, foo):
        self.foo = foo
    def remote_slow_count(self, number, callback = None):
        if callback:
            def cb(num, number):
                callback.callRemote('callback', num, number)
        else:
            cb = None
        d = deferToThread(self.foo.slow_count, number, callback=cb)
        return d

class FooServer(pb.Root):
    def remote_get_foo(self):
        f = Foo()
        return FooServerProxy(f)

if __name__ == '__main__':
    reactor.listenTCP(8000, pb.PBServerFactory(FooServer()))
    reactor.run()
