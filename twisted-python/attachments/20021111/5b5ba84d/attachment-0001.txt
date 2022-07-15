Index: twisted/scripts/tapconvert.py
===================================================================
RCS file: /cvs/Twisted/twisted/scripts/tapconvert.py,v
retrieving revision 1.5
diff -u -r1.5 tapconvert.py
--- twisted/scripts/tapconvert.py	11 Sep 2002 18:59:59 -0000	1.5
+++ twisted/scripts/tapconvert.py	11 Nov 2002 22:02:26 -0000
@@ -57,9 +57,9 @@
             self.read()
         return self.decode()       
         
-    def read(self, filename):
-        pass
-
+    def read(self):
+        self.data = open(self.filename, 'r').read()
+        
     def decrypt(self):
         try:
             import md5
@@ -73,8 +73,6 @@
 
 class LoaderXML(LoaderCommon):
     loadmessage = '<Loading file="%s" />' 
-    def read(self, filename):
-        self.data = open(filename, 'r').read()
     def decode(self):
         from twisted.persisted.marmalade import unjellyFromXML
         sys.modules['__main__'] = EverythingEphemeral()
@@ -84,24 +82,22 @@
         return application
 
 class LoaderPython(LoaderCommon):
+    def read(self):
+        pass
     def decrypt(self):
         log.msg("Python files are never encrypted")
-    
     def decode(self):
         pyfile = os.path.abspath(self.filename)
         d = {'__file__': self.filename}
-        execfile(pyfile, dict, dict)
+        execfile(pyfile, d, d)
         try:
-            application = dict['application']
+            application = d['application']
         except KeyError:
             log.msg("Error - python file %s must set a variable named 'application', an instance of twisted.internet.app.Application. No such variable was found!" % repr(self.filename))
             sys.exit()
         return application
 
 class LoaderSource(LoaderCommon):
-    def read(self):
-        self.data = open(self.filename, 'r').read()
-
     def decode(self):
         from twisted.persisted.aot import unjellyFromSource
         sys.modules['__main__'] = EverythingEphemeral()
@@ -112,9 +108,6 @@
         return application
 
 class LoaderTap(LoaderCommon):
-    def read(self):
-        self.data = open(self.filename, 'rb').read()
-
     def decode(self):
         sys.modules['__main__'] = EverythingEphemeral()
         application = load(StringIO(self.data))
@@ -170,22 +163,25 @@
         passphrase = getpass.getpass('Passphrase: ')
 
     if options["typein"] == "guess":
-        if options["in"][-3:] == '.py':
-            options["typein"] = 'python'
-        else:
-            try:
-                options["typein"] = ({ '.tap': 'pickle',
-                                       '.tas': 'source',
-                                       '.tax': 'xml' }[options["in"][-4:]])
-            except KeyError:
-                print "Error: Could not guess the type."
-                return
+        ext = os.path.splitext(options["in"])[1]
+        try:
+            options["typein"] = ({ '.py':  'python',
+                                   '.tap': 'pickle',
+                                   '.tas': 'source',
+                                   '.tax': 'xml' }[ext])
+        except KeyError:
+            print "Error: Could not guess the type."
+            return
 
     if None in [options['in']]:
         options.opt_help()
     a = loadPersisted(options["in"], options["typein"], options["decrypt"], passphrase)
-    a.persistStyle = ({'xml': 'xml',
-                       'source': 'aot', 
-                       'pickle': 'pickle'}
-                       [options["typeout"]])
+    try:
+        a.persistStyle = ({'xml': 'xml',
+                           'source': 'aot', 
+                           'pickle': 'pickle'}
+                          [options["typeout"]])
+    except KeyError:
+        print "Error: Unsupported output type."
+        return
     savePersisted(a, filename=options["out"], encrypted=options["encrypt"])
