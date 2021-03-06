Index: twisted/internet/app.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/app.py,v
retrieving revision 1.4
diff -c -r1.4 app.py
*** twisted/internet/app.py	13 Dec 2001 07:01:59 -0000	1.4
--- twisted/internet/app.py	24 Dec 2001 14:52:29 -0000
***************
*** 125,130 ****
--- 125,132 ----
          self.name = name
          # a list of (tcp, ssl, udp) Ports
          self.ports = []
+         # a list of (tcp, ssl, udp) Connectors
+         self.connectors = []
          # a list of twisted.python.delay.Delayeds
          self.delayeds = []
          # a list of twisted.internet.passport.Services
***************
*** 152,159 ****
          self.lock()
          
  
!     persistenceVersion = 3
! 
      def upgradeToVersion3(self):
          """Version 3 Persistence Upgrade
          """
--- 154,166 ----
          self.lock()
          
  
!     persistenceVersion = 4
!     
!     def upgradeToVersion4(self):
!         """Version 4 Persistence Upgrade
!         """
!         self.connectors = []
!     
      def upgradeToVersion3(self):
          """Version 3 Persistence Upgrade
          """
***************
*** 235,240 ****
--- 242,266 ----
          if self.running:
              port.startListening()
  
+     def connectTCP(self, host, port, factory):
+         """Connect a given client protocol factory to a specific TCP server."""
+         from twisted.internet import tcp
+         self.addConnector(tcp.Connector(host, port, factory))
+     
+     def connectSSL(self, host, port, factory, ctxFactory=None):
+         """Connect a given client protocol factory to a specific SSL server."""
+         from twisted.internet import ssl
+         c = ssl.Connector(host, port, factory)
+         if ctxFactory:
+             c.contextFactory = ctxFactory
+         self.addConnector(c)
+     
+     def addConnector(self, connector):
+         """Add a connector to this Application."""
+         self.connectors.append(connector)
+         if self.running:
+             connector.startConnecting()
+     
      def addDelayed(self, delayed):
          """
          Adds a twisted.python.delay.Delayed object for execution in my event loop.
***************
*** 326,331 ****
--- 352,359 ----
                  except socket.error:
                      print 'port %s already bound' % port.port
                      return
+             for connector in self.connectors:
+                 connector.startConnecting()
              for port in self.ports:
                  port.factory.startFactory()
              resolver = self.resolver
Index: twisted/internet/tcp.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/tcp.py,v
retrieving revision 1.35
diff -c -r1.35 tcp.py
*** twisted/internet/tcp.py	28 Nov 2001 07:17:29 -0000	1.35
--- twisted/internet/tcp.py	24 Dec 2001 14:52:30 -0000
***************
*** 239,251 ****
          s = '<%s to %s at %x>' % (self.__class__, self.addr, id(self))
          return s
  
  class Connector:
!     def __init__(self, host, factory, portno, timeout=30):
          self.host = host
          self.portno = portno
!         self.factory = factory
!         self.portno = portno
! 
      def connectionFailed(self):
          self.startConnecting()
  
--- 239,256 ----
          s = '<%s to %s at %x>' % (self.__class__, self.addr, id(self))
          return s
  
+ 
  class Connector:
!     """Connect a protocol to a server using TCP and if it fails make a new one."""
!     
!     transportFactory = Client
!     
!     def __init__(self, host, portno, protocolFactory, timeout=30):
          self.host = host
          self.portno = portno
!         self.factory = protocolFactory
!         self.timeout = timeout
!     
      def connectionFailed(self):
          self.startConnecting()
  
***************
*** 254,260 ****
  
      def startConnecting(self):
          proto = self.factory.buildProtocol((self.host, self.portno))
!         Client(self.host, self.portno, proto, 30, self)
          
  
  
--- 259,265 ----
  
      def startConnecting(self):
          proto = self.factory.buildProtocol((self.host, self.portno))
!         self.transportFactory(self.host, self.portno, proto, self.timeout, self)
          
  
  
Index: twisted/internet/ssl.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/ssl.py,v
retrieving revision 1.6
diff -c -r1.6 ssl.py
*** twisted/internet/ssl.py	29 Nov 2001 12:20:32 -0000	1.6
--- twisted/internet/ssl.py	24 Dec 2001 14:52:30 -0000
***************
*** 88,96 ****
      """I am an SSL client.
      """
      
!     def __init__(self, host, port, protocol, ctxFactory, timeout=None):
          self.ctxFactory = ctxFactory
!         apply(tcp.Client.__init__, (self, host, port, protocol), {'timeout': timeout})
      
      def createInternetSocket(self):
          """(internal) create an SSL socket
--- 88,96 ----
      """I am an SSL client.
      """
      
!     def __init__(self, host, port, protocol, ctxFactory, timeout=None, connector=None):
          self.ctxFactory = ctxFactory
!         apply(tcp.Client.__init__, (self, host, port, protocol), {'timeout': timeout, 'connector': connector})
      
      def createInternetSocket(self):
          """(internal) create an SSL socket
***************
*** 146,148 ****
--- 146,159 ----
              protocol.makeConnection(transport, self)
          except:
              traceback.print_exc(file=log.logfile)
+ 
+ 
+ class Connector(tcp.Connector):
+     """Connect a protocol to a server using SSL and if it fails make a new one."""
+     
+     transportFactory = Client
+     contextFactory = ClientContextFactory
+     
+     def startConnecting(self):
+         proto = self.factory.buildProtocol((self.host, self.portno))
+         self.transportFactory(self.host, self.portno, proto, self.contextFactory, self.timeout, self)
