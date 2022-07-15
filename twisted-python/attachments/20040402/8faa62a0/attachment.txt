from twisted.internet import reactor, protocol, defer
from twisted.web import client
import out
import cStringIO as _StringIO

#
# The problem is at about the 400 (more or less)  body downloaded
# since Twisted locks and I need to press Ctrl+C to unlock it
# Using strace you can see that at the moment of locking, although
# there is no download in progress, there are over 300 sockets already
# watched in the main select.
# looking with spewer you can see that it locks when closing a socket
#

NUM=0

def printer(data, args=None):
    global NUM
    print 'got data', NUM
    return data

def transf(data, args=None):
    transfd_data = _StringIO.StringIO(str(data))
    return transfd_data

def gotError(data, args=None):
    global NUM
    print 'got error'
    return

def ender(data,args=None):
    global NUM
    NUM += 1
    if NUM > len(out.rss_feed):
        reactor.stop()
def main():
    for i in out.rss_feed:
        d = client.getPage(i[0])
        d.addCallback(printer)
        d.addErrback(gotError)
        d.addCallback(transf)
        d.addErrback(gotError)
        d.addCallback(ender)
        d.addErrback(gotError)
    print "finished setting all deferreds"
main()
reactor.run()
