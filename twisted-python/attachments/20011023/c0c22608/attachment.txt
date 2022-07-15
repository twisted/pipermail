Index: twisted/internet/passport.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/passport.py,v
retrieving revision 1.14
diff -u -u -r1.14 passport.py
--- twisted/internet/passport.py	2001/10/09 06:53:41	1.14
+++ twisted/internet/passport.py	2001/10/23 16:30:59
@@ -296,7 +296,12 @@
         md = md5.new()
         md.update(plaintext)
         userPass = md.digest()
-        return (userPass == self.hashedPassword)
+        req = defer.Deferred()
+        if userPass == self.hashedPassword:
+            req.callback(self)
+        else:
+            req.errback(self)
+        return req
 
     # TODO: service discovery through listing of self.keyring.
 
Index: twisted/reality/plumbing.py
===================================================================
RCS file: /cvs/Twisted/twisted/reality/plumbing.py,v
retrieving revision 1.10
diff -u -u -r1.10 plumbing.py
--- twisted/reality/plumbing.py	2001/09/06 23:36:25	1.10
+++ twisted/reality/plumbing.py	2001/10/23 16:31:00
@@ -64,36 +64,41 @@
             return 'Command'
         return "Pending"
 
+    def loginSuccessful(self, ident):
+        # The identity checks out.
+        characters = []
+        # XXX REFACTOR: Hmm.  Is this next bit common behavior?
+        r = self.factory.reality
+        nm = r.getServiceName()
+        for serviceName, perspectiveName in identity.getAllKeys():
+            if serviceName == nm:
+                characters.append(r.getPerspectiveNamed(perspectiveName))
+        lc = len(characters)
+        if lc == 1:
+            p = characters[0]
+        elif lc > 1:
+            p = characters[0]
+            self.transport.write("TODO: character selection menu\r\n")
+        else:
+            raise passport.Unauthorized("that identity has no TR characters")
+
+        p = p.attached(self, identity)
+        self.player = p
+        self.identity = identity
+        self.transport.write("Hello "+self.player.name+", welcome to Reality!\r\n"+
+                             telnet.IAC+telnet.WONT+telnet.ECHO)
+        self.mode = "Command"
+
+    def loginFailure(self, ident):
+        log.msg("incorrect password") 
+        self.transport.loseConnection()
+
     def loggedIn(self, identity):
         """The player's identity has been retrieved.  Now, check their password.
         """
-        if identity.verifyPlainPassword(self.pw):
-            # The identity checks out.
-            characters = []
-            # XXX REFACTOR: Hmm.  Is this next bit common behavior?
-            r = self.factory.reality
-            nm = r.getServiceName()
-            for serviceName, perspectiveName in identity.getAllKeys():
-                if serviceName == nm:
-                    characters.append(r.getPerspectiveNamed(perspectiveName))
-            lc = len(characters)
-            if lc == 1:
-                p = characters[0]
-            elif lc > 1:
-                p = characters[0]
-                self.transport.write("TODO: character selection menu\r\n")
-            else:
-                raise passport.Unauthorized("that identity has no TR characters")
-
-            p = p.attached(self, identity)
-            self.player = p
-            self.identity = identity
-            self.transport.write("Hello "+self.player.name+", welcome to Reality!\r\n"+
-                                 telnet.IAC+telnet.WONT+telnet.ECHO)
-            self.mode = "Command"
-        else:
-            log.msg("incorrect password") 
-            self.transport.loseConnection()
+        pwrq = identity.verifyPlainPassword(self.pw)
+        pwrq.addCallbacks(self.loginSuccessful, self.loginFailure)
+        pwrq.arm()
 
     def notLoggedIn(self, err):
         log.msg('requested bad username')
Index: twisted/web/guard.py
===================================================================
RCS file: /cvs/Twisted/twisted/web/guard.py,v
retrieving revision 1.1
diff -u -u -r1.1 guard.py
--- twisted/web/guard.py	2001/09/08 11:09:43	1.1
+++ twisted/web/guard.py	2001/10/23 16:31:01
@@ -21,6 +21,7 @@
 
 # Twisted Imports
 from twisted.internet import passport
+from twisted.python import defer
 
 # Sibling Imports
 import error
@@ -40,22 +41,51 @@
     def __init__(self, reqauth):
         self.reqauth = reqauth
 
-    def gotIdentity(self, ident, password, request, perspectiveName):
-        if ident.verifyPlainPassword(password):
-            try:
-                perspective = ident.getPerspectiveForKey(self.reqauth.serviceName, perspectiveName)
-            except KeyError:
-                traceback.print_exc()
-            else:
-                resKey = string.join(['AUTH',self.reqauth.serviceName]+request.prepath, '_')
-                setattr(request.getSession(), resKey, perspective)
-                return self.reqauth.reallyRender(request)
+    def loginSuccessful(self, ident, request, perspectiveName):
+        try:
+            perspective = ident.getPerspectiveForKey(self.reqauth.serviceName, perspectiveName)
+        except KeyError:
+            traceback.print_exc()
+            # TODO: render the form as if an exception were thrown from the
+            # data processing step...
+            request.write("""
+                <html><head><title>Authorization Required</title></head>
+    <body>
+    <center>
+    beep
+    </center>
+    </body>
+    </html>
+    """)
+            request.finish()
         else:
-            print 'password not verified'
+            resKey = string.join(['AUTH',self.reqauth.serviceName]+request.prepath, '_')
+            setattr(request.getSession(), resKey, perspective)
+            self.reqauth.reallyRender(request)
+
+    def loginFailure(self, ident, request):
+        print 'password not verified'
         # TODO: render the form as if an exception were thrown from the
         # data processing step...
-        return "beep"
+        request.write("""
+        <html><head><title>Authorization Required</title></head>
+        <body>
+        <center>
+        beep
+        </center>
+        </body>
+        </html>
+        """)
+        request.finish()
 
+    def gotIdentity(self, ident, password, request, perspectiveName):
+        pwrq = ident.verifyPlainPassword(password)
+        pwrq.addCallbacks(self.loginSuccessful, self.loginFailure,
+                          callbackArgs=(request,perspectiveName),
+                          errbackArgs=(request,))
+        pwrq.arm()
+        return widgets.FORGET_IT
+
     def didntGetIdentity(self, unauth, request):
         return "beep"
 
@@ -125,7 +155,6 @@
             traceback.print_exc(file=io)
             request.write(html.PRE(io.getvalue()))
             request.finish()
-        return widgets.FORGET_IT
 
     def render(self, request):
         session = request.getSession()
Index: twisted/words/ircservice.py
===================================================================
RCS file: /cvs/Twisted/twisted/words/ircservice.py,v
retrieving revision 1.20
diff -u -u -r1.20 ircservice.py
--- twisted/words/ircservice.py	2001/08/20 19:46:55	1.20
+++ twisted/words/ircservice.py	2001/10/23 16:31:03
@@ -168,23 +168,29 @@
         req.addCallbacks(self.loggedInAs, self.notLoggedIn)
         req.arm()
 
-    def loggedInAs(self, ident):
+    def loginSuccessful(self, ident):
         """Successfully logged in.
         """
-        if ident.verifyPlainPassword(self.pendingPassword):
-            self.identity = ident
-            self.pendingLogin.attached(self, self.identity)
-            self.participant = self.pendingLogin
-            self.receiveDirectMessage("*login*", "Authentication accepted.  Thank you.")
-        else:
-            self.notLoggedIn("unauthorized")
+        self.identity = ident
+        self.pendingLogin.attached(self, self.identity)
+        self.participant = self.pendingLogin
+        self.receiveDirectMessage("*login*", "Authentication accepted.  Thank you.")
         del self.pendingLogin
         del self.pendingPassword
 
+    def loggedInAs(self, ident):
+        """Login in progress
+        """
+        pwrq = ident.verifyPlainPassword(self.pendingPassword)
+        pwrq.addCallbacks(self.loginSuccessful, self.notLoggedIn)
+        pwrq.arm()
+
     def notLoggedIn(self, message):
         """Login failed.
         """
         self.receiveDirectMessage("*login*", "Login failed: %s" % message)
+        del self.pendingLogin
+        del self.pendingPassword
 
     def irc_USER(self, prefix, params):
         """User message -- Set your realname.
