import time
from nevow import rend
from nevow import inevow
from nevow import tags as T

class HelloPage(rend.Page):
    docFactory = rend.htmlfile('example1.html')
    
    def data_title(self, context, data):
        return "Hello Nevow World"
    
    def render_timestamp(self, context, data):
        return time.strftime('%c %Z')

def printPage():
    p = HelloPage()
    # Ordinarily this remembering nonsense is done for us.
    p.remember(p, inevow.IData)
    p.remember(p, inevow.IRendererFactory)
    # Rend.Page.renderString() returns a deferred, so...
    def gotRenderedPage(html):
        print
        print 'Page:'
        print html
    p.renderString().addCallback(gotRenderedPage)

from nevow import appserver
from twisted.application import service
from twisted.application import internet

root_resource = HelloPage()
application = service.Application('example1')
webservice = internet.TCPServer(8080, appserver.NevowSite(root_resource))
webservice.setServiceParent(application)

if __name__ == '__main__':
    printPage()
