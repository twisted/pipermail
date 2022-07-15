Index: twistd.py
===================================================================
RCS file: /cvs/Twisted/twisted/scripts/twistd.py,v
retrieving revision 1.52
diff -u -r1.52 twistd.py
--- twistd.py	5 Jul 2003 02:50:14 -0000	1.52
+++ twistd.py	10 Jul 2003 03:11:02 -0000
@@ -60,6 +60,7 @@
                 ['debug', 'b',    "run the application in the Python Debugger (implies nodaemon), sending SIGINT will drop into debugger"],
                 ['quiet','q',     "be a little more quiet"],
                 ['no_save','o',   "do not save state on shutdown"],
+                ['nosig', None,   "do not install signal handlers (implies no_save)"],
                 ['originalname', None, "Don't try to change the process name"],
                 ['syslog', None,   "Log to syslog, not to file"],
                 ['euid', '',     "Set only effective user-id rather than real user-id. "
@@ -409,6 +410,8 @@
                 signal.signal(signal.SIGINT, debugSignalHandler)
             pdb.run("application.run(%d)" % (not config['no_save']),
                     globals(), locals())
+        elif config['nosig']:
+            application.run(config['no_save'], installSignalHandlers=0)
         else:
             application.run(not config['no_save'])
     except:
