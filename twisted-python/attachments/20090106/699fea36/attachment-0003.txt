#! /usr/bin/python

from zope.interface import implements

from twisted.cred import portal, checkers, credentials, error
from twisted.cred.checkers import ICredentialsChecker
from twisted.spread import pb
from twisted.internet import reactor, defer

class AuthError(pb.Error):
    pass

class Server(pb.Viewable):

    def view_echo(self, avatar, message):
        print 'Message received from avatar %s: %s' % (avatar, message)

class ServerRealm:
    implements(portal.IRealm)

    def __init__(self, server):
        self.server = server

    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = User(avatarID, self.server)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class User(pb.Avatar):

    def __init__(self, name, server):
        self.name = name
        self.server = server

    def detached(self, mind):
        pass

    def perspective_getAppServer(self):
        return self.server

class UserChecker:
    implements(ICredentialsChecker)

    credentialInterfaces = (credentials.IUsernamePassword, \
                            credentials.IUsernameHashedPassword)

    @defer.inlineCallbacks
    def requestAvatarId(self, credentials):

        pwdList = {'user': 'pass'}

        if pwdList.has_key(credentials.username):
            matched = yield credentials.checkPassword(pwdList[credentials.username])
            if matched:
                print 'OK: Login successful'
                defer.returnValue(None)

        print 'ERR: Login failed'
        raise AuthError

appServer = Server()
realm = ServerRealm(appServer)

checker = UserChecker()
p = portal.Portal(realm, [checker])

reactor.listenTCP(8000, pb.PBServerFactory(p))
print "Server started listening"
reactor.run()