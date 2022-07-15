from twisted.web import server, resource, template, client
from twisted.internet import reactor, defer, threads

import time
import pprint

blocking_first = """<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1"> Blocking:<t:transparent t:render="blocking"/>Non-blocking:<t:transparent t:render="non_blocking"/></html>"""
blocking_second = """<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1"> Non-blocking:<t:transparent t:render="non_blocking"/>Blocking:<t:transparent t:render="blocking"/></html>"""

class ExampleTemplate(template.Element):
    
    loader = template.XMLString(blocking_second)
    
    def non_blocking_call(self):
        print 'called non-blocking'
        d = defer.Deferred()
        d.addCallback(lambda ign: str(int(time.time())))
        reactor.callLater(2, d.callback, None)
        return d

    def blocking_call(self):
        print 'called blocking'
        time.sleep(2)
        return str(int(time.time()))    

    @template.renderer
    def blocking(self, request, tag):
        '''
        switch to 
        yield threads.deferToThread(self.blocking_call)
        to unblock
        '''
        return self.blocking_call()
    
    @template.renderer
    def non_blocking(self, request, tag):        
        yield self.non_blocking_call()

class ExampleResource(resource.Resource):
    
    isLeaf = True         
    
    def render_GET(self, request):   
        print 'get:', int(time.time())     
        d = template.flattenString(request, ExampleTemplate())  
        d.addCallback(request.write)
        d.addCallback(lambda ign: request.finish())
        return server.NOT_DONE_YET

site = server.Site(ExampleResource())

def simulataneous():
    dl = defer.DeferredList([client.getPage('http://localhost:6789'), client.getPage('http://localhost:6789')])
    dl.addCallback(lambda res: [pprint.pprint(ans[1]) for ans in res ])
    dl.addErrback(lambda err: pprint.pprint(err))

if __name__ == '__main__':    
    reactor.listenTCP(6789, site)
    reactor.callWhenRunning(simulataneous)
    reactor.run()