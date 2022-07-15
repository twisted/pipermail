import sys
import urlparse

from twisted.internet import reactor
from twisted.web import client, resource, server
from twisted.python import log

class HTTPProxy(resource.Resource):
    def _parseURL(self, url):
        host, port = urlparse.urlparse(url)[1], 80
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        return host, port

    def cbRequestDone(self, data, (request, factory)):
        if factory.response_headers:
            for name, value in factory.response_headers.items():
                request.setHeader(name, ';'.join(value))
        request.write(data + '\r\n')
        request.finish()
        
    def render(self, request):
        factory = client.HTTPClientFactory(request.uri)
        host, port = self._parseURL(request.uri)
        reactor.connectTCP(host, port, factory)
        factory.deferred.addCallback(self.cbRequestDone,
                                     (request, factory))
        return server.NOT_DONE_YET

    getChild = lambda self, *_: self
        
log.startLogging(sys.stdout)
resource = HTTPProxy()
factory = server.Site(resource)
reactor.listenTCP(8080, factory)
reactor.run()
