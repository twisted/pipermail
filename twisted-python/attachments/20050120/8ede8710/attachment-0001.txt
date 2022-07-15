from twisted.internet import reactor, defer

def _succeedForOneOf(cbResult, items, func, *args, **kw):
    if len(items) == 0:
        raise Exception("None Succeeded")
    return func(items[0], *args, **kw
        ).addErrback(_succeedForOneOf, items[1:], func, *args, **kw)

def succeedForOneOf(items, func, *args, **kw):
    """Try calling func(item, args, kw) for every
    item in the list of items until one of them succeeds.
    Return the successful results.  If none succeed,
    raise an Exception.
    """
    return _succeedForOneOf(None, items, func, *args, **kw)

def _print(x):
    print "%s is the winner" % x

def f(x):
    print x
    d = defer.Deferred()
    if x == 5:
        print "true"
        d.callback(x)
    else:
        print "false"
        d.errback(x)
    return d

l = [1,2,3,4,5,6,7]

succeedForOneOf(l, f).addCallback(_print).addBoth(lambda _: reactor.stop())
reactor.run()
