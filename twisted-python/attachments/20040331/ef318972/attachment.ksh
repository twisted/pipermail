from twisted.internet import reactor, protocol, defer
from twisted.web import client
import feedparser, time, out

rss_feeds = out.rss_feed
# This is the default site list
#rss_feeds = [('http://www.nongnu.org/straw/news.rss','straw'),
#             ('http://googlenews.74d.com/rss/google_it.rss','google'),
#             ('http://www.pythonware.com/daily/rss.xml','pythonware'),
#             ('http://www.theinquirer.net/inquirer.rss','inq'),
#             ('http://www.groklaw.net/backend/GrokLaw.rdf','grok'),
#             ('http://www.livejournal.com/users/moshez/data/rss','zadka'),
#             ('http://www.pythonware.com/news.rdf','pwn')]

# michele@berthold.com

INTER_QUERY_TIME = 300

class FeederProtocol(object):
    def __init__(self):
        self.parsed = 0
        
        # This dict structure will be the following:
        # { 'URL': (TIMESTAMP, value) }
        self.cache = {}
        
    def gotError(self, data=None, extra_args=None):
        # An Error as occurred, print traceback infos and go on
        print data
        self.parsed += 1
        print "="*20
        print "Trying to go on..."
        
    def getFeeds(self, where=None):
        #print "getting feeds"
        # This is to get the feeds we want
        if not where: # We don't have a database, then we use the local
                      # variabile rss_feeds
            return rss_feeds
        else: return None

    def memoize(self, feed, site=None, extra=None):
        # extra is the second element of each tuple of rss_feeds
        # site is the address of the feed, also the first element of each tuple
        # of rss_feeds
        print "Memoizing",site,"..."
        self.cache.setdefault(site, (time.time(),feed))
        return feed
    
    def stopWorking(self, data=None):
        print "Closing connection number %d..."%(self.parsed,)
        print "-"*20
        
        # This is here only for testing. When a protocol/interface will be
        # created to communicate with this rss-aggregator server, we won't need
        # to die after we parsed some feeds just one time.
        self.parsed += 1
        if self.parsed >= len(rss_feeds):
            print "Closing all..."
            #for i in self.cache:
            #    print i
            print time.time()-tp
            #reactor.stop()

    def getPageFromMemory(self, key=None):
        #print "getting from memory"
        
        # Getting the second element of the tuple which is the parsed structure
        # of the feed at address key, the first element of the tuple is the
        # timestamp
        d = defer.succeed(self.cache.get(key,key)[1])
        return d    

    def parseFeed(self, feed):
        # This is self explaining :)
        return feedparser.parse(feed)
   
    def startDownloading(self, site):
        #print "Looking if",site[0],"cached...",
        
        # Try to get the tuple (TIMESTAMP, FEED_STRUCT) from the dict if it has
        # already been downloaded. Otherwise assign None to already_got
        already_got = self.cache.get(site[0], None)

        # Ok guys, we got it cached, let's see what we will do
        if already_got:
            
            # Well, it's cached, but will it be recent enough?
            #print "It is\n Looking if timestamp for",site[0],"is recent enough...",
            elapsed_time = time.time() - already_got[0]
            
            # Woooohooo it is, elapsed_time is less than INTER_QUERY_TIME so I
            # can get the page from the memory, recent enough
            if elapsed_time < INTER_QUERY_TIME:
                #print "It is"
                return self.getPageFromMemory(site[0])
            else:
                
                # Uhmmm... actually it's a bit old, I'm going to get it from the
                # Net then, then I'll parse it and then I'll try to memoize it
                # again
                #print "Getting",site[0],"from the Net because old"
                return self.downloadPage(site)
        else: 
            
            # Well... We hadn't it cached in, so we need to get it from the Net
            # now, It's useless to check if it's recent enough, it's not there.
            #print "Getting",site[0],"from the Net"    
            return self.downloadPage(site)

    def downloadPage(self, site):  
        #print "Now downloading..."
        # Self-explanatory
        d = client.getPage(site[0])

        # Uncomment the following if you want to make everything crash :), since
        # it will save the feed on a file, but with the memoize feature it will
        # crash everything cuz it will break the get-->parse-->memoize chain
        #d = client.downloadPage(site[0],site[1])
        
        # Parse the feed and if there's some errors call self.gotError
        d.addCallbacks(self.parseFeed, self.gotError)
        
        # Now memoize it, if there's some error call self.getError
        d.addCallbacks(self.memoize, self.gotError, site)
        return d
    
    def workOnPage(self, parsed_feed=None, site=None, extra_args=None,
            extra_key=None):
        print "-"*20
        #print "finished retrieving"
        print "Feed Version:",parsed_feed.get('version','Unknown')
        
        #
        #  Uncomment the following if you want to print the feeds
        #
        chan = parsed_feed.get('channel', None)
        if chan:
            print chan.get('title', '')
            #print chan.get('link', '')
            #print chan.get('tagline', '')
            #print chan.get('description','')
        print "-"*20
        #items = parsed_feed.get('items', None)
        #if items:
        #    for item in items:
        #        print '\tTitle: ', item.get('title','')
        #        print '\tDate: ', item.get('date', '')
        #        print '\tLink: ', item.get('link', '')
        #        print '\tDescription: ', item.get('description', '')
        #        print '\tSummary: ', item.get('summary','')
        #        print "-"*20
        #print "got",site
        #print "="*40
        
    def start(self, data=None):
        # Here we gather all the urls for the feeds
        #self.factory.tries += 1
        for feed in self.getFeeds():
        
            # Now we start telling the reactor that it has
            # to get all the feeds one by one...
            d = self.startDownloading(feed)
            
            # The it will pass the result of
            # startDownloading to workOnPage (this is hidden in twisted)
            # together with the feed url (just to use some extra infos
            # in the workOnPage method)
            d.addCallbacks(self.workOnPage, self.gotError, feed)
            
            # And when the for loop is ended we put 
            # stopWorking on the callback for the last 
            # feed gathered
            d.addCallbacks(self.stopWorking, self.gotError)

        # This is to try the memoize feature
        #if self.factory.tries<3:
        #    d.addCallback(self.start)    

class FeederFactory(protocol.ClientFactory):
    protocol = FeederProtocol()
    def __init__(self):
        # tries is used to make more connection to use the
        # memoizing feature
        #self.tries = 0
        
        # Here we put in the FeederProtocol instance a reference to
        # FeederFactory under the name of self.factory (seen from protocol)
        self.protocol.factory = self
        self.protocol.start()

f = FeederFactory()
tp = time.time()
reactor.run()
