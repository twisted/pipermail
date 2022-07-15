--- TwistedClean/twisted/persisted/apploader.py	Wed Dec  4 11:33:08 2002
+++ Twisted/twisted/persisted/apploader.py	Tue Dec  3 12:36:59 2002
@@ -0,0 +1,163 @@
+# Twisted, the Framework of Your Internet
+# Copyright (C) 2001 Matthew W. Lefkowitz
+#
+# This library is free software; you can redistribute it and/or
+# modify it under the terms of version 2.1 of the GNU Lesser General Public
+# License as published by the Free Software Foundation.
+#
+# This library is distributed in the hope that it will be useful,
+# but WITHOUT ANY WARRANTY; without even the implied warranty of
+# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
+# Lesser General Public License for more details.
+#
+# You should have received a copy of the GNU Lesser General Public
+# License along with this library; if not, write to the Free Software
+# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
+
+from twisted.python import log, util
+from twisted.persisted import styles
+
+# System imports
+import os, sys
+from cPickle import load
+from cStringIO import StringIO
+
+mainMod = sys.modules['__main__']
+
+# Functions from twistd/mktap
+
+class EverythingEphemeral(styles.Ephemeral):
+    def __getattr__(self, key):
+        try:
+            return getattr(mainMod, key)
+        except AttributeError:
+            log.msg("Warning!  Loading from __main__: %s" % key)
+            return styles.Ephemeral()
+
+
+class LoaderCommon:
+    """Simple logic for loading persisted data"""
+
+    loadmessage = "Loading %s..."
+
+    def __init__(self, filename, encrypted=None, passphrase=None):
+        self.filename = filename
+        self.encrypted = encrypted
+        self.passphrase = passphrase
+
+    def load(self):
+        "Returns the application"
+        log.msg(self.loadmessage % self.filename)
+        self.read()
+        if self.encrypted:
+            self.decrypt()
+        return self.decode()       
+        
+    def read(self):
+        self.data = open(self.filename, 'r').read()
+        
+    def decrypt(self):
+        try:
+            import md5
+            from Crypto.Cipher import AES
+            self.data = AES.new(md5.new(self.passphrase).digest()[:16]).decrypt(self.data)
+        except ImportError:
+            print "The --decrypt flag requires the PyCrypto module, no file written."
+            
+    def decode(self):
+        pass
+
+
+class LoaderXML(LoaderCommon):
+
+    loadmessage = '<Loading file="%s" />' 
+
+    def decode(self):
+        from twisted.persisted.marmalade import unjellyFromXML
+        sys.modules['__main__'] = EverythingEphemeral()
+        application = unjellyFromXML(StringIO(self.data))
+        sys.modules['__main__'] = mainMod
+        styles.doUpgrade()
+        return application
+
+
+class LoaderPython(LoaderCommon):
+
+    def read(self):
+        pass
+
+    def decrypt(self):
+        log.msg("Python files are never encrypted")
+
+    def decode(self):
+        pyfile = os.path.abspath(self.filename)
+        d = {'__file__': self.filename}
+        execfile(pyfile, d, d)
+        try:
+            application = d['application']
+        except KeyError:
+            log.msg("Error - python file %s must set a variable named 'application', an instance of twisted.internet.app.Application. No such variable was found!" % repr(self.filename))
+            sys.exit()
+        return application
+
+
+class LoaderSource(LoaderCommon):
+
+    def decode(self):
+        from twisted.persisted.aot import unjellyFromSource
+        sys.modules['__main__'] = EverythingEphemeral()
+        application = unjellyFromSource(StringIO(self.data))
+        application.persistStyle = "aot"
+        sys.modules['__main__'] = mainMod
+        styles.doUpgrade()
+        return application
+
+
+class LoaderTap(LoaderCommon):
+
+    def decode(self):
+        sys.modules['__main__'] = EverythingEphemeral()
+        application = load(StringIO(self.data))
+        sys.modules['__main__'] = mainMod
+        styles.doUpgrade()
+        return application
+
+
+def guess(filename):
+    ext = os.path.splitext(filename)[1]
+    return { '.py':  'python',
+             '.tap': 'pickle',
+             '.tas': 'source',
+             '.tax': 'xml' }[ext]
+
+def guessLoader(filename, *args, **kwargs):
+    kind = guess(filename)
+    ## try:
+    Loader = loaders[kind]
+    ## except KeyError:
+    ##  XXX
+    return Loader(filename, *args, **kwargs)
+
+loaders = {'python': LoaderPython,
+           'xml': LoaderXML,
+           'source': LoaderSource,
+           'pickle': LoaderTap,
+           'guess': guessLoader
+           }
+
+    
+def loadPersisted(filename, kind=None, encrypted=0, passphrase='', naive=0):
+    "Loads filename, of the specified kind and returns an application"
+
+    if kind is None:
+        kind = 'guess'
+
+    Loader = loaders[kind]
+
+    # prevent mktap and coil from overwriting startup scripts
+    if Loader is LoaderTap and naive:
+        raise usageError, "Loading applications from scripts is disabled in this script for safety reasons. Use tapconvert to convert it to something else."
+
+    l = Loader(filename, encrypted, passphrase)
+    application = l.load()
+    return application
--- TwistedClean/twisted/scripts/mktap.py	Mon Sep 30 04:25:20 2002
+++ Twisted/twisted/scripts/mktap.py	Mon Dec  2 16:34:24 2002
@@ -39,7 +39,7 @@
 
 def loadPlugins(debug = 0, progress = 0):
     try:
-        plugins = getPlugIns("tap", debug, progress)
+        plugins = getPlugIns("tap", debug, progres`s)
     except IOError:
         print "Couldn't load the plugins file!"
         sys.exit(2)
@@ -70,14 +70,21 @@
     optParameters = [['uid', 'u', '0'],
                   ['gid', 'g', '0'],
                   ['append', 'a', None,   "An existing .tap file to append the plugin to, rather than creating a new one."],
-                  ['type', 't', 'pickle', "The output format to use; this can be 'pickle', 'xml', or 'source'."]]
+                  ['type', 't', 'guess', "The output format to use; this can be 'pickle', 'xml', or 'source'."]]
     
-    optFlags = [['xml', 'x',       "DEPRECATED: same as --type=xml"],
-                ['source', 's',    "DEPRECATED: same as --type=source"],
-                ['encrypted', 'e', "Encrypt file before writing"],
+    optFlags = [['encrypted', 'e', "Encrypt file before writing"],
                 ['progress', 'p',  "Show progress of plugin loading"],
                 ['debug', 'd',     "Show debug information for plugin loading"]]
 
+    def opt_xml(self):
+        """DEPRECATED: same as --type=xml"""
+        self['type'] = 'xml'
+    opt_x = opt_xml
+
+    def opt_source(self):
+        """DEPRECATED: same as --type=source"""
+        self['type'] = 'source'
+    opt_s = opt_source
     
     def __init__(self, tapLookup):
         usage.Options.__init__(self)
@@ -89,7 +96,6 @@
         self.subCommands.sort()
         self['help'] = 0 # default
 
-
     def opt_help(self):
         """display this message"""
         # Ugh, we can't print the help now, we need to let getopt
@@ -97,12 +103,23 @@
         self['help'] = 1
 
     def postOptions(self):
+        if self['help']:
+            if hasattr(self, 'subOptions'):
+                self.subOptions.opt_help()
+            usage.Options.opt_help(self)
+            sys.exit()       
         self['progress'] = int(self['progress'])
         self['debug'] = int(self['debug'])
 
     def parseArgs(self, *args):
         self.args = args
 
+def loadForAppend(options, passphrase):
+    from twisted.persisted.apploader import guess, loadPersisted
+    filename = options['append']
+    a = loadPersisted(filename, options['type'], options['encrypted'],
+                      passphrase, naive=1)
+    return a
 
 # Rest of code in "run"
 
@@ -137,13 +154,24 @@
         sys.exit()
 
     mod = getModule(tapLookup, options.subCommand)
+
+    passphrase = None
+    if options['encrypted']:
+        try:
+            import Crypto
+            passphrase=util.getPassword("Encryption passphrase: ")
+        except ImportError:
+            print "The --encrypt flag requires the PyCrypto module, no file written."
+            system.exit(1)
+    if options['append']:
+        try:
+            a = loadForAppend(options, passphrase)
+        except:
+            options['append'] = None
     if not options['append']:
+        if options['type'] == 'guess':
+            options['type'] = 'pickle'
         a = app.Application(options.subCommand, int(options['uid']), int(options['gid']))
-    else:
-        if os.path.exists(options['append']):
-            a = cPickle.load(open(options['append'], 'rb'))
-        else:
-            a = app.Application(options.subCommand, int(options['uid']), int(options['gid']))
 
     try:
         mod.updateApplication(a, options.subOptions)
@@ -158,22 +186,13 @@
         for portno, factory in mod.getPorts():
             a.listenTCP(portno, factory)
 
-    # backwards compatibility for old --xml and --source options
-    if options['xml']:
-        options['type'] = 'xml'
-    if options['source']:
-        options['type'] = 'source'
-
-    a.persistStyle = ({'xml': 'xml',
-                       'source': 'aot',
-                       'pickle': 'pickle'}
-                       [options['type']])
+    if not options['append']:
+        a.persistStyle = ({'xml': 'xml',
+                           'source': 'aot',
+                           'pickle': 'pickle'}
+                          [options['type']])
     if options['encrypted']:
-        try:
-            import Crypto
-            a.save(passphrase=util.getPassword("Encryption passphrase: "))
-        except ImportError:
-            print "The --encrypt flag requires the PyCrypto module, no file written."
+        a.save(passphrase)
     elif options['append']:
         a.save(filename=options['append']) 
     else:
--- TwistedClean/twisted/scripts/twistd.py	Tue Nov 26 00:07:33 2002
+++ Twisted/twisted/scripts/twistd.py	Sat Nov 30 18:32:06 2002
@@ -19,12 +19,11 @@
 from twisted import copyright
 from twisted.python import usage, util, runtime, register, plugin
 from twisted.python import log, logfile
-from twisted.persisted import styles
+#from twisted.persisted import styles
+from twisted.persisted.apploader import loaders, loadPersisted
 util.addPluginDir()
 
 # System Imports
-from cPickle import load, loads
-from cStringIO import StringIO
 import traceback
 import imp
 import sys, os
@@ -57,27 +56,43 @@
                                   "spawning processes.  Use with caution.)"],
                 ['encrypted', 'e', "The specified tap/aos/xml file is encrypted."]]
 
-    optParameters = [['logfile','l', None,
-                   "log to a specified file, - for stdout"],
-                  ['file','f','twistd.tap',
-                   "read the given .tap file"],
-                  ['prefix', None,'twisted',
-                   "use the given prefix when syslogging"],
-                  ['python','y', None,
-                   "read an application from within a Python file"],
-                  ['xml', 'x', None,
-                   "Read an application from a .tax file (Marmalade format)."],
-                  ['source', 's', None,
-                   "Read an application from a .tas file (AOT format)."],
-                  ['pidfile','','twistd.pid',
-                   "Name of the pidfile"],
-                  ['rundir','d','.',
-                   'Change to a supplied directory before running'],
-                  ['chroot', None, None,
-                   'Chroot to a supplied directory before running'],
-                  ['reactor', 'r', None,
-                   'Which reactor to use out of: %s.' % ', '.join(reactorTypes.keys())]]
+    optParameters =  [['logfile','l', None,
+                       "log to a specified file, - for stdout"],
+                      ['type','t', 'guess',
+                       "format of config file out of: %s." %', '.join(loaders.keys())],
+                      ['file','f','twistd.tap',
+                       "read the given .tap file"],
+                      ['prefix', None,'twisted',
+                       "use the given prefix when syslogging"],
+                      ['pidfile','','twistd.pid',
+                       "Name of the pidfile"],
+                      ['rundir','d','.',
+                       'Change to a supplied directory before running'],
+                      ['chroot', None, None,
+                       'Chroot to a supplied directory before running'],
+                      ['reactor', 'r', 'default',
+                       'Which reactor to use out of: %s.' % ', '.join(reactorTypes.keys())]]
 
+    def opt_python(self, filename):
+        """read an application from within a Python file
+        """
+        self['type'] = 'python'
+        self['file'] = filename
+    opt_y = opt_python
+
+    def opt_xml(self, filename):
+        """Read an application from a .tax file (Marmalade format).
+        """
+        self['type'] = 'xml'
+        self['file'] = filename
+    opt_x = opt_xml
+
+    def opt_source(self, filename):
+        """Read an application from a .tas file (AOT format)."""
+        self['type'] = 'source'
+        self['file'] = filename
+    opt_s = opt_source
+    
     def opt_plugin(self, pkgname):
         """read config.tac from a plugin package, as with -y
         """
@@ -86,7 +101,7 @@
         except ImportError:
             print "Error: Package %s not found. Is it in your ~/TwistedPlugins directory?" % pkgname
             sys.exit()
-        self.opts['python'] = os.path.join(fname, 'config.tac')
+        self.opt_python(os.path.join(fname, 'config.tac'))
 
     def opt_version(self):
         """Print version information and exit.
@@ -111,93 +126,9 @@
 
     opt_g = opt_plugin
 
-
-def decrypt(passphrase, data):
-    import md5
-    from Crypto.Cipher import AES
-    return AES.new(md5.new(passphrase).digest()[:16]).decrypt(data)
-
-
-def createApplicationDecoder(config):
-    mainMod = sys.modules['__main__']
-
-    # Twisted Imports
-    class EverythingEphemeral(styles.Ephemeral):
-        def __getattr__(self, key):
-            try:
-                return getattr(mainMod, key)
-            except AttributeError:
-                if initRun:
-                    raise
-                else:
-                    log.msg("Warning!  Loading from __main__: %s" % key)
-                    return styles.Ephemeral()
-
-    # Application creation/unserializing
-    if config['python']:
-        def decode(filename, data):
-            log.msg('Loading %s...' % (filename,))
-            d = {'__file__': filename}
-            exec data in d, d
-            try:
-                return d['application']
-            except KeyError:
-                log.msg("Error - python file %s must set a variable named 'application', an instance of twisted.internet.app.Application. No such variable was found!" % (repr(filename),))
-                sys.exit()
-        filename = os.path.abspath(config['python'])
-        mode = 'r'
-    elif config['xml']:
-        def decode(filename, data):
-            from twisted.persisted.marmalade import unjellyFromXML
-            log.msg('<Loading file="%s" />' % (filename,))
-            sys.modules['__main__'] = EverythingEphemeral()
-            application = unjellyFromXML(StringIO(data))
-            application.persistStyle = 'xml'
-            sys.modules['__main__'] = mainMod
-            styles.doUpgrade()
-            return application
-        filename = config['xml']
-        mode = 'r'
-    elif config['source']:
-        def decode(filename, data):
-            from twisted.persisted.aot import unjellyFromSource
-            log.msg("Loading %s..." % (filename,))
-            sys.modules['__main__'] = EverythingEphemeral()
-            application = unjellyFromSource(StringIO(data))
-            application.persistStyle = 'aot'
-            sys.modules['__main__'] = mainMod
-            styles.doUpgrade()
-            return application
-        filename = config['source']
-        mode = 'r'
-    else:
-        def decode(filename, data):
-            log.msg("Loading %s..." % (filename,))
-            sys.modules['__main__'] = EverythingEphemeral()
-            application = loads(data)
-            sys.modules['__main__'] = mainMod
-            styles.doUpgrade()
-            return application
-        filename = config['file']
-        mode = 'rb'
-    return filename, decode, mode
-
-
-def loadApplication(config, passphrase):
-    filename, decode, mode = createApplicationDecoder(config)
-    if config['encrypted']:
-        data = open(filename, 'rb').read()
-        data = decrypt(passphrase, data)
-        try:
-            return decode(filename, data)
-        except:
-            # Too bad about this.
-            log.msg("Error loading Application - perhaps you used the wrong passphrase?")
-            raise
-    else:
-        data = open(filename, mode).read()
-        return decode(filename, data)
-
+def loadApplication(cfg, passphrase):
+    app = loadPersisted(cfg['file'], cfg['type'], cfg['encrypted'], passphrase)
+    return app
 
 def debugSignalHandler(*args):
     """Break into debugger."""
--- TwistedClean/twisted/scripts/coil.py	Wed Apr 24 01:58:21 2002
+++ Twisted/twisted/scripts/coil.py	Mon Dec  2 16:23:01 2002
@@ -37,8 +37,9 @@
 
 """
     
-    optParameters = [["new", "n", None],
-                     ["port", "p", 9080]]
+    optParameters = [["new",    "n", None],
+                     ["port",   "p", 9080],
+                     ["format", "f", 'guess']]
     
     optFlags = [["localhost", "l"]]
 
@@ -73,9 +74,8 @@
     if new:
         application = app.Application(new)
     else:
-        f = open(tapFile, "rb")
-        application = pickle.loads(f.read())
-        f.close()
+        from twisted.internet.apploader import loadPersisted
+        application = loadPersisted(tapFile, config['format'], naive=1)
         if not isinstance(application, app.Application):
             raise TypeError, "The loaded object %s is not a twisted.internet.app.Application instance." % application
     
--- TwistedClean/twisted/scripts/tapconvert.py	Tue Nov 26 00:07:32 2002
+++ Twisted/twisted/scripts/tapconvert.py	Sat Nov 30 18:53:05 2002
@@ -22,122 +22,7 @@
 from cPickle import load
 from cStringIO import StringIO
 
-mainMod = sys.modules['__main__']
-
-# Functions from twistd/mktap
-
-class EverythingEphemeral(styles.Ephemeral):
-    def __getattr__(self, key):
-        try:
-            return getattr(mainMod, key)
-        except AttributeError:
-            log.msg("Warning!  Loading from __main__: %s" % key)
-            return styles.Ephemeral()
-
-
-class LoaderCommon:
-    """Simple logic for loading persisted data"""
-
-    loadmessage = "Loading %s..."
-
-    def __init__(self, filename, encrypted=None, passphrase=None):
-        self.filename = filename
-        self.encrypted = encrypted
-        self.passphrase = passphrase
-
-    def load(self):
-        "Returns the application"
-        log.msg(self.loadmessage % self.filename)
-        if self.encrypted:
-            self.data = open(self.filename, 'r').read()
-            self.decrypt()
-        else:
-            self.read()
-        return self.decode()       
-        
-    def read(self):
-        self.data = open(self.filename, 'r').read()
-        
-    def decrypt(self):
-        try:
-            import md5
-            from Crypto.Cipher import AES
-            self.data = AES.new(md5.new(self.passphrase).digest()[:16]).decrypt(self.data)
-        except ImportError:
-            print "The --decrypt flag requires the PyCrypto module, no file written."
-            
-    def decode(self):
-        pass
-
-
-class LoaderXML(LoaderCommon):
-
-    loadmessage = '<Loading file="%s" />' 
-
-    def decode(self):
-        from twisted.persisted.marmalade import unjellyFromXML
-        sys.modules['__main__'] = EverythingEphemeral()
-        application = unjellyFromXML(StringIO(self.data))
-        sys.modules['__main__'] = mainMod
-        styles.doUpgrade()
-        return application
-
-
-class LoaderPython(LoaderCommon):
-
-    def read(self):
-        pass
-
-    def decrypt(self):
-        log.msg("Python files are never encrypted")
-
-    def decode(self):
-        pyfile = os.path.abspath(self.filename)
-        d = {'__file__': self.filename}
-        execfile(pyfile, d, d)
-        try:
-            application = d['application']
-        except KeyError:
-            log.msg("Error - python file %s must set a variable named 'application', an instance of twisted.internet.app.Application. No such variable was found!" % repr(self.filename))
-            sys.exit()
-        return application
-
-
-class LoaderSource(LoaderCommon):
-
-    def decode(self):
-        from twisted.persisted.aot import unjellyFromSource
-        sys.modules['__main__'] = EverythingEphemeral()
-        application = unjellyFromSource(StringIO(self.data))
-        application.persistStyle = "aot"
-        sys.modules['__main__'] = mainMod
-        styles.doUpgrade()
-        return application
-
-
-class LoaderTap(LoaderCommon):
-
-    def decode(self):
-        sys.modules['__main__'] = EverythingEphemeral()
-        application = load(StringIO(self.data))
-        sys.modules['__main__'] = mainMod
-        styles.doUpgrade()
-        return application
-
-
-loaders = {'python': LoaderPython,
-           'xml': LoaderXML,
-           'source': LoaderSource,
-           'pickle': LoaderTap}
-
-
-def loadPersisted(filename, kind, encrypted, passphrase):
-    "Loads filename, of the specified kind and returns an application"
-    Loader = loaders[kind]
-    l = Loader(filename, encrypted, passphrase)
-    application = l.load()
-    return application
-
+from twisted.persisted.apploader import loadPersisted
 
 def savePersisted(app, filename, encrypted):
     if encrypted:
@@ -167,19 +52,6 @@
             raise usage.UsageError("You must specify the input filename.")
 
 
-def guessType(filename):
-    ext = os.path.splitext(filename)[1]
-    try:
-        return {
-            '.py':  'python',
-            '.tap': 'pickle',
-            '.tas': 'source',
-            '.tax': 'xml'
-        }[ext]
-    except KeyError:
-        raise usage.UsageError("Could not guess type for '%s'" % (filename,))
-
-
 def run():
     options = ConvertOptions()
     try:
@@ -193,6 +65,8 @@
         import getpass
         passphrase = getpass.getpass('Passphrase: ')
 
+    if None in [options['in']]:
+        options.opt_help()
     if options["typein"] == "guess":
         options["typein"] = guessType(options["in"])
 
