"""
Base Class for AVS NBT Client Communication
"""
from twisted.internet import reactor, protocol
from struct import *
import nmb
import time
from avsMessageHandling import *

# AVS NBT client protocol

class AvsNbtClient(protocol.Protocol):

    def __init__(self, myReadableName, remoteReadableName, messageHandler, maxLoop, instanceName):
        self.myReadableName = myReadableName
        self.remoteReadableName = remoteReadableName
        self.messageHandler = messageHandler
        self.maxLoop = maxLoop
        self.instanceName = instanceName

        self.sessionEstablished = False
        self.loopCount = 0
    

    def connectionMade(self):
        #print "%s connection made. requesting session establishment ..." % self.instanceName
        self.myName = nmb.encode_name(self.myReadableName, nmb.TYPE_WORKSTATION, '')
        self.remoteName = nmb.encode_name(self.remoteReadableName, nmb.TYPE_SERVER, '')
        #print "myName= %s   remoteName= %s\n" % (self.myReadableName, self.remoteReadableName)
        self.buf = '\x81\x00' + pack('>H', len(self.remoteName) + len(self.myName)) + self.remoteName + self.myName 
        #print "buf= %s" % repr(self.buf)
        self.transport.write(self.buf)

    def dataReceived(self, data):
        #print "%s Server said: %s" % (self.instanceName, repr(data))
        if not self.sessionEstablished:
           if data[0] == '\x82':
              #print "%s Positive Service Response Packet received!" % self.instanceName
              self.sessionEstablished = True
              #self._sendServerData()
           else:
              print "%s failed to establish session" % self.instanceName
        self.transport.loseConnection()
    
    
    #def connectionLost(self, reason):
        #print "%s connection lost" % self.instanceName

    def _sendServerData(self):
        self.loopCount += 1

        if self.loopCount > self.maxLoop:
           print "loopCount exceeded. terminating session ..."
           self.transport.loseConnection()
        else:
           self.toServerData = self.messageHandler.getMessage()
           print "%s TRANS CODE= %s\n" % (self.instanceName, self.messageHandler.getTransCode())
           self.toServer = '\x00\x00' + pack('>H', len(self.toServerData)) + self.toServerData
           print "%s sending server data ..." % self.instanceName
           self.transport.write(self.toServer)
           print "%s finished sending server data" % self.instanceName


class NBTFactory(protocol.ClientFactory):
    protocol = AvsNbtClient
    messageHandler = None
    maxLoop = 3
    myName = None
    remoteName = None
    instanceName = None

    def buildProtocol(self, addr):
        print "buildProtocol with myName= %s instanceName= %s\n" % (self.myName, self.instanceName)
        p = self.protocol(self.myName, self.remoteName, self.messageHandler, self.maxLoop, self.instanceName)
        p.factory = self
        return p

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        print reason
    
    def clientConnectionLost(self, connector, reason):
        print "%s Connection lost - goodbye!" % self.instanceName


