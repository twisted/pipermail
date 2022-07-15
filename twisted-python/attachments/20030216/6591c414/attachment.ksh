#!/usr/bin/env python
## by grrrendel@comcast.net
"""
qtManhole - manhole client that uses qt for gui
"""

from qt import *
A=QApplication([])

from twisted.internet import qtreactor
qtreactor.install( A )

from twisted.cred.error import *
from twisted.internet.error import *
from twisted.spread import pb
from twisted.python import usage
import string,traceback

class Options( usage.Options ):
    synopsis="Usage: qtManhole [options]"
    optParameters=[["host","h", None,
                    "Host address"],
                   ["port","p", None,
                    "Port number"],
                   ["user","u", None,
                    "Username"],
                   ["pswd","w", None,
                    "Password"]]

    def postOptions( self ):
        for i in self.opts.keys():
            if not self.opts[i]:
                raise usage.UsageError, "Wrong, try again."

class Interaction( pb.Referenceable ):
    capabilities={}

    def __init__( self, gui ):
        self.gui=gui

    def remote_console( self, message ):
        for i in message:
            if i[0] == 'exception':
                s=traceback.format_list(i[1]['traceback'])
                s.extend(i[1]['exception'])
                s=string.join(s,'')
            else:
                s=i[1]

            self.gui.showoutput( str( s ) )

    def remote_recieveExplorer( self, xplorer ):
        pass

    def remote_listCapabilities( self ):
        return self.capabilities

class CLI( QWidget ):
    def __init__( self, parent=None, name=None ):
	QWidget.__init__( self, parent, name )
        self.vlo=QVBoxLayout( self )
        self.output=QTextView( self )
        self.vlo.addWidget( self.output )
        self.input=QLineEdit( self )
        self.vlo.addWidget( self.input )
        self.input.setFocus()

class HoleClient( QMainWindow ):
    def __init__( self, opts ):
        QMainWindow.__init__( self, None, None )
        self.host=opts['host']
        self.port=int(opts['port'])
        self.user=opts['user']
        self.pswd=opts['pswd']
	self.service='manhole'

        self.setCaption( "qtManhole" )
        self.resize( 500, 500 )

        self.io=CLI(self)
        self.setCentralWidget( self.io )
        self.client=Interaction( self )

        self.status=self.statusBar()
        self.menubar=self.menuBar()
        self.filemenu=QPopupMenu( self ) 
        self.filemenu.insertItem( '&Close', self.close )
        self.menubar.insertItem( '&File',  self.filemenu )

	self.connect( self.io.input, 
	              SIGNAL( "returnPressed()" ),
		      self.do )

	self.getPersp()

    def getPersp( self ):
        pb.connect( self.host, self.port, self.user, self.pswd,
                    self.service, client=self.client ).addCallbacks( self._setPersp, self._eb_getPersp )

    def _setPersp( self, persp ):
        self.persp=persp

    def _eb_getPersp( self, fail ):
	e = fail.trap( ConnectError, Unauthorized, KeyError )
	QMessageBox.warning( self, 'Warning', str( e ) )

    def do( self ):
	text=str( self.io.input.text() )
	self.persp.callRemote( 'do',  text ).addErrback( self._eb_do )
        self.showoutput("<font color=red>>> "+ text)
	self.io.input.clear()

    _eb_do=_eb_getPersp

    def showoutput( self, text ):
	self.io.output.append( text )

if __name__ == '__main__':
    from twisted.internet import reactor
    opts=Options()
    try:
        opts.parseOptions()
    except usage.UsageError, e:
        print str(e)
        print str(opts)
        raise SystemExit
    else:
        HoleClient(opts).show()
        reactor.addSystemEventTrigger('after', 'shutdown', A.quit )
        A.connect( A, SIGNAL("lastWindowClosed()"), reactor.stop )
        reactor.run()

