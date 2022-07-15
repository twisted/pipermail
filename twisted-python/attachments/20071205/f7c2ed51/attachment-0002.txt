
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


from OpenSSL import SSL

class ServerContextFactory:
    
    def getContext(self):
        """Create an SSL context.
        
        This is a sample implementation that loads a certificate from a file 
        called 'server.pem'."""
        ctx = SSL.Context(SSL.TLSv1_METHOD)
        ctx.use_certificate_file('server.cert')
        ctx.use_privatekey_file('server.pkey')
        return ctx


if __name__ == '__main__':
    import echoserv, sys
    from twisted.internet.protocol import Factory
    from twisted.internet import ssl, reactor
    from twisted.python import log
    log.startLogging(sys.stdout)
    factory = Factory()
    factory.protocol = echoserv.Echo
    reactor.listenSSL(8890, factory, ServerContextFactory())
    reactor.run()
