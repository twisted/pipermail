peter@think:/space/src/twisted/Twisted> svn diff doc/names/examples/testdns.py
Index: doc/names/examples/testdns.py
===================================================================
--- doc/names/examples/testdns.py       (revision 13290)
+++ doc/names/examples/testdns.py       (working copy)
@@ -1,9 +1,8 @@
 #!/usr/bin/env python

 import sys
-from twisted.names import client
+from twisted.names import client, dns
 from twisted.internet import reactor
-from twisted.protocols import dns

 r = client.Resolver('/etc/resolv.conf')

@@ -27,6 +26,10 @@
 if __name__ == '__main__':
     import sys

+    if len( sys.argv ) < 2:
+        print 'usage: testdns.py domain_name'
+        sys.exit( 1 )
+
     r.lookupAddress(sys.argv[1]).addCallback(gotAddress).addErrback(gotError)
     r.lookupMailExchange(sys.argv[1]).addCallback(gotMails).addErrback(gotError)
     r.lookupNameservers(sys.argv[1]).addCallback(gotNameservers).addErrback(gotError)
