from twisted.web.client import getPage
from feedparser import FeedParser
from twisted.internet import reactor, threads

def parsePage(data):
    parser = FeedParser()
    d = threads.deferToThread(parser.feed, data)
    d.addCallback(lambda result: {'channel':parser.channel, 
                                  'items':parser.items})
    return d

def printResults(data):
    print data['channel'].get('title'), '\n'
    for i in data['items']: print i.get('title')

def parsePageAndPrint(data):
    d = parsePage(data)
    d.addCallback(printResults)
    d.addCallback(lambda printed: reactor.stop())

url = 'http://www.fettig.net/?flav=rss'
getPage(url).addCallback(parsePageAndPrint)
reactor.run()
