# -*- coding: utf-8 -*-

#############################################################
# Executes a python code on the remote host using SSH
#############################################################

from twisted.conch.ssh import transport, userauth, connection, common, keys, channel
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import sys, os, re

class lqSSHException(Exception):
    def __init__(self, errorcode, message):
        self.errorcode = errorcode
        self.message = message
    
    def __str__(self):
        return '%s %s' % (self.errorcode, self.message)

class lqSSHClient(protocol.ClientFactory):
    '''
    Executes a remote python code
    '''
    def __init__(self, username, server, keyfile, command):
        '''
        Necessary information to connect
        '''
        self.username = username
        self.server = server
        self.keyfile = keyfile
        self.command = command
        self._deferer_ = defer.Deferred()
        self._transport = None
    
    def buildProtocol(self, addr):
        '''
        Create the protocol after connection
        '''
        self._transport = lqSSHTransport(self.username, self.keyfile, self.command, self._deferer_)
        return self._transport
    
    def connect(self):
        reactor.connectTCP(self.server, 22, self)
        self._deferer_.addCallback(self.disconnectOnSuccess)
        self._deferer_.addErrback(self.disconnectOnError)
        return self._deferer_
    
    def disconnect(self):
        if self._transport is not None:
            self._transport.loseConnection()
            
    def disconnectOnError(self, failure):
        self.disconnect()
        raise failure
    
    def disconnectOnSuccess(self, result):
        self.disconnect()
        return result
    
    def clientConnectionFailed(self, connector, reason):
        '''
        When connection failed
        '''
        protocol.ClientFactory.clientConnectionFailed(self, connector, reason)
        log.err(reason)
        self._deferer_.errback(reason)
    
class lqSSHTransport(transport.SSHClientTransport):
    
    def __init__(self, username, keyfile, command, _deferer_):
        '''
        Necessary info to start SSH connection
        '''
        self.username = username
        self.keyfile = keyfile
        self.command = command
        self._deferer_ = _deferer_
        self.timeout = reactor.callLater(30, self.sshTransportTimeout)
    
    def verifyHostKey(self, hostKey, fingerprint):
        '''
        Check fingerprint
        '''
        # print 'host key fingerprint: %s' % fingerprint
        self.timeout.cancel()
        return defer.succeed(1)
    
    def connectionSecure(self):
        '''
        User authentication 
        '''
        self.requestService(
            lqSSHUserAuth(self.username, self.keyfile, self._deferer_,
                lqSSHConnection(self.command, self._deferer_)))

    def sshTransportTimeout(self):
        '''
        If the connection times out
        '''
        self.loseConnection()
        self._deferer_.errback(lqSSHException('408', 'Bağlantı zaman aşımına uğradı'))
    
class lqSSHUserAuth(userauth.SSHUserAuthClient):
    
    def __init__(self, username, keyfile, _deferer_, connection):
        '''
        User authentication
        '''
        userauth.SSHUserAuthClient.__init__(self, username, connection)
        self.keyfile = keyfile
        self._deferer_ = _deferer_
    
    def getPassword(self):
        '''
        Password auth is not provided, give error
        '''
        self.transport.sendDisconnect(transport.DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE, 'no more auths')
        self._deferer_.errback(lqSSHException('401', 'Wrong Key / Key authentication failed'))
        return
    
    def getGenericAnswers(self, name, instruction, questions):
        '''
        Keyboard interactive password is not provided, give erro
        '''
        self.transport.sendDisconnect(transport.DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE, 'no more auths')
        self._deferer_.errback(lqSSHException('401', 'User authentication failed'))
        return defer.fail(None)
    
    def getPublicKey(self):
        '''
        Create the public key
        '''
        if not os.path.exists(self.keyfile) or self.lastPublicKey:
            return
        
        return keys.Key.fromFile(self.keyfile+'.pub')
    
    def getPrivateKey(self):
        '''
        Create the private key
        '''
        return defer.succeed(keys.Key.fromFile(self.keyfile))

class lqSSHConnection(connection.SSHConnection):
    
    def __init__(self, command, _deferer_, *args, **kwargs):
        '''
        Tracks the SSH connection
        '''
        connection.SSHConnection.__init__(self)
        self.command = command
        self._deferer_ = _deferer_
    
    def serviceStarted(self):
        '''
        Runs just after the authentication finished
        '''
        self.openChannel(lqSSHChannel(self.command, self._deferer_, \
                                      2**16, 2**15, conn=self))
    
    def serviceStopped(self):
        '''
        Runs if the service stopped
        '''
    
class lqSSHChannel(channel.SSHChannel):
    
    name = 'session'
    
    _buffer = ''
    delimiter = '\n'
    MAX_LENGTH = 16384

    def __init__(self, command, _deferer_, *args, **kwargs):
        '''
        SSH channel parameters
        '''
        channel.SSHChannel.__init__(self, *args, **kwargs)
        self.command, self.input = command
        self._deferer_ = _deferer_
        self.success = True
        self.output = ''
    
    def openFailed(self, reason):
        self._deferer_.errback(reason)
    
    def channelOpen(self, ignoredData):
        d = self.conn.sendRequest(self, 'exec', common.NS(self.command), wantReply = True)
        d.addCallback(self._cbRequest)
    
    def _cbRequest(self, ignored):
        if self.input:
            self.write(self.input)
        self.conn.sendEOF(self)
    
    def dataReceived(self, data):
        """
        Splits the data to lines
        """
        lines  = (self._buffer+data).split(self.delimiter)
        self._buffer = lines.pop(-1)
        for line in lines:
            if len(line) > self.MAX_LENGTH:
                return self.lineLengthExceeded(line)
            else:
                self.lineReceived(line)
        if len(self._buffer) > self.MAX_LENGTH:
            return self.lineLengthExceeded(self._buffer)
    
    def lineReceived(self, line):
        code, message = line.strip().split(' ', 1)
        self.output += line + self.delimiter
        if code != '200':
            self.success = False
            self._deferer_.errback(lqSSHException(code, message))
    
    def lineLengthExceeded(line):
        self.success = False
        self._deferer_.errback(lqSSHException('500', 'Very long line'))
    
    def extReceived(self, dataType, data):
        print "500 Extended data:", dataType, data
    
    def closed(self):
        if self.success:
            self._deferer_.callback(self.output)
    
if __name__ == "__main__":
    
    USER = os.getlogin()
    HOST = 'localhost'
    KEYFILE = os.path.expanduser('~/.ssh/id_dsa')
    
    def done(result):
        print result
        reactor.stop()
    
    def failed(failure):
        print >> sys.stderr, failure.getErrorMessage()
        reactor.stop()
    
    remoteCode = "print 'Hello World'"
    
    client = lqSSHClient(USER, HOST, KEYFILE, ('python', remoteCode))
    d = client.connect()
    d.addCallback(done)
    d.addErrback(failed)
    
    reactor.run()