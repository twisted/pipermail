from twisted.internet import reactor, defer

def do_something_inbetween(x):
    print "doing something else: ", x
    return "done something else"

def print_something(x):
    print "printing: ", x
    d = defer.Deferred()
    d.addCallbacks(do_something_inbetween, oops, ("printed something"))
    return d

def finish_up(x):
    print "finishing up with: ", x

def oops(e):
    print str(e)

print "constructed deferred"
d = defer.Deferred()
d.addCallbacks(print_something)
d.addCallbacks(finish_up)
d.addErrback(oops)
reactor.callLater(1, d.callback, "hello mr")
reactor.callLater(5, reactor.stop)
print "setup everything"
reactor.run()
