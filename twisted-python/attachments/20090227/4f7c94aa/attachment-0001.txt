--- /usr/lib/python2.5/site-packages/twisted/internet/base.py	2008-07-29 22:13:54.000000000 +0200
+++ internet/base.py	2009-02-20 12:27:42.000000000 +0100
@@ -1127,17 +1127,32 @@
         self.startRunning(installSignalHandlers=installSignalHandlers)
         self.mainLoop()
 
+        
+    def setLoopCall(self, f, *args, **kw):
+        self.loopCall = (f, args, kw)
+
+
+    def myIteration(self, t):
+        # Advance simulation time in delayed event
+        # processors.
+        self.runUntilCurrent()
+
+        if (t is None):
+            t2 = self.timeout()
+            t = self.running and t2
+
+        self.doIteration(t)
+
+        if ("loopCall" in dir(self)):
+            f, args, kw = self.loopCall
+            f(*args, **kw)
+
 
     def mainLoop(self):
         while self._started:
             try:
                 while self._started:
-                    # Advance simulation time in delayed event
-                    # processors.
-                    self.runUntilCurrent()
-                    t2 = self.timeout()
-                    t = self.running and t2
-                    self.doIteration(t)
+                    self.myIteration(None)
             except:
                 log.msg("Unexpected error in main loop.")
                 log.err()
