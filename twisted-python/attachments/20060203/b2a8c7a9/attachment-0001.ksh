from twisted.internet import reactor, protocol
from avsNbtClientProtocol import *
from avsMessageHandling import *
import datetime

def getYYYYMMDDToday():
    return str(datetime.date.today())

if __name__ == '__main__':
    import sys
    if not len(sys.argv) == 6:
       print "Usage: %s host port remoteName myName maxLoop" % sys.argv[0]
       sys.exit(1)

    f = NBTFactory()
    host = sys.argv[1]
    port = int(sys.argv[2])
    f.remoteName = sys.argv[3]
    f.myName = sys.argv[4]
    f.maxLoop = int(sys.argv[5])
    f.messageHandler = HelloThereMessageHandler()
    f.instanceName = 'conn1'
    reactor.connectTCP(host, port, f)

    g = NBTFactory()
    g.remoteName = sys.argv[3]
    g.myName = 'W04BS03'
    g.maxLoop = int(sys.argv[5])
    g.messageHandler = HelloThereMessageHandler()
    g.instanceName = 'conn2'
    reactor.connectTCP(host, port, g)

    reactor.run()
