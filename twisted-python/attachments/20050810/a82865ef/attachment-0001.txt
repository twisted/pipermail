"""Standard input/out/err support for Windows!

10/8/05
"""

# system imports
import msvcrt
from zope.interface import implements

# Twisted imports
from twisted.python import failure

# Sibling Imports
from twisted.internet import reactor, task, interfaces

_stdio_in_use = 0


class StandardIOTransport:
    implements(interfaces.ITransport)

    closed = 0
    disconnecting = 0
    producer = None
    streamingProducer = 0

    def write(self, data):
        try:
            for x in data:
                msvcrt.putch(x)
        except:
            self.handleException()
        # self._checkProducer()

    def _checkProducer(self):
        # Cheating; this is called at "idle" times to allow producers to be
        # found and dealt with
        if self.producer:
            self.producer.resumeProducing()

    def registerProducer(self, producer, streaming):
        """From abstract.FileDescriptor
        """
        self.producer = producer
        self.streamingProducer = streaming
        if not streaming:
            producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def stopConsuming(self):
        self.unregisterProducer()
        self.loseConnection()

    def writeSequence(self, iovec):
        self.write("".join(iovec))

    def loseConnection(self):
        self.closed = 1

    def getPeer(self):
        return 'file', 'file'

    def getHost(self):
        return 'file'

    def handleException(self):
        pass

    def resumeProducing(self):
        # Never sends data anyways
        pass

    def pauseProducing(self):
        # Never sends data anyways
        pass
    
    def stopProducing(self):
        self.loseConnection()


class StandardIO(StandardIOTransport):
    """I can connect Standard IO to a twisted.protocol
    I act as a selectable for sys.stdin, and provide a write method that writes
    to stdout.
    """
    
    def __init__(self, _protocol):
        """Create me with a protocol.

        This will fail if a StandardIO has already been instantiated.
        """

        global _stdio_in_use
        if _stdio_in_use:
            raise RuntimeError, "Standard IO already in use."
        _stdio_in_use = 1

        self.protocol = _protocol
        self.protocol.makeConnection(self)

        self.reader = task.LoopingCall(self._tryToRead)
        self.reader.start(0.05)

    def _tryToRead(self):
        if msvcrt.kbhit():
            c = msvcrt.getch()
            if c == '\x1a': # ^Z
                self.protocol.connectionLost(failure.Failure(EOFError()))
            else:
                if c == '\r':
                    c = '\r\n'
                [msvcrt.putch(x) for x in list(c)]    # echo
                self.protocol.dataReceived(c)

    def loseConnection(self):
        self.closed = 1
        self.reader.stop()
