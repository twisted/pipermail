from wxPython.wx import *

#~ if sys.platform == 'win32':
    #~ from twisted.internet import win32eventreactor
    #~ win32eventreactor.install()

from twisted.internet import reactor
from twisted.python import threadable
threadable.init(1)
import threading

def startTwistedAndWx(app):
    """Start twisteds mainloop it its own thread, run the wx mainloop
    in the main thread"""
    global twistedthread
    reactor.startRunning()
    twistedthread = threading.Thread(target=reactor.mainLoop)
    twistedthread.start()
    app.MainLoop()

def stopTwisted():
    """stop the twisted thread, wx still runs"""
    global twistedthread
    reactor.stop()
    #wait until reactor has shut down
    while twistedthread.isAlive():
        wxYield()



ID_EXIT  = 101

class MyFrame(wxFrame):
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, wxSize(300, 200))
        menu = wxMenu()
        menu.Append(ID_EXIT, "E&xit", "Terminate the program")
        menuBar = wxMenuBar()
        menuBar.Append(menu, "&File");
        self.SetMenuBar(menuBar)
        EVT_MENU(self, ID_EXIT,  self.DoExit)
        EVT_CLOSE(self, self.OnCloseWindow)
        self.text = wxTextCtrl(self, -1, "Text\n", style=wxTE_MULTILINE)
        reactor.callLater(0, self.twistedCallsMe, 0)
        
    def DoExit(self, event):
        self.Close(true)

    def OnCloseWindow(self, event):
        stopTwisted()
        self.Destroy()
    
    def twistedCallsMe(self, count):
        print count
        self.text.AppendText('%d\r\n' % count)
        reactor.callLater(0.5, self.twistedCallsMe, count + 1)
        
class MyApp(wxApp):
    def OnInit(self):
        # Do whatever you need to do here
        self.frame = MyFrame(NULL, -1, "Hello, world")
        self.frame.Show(true)
        self.SetTopWindow(self.frame)
        return true

def demo():
    app = MyApp(0)
    startTwistedAndWx(app)

if __name__ == '__main__':
    demo()
