#!/usr/bin/python

import sys
from qt import *

from twisted.internet import qtreactor, protocol, defer

app = QApplication([])
qtreactor.install(app)

from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword

INTERVAL = 3

class TestPBClientFactory(pb.PBClientFactory):
    
    def clientConnectionFailed(self, connector, reason):
        print "Failed:", reason.getErrorMessage()

    def clientConnectionLost(self, connector, reason):
        print "Lost:", reason.getErrorMessage()

class TestWindow(QMainWindow):
    
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        button = QPushButton("Dummy", self, "button")
        self.setCentralWidget(button)
        
        factory = TestPBClientFactory()
        reactor.connectTCP("localhost", 4242, factory)
        factory.login(UsernamePassword("guest", "guest")) \
               .addCallbacks(self.connected, self.failure)
    
    def success(self, message):
        print "Successful ping"
        return self.openModalDialog(None)
    
    def failure(self, error):
        print "error received:", error
        reactor.stop()
    
    def pingRegularly(self, perspective):
        perspective.callRemote('ping').addCallbacks(self.success, self.failure)
        reactor.callLater(INTERVAL, self.pingRegularly, perspective)
    
    def connected(self, perspective):
        reactor.callLater(INTERVAL, self.pingRegularly, perspective)
        print "connected."
    
    def openModalDialog(self, ignore):
        print "Opening modal dialog"
        dialog = QDialog(self, 'dialog', True)
        return dialog.exec_loop()

if __name__ == '__main__':
    win = TestWindow()
    win.show()

    reactor.addSystemEventTrigger('after', 'shutdown', app.quit)

    app.connect(app, SIGNAL("lastWindowClosed()"), reactor.stop)
    reactor.run()
