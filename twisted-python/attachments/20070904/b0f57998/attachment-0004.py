from twisted.internet import reactor, defer
from twisted.python import threadable
from twisted.spread import pb

import threading
import signal

def wait_factory():
    "Returns a callback to apply to a deffered, and event to wait on"
    evt = threading.Event()
    def set_event(result):
        evt.set()
        return result
    return set_event, evt

class RemoteCallback(pb.Referenceable):
    def __init__(self, callback):
        self.callback = callback
    def remote_callback(self, *args, **kwargs):
        self.callback(*args, **kwargs)

class FooClientProxy(object):
    def __init__(self, remotefoo):
        self.remotefoo = remotefoo
    def slow_count(self, number, callback = None):
        if callback:
            cb = RemoteCallback(callback)
        else:
            cb = None
        f, e = wait_factory()
        d = self.remotefoo.callRemote('slow_count', number, cb)
        d.addCallback(f)
        e.wait()
        return d.result

class FooFactory(object):
    def __init__(self, host = None, port = None):
        self.host = host
        self.port = port
        self.root = None
        self._got_root_evt = None
    def _got_root(self, root):
        self.root = root
        self._got_root_evt.set()
    def _connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host, self.port, factory)
        d = factory.getRootObject()
        d.addCallback(self._got_root)
        reactor.run(installSignalHandlers=0)
    def connect(self, host, port):
        if host:
            self.host = host
        if port:
            self.port = port
        self._got_root_evt = threading.Event()
        self.conn_thread = threading.Thread(target=self._connect)
        self.conn_thread.start()
        self._got_root_evt.wait()
    def close(self):
        reactor.stop()
    def get_foo(self):
        f, e = wait_factory()
        d = self.root.callRemote('get_foo')
        d.addCallback(f)
        e.wait()
        return FooClientProxy(d.result)

def progress(num, number):
    print "Up to %s of %s" % (num, number)

def main():
    ff = FooFactory()
    ff.connect('localhost', 8000)
    foo = ff.get_foo()

    result = foo.slow_count(50, callback=progress)
    print result

    ff.close()

if __name__ == '__main__':
    main()
