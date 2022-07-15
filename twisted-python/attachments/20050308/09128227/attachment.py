import wx
from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor

[wxID_FRAME1, wxID_FRAME1BUTTON1, wxID_FRAME1STATICTEXT1, 
] = [wx.NewId() for _init_ctrls in range(3)]

class Frame1(wx.Frame):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Frame.__init__(self, id=wxID_FRAME1, name='', parent=prnt,
              pos=wx.Point(566, 203), size=wx.Size(166, 155),
              style=wx.DEFAULT_FRAME_STYLE, title='Frame1')
        self.SetClientSize(wx.Size(158, 121))
        self.Bind(wx.EVT_CLOSE, self.OnFrame1Close)

        self.button1 = wx.Button(id=wxID_FRAME1BUTTON1, label=u'ClickMe',
              name='button1', parent=self, pos=wx.Point(40, 80),
              size=wx.Size(75, 23), style=0)
        self.button1.Bind(wx.EVT_BUTTON, self.OnButton1Button,
              id=wxID_FRAME1BUTTON1)

        self.staticText1 = wx.StaticText(id=wxID_FRAME1STATICTEXT1,
              label=u'Test', name='staticText1', parent=self, pos=wx.Point(64,
              32), size=wx.Size(21, 13), style=0)

    def __init__(self, parent):
        self._init_ctrls(parent)

    def OnButton1Button(self, event):
        dlg = wx.TextEntryDialog(
                self, "Test",
                'Python', style = wx.OK | wx.CANCEL)
        if dlg.ShowModal() == wx.ID_OK:
            print dlg.GetValue()
        dlg.Destroy()
        print "I'm going out"

    def OnFrame1Close(self, event):
        event.Skip()
        reactor.stop()

class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.main = Frame1(None)
        self.main.Show()
        self.SetTopWindow(self.main)
        return True

def main():
    app = MyApp(0)
    #app.MainLoop()            # Try to uncomment this line
    reactor.registerWxApp(app) # Try to comment this line
    reactor.run()              # and this line

if __name__ == '__main__':
    main()
