--- twisted-1.3.0/twisted/protocols/ftp.py	2004-03-03 21:42:26.000000000 +1100
+++ ftp.py	2004-12-04 15:14:26.000000000 +1100
@@ -337,6 +337,7 @@
             d.errback(BogusClientError("%s != %s" % (peer[1], self.pi.peerHost[1])))   
             return
 
+        self.mode = -1
         log.debug('firing dtpFactory deferred')
         d, self.factory.deferred = self.factory.deferred, defer.Deferred()
         d.callback(None)
@@ -364,21 +365,48 @@
         # lets set self.pi.fp file pointer to 0 just to 
         # make sure the avatar didn't forget, hmm?
         self.pi.fp.seek(0)
+        self.mode = 0
         return fs.beginFileTransfer(self.pi.fp, self.transport, transform
                 ).addCallback(debugDeferred,'firing at end of file transfer'
                 ).addCallback(self._dtpPostTransferCleanup
                 )
 
+    def dtp_STOR (self):
+        filename = _getFPName(self.pi.fp)
+        log.debug('receiving to %s' % filename)
+        self.mode = 1
+        self.deferred = defer.Deferred ()
+        self.deferred.addCallback(debugDeferred,'firing at end of file transfer'
+                ).addCallback(self._dtpPostTransferCleanup
+                )
+        return self.deferred
+
+    def dataReceived (self, data):
+        if self.mode <> 1:
+            log.debug ('received data when we shouldn''t [%s]' % data)
+            return
+        if not self.pi.binary:
+            data = self.transformChunk (data)
+        self.pi.fp.write (data)
+
     def _dtpPostTransferCleanup(self, *arg):
         log.debug("dtp._dtpPostTransferCleanup")
         self.transport.loseConnection()
 
     def connectionLost(self, reason):
         log.debug('dtp.connectionLost: %s' % reason)
-        self.pi.finishedFileTransfer()
+        if self.mode == 0:
+            self.pi.finishedFileTransfer()
+        elif self.mode == 1:
+            self.deferred.callback (None)
+            self.pi.finishedFileUpload ()
+        else:
+            print "closed without transfer"
         self.isConnected = False
 
+    def clientConnectionFailed (self, reason):
+        pass
+
 class DTPFactory(protocol.Factory): 
     __implements__ = (IDTPFactory,)
     # -- configuration variables --
@@ -402,6 +430,12 @@
         self.pi.dtpInstance = p
         return p
 
+    def startedConnecting (self, connector):
+        pass
+
+    def clientConnectionLost (self, connector, reason):
+        pass
+
     def stopFactory(self):
         log.debug('dtpFactory.stopFactory')
         self.cancelTimeout()
@@ -458,7 +492,7 @@
     """
     __implements__ = (IDTPParent,IProtocol,)
     # FTP is a bit of a misonmer, as this is the PI - Protocol Interpreter
-    blockingCommands = ['RETR', 'STOR', 'LIST', 'PORT']
+    blockingCommands = ['RETR', 'STOR', 'LIST']
     reTelnetChars = re.compile(r'(\\x[0-9a-f]{2}){1,}')
 
     # how long the DTP waits for a connection
@@ -635,8 +672,8 @@
         if not hasattr(self, 'TestingSoJustSkipTheReactorStep'):    # to allow for testing
             if self.dtpTxfrMode == PASV:    
                 self.dtpPort = reactor.listenTCP(0, self.dtpFactory)
-            elif self.dtpTxfrMode == PORT: 
-                self.dtpPort = reactor.connectTCP(self.dtpHostPort[1], self.dtpHostPort[2])
+            elif self.dtpTxfrMode == PORT:
+                self.dtpPort = reactor.connectTCP(self.dtpHostPort[0], self.dtpHostPort[1], self.dtpFactory)
             else:
                 log.err('SOMETHING IS SCREWY: _createDTP')
 
@@ -726,6 +763,12 @@
                 self.reply(CNX_CLOSED_TXFR_ABORTED)
             self.fp.close()
 
+    def finishedFileUpload (self, *args):
+        log.debug ("finished file upload")
+        if self.fp is not None and not self.fp.closed:
+            self.reply(TXFR_COMPLETE_OK)
+            self.fp.close ()
+
     def _cbDTPCommand(self):
         """called back when any DTP command has completed successfully"""
         log.debug("DTP Command success")
@@ -947,7 +990,7 @@
                 self._createDTP()
             except OSError, (e,):           # we're watching for a could not listen on port error
                 log.msg("CRITICAL BUG!! THIS SHOULD NOT HAVE HAPPENED!!! %s" % e)
-        self.reply(PORT_MODE_OK)
+        self.reply(ENTERING_PORT_MODE)
 
     def ftp_CWD(self, params):
         self.shell.cwd(cleanPath(params))
@@ -968,6 +1011,17 @@
             self.reply(FILE_STATUS_OK_OPEN_DATA_CNX)
         self._doDTPCommand('RETR')
 
+    def ftp_STOR(self, params):
+        if self.dtpTxfrMode is None:
+            raise BadCmdSequenceError('must send PORT or PASV before STOR')
+        self.fp = self.shell.stor(cleanPath(params))
+        log.debug('self.fp = %s' % self.fp)
+        if self.dtpInstance and self.dtpInstance.isConnected:
+            self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
+        else:
+            self.reply(FILE_STATUS_OK_OPEN_DATA_CNX)
+        self._doDTPCommand('STOR')
+        
     def ftp_STRU(self, params=""):
         p = params.upper()
         if params == 'F':
