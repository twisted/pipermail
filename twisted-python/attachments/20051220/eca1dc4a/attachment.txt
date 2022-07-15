#!/usr/bin/env python


from twisted.conch.ssh import transport, userauth, connection, channel
from twisted.conch.ssh.common import NS
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import sys, os, getpass

USER, PASS, HOST, CMD, SRC, DST = None, None, None, None, None, None

# The "Transport" is the crypto layer on top of port 22
class Transport(transport.SSHClientTransport):
    def verifyHostKey(self, hostKey, fingerprint):
        # For info only
        log.msg('host key fingerprint: %s' % fingerprint)
        # FIXME: this is insecure
        return defer.succeed(1)

    def connectionSecure(self):
        # Once we're secure (server key valid) we ask for userauth service
        # on a new "connection" object
        self.requestService(UserAuth(USER, Connection()))

class UserAuth(userauth.SSHUserAuthClient):
    def getPassword(self):
        # Ack! Globals!
        return defer.succeed(PASS)
    
    def getPublicKey(self):
        # returning None means always use username/password auth
        return

class Connection(connection.SSHConnection):
    def serviceStarted(self):
        # Once userauth has succeeded we ask for a channel on this
        # connection
        self.openChannel(ScpChannel(2**16, 2**15, self))

class XferChannelBase(channel.SSHChannel):
    name = 'session'
    
    state = None
    todo = 0
    buf = ''
    
    def openFailed(self, reason):
        log.err(reason)
        
    def channelOpen(self, data):
        # Might display/process welcome screen
        self.welcome = data

        # We might be an SCP or SFTP requests
        if 'scp' in CMD or CMD.startswith('/'):
            kind = 'exec'
        else:
            kind = 'subsystem'
        # Call our handler
        d = self.conn.sendRequest(self, kind, NS(CMD), wantReply=1)
        d.addCallbacks(self.channelOpened, log.err)
        
    def closed(self):
        self.loseConnection()
        reactor.stop()


class SftpChannel(XferChannelBase):
    def channelOpened(self, data):
        log.msg("channelOpened: %r" % (data,))
        self.client = filetransfer.FileTransferClient()
        self.client.makeConnection(self)
        self.dataReceived = self.client.dataReceived
        d = self.client.openFile(SRC, filetransfer.FXF_READ, {})
        d.addCallbacks(self.fileOpened, log.err)

    def fileOpened(self, rfile):
        rfile.getAttrs().addCallbacks(self.fileStatted, log.err, (rfile,))

    def fileStatted(self, attrs, rfile):
        rfile.readChunk(0, 4096).addCallbacks(self.did_read, log.err, (rfile, 0, attrs['size'])).addCallback(self.done)
            
    def did_read(self, data, f, pos, todo):
        if len(data)>todo:
            log.msg("got %i bytes more than expected, trimming" % (len(data)-todo,))
            data = data[:todo]
            
        DST.write(data)
        todo -= len(data)
        pos += len(data)
        if todo<=0:
            return pos
        return f.readChunk(pos, 4096).addCallbacks(self.did_read, log.err, (f, pos, todo))

    def done(self, l):
        log.msg("done %i bytes" % (l,))
        self.loseConnection()

class ScpChannel(XferChannelBase):
    def channelOpened(self, data):
        # once the scp is exec'ed, start the SCP transfer
        self.write('\0')
        # we're a state machine
        self.state = 'waiting'

    def dataReceived(self, data):
        #log.msg('dataReceived: %s %r' % (self.state, data))

        # What we do with the data depends on where we are
        if self.state=='waiting':
            # we've started the transfer, and are expecting a C
            # Coctalperms size filename\n

            # might not get it all at once, buffer
            self.buf += data
            if not self.buf.endswith('\n'):
                return
            b = self.buf
            self.buf = ''

            # Must be a C
            if not b.startswith('C'):
                log.msg("expecting C command: %r" % (self.buf,))
                self.loseConnection()
                return

            # Get the file info
            p, l, n = b[1:-1].split(' ')
            perms = int(p, 8)
            self.todo = int(l)
            log.msg("getting file %s mode %s len %i" % (n, oct(perms), self.todo))
            
            # Tell the far end to start sending the content
            self.state = 'receiving'
            self.write('\0')
            
        elif self.state=='receiving':
            # we've started the file body
            #log.msg('got %i bytes' % (len(data),))
            
            if len(data)>self.todo:
                extra = data[self.todo:]
                data = data[:self.todo]
                if extra!='\0':
                    log.msg("got %i more bytes than we expected, ignoring: %r" % (len(extra), extra))
                
            DST.write(data)
            self.todo -= len(data)
            
            if self.todo<=0:
                log.msg('done')
                self.loseConnection()
        else:
            log.err("dataReceived in unknown state: %r" % (self.state,))


def usage(ex):
    print >>sys.stderr, """%s: [user[:pass]@]hostname:sourcefile destfile""" % (sys.argv[0],)
    if ex:
        sys.exit(ex)
    
if __name__=='__main__':
    args = sys.argv[1:]
    if len(args)<2:
        usage(1)
        
    SRC = args[0]
    DST = args[1]

    if '@' in SRC:
        USER, SRC = SRC.split('@', 1)
    else:
        USER = os.environ['USERNAME']
        
    if not ':' in SRC:
        usage(1)
        
    HOST, SRC = SRC.split(':', 1)
            
    if ':' in USER:
        USER, PASS = USER.split(':', 1)
    else:
        PASS = getpass.getpass('password for %s@%s: ' % (USER, HOST))

    DST = open(DST, 'wb')

    if 'sftp' in sys.argv[0]:
        CMD = 'sftp'
    else: 
        CMD = 'scp -f %s' % (SRC,)
        
    protocol.ClientCreator(reactor, Transport).connectTCP(HOST, 22)
    log.startLogging(sys.stderr)
    reactor.run()

