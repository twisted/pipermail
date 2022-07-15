#! /usr/bin/python

from twisted.spread import pb
from twisted.application import service
from twisted.internet import reactor, ssl
        

from OpenSSL import SSL

CERT_FILE='stunnel.pem'

class ServerContextFactory:
    
    def getContext(self):
        """Create an SSL context.
        
        This is a sample implementation that loads a certificate from a file 
        whose name is held in CERT_FILE."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(CERT_FILE)
        ctx.use_privatekey_file(CERT_FILE)
        return ctx
    
class ServerObject(pb.Root):
    def remote_add(self, one, two):
        answer = one + two
        print "returning result:", answer
        return answer
    def remote_subtract(self, one, two):
        return one - two
    
app = service.Application("server1")
#reactor.listenTCP(8800, pb.BrokerFactory(ServerObject()))
sslContext = ssl.DefaultOpenSSLContextFactory(
			'stunnel.pem', 
			'stunnel.pem',
		)
root = pb.PBServerFactory(ServerObject())
reactor.listenSSL(8800, root, ServerContextFactory())#sslContext)
reactor.run()
