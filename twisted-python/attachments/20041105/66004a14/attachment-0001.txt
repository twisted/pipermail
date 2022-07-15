import feedparser

from twisted.internet   import reactor
from twisted.web.client import HTTPClientFactory

class pageGetter(HTTPClientFactory):
    def __init__(self, url):
        headers = None
        HTTPClientFactory.__init__(self, url, headers=headers, agent="Audry" )

    def page(self, page):
        if self.waiting:
            self.waiting = 0
            self.error = ''
            reactor.callLater(0, ProcessFeed, page, self)

    def noPage(self, reason):
        if self.waiting:
            self.waiting = 0
            self.error = reason
            page = ''
            reactor.callLater(0, ProcessFeed, page, self)

    def clientConnectionFailed(self, _, reason):
        if self.waiting:
            self.waiting = 0
            self.error = reason
            page = ''
            reactor.callLater(0, ProcessFeed, page, self)

def ProcessFeed(page, getter):
    if getter.error:
        print 'feed retrieval failed: ', getter.error
    else:
        print 'Feed retrieved'
        print getter.response_headers
        print getter.version
        print getter.status
        print getter.message

        fp = file('test.xml', 'w')
        fp.write(str(page))
        fp.close()

        f = feedparser.parse(page)

        fp = file('test.txt', 'w')
        fp.write(str(f))
        fp.close()

    reactor.stop()

reactor.connectTCP('washingtonmonthly.com', 80, pageGetter('http://www.washingtonmonthly.com/index.rdf'))
reactor.run()


