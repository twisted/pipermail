--- procmon.orig.py	2003-03-15 13:04:11.000000000 +0100
+++ procmon.py	2003-08-12 19:52:41.000000000 +0200
@@ -179,10 +179,10 @@
         if self.active and self.processes.has_key(name):
             reactor.callLater(delay, self.startProcess, name)
 
-    def startProcess(self, name):
+    def startProcess(self, name, protocol = LoggingProtocol):
         if self.protocols.has_key(name):
             return
-        p = self.protocols[name] = LoggingProtocol()
+        p = self.protocols[name] = protocol()
         p.service = self
         p.name = name
         args, uid, gid = self.processes[name]

