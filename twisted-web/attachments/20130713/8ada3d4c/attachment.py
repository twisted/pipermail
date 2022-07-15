#!/usr/bin/python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example of a proxy which logs all requests processed through it.

Usage:
    $ python logging-proxy.py

Then configure your web browser to use localhost:8080 as a proxy, and visit a
URL (This is not a SOCKS proxy). When browsing in this configuration, this
example will proxy connections from the browser to the server indicated by URLs
which are visited.  The client IP and the request hostname will be logged for
each request.

HTTP is supported.  HTTPS is not supported.

See also proxy.py for a simpler proxy example.
"""

from twisted.internet import reactor
from twisted.web import proxy, http

class LoggingProxyClient(proxy.ProxyClient):
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version,
                headers, data, father)

    def handleStatus(self, version, code, message):
        print "RESP:", code, message
        proxy.ProxyClient.handleStatus(self, version, code, message)

    def handleHeader(self, key, value):
        print "RESP:", "%s: %s" % (key, value)
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponseEnd(self):
        print
        proxy.ProxyClient.handleResponseEnd(self)

class LoggingProxyClientFactory(proxy.ProxyClientFactory):
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClientFactory.__init__(self, command, rest, version,
                headers, data, father)

    def buildProtocol(self, addr):
        return LoggingProxyClient(self.command, self.rest, self.version,
                self.headers, self.data, self.father)

class LoggingProxyRequest(proxy.ProxyRequest):
    protocols = {'http': LoggingProxyClientFactory}

    def requestReceived(self, command, path, version):
        print "REQ:", command, path, version
        headers = self.getAllHeaders()
        for h in headers:
            print "REQ: %s: %s" % (h, headers[h])
        print
        proxy.ProxyRequest.requestReceived(self, command, path, version)

class LoggingProxy(proxy.Proxy):
    requestFactory = LoggingProxyRequest

class LoggingProxyFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        return LoggingProxy()

reactor.listenTCP(8080, LoggingProxyFactory())
reactor.run()
