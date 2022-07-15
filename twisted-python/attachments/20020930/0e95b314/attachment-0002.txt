? twisted_diff
? admin/test.log
? doc/examples/policy_example.py
? pyunit/test.log
? twisted/internet/gtkreactor.py.fixed
? twisted/internet/gtkreactor.py.patch
? twisted/protocols/irc.old.py
? twisted/protocols/irc.py.patch
? twisted/test/myrebuilder.py
? twisted/test/test.log
Index: twisted/internet/interfaces.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/interfaces.py,v
retrieving revision 1.45
diff -u -r1.45 interfaces.py
--- twisted/internet/interfaces.py	29 Sep 2002 04:27:50 -0000	1.45
+++ twisted/internet/interfaces.py	30 Sep 2002 05:41:20 -0000
@@ -26,6 +26,14 @@
 
 ### Reactor Interfaces
 
+class IFactoryPolicy(Interface):
+    """Object used to verify connections before buildProtocol is called
+       on a factory"""
+
+    def verify(self, addr):
+        """Method called for each connection, addr is a tuple of
+           (type, host, port), ie. ('INET','127.0.0.1','8080')"""
+
 class IConnector(Interface):
     """Object used to interface between connections and protocols.
 
Index: twisted/internet/protocol.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/protocol.py,v
retrieving revision 1.21
diff -u -r1.21 protocol.py
--- twisted/internet/protocol.py	27 Sep 2002 15:38:18 -0000	1.21
+++ twisted/internet/protocol.py	30 Sep 2002 05:41:21 -0000
@@ -214,6 +214,36 @@
     """Subclass this to indicate that your protocol.Factory is only usable for servers.
     """
 
+    policies = []
+
+    def addPolicy(self, policy):
+        """Add a policy to the list of policies that get verified per
+           connection"""
+        self.policies.append(policy)
+
+    def removePolicy(self, policy):
+        """Remove a policy from the list of policies"""
+        try: self.policies.remove(policy)
+        except ValueError: pass
+
+    def verifyPolicies(self, addr):
+        """Verify each policy of this factory.  Returns true only if
+           all policies verified the connection"""
+
+        for policy in self.policies:
+           if not policy.verify(addr): return 0
+        return 1
+
+    def buildProtocol(self, addr):
+        """ Default buildProtocol for each ServerFactory, subclasses wanting
+            support for policies will have to do their own verifying which involves
+            calling the verifyPolicies method as below """
+
+        if not self.verifyPolicies(addr):
+            return None
+        return Factory.buildProtocol(self, addr)
+
+
 
 class BaseProtocol:
     """This is the abstract superclass of all protocols.
Index: twisted/test/test_internet.py
===================================================================
RCS file: /cvs/Twisted/twisted/test/test_internet.py,v
retrieving revision 1.9
diff -u -r1.9 test_internet.py
--- twisted/test/test_internet.py	30 Aug 2002 19:15:21 -0000	1.9
+++ twisted/test/test_internet.py	30 Sep 2002 05:41:23 -0000
@@ -192,3 +192,18 @@
         protocol = factory.buildProtocol(None)
         self.assertEquals(protocol.factory, factory)
         self.assert_( isinstance(protocol, factory.protocol) )
+
+
+class MyPolicyFactory(protocol.ServerFactory): protocol = protocol.Protocol
+
+class MyPolicy:
+
+    def verify(self, addr): return 0
+
+class PolicyTestCase(unittest.TestCase):
+
+    def testPolicy(self):
+        factory = MyPolicyFactory()
+        factory.addPolicy(MyPolicy())
+        protocol = factory.buildProtocol(None)
+        assert protocol == None, "verify shouldn't have given me this protocol"
