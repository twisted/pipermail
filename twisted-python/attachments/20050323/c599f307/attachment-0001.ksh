peter@think:/space/src/twisted/Twisted> svn diff twisted/names/dns.py
Index: twisted/names/dns.py
===================================================================
--- twisted/names/dns.py        (revision 13294)
+++ twisted/names/dns.py        (working copy)
@@ -1086,7 +1086,8 @@
         m = Message()
         m.fromStr(data)
         if self.liveMessages.has_key(m.id):
-            d = self.liveMessages[m.id]
+            d, timeout_call = self.liveMessages[m.id]
+            timeout_call.cancel( )
             del self.liveMessages[m.id]
             # XXX we shouldn't need this hack of catching exceptioon on callback()
             try:
@@ -1123,8 +1124,13 @@
             self.resends[id] = 1
         m = Message(id, recDes=1)
         m.queries = queries
-        d = self.liveMessages[id] = defer.Deferred()
-        d.setTimeout(timeout, self._clearFailed, id)
+
+        from twisted.internet import reactor
+        d = defer.Deferred()
+        timeoutCall = reactor.callLater(
+            timeout,
+            lambda: d.called or self._clearFailed( d, id ) )
+        self.liveMessages[id] = ( d, timeoutCall )
         self.writeMessage(m, address)
         return d
