from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site
from twisted.internet import reactor, defer
from twisted.web.client import getPage
import time

class DelayedResource(Resource):
    
    isLeaf = True
    
    def _delayedRender(self, request):
        request.write(str(int(time.time())))
        request.finish()

    def render_GET(self, request):
        d = deferLater(reactor, 5, lambda: request)
        d.addCallback(self._delayedRender)
        return NOT_DONE_YET
    
def results(res, init_time):
    print init_time, res[0][1], res[1][1], int(time.time())
    
def done_or_error(ans = None):
    print 'done_or_error:', ans
    reactor.stop() 

def double_request():
    init_time = int(time.time())
    dl = defer.DeferredList([getPage('http://localhost:8080'), getPage('http://localhost:8080')])
    dl.addCallback(results, init_time)
    dl.addBoth(done_or_error)

if __name__ == '__main__':
    reactor.listenTCP(8080, Site(DelayedResource()))
    reactor.callWhenRunning(double_request)
    print 'start reactor'
    reactor.run()