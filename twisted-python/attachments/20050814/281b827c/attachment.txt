"""
PyCrust is a python shell and namespace browser application.
tCrust is a version of PyCrust that works with Twisted.
"""

# The next two lines, and the other code below that makes use of
# ``__main__`` and ``original``, serve the purpose of cleaning up the
# main namespace to look as much as possible like the regular Python
# shell environment.
import __main__
original = __main__.__dict__.keys()

__original_author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"

import wx

class App(wx.App):
    """PyCrust standalone application."""

    def OnInit(self):
        import wx
        from wx import py

        wx.InitAllImageHandlers()

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # make some adaptations
        self.frame = py.crust.CrustFrame(title="Twisted PyCrust!",
                                         InterpClass=self.getInterpClass())
        def myOnClose(self, event):
            from twisted.internet import reactor
            reactor.addSystemEventTrigger('after', 'shutdown', self._OnClose, (None,))
            reactor.stop()
        self.frame._OnClose = self.frame.OnClose
        self.frame.OnClose = myOnClose
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        self.frame.SetSize((800, 600))
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

    def getInterpClass(self):
        import sys
        from wx import py
        from twisted.conch.manhole import ManholeInterpreter

        class ManholeCrustInterpreter(py.interpreter.Interpreter):
            """A version of the PyCrust interpreter that uses the manhole display hook"""
            def __init__(self, locals=None, rawin=None,
                         stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
                py.interpreter.Interpreter.__init__(self, locals, rawin,
                                                    stdin, stdout, stderr)
                self.manhole = ManholeInterpreter(self, locals)

            def addOutput(self, data, async):
                self.write(data)
                
            def runcode(self, *a, **kw):
                orighook, sys.displayhook = sys.displayhook, self.manhole.displayhook
                try:
                    py.interpreter.Interpreter.runcode(self, *a, **kw)
                finally:
                    sys.displayhook = orighook

        return ManholeCrustInterpreter                    

'''
The main() function needs to handle being imported, such as with the
pycrust script that wxPython installs:

    #!/usr/bin/env python

    from wx.py.PyCrust import main
    main()
'''

def main():
    """The main function for the PyCrust program."""
    # Cleanup the main namespace, leaving the App class.
    import __main__
    md = __main__.__dict__
    keepers = original
    keepers.append('App')
    for key in md.keys():
        if key not in keepers:
            del md[key]
    # Create an application instance.
    app = App(0)
    # Mimic the contents of the standard Python shell's sys.path.
    import sys
    if sys.path[0]:
        sys.path[0] = ''
    # Add the application object to the sys module's namespace.
    # This allows a shell user to do:
    # >>> import sys
    # >>> sys.app.whatever
    sys.app = app
    del sys
    # Cleanup the main namespace some more.
    if md.has_key('App') and md['App'] is App:
        del md['App']
    if md.has_key('__main__') and md['__main__'] is __main__:
        del md['__main__']
    # Start the wxPython event loop.

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # this is to integrate Twisted and wxPython
    from twisted.internet import threadedselectreactor
    threadedselectreactor.install()
    from twisted.internet import reactor
    import wx
    reactor.interleave(wx.CallAfter)
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    app.MainLoop()

if __name__ == '__main__':
    main()
