# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Acceptance tests for wxreactor.

Please test on Linux, Win32 and OS X:
1. Startup event is called at startup.
2. Scheduled event is called after 2 seconds.
3. Shutdown takes 3 seconds, both when quiting from menu and when closing
   window (e.g. Alt-F4 in metacity). This tests reactor.stop() and
   wx.App.ExitEventLoop().
4. 'hello, world' continues to be printed even when modal dialog is open
   (use dialog menu item), when menus are held down, when window is being
   dragged.
"""

import sys, time, os
import wx

from twisted.python import log
from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor, defer


# set up so that "hello, world" is printed continously
dc = None
def helloWorld():
    global dc
    print "hello, world", time.time()
    dc = reactor.callLater(4, helloWorld)
dc = reactor.callLater(4, helloWorld)

def twoSecondsPassed():
    print "two seconds passed"

def printer(s):
    print s

def shutdown():
    print "shutting down in 3 seconds"
    if dc.active():
        dc.cancel()
    reactor.callLater(1, printer, "2...")
    reactor.callLater(2, printer, "1...")
    reactor.callLater(3, printer, "0...")
    d = defer.Deferred()
    reactor.callLater(3, d.callback, 1)
    return d

def startup():
    print "Start up event!"

reactor.callLater(2, twoSecondsPassed)
reactor.addSystemEventTrigger("after", "startup", startup)
reactor.addSystemEventTrigger("before", "shutdown", shutdown)


ID_DIALOG = 102
ID_OPENFILE = 103

class MyFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition,
                          wx.Size(300, 200))
        menu = wx.Menu()
        menu.Append(ID_DIALOG, "D&ialog", "Show dialog")
        menu.Append(ID_OPENFILE, "&Open", "Open a file ...")
        menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        menuBar = wx.MenuBar()
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        wx.EVT_MENU(self, wx.ID_EXIT,  self.DoExit)
        wx.EVT_MENU(self, ID_DIALOG,  self.DoDialog)
        wx.EVT_MENU(self, ID_OPENFILE,  self.onOpenFile)
        # you really ought to do this instead of reactor.stop() in
        # DoExit, but for the sake of testing we'll let closing the
        # window shutdown wx without reactor.stop(), to make sure that
        # still does the right thing.
        #wx.EVT_CLOSE(self, lambda evt: reactor.stop())

    def DoDialog(self, event):
        dl = wx.MessageDialog(self, "Check terminal to see if messages are "
                              "still being printed by Twisted.")
        dl.ShowModal()
        dl.Destroy()

    def onOpenFile(self, event):
        wildcard = "All files (*.*)|*.*"
        dl = wx.FileDialog(self, message="Choose a file",
                          defaultDir=os.getcwd(), 
                          defaultFile="",
                          wildcard=wildcard,
                          style=wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
        if dl.ShowModal() == wx.ID_OK:
            # paths = dl.GetPaths()
            pass
        dl.Destroy()

    def DoExit(self, event):
        self.Show(False)
        reactor.stop()


class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, -1, "Hello, world")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


def demo():
    log.startLogging(sys.stdout)
    app = MyApp(0)
    reactor.registerWxApp(app)
    reactor.run()


if __name__ == '__main__':
    demo()

