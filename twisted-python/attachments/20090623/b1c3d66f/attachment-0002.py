##
## A Twisted SerialConnector.
## Iap, Singuan. 2009/6/23
## 

##
## Modify the parameter for your environment.
##
comport = 'COM10'
baudrate = 38400

import sys
from twisted.internet import win32eventreactor
win32eventreactor.install()
    
from twisted.internet.interfaces import IConnector,IAddress
from twisted.internet.serialport import SerialPort
from zope.interface import implements
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor,main
from twisted.protocols.basic import LineReceiver
from twisted.python import failure

class SerialAddress(object):
    implements(IAddress)
    def __init__(self,addr,channel):
        self.address = addr
        self.channel = channel
    def __getitem__(self,idx):
        return (self.address, self.channel)
    def __getslice__(self,start,end):
        return (self.address, self.channel)
    def __eq__(self,other):
        return other.address==self.address and other.channel == this.channel
    def __str__(self):
        return 'SerialPort("%s",%s)' % (self.address,self.channel)


class SerialConnector:
    implements(IConnector)
    factoryStarted = 0
    def __init__(self,comport,baudrate,factory=None,reactor=None):
        self.baudrate = baudrate
        self.comport = comport
        self.transport = None
        self.state = 'disconnected'
        self.factory = factory
        self.reactor = reactor
        self.connectTimerId = None
    def disconnect(self):        
        if self.transport:
            ## I thought that by calling the flushInput,flushOutput
            ## the loseConnection will not dump tracebacks again.
            ## I am wrong.
            if 0:
                self.transport.flushInput()
                self.transport.flushOutput()
            ##
            ## Actually, it is this line which gets ride off the tracebacks.
            ## Comment out this line to see the tracebacks.
            reactor._disconnectSelectable(self.transport,failure.Failure(main.CONNECTION_DONE),0)
            
            self.transport.loseConnection()
        self.state = 'disconnected'
        if self.factoryStarted:
            self.factory.doStop()
            self.factoryStarted=False
    def getDestination(self): 
        return  SerialAddress(self.comport,self.baudrate)
    def connect(self):
        if not self.state == 'disconnected':
            raise RuntimeError,'not connected'
        self.state = 'connecting'
        if not self.factoryStarted:            
            self.factory.doStart()
            self.factoryStarted = 1
        m = self.factory.protocol()
        m.factory  = self.factory
        self.transport= SerialPort(m, self.comport, reactor, baudrate=self.baudrate)        
        self.transport.connector = self
        self.factory.startedConnecting(self)
class SerialAPI(LineReceiver):
    def connectionMade(self):
        print 'Serial connected, protoco=',self
        print 'Serial port=',self.transport
        self.setLineMode()
        ##
        ## Modify this line to generate traffic.
        ##
        self.transport.write('echo Hello world\n')
    def lineReceived(self,line):
        print '>>',line

class SerialFactory(ClientFactory):
    protocol = SerialAPI


if __name__ == '__main__':
    def test():
        factory = SerialFactory()
        connector = reactor.connectWith(SerialConnector,comport,baudrate,factory)
        def reconnect(connector):        
            print '^' * 80
            print 'Disconnect and starts a new connection seconds later'
            connector.disconnect()
            reactor.callLater(1,test)
        reactor.callLater(3,reconnect,connector)
    reactor.callWhenRunning(test)
    reactor.run()
