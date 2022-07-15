from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site
from twisted.internet import reactor, defer, threads
from twisted.web.xmlrpc import Proxy
from twisted.web.xmlrpc import XMLRPC
from twisted.web.client import getPage

import time
import xmlrpclib

class TestResource(Resource):
    
    isLeaf = True
    
    def render_ERROR(self, err, request):
        print 'xmlrpc error:', self.__class__.__name__, err
        request.finish()
            
    def render_TIMESTAMP(self, ts, request):
        request.write(str(ts))
        request.finish()

    def render_GET(self, request):
        print 'test:', int(time.time())
        d = Proxy('http://localhost:8082').callRemote('timestamp')
        d.addCallback(self.render_TIMESTAMP, request)
        d.addErrback(self.render_ERROR, request)
        return NOT_DONE_YET    

class Test1Resource(TestResource):
         
    isLeaf = True
    
    def render_GET(self, request):
        print 'test1:', int(time.time())        
        d = threads.deferToThread(xmlrpclib.ServerProxy("http://localhost:8082").timestamp)
        d.addCallback(self.render_TIMESTAMP, request)
        d.addErrback(self.render_ERROR, request)
        return NOT_DONE_YET

class Test2Resource(XMLRPC):
    
    def delayed_html(self):
        time.sleep(5)
        return int(time.time())
    
    def xmlrpc_timestamp(self):        
        print 'timestamp:', int(time.time())
        '''
        blocking!!!!!!
        return self.delayed_html()
        '''         
        return threads.deferToThread(self.delayed_html)
 
def done_or_error(ans = None):
    print 'done_or_error:', ans
    reactor.stop()
    
def results(res, init_time):
    print init_time, res[0][1], res[1][1], res[2][1], res[3][1], int(time.time()) 
 
def quad_request():
    init_time = int(time.time())
    dl = defer.DeferredList([getPage('http://localhost:8080'), getPage('http://localhost:8080'), getPage('http://localhost:8081'), getPage('http://localhost:8081')])
    dl.addCallback(results, init_time)
    dl.addBoth(done_or_error)
 
if __name__ == '__main__':
    print 'start reactor'
    reactor.listenTCP(8080, Site(TestResource()))
    reactor.listenTCP(8081, Site(Test1Resource()))
    reactor.listenTCP(8082, Site(Test2Resource()))
    reactor.callWhenRunning(quad_request)    
    reactor.run()