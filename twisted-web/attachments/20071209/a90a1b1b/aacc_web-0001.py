# -*- coding: utf-8 -*-
""" aacc_web
"""

from twisted.application import service, internet
from twisted.internet import reactor, protocol, defer, task, ssl
from twisted.protocols import basic
from twisted.python import log, logfile, util
from twisted.cred import portal, checkers, credentials
from twisted.web import static

from nevow import appserver
from nevow import tags, guard
from nevow import rend, loaders, inevow, athena
from nevow import url
from nevow.inevow import IRequest

import os, logging, pprint, time, sys


class Users(athena.LiveFragment):
    jsClass=u"AaccWeb.Users"

    docFactory = loaders.xmlstr("""
<div xmlns:nevow="http://nevow.com/ns/nevow/0.1"
   xmlns:athena="http://divmod.org/ns/athena/0.7"
   nevow:render="liveFragment" class="Users">
</div>
""")

    running = False
    
    def __init__(self, **kwargs):
        print 'start Users AJAX session'
        
    def aacc_start(self):
        if self.running:
            return
        reactor.callLater(1, self.updateConference, True)
        self.running = True
    athena.expose(aacc_start)

    def aacc_keypress(self, charcode=None, keycode=None, metakey=None, altkey=None, ctrlkey=None, shiftkey=None):
        print 'charcode: %s keycode: %s metakey: %s altkey: %s ctrlkey: %s shiftkey: %s' % (charcode, keycode, metakey, altkey, ctrlkey, shiftkey)
        self.updateConference(True, unichr(charcode))
    athena.expose(aacc_keypress)

    def updateConference(self, force=False, sym=''):
        """ updateConference """
        #print 'updateConference'
        def onUpdateConferenceOk(result):
            self.callUpdateConference = reactor.callLater(1, self.updateConference)
        def onUpdateConferenceErr(err):
            self.running = False

        if not force:
            self.callUpdateConference = reactor.callLater(1, self.updateConference)
            return

        #mystr = u"""<textarea id="termid" cols="10" rows="5" onkeypress="return keypress(event)">""" + sym + u"""</textarea>"""
        mystr = u"""<textarea cols="10" rows="5" onkeypress="return Nevow.Athena.Widget.get(this).keypress2(event);">""" + sym + u"""</textarea>"""

        #self.callRemote('setFocus')
        df = self.callRemote('showConference', mystr)
        df.addCallbacks(onUpdateConferenceOk, onUpdateConferenceErr)

class ConferencePage(athena.LivePage):

    docFactory = loaders.xmlstr("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <nevow:invisible nevow:render="liveglue"/>
        <script type="text/javascript" src="aacc_web.js">
        </script>
    </head>
    <body>
        <div nevow:render="conference">
        </div>
    </body>
</html>
""")

    def __init__(self, *a, **kw):
        super(ConferencePage, self).__init__(*a, **kw)
        self.jsModules.mapping[u'AaccWeb'] = util.sibpath(__file__, 'aacc_web.js')

    addSlash = True

    def render_liveglue(self, ctx, data):
        req = ctx.locate(IRequest)
        args = dict([(k,v[0]) for (k,v) in req.args.items()])
        self.args = args
        return athena.LivePage.render_liveglue(self, ctx, data)

    def render_conference(self, ctx, data):
        args = dict([(k,v) for (k,v) in self.args.items()])
        c = Users(**args)
        c.page = self
        reactor.callLater(0, c.aacc_start)
        return ctx.tag[c]

class RootPage(rend.Page):
    """ """
    addSlash = True
    docFactory = loaders.xmlstr("""
<html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
    <body>
    </body>
</html>
""")

    def renderHTTP(self, ctx):
        print 'render of root page'
        req = ctx.locate(IRequest)
        my_url = url.here.child('conference')
        return my_url

    def child_conference(self, ctx):
        return ConferencePage()


class aacc_web:
    """ """

    def __init__(self, **kwargs):
        """ """
        resource = RootPage()
        site = appserver.NevowSite(resource)
        reactor.listenTCP(8080, site)


if __name__ == "__main__":
    aacc_web = aacc_web()
    reactor.run()