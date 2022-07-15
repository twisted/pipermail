import types
from twisted.internet import defer, reactor
from twisted.python.util import mergeFunctionMetadata

def altInlineCallbacks(f):
    def unwindGenerator(*args, **kwargs):
        deferred = defer.Deferred()
        try:
            result = f(*args, **kwargs)
        except Exception, e:
            deferred.errback(e)
            return deferred
        if isinstance(result, types.GeneratorType):
            return defer._inlineCallbacks(None, result, deferred)
        deferred.callback(result)
        return deferred
            
    return mergeFunctionMetadata(f, unwindGenerator)

@altInlineCallbacks
def f0():
    # This causes mayhem with the normal inlineCallbacks
    class yes():
        def send(x, y):
            print 'yes'
    return yes()

@altInlineCallbacks
def f1():
    return 'hey'

@altInlineCallbacks
def f2():
    raise Exception('whoops!')

@altInlineCallbacks
def f3():
    if True:
        raise Exception('ouch!')
    d = defer.Deferred()
    reactor.callLater(0, d.callback, None)
    yield d

@altInlineCallbacks
def f4():
    d = defer.Deferred()
    reactor.callLater(0, d.callback, None)
    yield d

def ok(result, name):
    print '%s ok: %s' % (name, result)

def fail(failure, name):
    print '%s fail: %s' % (name, failure)

def stop(_):
    reactor.stop()
    
def main():
    L = []
    for func in f0, f1, f2, f3, f4:
        name = func.__name__
        L.append(func().addCallbacks(
            ok, fail, callbackArgs=[name], errbackArgs=[name]))
    d = defer.DeferredList(L)
    d.addBoth(stop)
    

if __name__ == '__main__':
    reactor.callLater(0, main)
    reactor.run()
