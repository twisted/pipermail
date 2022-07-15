diff -urN ./names/authority.py /usr/local/python/lib/python2.3/site-packages/twisted/names/authority.py
--- ./names/authority.py	Fri Sep 19 14:37:13 2003
+++ /usr/local/python/lib/python2.3/site-packages/twisted/names/authority.py	Sun Feb 15 21:40:34 2004
@@ -226,13 +226,12 @@
             L.append(line.split())
         return filter(None, L)
 
-
     def parseLines(self, lines):
         TTL = 60 * 60 * 3
         ORIGIN = self.origin
-        
+
         self.records = {}
-        
+
         for (line, index) in zip(lines, range(len(lines))):
             if line[0] == '$TTL':
                 TTL = dns.str2time(line[1])
@@ -321,3 +320,97 @@
 #        print 'rdata is ', rdata
 
         self.addRecord(owner, ttl, type, domain, cls, rdata)
+
+
+class TinyDNSAuthority(FileAuthority):
+    """An Authority that loads Tiny DNS configuration files"""
+    
+    def loadFile(self, filename):
+        self.origin = os.path.basename(filename) + '.' # XXX - this might suck
+        lines = open(filename).readlines()
+        lines = self.stripComments(lines)
+        lines = self.collapseContinuations(lines)
+        self.parseLines(lines)
+
+
+    def stripComments(self, lines):
+        return [
+        x for x in [
+                a.find('#') == -1 and a or a[:a.find('#')] for a in [
+                   b.strip() for b in lines
+                ]
+        ] if x != ''    
+        ]
+
+
+    def collapseContinuations(self, lines):
+        return lines
+
+
+    def parseLines(self, lines):
+    # http://cr.yp.to/djbdns/tinydns-data.html
+
+        self.records = {}
+
+        for line in lines:
+            # .fqdn:ip:x:ttl:timestamp:lo
+            if line[0] == "." :
+                (fqdn, ip, x, ttl) = line[1:].split(":")
+                if x.find('.') == -1 : 
+                    x = "%s.ns.%s" % ( x, fqdn )
+
+                soa_record = dns.Record_SOA( mname     = x, 
+                                             rname     = "hostmaster.%s" % ( fqdn ), 
+                                             serial    = time.time(),
+                                             refresh   = 16384,
+                                             retry     = 2048,
+                                             expire    = 1048576,
+                                             minimum   = 2560,
+                                             ttl       = ttl )
+    
+                self.addRecord( fqdn, soa_record )
+                self.soa = (fqdn, soa_record)
+
+                self.addRecord( x, dns.Record_NS( fqdn, ttl ) )
+
+                if ip != '':
+                    self.addRecord( x, dns.Record_A( ip, ttl ) )
+
+            # &fqdn:ip:x:ttl:timestamp:lo
+            elif line[0] == "&" :
+                (fqdn, ip, x, ttl) = line[1:].split(":")
+                if x.find('.') == -1 : 
+                    x = "%s.ns.%s" % ( x, fqdn )
+
+                self.addRecord( x, dns.Record_NS( fqdn, ttl ) )
+                self.addRecord( x, dns.Record_A( ip, ttl ) )
+
+            # =fqdn:ip:ttl:timestamp:lo
+            elif line[0] == "=" :
+                (fqdn, ip, ttl) = line[1:].split(":")
+                self.addRecord( fqdn, dns.Record_A( ip, ttl ) )
+                (a,b,c,d) = ip.split('.')
+                self.addRecord( '%s.%s.%s.%s.in-addr.arpa' % (d,c,b,a), dns.Record_PTR( fqdn, ttl ) )
+
+            # +fqdn:ip:ttl:timestamp:lo
+            elif line[0] == "+" :
+                (fqdn, ip, ttl) = line[1:].split(":")
+                self.addRecord( fqdn, dns.Record_A( ip, ttl ) )
+
+            # @fqdn:ip:x:dist:ttl:timestamp:lo
+            elif line[0] == "@" :
+                (fqdn, ip, x, dist, ttl) = line[1:].split(":")
+                if x.find('.') == -1 : 
+                    x = "%s.mx.%s" % ( x, fqdn )
+                if dist == '' :
+                    dist = '0'
+
+                self.addRecord( x, dns.Record_A( ip, ttl ) )
+                self.addRecord( fqdn, dns.Record_MX( dist, x ) )
+
+            else :
+                raise NotImplementedError, "Data line '%s' not supported yet" % line[0]
+
+
+    def addRecord( self, domain, record ) :
+        self.records.setdefault(domain.lower(), []).append(record)
diff -urN ./names/tap.py /usr/local/python/lib/python2.3/site-packages/twisted/names/tap.py
--- ./names/tap.py	Thu Dec  4 20:54:03 2003
+++ /usr/local/python/lib/python2.3/site-packages/twisted/names/tap.py	Sun Feb 15 07:00:15 2004
@@ -50,6 +50,7 @@
         usage.Options.__init__(self)
         self['verbose'] = 0
         self.bindfiles = []
+        self.tinydnsfiles = []
         self.zonefiles = []
         self.secondaries = []
 
@@ -60,6 +61,14 @@
             raise usage.UsageError(filename + ": No such file")
         self.zonefiles.append(filename)
 
+
+    def opt_tinydnszone(self, filename):
+        """Specify the filename of a Tiny DNS syntax zone definition"""
+        if not os.path.exists(filename):
+            raise usage.UsageError(filename + ": No such file")
+        self.tinydnsfiles.append(filename)
+
+
     def opt_bindzone(self, filename):
         """Specify the filename of a BIND9 syntax zone definition"""
         if not os.path.exists(filename):
@@ -95,12 +104,21 @@
             except Exception, e:
                 traceback.print_exc()
                 raise usage.UsageError("Invalid syntax in " + f)
+
         for f in self.bindfiles:
             try:
                 self.zones.append(authority.BindAuthority(f))
             except Exception, e:
                 traceback.print_exc()
                 raise usage.UsageError("Invalid syntax in " + f)
+
+        for f in self.tinydnsfiles:
+            try:
+                self.zones.append(authority.TinyDNSAuthority(f))
+            except Exception, e:
+                traceback.print_exc()
+                raise usage.UsageError("Invalid syntax in " + f)
+
         for f in self.secondaries:
             self.svcs.append(secondary.SecondaryAuthorityService(*f))
             self.zones.append(self.svcs[-1].getAuthority())
