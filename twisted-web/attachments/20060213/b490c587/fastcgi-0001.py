"""
   Twisted.web2 FastCGI backend support.
"""

"""
Okay, FastCGI is a pretty stupid protocol.
Let me count some reasons:

1) Specifies ability to multiplex streams of data over a single
socket, but has no form of flow control. This is fine for multiplexing
stderr, but serving more than one request over a channel with no flow
control is just *asking* for trouble. I avoid this and enforce one
outstanding request per connection. This basically means the whole
"requestId" field is worthless.

2) Has variable length packet padding. If you want padding, just make
it always pad to 8 bytes fercrissake!

3) Why does every packet need to specify the version. How about just
sending it once.

4) Name/value pair format. Come *on*. Is it *possible* to come up with
a more complex format to send them with?? Even if you think you've
gotten it down, you probably forgot that it's a stream, and the
name/values can be split between two packets. (Yes, this means
*you*. Don't even try to pretend you didn't miss this detail.)
"""

from twisted.internet import protocol, tcp, unix
from twisted.python import log
from twisted.web2 import responsecode
from twisted.web2.channel import cgi

# Values for type component of FCGI_Header

FCGI_BEGIN_REQUEST       = 1
FCGI_ABORT_REQUEST       = 2
FCGI_END_REQUEST         = 3
FCGI_PARAMS              = 4
FCGI_STDIN               = 5
FCGI_STDOUT              = 6
FCGI_STDERR              = 7
FCGI_DATA                = 8
FCGI_GET_VALUES          = 9
FCGI_GET_VALUES_RESULT   = 10
FCGI_UNKNOWN_TYPE        = 11

typeNames = {
    FCGI_BEGIN_REQUEST    : 'fcgi_begin_request',
    FCGI_ABORT_REQUEST    : 'fcgi_abort_request',
    FCGI_END_REQUEST      : 'fcgi_end_request',
    FCGI_PARAMS           : 'fcgi_params',
    FCGI_STDIN            : 'fcgi_stdin',
    FCGI_STDOUT           : 'fcgi_stdout',
    FCGI_STDERR           : 'fcgi_stderr',
    FCGI_DATA             : 'fcgi_data',
    FCGI_GET_VALUES       : 'fcgi_get_values',
    FCGI_GET_VALUES_RESULT: 'fcgi_get_values_result',
    FCGI_UNKNOWN_TYPE     : 'fcgi_unknown_type'}

# Mask for flags component of FCGI_BeginRequestBody
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BeginRequestBody
FCGI_RESPONDER  = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER     = 3

# Values for protocolStatus component of FCGI_EndRequestBody

FCGI_REQUEST_COMPLETE = 0
FCGI_CANT_MPX_CONN    = 1
FCGI_OVERLOADED       = 2
FCGI_UNKNOWN_ROLE     = 3

FCGI_LISTENSOCK_FILENO = 0

FCGI_MAX_PACKET_LEN = 0xFFFF

class Record(object):
    def __init__(self, type, reqId, content, version=1):
        self.version = version
        self.type = type
        self.reqId = reqId
        self.content = content
        self.contentLength = len(content)
        if self.contentLength > FCGI_MAX_PACKET_LEN:
            raise ValueError("Record length too long: %d > %d" %
                             (self.contentLength, FCGI_MAX_PACKET_LEN))
        self.paddingLength = 8 - (self.contentLength & 7)
        self.totalLength = 8 + self.contentLength + self.paddingLength
        self.reserved = 0

    def fromHeaderString(clz, rec):
        self = object.__new__(clz)
        self.version = ord(rec[0])
        self.type = ord(rec[1])
        self.reqId = (ord(rec[2])<<8)|ord(rec[3])
        self.contentLength = (ord(rec[4])<<8)|ord(rec[5])
        self.paddingLength = ord(rec[6])
        self.reserved = ord(rec[7])
        self.content = None
        self.totalLength = 8 + self.contentLength + self.paddingLength
        return self
    
    fromHeaderString = classmethod(fromHeaderString)

    def toOutputString(self):
        return ("%c%c%c%c%c%c%c%c" % (self.version, self.type,
                                      (self.reqId&0xFF00)>>8, self.reqId&0xFF,
                                      (self.contentLength&0xFF00)>>8,
                                      self.contentLength & 0xFF,
                                      self.paddingLength, self.reserved)
               + self.content + '\0'*self.paddingLength)
        
    def __repr__(self):
        return "<FastCGIRecord version=%d type=%d(%s) reqId=%d content=%r>" % (
            self.version, self.type, typeNames.get(self.type), self.reqId, self.content)
    
def parseNameValues(s):
    off = 0
    while off < len(s):
        nameLen = ord(s[off])
        off += 1
        if nameLen&0x80:
            nameLen=(nameLen&0x7F)<<24 | ord(s[off])<<16 | ord(s[off+1])<<8 | ord(s[off+2])
            off += 3
        valueLen=ord(s[off])
        off += 1
        if valueLen&0x80:
            valueLen=(nameLen&0x7F)<<24 | ord(s[off])<<16 | ord(s[off+1])<<8 | ord(s[off+2])
            off += 3
        yield (s[off:off+nameLen], s[off+nameLen:off+nameLen+valueLen])
        off += nameLen + valueLen

def getLenBytes(length):
    if length<0x80:
        return chr(length)
    elif 0 < length <= 0x7FFFFFFF:
        return (chr(0x80|(length>>24)&0x7F) + chr((length>>16)&0xFF) + 
                chr((length>>8)&0xFF) + chr(length&0xFF))
    else:
        raise ValueError("Name length too long.")

def writeNameValue(name, value):
    return getLenBytes(len(name)) + getLenBytes(len(value)) + name + value

class FastCGIChannelRequest(cgi.BaseCGIChannelRequest):

    def __init__(self, requestFactory, reqId, keepalive):
        self.requestFactory = requestFactory
        self.reqId = reqId
        self.keepalive = keepalive
        self.params = ""

    def writeHeaders(self, code, headers):
        l = []
        code_message = responsecode.RESPONSES.get(code, "Unknown Status")
        l.append("Status: %s %s\n" % (code, code_message))
        if headers is not None:
            for name, valuelist in headers.getAllRawHeaders():
                for value in valuelist:
                    l.append("%s: %s\n" % (name, value))
        l.append('\n')
        self.transport.write(''.join(l))

class FastCGIRequestTransport:

    def __init__(self, protocol, reqId):
        self.protocol = protocol
        self.reqId = reqId

    def write(self, data):
        self.protocol.writeRequest(self.reqId, data)

    def loseConnection(self):
        self.protocol.finishRequest(self.reqId, FCGI_REQUEST_COMPLETE)

    def registerProducer(self, producer, streaming):
        producer.resumeProducing()
    
    def unregisterProducer(self):
        pass

class FastCGIProtocol(protocol.Protocol):

    maxConnections = 100
    maxRequests = 100

    chanRequestFactory = FastCGIChannelRequest
    transportFactory = FastCGIRequestTransport

    producerPaused = False
    pendingRecord = None
    dataBuffer = ""

    multiplexed = False

    def __init__(self):
        self._chanRequests = {}

    # Packet handling

    def packetReceived(self, packet):
        #print "Got packet", packet
        if packet.version != 1:
            protocolError("FastCGI packet received with version != 1")
        
        func = getattr(self, typeNames.get(packet.type), None)
        if func is None:
            self.writePacket(Record(FCGI_UNKNOWN_TYPE, packet.reqId,
                                    chr(packet.type)+"\0\0\0\0\0\0\0"))
        else:
            func(packet)

    def fcgi_get_values(self, packet):
        if packet.reqId != 0:
            raise ValueError("Packet reqId should be 0!")
        
        content = ""
        for name,value in parseNameValues(packet.content):
            outval = None
            if name == "FCGI_MAX_CONNS":
                outval = str(self.maxConnections)
            elif name == "FCGI_MAX_REQS":
                outval = str(self.maxRequests)
            elif name == "FCGI_MPXS_CONNS":
                outval = self.multiplex and "1" or "0"
            if outval:
                content += writeNameValue(name, outval)
        self.writePacket(Record(FCGI_GET_VALUES_RESULT, 0, content))

    def fcgi_begin_request(self, packet):
        role = ord(packet.content[0])<<8 | ord(packet.content[1])
        flags = ord(packet.content[2])
        if packet.reqId == 0:
            raise ValueError("ReqId shouldn't be 0!")
        if role != FCGI_RESPONDER:
            self.finishRequest(packet.reqId, FCGI_UNKNOWN_ROLE)
        else:
            chanRequest = self.chanRequestFactory(self.requestFactory,
                                                  packet.reqId,
                                                  flags & FCGI_KEEP_CONN)
            chanRequest.makeConnection(self.transportFactory(self,
                                                             packet.reqId))
            self._chanRequests[packet.reqId] = chanRequest

    def fcgi_abort_request(self, packet):
        chanRequest = self._chanRequests.get(packet.reqId)
        if not chanRequest:
            return
        chanRequest.abortConnection()
        del self._chanRequests[packet.reqId]

    def fcgi_params(self, packet):
        chanRequest = self._chanRequests.get(packet.reqId)
        if not chanRequest:
            return
        if packet.content:
            chanRequest.params += packet.content
        else:
            chanRequest.makeRequest(dict(parseNameValues(chanRequest.params)))
            chanRequest.request.process()
        
    def fcgi_stdin(self, packet):
        chanRequest = self._chanRequests.get(packet.reqId)
        if not chanRequest:
            return
        if packet.content:
            chanRequest.request.handleContentChunk(packet.content)
        else:
            chanRequest.request.handleContentComplete()
        
    def fcgi_data(self, packet):
        # For filter roles only, which is currently unsupported.
        pass

    # Methods for FastCGIRequestTransport

    def writeRequest(self, reqId, data):
        if len(data) <= FCGI_MAX_PACKET_LEN:
            self.writePacket(Record(FCGI_STDOUT, reqId, data))
        else:
            while data:
                self.writePacket(Record(FCGI_STDOUT, reqId,
                                        data[:FCGI_MAX_PACKET_LEN]))
                data = data[FCGI_MAX_PACKET_LEN:]

    def finishRequest(self, reqId, status):
        self.writePacket(Record(FCGI_END_REQUEST, reqId,
                                "\0\0\0\0"+chr(status)+"\0\0\0"))
        if not self._chanRequests[reqId].keepalive:
            self.transport.loseConnection()
        del self._chanRequests[reqId]

    # Raw data handling

    def writePacket(self, packet):
        #print "Writing record", packet
        self.transport.write(packet.toOutputString())
        
    def dataReceived(self, data):
        self.dataBuffer = self.dataBuffer + data
        record = self.pendingRecord
        while len(self.dataBuffer) >= 8 and not self.producerPaused:
            if not record:
                record = Record.fromHeaderString(self.dataBuffer[:8])
            if len(self.dataBuffer) < record.totalLength:
                break
            record.content = self.dataBuffer[8:record.contentLength+8]
            self.dataBuffer = self.dataBuffer[record.totalLength:]
            self.packetReceived(record)
            record = None
        self.pendingRecord = record

    # Producer interface

    def pauseProducing(self):
        self.producerPaused = True
        self.transport.pauseProducing()

    def resumeProducing(self):
        self.producerPaused = False
        self.transport.resumeProducing()
        self.dataReceived('')

    def stopProducing(self):
        self.producerPaused = True
        self.transport.stopProducing()


class FastCGIFactory(protocol.ServerFactory):

    protocol = FastCGIProtocol

    def __init__(self, requestFactory):
        self.requestFactory = requestFactory

    def buildProtocol(self, addr):
        p = protocol.ServerFactory.buildProtocol(self, addr)
        p.requestFactory = self.requestFactory
        return p


class FDPortMixIn(object):

    def createInternetSocket(self):
        import socket
        import fcntl
        s = socket.fromfd(self.port, self.addressFamily, self.socketType)
        s.setblocking(0)
        if fcntl and hasattr(fcntl, 'FD_CLOEXEC'):
            old = fcntl.fcntl(s.fileno(), fcntl.F_GETFD)
            fcntl.fcntl(s.fileno(), fcntl.F_SETFD, old | fcntl.FD_CLOEXEC)
        return s

    def startListening(self):
        self.socket = self.createInternetSocket()
        self.factory.doStart()
        self.connected = 1
        self.numberAccepts = 100
        self.fileno = self.socket.fileno
        self.startReading()

    

class TCPFDPort(FDPortMixIn, tcp.Port):
    pass

class UNIXFDPort(FDPortMixIn, unix.Port):
    def connectionLost(self, reason):
        # No unlinking here.
        tcp.Port.connectionLost(self, reason)

def startFastCGI(site):
    from twisted.internet import reactor
    import socket

    sock = socket.fromfd(FCGI_LISTENSOCK_FILENO,
                         socket.AF_INET, socket.SOCK_STREAM)
    if type(sock.getsockname()) is str:
        portFactory = UNIXFDPort
    else:
        portFactory = TCPFDPort

    reactor.listenWith(portFactory, FCGI_LISTENSOCK_FILENO,
                       FastCGIFactory(site))
    reactor.run()

