
"""
Demonstrate transport-level zlib compression.

Save in zip.py.  Run "python zip.py server" and then "python zip.py client".
"""

import zlib, sys

from zope.interface import implements

from twisted.python import log
log.startLogging(sys.stdout)

from twisted.protocols import policies
from twisted.spread import pb
from twisted.internet import reactor

class ZipWrapper(policies.ProtocolWrapper):
    def connectionMade(self):
        self.compressor = zlib.compressobj()
        self.decompressor = zlib.decompressobj()
        policies.ProtocolWrapper.connectionMade(self)

    def dataReceived(self, bytes):
        bytes = self.decompressor.decompress(bytes)
        return policies.ProtocolWrapper.dataReceived(
            self, bytes)

    def write(self, bytes):
        bytes = (self.compressor.compress(bytes) +
                 self.compressor.flush(zlib.Z_SYNC_FLUSH))
        return policies.ProtocolWrapper.write(
            self, bytes)

    def writeSequence(self, vec):
        return self.write(''.join(vec))


def runClient(host, port):
    clientFactory = pb.PBClientFactory()
    d = clientFactory.getRootObject()
    def gotRootObj(obj):
        d2 = obj.callRemote('echo', 'hello, world')
        def echoed(result):
            print result
            reactor.stop()
        d2.addCallback(echoed)
    d.addCallback(gotRootObj)
    f = policies.WrappingFactory(clientFactory)
    f.protocol = ZipWrapper
    reactor.connectTCP(host, port, f)
    reactor.run()

class DummyRoot(pb.Root):
    implements(pb.IPBRoot)

    def rootObject(self, proto):
        return self

    def remote_echo(self, arg):
        return arg

def runServer(host, port):
    serverFactory = pb.PBServerFactory(DummyRoot())
    f = policies.WrappingFactory(serverFactory)
    f.protocol = ZipWrapper
    reactor.listenTCP(port, f, interface=host)
    reactor.run()

if __name__ == '__main__':
    if sys.argv[1] == 'client':
        runClient('localhost', 12345)
    else:
        runServer('localhost', 12345)
