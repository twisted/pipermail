# -*- coding: utf-8 -*-
from twisted.web import sux
from twisted.words.xish import domish

class __RawXmlToElement(object):

    def __call__(self, s):
        self.result = None
        def onStart(el):
            self.result = el
        def onEnd():
            pass
        def onElement(el):
            self.result.addChild(el)

        parser = domish.elementStream()
        parser.DocumentStartEvent = onStart
        parser.ElementEvent = onElement
        parser.DocumentEndEvent = onEnd
        tmp = domish.Element(("", "s"))
        tmp.addRawXml(s)
        parser.parse(tmp.toXml().encode("utf-8"))

        return self.result.firstChildElement()

rawXmlToElement = __RawXmlToElement()

if(__name__ == "__main__"):

    res = rawXmlToElement("<t>reçu</t>")
    print "Result : %s" % res.toXml()
