from nevow import rend, inevow

from nevow.flat import flatten
from twisted.internet import defer
import md5

class ETagPage(rend.Page):

    buffered = True

    def flattenFactory(self, stan, ctx, writer, finisher):
        finished = defer.Deferred()
        st = flatten(stan, ctx)
        request = ctx.locate(inevow.IRequest)
        request.setETag(md5.md5(st).hexdigest())
        writer(st)
        finished.callback('')
        return finished.addCallback(finisher)
