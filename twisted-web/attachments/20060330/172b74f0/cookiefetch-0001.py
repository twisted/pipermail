from twisted.web import client
from twisted.internet import reactor

import cookielib
import urllib2

    
class HTTPCookiePageGetter(client.HTTPPageGetter):
    """ HTTP Client Protocol implementation that uses the cookiejar
    module for handling cookies."""
    
    def connectionMade(self):
        # We send our cookies from the cookie jar. We cannot easily
        # hook into this method, so we override it completely.

        method = getattr(self.factory, 'method', 'GET')
        self.sendCommand(method, self.factory.path)
        self.sendHeader('Host', self.factory.headers.get("host", self.factory.host))
        self.sendHeader('User-Agent', self.factory.agent)

        req = urllib2.Request(self.factory.url)
        self.factory.jar.add_cookie_header(req)

        for k, v in req.unredirected_hdrs.items():
            self.sendHeader(k, v)

        data = getattr(self.factory, 'postdata', None)
        if data is not None:
            self.sendHeader("Content-Length", str(len(data)))
        for (key, value) in self.factory.headers.items():
            if key.lower() != "content-length":
                # we calculated it on our own
                self.sendHeader(key, value)
        self.endHeaders()
        self.headers = {}
        
        if data is not None:
            self.transport.write(data)
        return
    
    
class HTTPWithCookie(client.HTTPClientFactory):
    """ A HTTP Client Factory that can update and use a CookieJar from
    cookielib."""
    
    protocol = HTTPCookiePageGetter

    def __init__(self, url, jar, *args, **kwargs):
        client.HTTPClientFactory.__init__(self, url, *args, **kwargs)

        self.jar = jar
        return
    
    def gotHeaders(self, headers):
        # Simulate the Reponse object from urllib2, so that we can use
        # the extract_cookies method from cookiejar. Yuck.
        class _Response(object):
            def info(self):
                class _Meta(object):
                    def getheaders(self, name):
                        return headers.get(name.lower(), [])
                return _Meta()
                
        self.jar.extract_cookies(_Response(), urllib2.Request(url))

        return client.HTTPClientFactory.gotHeaders(self, headers)



if __name__ == '__main__':
    import sys

    url = sys.argv[1]

    cookies = cookielib.CookieJar()


    def dump(data):
        print "Yay, received %s bytes!" % len(data)
        print "Your cookie box contains", cookies
        
        reactor.stop()

    def err(failure):
        print "Arrrrg", failure.getErrorMessage()
        reactor.stop()



    scheme, host, port, path = client._parse(url)
    assert scheme == 'http'

    factory = HTTPWithCookie(url, cookies)
    reactor.connectTCP(host, port, factory)

    factory.deferred.addCallback(dump).addErrback(err)
    reactor.run()
