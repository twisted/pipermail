
import os, sha
import defgen

from twisted.internet import defer
from twisted.python import log, util

def sleep(n):
    from twisted.internet import reactor
    d = defer.Deferred()
    reactor.callLater(n, d.callback, None)
    return d

def recursivelyIterate(iterator, rate=0.01):
    stack = [iterator]
    while stack:
        g = stack.pop()
        try:
            v = g.next()
        except StopIteration:
            pass
        else:
            stack.append(g)
            if isinstance(v, defer.Deferred):
                yield defgen.waitForDeferred(v)
            else:
                try:
                    i = iter(v)
                except TypeError:
                    pass
                else:
                    stack.append(i)
        yield defgen.waitForDeferred(sleep(rate))
recursivelyIterate = defgen.deferredGenerator(recursivelyIterate)

def walk(root, visitor, *a, **kw):
    for f in os.listdir(root):
        f = os.path.join(root, f)
        if os.path.isdir(f):
            yield defgen.waitForDeferred(walk2(f, visitor, *a, **kw))
        else:
            yield defgen.waitForDeferred(visitor(f, *a, **kw))
walk2 = defgen.deferredGenerator(walk)

def hash(filename, result):
    if os.path.isfile(filename):
        hashObj = sha.sha()
        fObj = file(filename)
        for bytes in iter(lambda: fObj.read(8192), ''):
            hashObj.update(bytes)
            yield None
        fObj.close()
        result(filename, hashObj.digest())
hash = defgen.deferredGenerator(hash)

def main(path='.'):
    from twisted.internet import reactor
    w = walk(path, 
             hash, 
             lambda f, h: util.println("%s: %s" % (f, h.encode('hex'))))
    recursivelyIterate(w
        ).addErrback(log.err
        ).addBoth(lambda r: reactor.stop()
        )
    reactor.run()

if __name__ == '__main__':
    main()
