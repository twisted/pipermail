from wxPython.wx import *
from twisted.internet import threadedselectreactor
threadedselectreactor.install()
from twisted.internet import reactor, threads, defer
import time

ID_EXIT  = 101
ID_TEST  =  102
class MyFrame(wxFrame):
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, wxSize(300, 200))
        menu = wxMenu()
        menu.Append(ID_EXIT, "E&xit", "Terminate the program")
        menu.Append(ID_TEST, "Do test", "Terminate the program")

        menuBar = wxMenuBar()
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        EVT_MENU(self, ID_EXIT,  self.DoExit)
        EVT_MENU(self, ID_TEST,  self.DoTest)
        reactor.interleave(wxCallAfter)

    def DoExit(self, event):
        reactor.addSystemEventTrigger('after', 'shutdown', self.Close, true)
        reactor.stop()

    def DoTest(self, event):
        t = threads.deferToThread(try_thread)
        t.addCallback(self.print_one)
        t.addErrback(self.err)

    def print_one(self, *args):
        print 'After create miniframe'

    def err(self,*args):
        print args

def try_thread():
    print 'Sleep for 1 second, simulate blocking code'
    time.sleep(1)
    print 'End sleep 1'
    f = openF()
    f.frm(None)

class openF:
    def frm(self, parent, *args):
        self.frm = wxMiniFrame(parent, title='My test', size = wxSize(200,200))
        self.frm.Show()
        print 'ok, miniframe created'
    def test(self, arg):
        print 'test ok, %s' % arg

class MyApp(wxApp):

    def OnInit(self):
        frame = MyFrame(NULL, -1, "Hello, world")
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

def demo():
    app = MyApp(0)
    app.MainLoop()


if __name__ == '__main__':
    demo()
