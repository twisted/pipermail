"""
A module to demonstrate some of the simplest twisted client code possible
@author: Richard Wall <richard (at) the-moon.net>
"""
import sys

from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from twisted.internet.task import Cooperator
from twisted.internet.protocol import ClientCreator, Protocol
from twisted.internet.error import ConnectionRefusedError, TimeoutError

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_TIMEOUT = "timeout"

MAX_SIMULTANEOUS_CONNECTIONS = 100

def getPortStatus(host, port, timeout=1):
    """
    Return a deferred that is called back with one of: open, closed, timeout
    @param host: The hostname or IP with which to attempt a connection
    @param port: The port to connect
    @param timeout: Number of seconds to wait for connection before giving up
    @return: A deferred which will call back with one of 
             STATUS_{OPEN,CLOSED,TIMEOUT}
    """

    cli = ClientCreator(reactor, Protocol)

    d = cli.connectTCP(host, port, timeout=timeout)

    def cb(proto):
        proto.transport.loseConnection()
        return STATUS_OPEN

    def eb(err):
        expectedErrors = {
            ConnectionRefusedError: STATUS_CLOSED,
            TimeoutError: STATUS_TIMEOUT
        }

        e = err.trap(*expectedErrors.keys())
        if e:
            return expectedErrors[e]

    d.addCallbacks(cb, eb)

    return d

def main(argv): 
    """
    Command line access to the getPortStatus function. Pass me a hostname and
    one or more ports and I will report their status.
    """ 
    host = argv[1]
    ports = map(int, argv[2:])
    
    def cb(status, host, port):
         sys.stdout.write("%s:%d %s\n"%(host,port,status))

    def eb(err):
        sys.stderr.write("%s\n" % err.value)

    def portStatusGenerator(host, ports):
        for p in ports:
            d = getPortStatus(host, p)
            d.addCallbacks(cb, eb, (host, p))
            yield d

    # Limit parallelism otherwise we run out of file descriptors
    # See http://jcalderone.livejournal.com/24285.html
    work = portStatusGenerator(host, ports)
    coop = Cooperator()
    d = DeferredList(
            [coop.coiterate(work) for i in xrange(MAX_SIMULTANEOUS_CONNECTIONS)])

    d.addCallback(lambda ign: reactor.stop())
    reactor.run()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

