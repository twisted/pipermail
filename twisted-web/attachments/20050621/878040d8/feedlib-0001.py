# feedlib.py: Super-liberal and somewhat rude feedfinder. Need to
# add code for handling robots.txt.

# Derivative library from M. Pilgrims's feedfinder.py and D. Mertz's
# url-regexp from __Text_Processing_in_Python__. 
# 

# Maintained by Richard Frank Meraz rfmeraz@gmail.com

import sgmllib, urllib, urlparse, re


# regexp for url is public domain from D. Mertz
# in __Text Processing in Python__ p. 228. (Thanks David!)

pat_url = r'''   (?x)( # verbose identify URLs within text
                (http) # make sure we find a resource type
                   :// # ...needs to be followed by colon-slash-slash
        (\w+[:.]?){2,} # at least two domain groups, e.g. (gnosis.)(cx)
                  (/?| # could be just the domain name (maybe w/ slash)
            [^ \n\r">]+ # or stuff then space, newline, tab, quote
                [\w/]) # resource name ends in alphanumeric or slash
     (?=[\s\.,>)'"\]]) # assert: followed by white or clause ending
                     ) # end of match group
                       '''
re_url = re.compile(pat_url)

def extract_urls(_str):
    '''Extract all URLS from arbitrary string'''
    return [u[0] for u in re.findall(re_url,_str)]

##-- These are modified from M. Pilgrim's feedfinder.py
 
class BaseParser(sgmllib.SGMLParser):
    def __init__(self, baseuri):
        sgmllib.SGMLParser.__init__(self)
        self.links = []
        self.baseuri = baseuri
        
    def normalize_attrs(self, attrs):
        attrs = [(k.lower(), sgmllib.charref.sub(lambda m: chr(int(m.groups()[0])), v).strip()) for k, v in attrs]
        attrs = [(k, k in ('rel','type') and v.lower() or v) for k, v in attrs]
        return attrs
        
    def do_base(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('href'): return
        self.baseuri = attrsD['href']
        
class LinkParser(BaseParser):
    FEED_TYPES = ('application/rss+xml',
                  'text/xml',
                  'application/atom+xml',
                  'application/x.atom+xml',
                  'application/x-atom+xml')
    def do_link(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('rel'): return
        rels = attrsD['rel'].split()
        if 'alternate' not in rels: return
        if attrsD.get('type') not in self.FEED_TYPES: return
        if not attrsD.has_key('href'): return
        self.links.append(urlparse.urljoin(self.baseuri, attrsD['href']))

class ALinkParser(BaseParser):
    def start_a(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('href'): return
        self.links.append(urlparse.urljoin(self.baseuri, attrsD['href']))

# Modified by RFM rfmeraz@gmail.com
def getLinks(data, baseuri):
    try:
        p = LinkParser(baseuri)
        p.feed(data)
        return p.links 
    except:
        return []

# Modified by RFM rfmeraz@gmail.com
def getALinks(data, baseuri):
    try:
        p = ALinkParser(baseuri)
        p.feed(data)
        return p.links 
    except:
        return []

# Modified by RFM rfmeraz@gmail.com
# Smarter algorithm for determing local links.
def getLocalLinks(links, baseuri):
    '''Get local-links where locality is determined by matching basuri
    or more liberally by guessing the significant portion of the
    hostname and looking for its presence in the link. Eg. in www.yahoo.com
    the significant portion would be yahoo'''
    baseuri = baseuri.lower()
    host = urlparse.urlparse(baseuri)[1]
    parts = host.split(':')
    if len(parts) >=  3:
        host = parts[1]
    else:
        host = parts[0]
    return [l for l in links
            if l.lower().startswith(baseuri) or host in l]

# Modified by RFM rfmeraz@gmail.com
# Added fix for twisted.web.client bug (?) where baseuris that point to a
# directory (virtual or otherwise) choke if they are not terminated
# with a forward slash.  
def makeFullURI(uri):
    if (not uri.startswith('http://')) and (not uri.startswith('https://')):
        uri = 'http://%s' % uri
    if not '/' in urlparse.urlparse(uri)[2]:
        uri += '/'
    return uri

def isFeedLink(link):
    '''Canonical file-extensions for syndication content'''
    return link[-4:].lower() in ('.rss', '.rdf', '.xml', '.atom')

def isXMLRelatedLink(link):
    '''Heuristic for guessing whether a link might lead to syndication
    content'''
    link = link.lower()
    return link.count('rss') + link.count('rdf') + link.count('xml') + link.count('atom') 

def couldBeFeedData(data):
    '''Determine whether given string is feeddata by looking for
    xml syndication tags'''
    data = data.lower()
    if data.count('<html'): return 0
    return data.count('<rss') + data.count('<rdf') + data.count('<feed')


if __name__ == '__main__':
    # Library usage (rfmeraz@gmail.com for questions)

    import urllib

    # If url is not full make it so:
    uri = makeFullURI('news.yahoo.com')

    # Get the data somehow.
    data = urllib.urlopen(uri).read()

    # Now start the processing chain.
    # This example uses synchronous network IO for instructional
    # purposes.  Use asyncore.py or twisted to do this right.

    rawurls = extract_urls(data)
    links = getLinks(data,uri)
    alinks = getALinks(data,uri)
    all_links = set(rawurls + links + alinks)

    isFeed = lambda uri: couldBeFeedData(urllib.urlopen(uri).read())

    # Depth 1 crawl stops here. Recurse on links in these pages if
    # you want crawl deeper.
    feeds = [l for l in all_links if isXMLRelatedLink(l) and isFeed(l)]
    print str(feeds)
    

            
        
    
    

    
    
