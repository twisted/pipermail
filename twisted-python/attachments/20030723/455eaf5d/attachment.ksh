Index: components.html
===================================================================
RCS file: /cvs/Twisted/doc/howto/components.html,v
retrieving revision 1.6
diff -c -u -r1.6 components.html
--- components.html	18 Jul 2003 06:33:59 -0000	1.6
+++ components.html	24 Jul 2003 16:30:44 -0000
@@ -263,7 +263,7 @@
 from twisted.python import components
 
 class IAmericanSocket(components.Interface):
-    def voltage():
+    def voltage(self):
       """Return the voltage produced by this socket object, as an integer.
       """
     
