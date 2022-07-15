Index: twisted/scripts/_twistd_unix.py
===================================================================
--- twisted/scripts/_twistd_unix.py	(revision 27172)
+++ twisted/scripts/_twistd_unix.py	(working copy)
@@ -82,7 +82,13 @@
                 sys.exit("Can't check status of PID %s from pidfile %s: %s" %
                          (pid, pidfile, why[1]))
         else:
-            sys.exit("""\
+            # If the PID in the file is our same PID, then we can remove the
+            # stale file
+            if os.getpid() == pid:
+                log.msg('Removing stale pidfile %s' % pidfile, isError=True)
+                os.remove(pidfile)
+            else:
+                sys.exit("""\
 Another twistd server is running, PID %s\n
 This could either be a previously started instance of your application or a
 different application entirely. To start a new one, either run it in some other
