"""
inlineExample.py

Based on the example on page 41 of Abe Fettig's "Twisted Networking Programming
Essentials," this example uses an inclinecallback to allow the HTTP requestHandler
to make a twisted call and wait for the result.

"""


from twisted.web                         import http, client
from twisted.internet                    import defer


class MyRequestHandler(http.Request):
    
    @defer.inlineCallbacks
    def process(self):
        try:
            result = yield client.getPage("http://localhost")
        except Exception, err:
            log.err(err, "process getPage call failed")
        else:
            self.setHeader('Content-Type', 'text/html') 
            self.write(result)
            self.finish()
    

class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp

if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.listenTCP(8000, MyHttpFactory())
    print "server running"
    reactor.run()
