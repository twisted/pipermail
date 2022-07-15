# -*- coding: utf-8 -*-


from twisted.internet import address, error, base, tcp
import sys
import socket


# Problem1: we have an opened file (descriptor, handle, whatever your system provides),
# we want to run some protocol on top of that file, because that file is
# some sort of a connection to the outside world. Maybe it is a socket.
# But it may really be something like a PTY, we do not depend on that.
# This is a full-duplex select()able and poll()able system IO object,
# that supports read(), write() and close() and may be made O_NONBLOCK with fcntl.
#
# Problem2: we have two opened files, and since they are respectively read- and write- endpoints of
# two (perhaps)independent unidirectional data channels, we want to build a protocol session
# on top of bidirectional transport, that read()s from the first file and
# write()s to the second file. The files may be FIFOs, but we do not depend on
# that, because they also may be single dup()ed PTY or socket(), or even two separate sockets.
#
# Problem3: we have two unidirectional transports. First - is the IReadDescriptor, other is IWriteDescriptor.
# We want to combine that into IReadWriteDescriptor and optionally into IHalfCloseableDescriptor.
# And then use that to bootstrap a protocol on top of that.
#
# We know, what kind of protocol we want. We know precisely, whether it is
# client- or server- side of protocol, when protocol provide such asymmetry, ofcourse.
# And yes, we do want not limit ourselves to using only client or only server protocols.
#
#
#
#
# Proposed Solution: create a Transport instance and marry it with a newly
#  created Protocol instance.
#  Sounds simple.
#  like this:
#    transport = fullDuplexTransportOneFD(fileDescriptor)
#   or
#    transport = fullDuplexTransportTwoFDs(readFileDescripor, writeFileDescriptor)
#   or
#    transport = fullDuplexTransport(readTransport, writeTransport)
#   and then
#    protocol = someProtocol()
#    meet(transport, protocol)
#   or
#    protocol = buildProtocolOnTopOfTransport(protocolFactory, transport)
#
# But since, as does russian proverb say, living a life is not as easy as crossing a field,
# or in other words, life's a bitch,
# the solution is not practically possible to accomplish in a week. At least for a non twisted developer.
#
# Situation is as follows:
# There are Protocol factories. Worse, there are client and server protocol factories.
# They are operated separately and not interchangeable because their interfaces differ.
# Rumors say, that Protocol instances may be built without factories.
# But the code in several ProtocolFactory.buildProtocol() does this:
#   proto = create_the_protocol(...)
# and then
#   proto.factory = self
# So I doubt, that every protocol implementation will function without
# proper self.factory installed. But we want a solution for every
# possible transport/protocol pair, that makes sense ofcourse.
# Again, interface between protocol instance and it's factory is not
# unified among server and client variants.
# So we'll have to keep that ProtocolFactory complication, and keep it happy.
#
# Transports.
# There is Client and Server transport classes in t.i.tcp. Yes.
# And you will have to live with that...
# Every kind of transport is created by respective transport factory,
# that is the only one who knows how to do that.
#
# Transport Factories.
# There is no abstract TransportFactory implementation, that will incorporate common code,
# unrelated to transport type and to the connection side, that will be functional enough
# to construct a transport instance and meet it with a protocol instance.
# There are server transport connection (listen*, Port) and client transport connection (connect*, Connector) builders.
# They both do interface with ProtocolFactory, but interfaces differ.
# They may also interface directly with protocol instance:
#  t.i.tcp.Port.doRead: protocol.makeConnection(transport)
# Transport factory operates based on deep knowledge about the transport's underlying type of file
# and depending on the side, client's or server's.
# I have experimented trying to instantiate a server-side protocol instance
# out of PBServerFactory using a modified Connector and modified Client classes,
# but was stopped by the fact, that PBServerFactory does not provide an interface, that
# a Connector do count on.
# After on-the-fly patching of PBServerFactory instance with a noop methods,
# it worked, but I'm not sure whether that is enough for every other protocol and factory.
# And you know what, I'm sure that should not become a part of the twisted code, it is too ugly.
# Alexey.
#

# this is only a partial solution for one fd which must be a connected socket.

class FDSocketFakeConnector(base.BaseConnector):
    def __init__(self, fd, factory, reactor, transportClass):
        self.fd_arg = fd
        self.transportClass = transportClass
        base.BaseConnector.__init__(self, factory, None, reactor)
        

    def _makeTransport(self):
        import os
        sys.stderr.write("[%d]: FDSocketFakeConnector._makeTransport(0x%x)\n" %(os.getpid(), id(self)))
        self.transport = self.transportClass(self.fd_arg, self, self.reactor)
        return self.transport



class FDSocketTransport(tcp.BaseClient):
    realAddress = ""
    def __init__(self, fd, connector, reactor):
        import os
        sys.stderr.write("[%d]: FDSocketTransport(0x%x)\n" %(os.getpid(), id(self)))
        self.connector = connector
        if isinstance(fd, int) or isinstance(fd, long):
            self.sock = socket.fromfd(fd, self.addressFamily, self.socketType)
        elif isinstance(fd, socket._socket.socket):
            self.sock = fd
        else:
            self._finishInit(None, None, error.ConnectError("unknown socket type: %s" %(type(fd))), reactor)
            return
        self._finishInit(self.doConnect, self.sock, None, reactor)

    def createInternetSocket(self):
        import os
        sys.stderr.write("[%d]: createInternetSocket(0x%x)\n" %(os.getpid(), id(self)))
        self.sock.setblocking(0)
        return self.sock

    def failIfNotConnected(self, err):
        import os
        sys.stderr.write("[%d]: FDSocket.Transport(0x%x).failIfNotConnected(%s)" %(os.getpid(), id(self), err))
        try:
            raise Exception("")
        except:
            e = sys.exc_info()
        frame = e[2].tb_frame
        while frame:
            sys.stderr.write("\n  from %s, line %d" %(frame.f_code, frame.f_lineno))
            frame = frame.f_back
        sys.stderr.write("\n")
        tcp.BaseClient.failIfNotConnected(self, err)

    def doConnect(self):
        # I do not understand all of these, but I just copied all that. Alexey.
        
        if not hasattr(self, "connector"):
            # this happens when connection failed but doConnect
            # was scheduled via a callLater in self._finishInit
            return

        try:
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err:
                self.failIfNotConnected(error.getConnectError((err, strerror(err))))
                return
        except socket.error, exc:
            # this happens if you run inetd-managed server from your shell instead. Alexey.
            #
            if exc[0]==88:
                self.failIfNotConnected(SocketOperationOnNonSocket(0, exc))
            else:
                self.failIfNotConnected(error.getConnectError(exc))
            return
        del self.doWrite
        del self.doRead
        # we first stop and then start, to reset any references to the old doRead
        self.stopReading()
        self.stopWriting()
        self._connectDone()

class FDUNIXStreamSocket(FDSocketTransport):
    # don't know whether that additional class helps at all. Alexey.
    addressFamily = socket.AF_UNIX
    socketType = socket.SOCK_STREAM
    
    def getHost(self):
        return ""

    def getPeer(self):
        return ""

class SocketOperationOnNonSocket(error.ConnectError):
    """Application expected some kind of a socket, but got a non-socket instead"""

# use it:
#  c = FDSocketFakeConnector(fd, protocolFactory, reactor, FDUNIXStreamSocket)
#  c.connect()  - that will start the protocol
#
# for server protocol factory
# I have done this before it's usage:
#
#  protocolFactory.startedConnecting = lambda x=None: None
#  protocolFactory.clientConnectionFailed = lambda x=None, y=None: x
#  protocolFactory.clientConnectionLost = lambda x=None, y=None: None
#
# You may use subclassing for that aswell.
#
