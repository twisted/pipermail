#!/usr/bin/env python
from twisted.internet import reactor
from twistedsnmp import snmpprotocol, agentproxy

class SNMPClient:
    def __init__( self, hostname, community ):
    	self.port = snmpprotocol.port()
    	self.proxy = agentproxy.AgentProxy(
    		hostname, 161,
		    community,
		    snmpVersion = 'v2',
		    protocol = self.port.protocol)

    def mymain( self, proxy, oid ):
        df = proxy.get(	[oid], timeout=.25, retryCount=5	)
        df.addCallback( self.printResults )
        df.addCallback( self.exiter )
        df.addErrback( self.errorReporter )
        df.addErrback( self.exiter )
        return df

    def printResults( self, result ):
        t = result.keys()
        if result[ t[0] ]:
            self.result = result[ t[0] ]
        else:
            self.result = None
        return result

    def errorReporter( self, err ):
        print 'ERROR', err.getTraceback()
        self.result = None
        return err

    def exiter( self, value ):
        reactor.stop()
        return value

    def getValue( self, oid ):
    	reactor.callWhenRunning( self.mymain, self.proxy, oid )
    	reactor.run()
        return self.result

    def getLoad( self ):
        l1 = self.getValue( '.1.3.6.1.4.1.2021.10.1.3.1' )
#        l2 = self.getValue( '.1.3.6.1.4.1.2021.10.1.3.2' )
        return [ l1, l2 ]

agent = SNMPClient("127.0.0.1","public")
x = agent.getLoad()
print x
