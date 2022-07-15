from twisted.web import server, resource, template, client
from twisted.internet import reactor, defer

import pprint

class ExampleTemplate(template.Element):
    
    loader = template.XMLString("""<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">result:<t:transparent t:render="result"/></html>""")

    @template.renderer
    def result(self, request, tag):
        return request.result

class ExampleResource(resource.Resource):
    
    inventory = { 'item' : 1 }    
    isLeaf = True
    
    def shop(self, act, item, request):
        if act == 'buy':
            if item in self.inventory.keys() and self.inventory[item] > 0:
                self.inventory[item] += -1 
                request.result = "Bought"
            else:
                request.result = "Unavailable"
        elif act == 'sell':
            if item in self.inventory.keys():
                self.inventory[item] += 1
            else:
                self.inventory[item] = 1
            request.result = "Sold"
        else:
            request.result = "Can't " + act + " here"
    
    def render_GET(self, request):
        d = defer.DeferredLock().run(self.shop, request.args['action'][0], request.args['action'][1], request)     
        d.addCallback(lambda ign: template.flattenString(request, ExampleTemplate()))  
        d.addCallback(request.write)
        d.addCallback(lambda ign: request.finish())
        return server.NOT_DONE_YET

site = server.Site(ExampleResource())

def simulataneous():
    dl = defer.DeferredList([client.getPage('http://localhost:6789?action=buy&action=item'),client.getPage('http://localhost:6789?action=buy&action=item'),client.getPage('http://localhost:6789?action=sell&action=item'),client.getPage('http://localhost:6789?action=buy&action=item')])
    dl.addCallback(lambda res: [pprint.pprint(ans[1]) for ans in res])
    dl.addErrback(lambda err: pprint.pprint(err))

if __name__ == '__main__':    
    reactor.listenTCP(6789, site)
    reactor.callWhenRunning(simulataneous)
    reactor.run()