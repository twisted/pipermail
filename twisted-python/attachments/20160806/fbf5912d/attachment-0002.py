#!/usr/bin/python
## Uses a DeferredList to asynchronously fetch a number of pages
## Note: has problems if too much pages are being fetched async
import sys,re,json,feedparser
from time import strftime
from datetime import datetime
# sys.path.append("rawdog")
from   twisted.internet import reactor
from   twisted.internet.task import deferLater
from   twisted.python import log
from   twisted.web.http_headers import Headers
from   twisted.python.util import println
import twisted.web.client as client
from   twisted.internet.ssl import ClientContextFactory
from   twisted.internet.defer import setDebugging, Deferred, DeferredList, DeferredSemaphore, gatherResults
import psycopg2

# http://txpostgres.readthedocs.org/

global DEBUG_MODE
global agent

DEBUG_MODE=True
setDebugging(DEBUG_MODE)

TIMEOUT_HTTP_CLIENT=3.0
REDIRECT_LIMIT=3
CUSTOM_USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36'
pool = client.HTTPConnectionPool(reactor)
# add HTTPS policy, set timeout
baseAgent = client.Agent(reactor, contextFactory=client.BrowserLikePolicyForHTTPS(), connectTimeout=TIMEOUT_HTTP_CLIENT, pool=pool)
# follow redirects (with max limit)
agent = client.BrowserLikeRedirectAgent(baseAgent, redirectLimit=REDIRECT_LIMIT)
# support compression
agent = client.ContentDecoderAgent(agent, [(b'gzip', client.GzipDecoder)])

def getPage(url):
    d = agent.request(
            'GET',
            url,
            Headers({
                'User-Agent': [CUSTOM_USER_AGENT],
                # 'Accept-Encoding': ['gzip, deflate'],
                }),
            None,
            )
    d.addCallback(lambda out: out).addCallback(lambda resp: client.readBody(resp))
    d.addErrback(lambda err: err)
    return d

def set_up_client():
    # set up client with:
    #
    # set Twisted debug level
    # connect to the db
    DEBUG_MODE = True
    setDebugging(DEBUG_MODE)
    log.startLogging(sys.stdout)
    # db connection and deferred

def clean_up_and_exit(*args, **kwargs):
    # print "clean_up_and_exit"
    # print args

    log.msg('clean_up_and_exit')
    reactor.stop()

def parse_date(date1, date2):
    # edge-case for feed
    # pubdate is assumed to be a time.struct_time here
    pubdate_fmt = None

    pubdate = date1
    if pubdate:
        try:
            pubdate_fmt = strftime('%Y-%m-%d %H:%M:%S +0000',pubdate)
        except Exception, e:
            print e
            pubdate = None

    # edge-case for atom feed
    # e.get('updated') 2011-02-01T20:21:42+00:00
    pubdate = date2
    if pubdate and not pubdate_fmt:
        try:
            i1 = pubdate[:19]
            i1 = datetime.strptime(i1, "%Y-%m-%dT%H:%M:%S")
            pubdate_fmt = i1.strftime('%Y-%m-%d %H:%M:%S +0000')
        except Exception, e:
            print e
            pubdate = None

    return pubdate_fmt

# parse feeds
def store_fetched_data(data):
    # log.msg(data)
    # reactor.callLater(0, lambda a,b: None, 0, d)
    if data:
        query_data = []
        log.msg('store_fetched_data')
        for f in data:
            if 'response' in f and f['response'] is not None:
                try:
                    r = f['response']
                    # log.msg('len response: ' + str(len(r)))
                    feed = feedparser.parse(r)
                    if 'entries' in feed:
                        log.msg('entries: ' + str(len(feed['entries'])))
                        for e in feed['entries']:
                            try:
                                title = e.get('title','')
                                summary = e.get('summary','')

                                date1 = e.get('published_parsed',None)
                                date2 = e.get('updated', None)

                                pubdate_fmt = parse_date(date1, date2)

                                if not pubdate_fmt:
                                    continue

                                # query_data.append((e['title'],e['summary'],pubdate_fmt,))
                                # log.msg('cnt:' + str(cnt))
                                query_data.append({
                                    'title': title,
                                    'summary': summary,
                                    'pubdate': pubdate_fmt,
                                    })
                            except Exception, e:
                                print e
                                pass
                except Exception, e:
                    print e
                    pass
            else:
                print 'feed with empty response'

        len_query_data = len(query_data)
        if len_query_data == 0:
            pass
        else:
            pass
    else:
        # the request was empty
        print 'store_fetched_data received None'
        pass

def fetch_single(feed_meta=None):

    def fetched_callback(r):
        feed_complete_data = feed_meta
        feed_complete_data['response'] = r
        return feed_complete_data

    print "scheduling new request ", feed_meta
    d = getPage(feed_meta['feed_url'])
    d.addCallback(fetched_callback)
    d.addErrback(fetched_callback)
    return d


def batch_gen(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

def fetch_all(feeds):
    BATCH_SIZE=5
    batches = []
    for feeds_batch in batch_gen(feeds, BATCH_SIZE):
        sem = DeferredSemaphore(len(feeds_batch))
        batch = []
        for feed_ in feeds_batch:
            batch.append(sem.run(fetch_single, feed_meta=feed_))
        batchDef = gatherResults(batch, consumeErrors=False)
        batchDef.addCallback(store_fetched_data)
        batches.append(batchDef)

    # rendez-vous for all feeds that were fetched
    batchesDef = gatherResults(batches, consumeErrors=False)

    batchesDef.addCallbacks(
            clean_up_and_exit,
            errback=lambda x: None,
            )
    return batchesDef

def parse_feed_config_line(line):
    parts = re.split(r'\s+', line)
    url = parts[0]
    tags = map(lambda t: re.sub('[\'"]+','', t), parts[1:])
    return {
            'feed_url': url,
            'tags': tags,
            }

def parse_config_data(path=None):
    feeds = []

    with open('./urls','r') as f:
        entrylim = 99999999
        # entrylim = 3
        entrynum = 1
        for line in f:
            if re.match(r'^http', line):
                line = line.rstrip()
                o = parse_feed_config_line(line)
                feeds.append(o)
                entrynum += 1
                if entrynum > entrylim:
                    break

    return feeds

set_up_client()
feeds_metadata = parse_config_data('urls')
d = fetch_all(feeds_metadata)
reactor.run()

