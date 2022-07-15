Index: README
===================================================================
RCS file: /cvs/Twisted/README,v
retrieving revision 1.87
diff -u -r1.87 README
--- README	2 Jun 2002 04:38:28 -0000	1.87
+++ README	15 Jun 2002 06:15:38 -0000
@@ -44,8 +44,8 @@
 
 What can I do with it?
 
-  To install Twisted, just make sure the Twisted-$VERSION/twisted directory
-  is in the "PYTHONPATH" environment variable. For example, if you extracted
+  To install Twisted, just make sure the Twisted-$VERSION directory is in
+  the "PYTHONPATH" environment variable. For example, if you extracted
   Twisted-0.18.0.tar.gz to /home/bob/, then you would have something like:
 
     export PYTHONPATH=$PYTHONPATH:/home/bob/Twisted-0.18.0/
@@ -79,6 +79,9 @@
 
    % admin/runtests
 
+  Some of the tests may fail if you are running Python 2.2 or don't have
+  the Python XML support installed.
+
   If you're feeling more brave, you can try the new "acceptance tests".  These
   require some setup and are mainly for the developers to decide if it's OK to
   release, but:
@@ -95,6 +98,8 @@
 
   Note that the following examples only create the .tap files with the servers
   inside of them: to actually run the servers, see "Running Servers" below.
+  Also note that the commands used (mktap, coil, twistd, etc) can be found
+  in the bin directory of your Twisted installation.
 
   The normal type of server to create is a webserver.  You can run this
   command::
