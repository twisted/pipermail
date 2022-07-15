from twisted.conch import error
from twisted.conch.ssh import transport, keys, userauth, connection, common, channel
from twisted.internet import defer, protocol, reactor
import struct
import wingdbstub
class ClientTransport(transport.SSHClientTransport):
    
    def __init__(self,d,fingerprint,*args):
        self.fingerprint=fingerprint
        self.args=args
        self.d=d
    def verifyHostKey(self, pubKey, fingerprint):
        if fingerprint != self.fingerprint:
            return defer.fail(error.ConchError('mismatched fingerprint, expected %s have %s' %\
                                               (fingerprint,self.fingerprint)))
        else:
            return defer.succeed(1)

    def connectionSecure(self):
        (user,privkey,pubkey,args)=(self.args[0],self.args[1],self.args[2],self.args[3:])
        self.requestService(ClientUserAuth(user, ClientConnection(self.d,*args),privkey,pubkey))
        
class ClientUserAuth(userauth.SSHUserAuthClient):

    def __init__(self,user,instance,privkey,pubkey,*args):
        self.privkey=privkey
        self.pubkey=pubkey
        userauth.SSHUserAuthClient.__init__(self,user,instance)
        
    def getPassword(self, prompt = None):
        return 
        # this says we won't do password authentication

    def getPublicKey(self):
        return keys.getPublicKeyString(data = self.pubkey)

    def getPrivateKey(self):
        return defer.succeed(keys.getPrivateKeyObject(data = self.privkey)) 



class ClientConnection(connection.SSHConnection):
    
    def __init__(self,d,*args):
        self.args=args
        self.d=d
        connection.SSHConnection.__init__(self)
        
    def serviceStarted(self):
        self.openChannel(ExecCmdChannel(d=self.d,commands=self.args,conn = self))

class ExecCmdChannel(channel.SSHChannel):
    name = 'session'
    def __init__(self,*args,**kwargs):
        self.commands=kwargs.pop('commands')
        
        self.d=kwargs.pop('d')
        assert isinstance(self.d,defer.Deferred)
        channel.SSHChannel.__init__(self,*args,**kwargs)
    def channelOpen(self, data):
        d = self.conn.sendRequest(self, 'exec', common.NS(" ".join(self.commands)),
                                  wantReply = 1)
        d.addCallback(self._cbSendRequest)
        self.catData = ''
    
    def _cbSendRequest(self, ignored):        
#        self.conn.sendEOF(self)
        self.loseConnection()

    def dataReceived(self, data):
        self.catData += data
        
    def request_exit_status(self,data):
        self.exitcode=struct.unpack("!L",data)
        
    def extReceived(self, dataType, data):    
        self.extendedData=data
    def closed(self):
        extData=getattr(self,'extendedData',None)
        self.d.callback((self.catData,self.exitcode,extData))
    
    
    
#class CatChannel(channel.SSHChannel):

    #name = 'session'

    #def channelOpen(self, data):
        #d = self.conn.sendRequest(self, 'exec', common.NS('cat'),
                                  #wantReply = 1)
        #d.addCallback(self._cbSendRequest)
        #self.catData = ''

    #def _cbSendRequest(self, ignored):
        #self.write('This data will be echoed back to us by "cat."\r\n')
        #self.conn.sendEOF(self)
        #self.loseConnection()

    #def dataReceived(self, data):
        #self.catData += data

    #def closed(self):
        #print 'We got this from "cat":', self.catData
        
class CommandClientFactory(protocol.ClientFactory):
    def __init__(self,*args):        
        self.args=args
        
    def buildProtocol(self,addr):
        p = ClientTransport(*self.args)
        p.factory = self
        return p
        
def executeCommand(address,fingerprint,user,privkey,pubkey,command,*args):
    d=defer.Deferred()
    factory = CommandClientFactory(d,fingerprint,user,privkey,pubkey,command,*args)
    reactor.connectTCP(address, 22, factory)
    return d