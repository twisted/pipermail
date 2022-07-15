from twisted.internet import reactor, defer

def do_something_inbetween(x):
    print "doing something else: ", x
    return "done something else"

def print_something(x):
    print "printing: ", x
    d = defer.maybeDeferred(do_something_inbetween,'printed something')
    d.addCallbacks(finish_up, oops)
    return d

def finish_up(x):
    print "finishing up with: ", x
    return x

def oops(e):
    print str(e)

def go():
    print "constructed deferred"
    d = defer.Deferred()
    return d

def extra(r):
    print 'extra', r
    return r

d = go()
d.addCallback(print_something)
d.addCallback(extra)
d.addErrback(oops)
reactor.callLater(1, d.callback, "hello mr")
reactor.callLater(5, reactor.stop)
print "setup everything"
reactor.run()
