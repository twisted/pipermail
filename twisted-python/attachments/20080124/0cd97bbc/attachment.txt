"""
inlineExample.py

A simple example to see if I can use inlinecallbacks from an RequestHandler

"""


from twisted.web                         import http, client
from twisted.internet                    import defer


def gotPage(result):
    print result
    return defer.returnValue(result)


class MyRequestHandler(http.Request):
    
    @defer.inlineCallbacks
    def __process__(self):
        
        aResult = yield client.getPage("http://localhost").addCallback(gotPage)
       
        self.setHeader('Content-Type', 'text/html')    
        self.write(aResult)
        self.finish()


    def process(self):
        """
        I want process to wait until client.getPage is finished.
        
        """
        self.__process__()


class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp

if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.listenTCP(8000, MyHttpFactory())
    print "server running"
    reactor.run()
