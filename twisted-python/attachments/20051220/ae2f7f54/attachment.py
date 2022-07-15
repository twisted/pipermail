"""Minor revisions to echo server to use SSL sockets for connections"""
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.spread import pb
from twisted.cred.portal import IRealm

class DefinedError(pb.Error):
	pass


class SimplePerspective(pb.Avatar):

	def perspective_echo(self, text):
		print 'echoing',text
		return text

	def perspective_error(self):
		raise DefinedError("exception!")

	def logout(self):
		print self, "logged out"


class SimpleRealm:
	__implements__ = IRealm

	def requestAvatar(self, avatarId, mind, *interfaces):
		if pb.IPerspective in interfaces:
			avatar = SimplePerspective()
			return pb.IPerspective, avatar, avatar.logout 
		else:
			raise NotImplementedError("no interface")


if __name__ == '__main__':
	from twisted.internet import reactor, ssl 
	from twisted.application import internet
	from twisted.cred.portal import Portal
	from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
	def setup():
		portal = Portal(SimpleRealm())
		checker = InMemoryUsernamePasswordDatabaseDontUse()
		checker.addUser("guest", "guest")
		portal.registerChecker(checker)
		rootSite = pb.PBServerFactory(portal)
		sslContext = ssl.DefaultOpenSSLContextFactory(
			'privkey.pem', 
			'cacert.pem',
		)
		serve = internet.SSLServer(
			pb.portno, 
			rootSite, 
			sslContext,
		)
	reactor.callWhenRunning( setup )
	reactor.run()
