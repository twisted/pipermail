from twisted.web import server, resource, template, client
from twisted.internet import reactor

import pprint

class ElementResource(resource.Resource, template.Element):
        
    isLeaf = True
    loader = template.XMLString("""<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1"><t:transparent t:render="whatever"/></html>""")
    
    @template.renderer
    def whatever(self, request, tag):
        return 'whatever'             
    
    def render_GET(self, request):        
        d = template.flattenString(request, self)  
        d.addCallback(request.write)
        d.addCallback(lambda ign: request.finish())
        return server.NOT_DONE_YET


site = server.Site(ElementResource())

def test():
    d = client.getPage('http://localhost:6789')
    d.addCallback(lambda res: pprint.pprint(res))
    d.addErrback(lambda err: pprint.pprint(err.getErrorMessage()))

if __name__ == '__main__':    
    reactor.listenTCP(6789, site)
    reactor.callWhenRunning(test)
    reactor.run()