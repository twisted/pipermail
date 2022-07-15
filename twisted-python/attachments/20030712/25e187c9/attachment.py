from twisted.web.client import getPage
from feedparser import FeedParser
from twisted.internet import reactor, threads

def parsePageAndPrint(data):
    parser = FeedParser()
    parser.feed(data)
    print parser.channel.get('title'), '\n'
    for i in parser.items: print i.get('title')
    reactor.stop()

url = 'http://www.fettig.net/?flav=rss'
getPage(url).addCallback(parsePageAndPrint)
reactor.run()
