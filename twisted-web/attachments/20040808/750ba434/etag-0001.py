from nevow import rend, inevow

from nevow.flat import flatten
from twisted.internet import defer
import md5

class ETagPage(rend.Page):

    buffered = True

    def flattenFactory(self, stan, ctx, writer, finisher):
        output = []
        def capturingWriter(result):
            output.append(result)
            writer(result)

        def setETag(result):
            st = ''.join(output)
            request = ctx.locate(inevow.IRequest)
            request.setETag(md5.md5(st).hexdigest())

        d = rend.deferflatten(stan, ctx, capturingWriter)
        d.addCallback(setETag)
        d.addCallback(finisher)
        return d
