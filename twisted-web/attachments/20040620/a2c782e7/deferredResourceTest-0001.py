'''
Returning a deferred from getDynamicChild doesn't work
'''   

from twisted.application import service
from twisted.application import internet
from nevow import appserver, rend, tags, loaders
from nevow.stan import directive
from twisted.internet import defer
                                                                                                                                                                                  
class ChildPage(rend.Page):
                                                                                                                                                                                  
    def __init__(self, number):
        self.number = number
        rend.Page.__init__(self)
                                                                                                                                                                                  
    docFactory = loaders.stan(tags.html[
        tags.body[
            tags.h1["I was deferred by my parent"],
            tags.p(render = directive("number"))
        ]
    ])
                                                                                                                                                                                  
    def render_number(self, context, data):
        return context.tag["My number is %d" % self.number]
                                                                                                                                                                                  
class ParentPage(rend.Page):
                                                                                                                                                                                  
    docFactory = loaders.stan(tags.html[
        tags.body[
            tags.h1["I have a deferred child"]
        ]
    ])
                                                                                                                                                                                  
    def getDynamicChild(self, name, request):
        d = defer.succeed(3)
        d.addCallback(ChildPage)
        return d
                                                                                                                                                                                  
application = service.Application("test deferred child")
internet.TCPServer(
    8080,
    appserver.NevowSite(
        ParentPage()
    )
).setServiceParent(application)
