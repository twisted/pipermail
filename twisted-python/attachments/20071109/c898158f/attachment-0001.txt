Index: locals/twisted/TwistedWords-0.5.0/twisted/words/xish/domish.py
===================================================================
--- locals/twisted/TwistedWords-0.5.0/twisted/words/xish/domish.py (revision 6902)
+++ locals/twisted/TwistedWords-0.5.0/twisted/words/xish/domish.py (revision 9488)
@@ -440,4 +440,8 @@
 
     def __getattr__(self, key):
+        # To prevent recursion on pickling Element objects we need to return 
+        # when key equals 'children'
+        if key == 'children':
+            return []
         # Check child list for first Element with a name matching the key
         for n in self.children: