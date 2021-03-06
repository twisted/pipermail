#!/usr/bin/env python

from zope.interface import implements

from twisted.cred import portal, checkers
from twisted.spread import pb
from twisted.internet import reactor

class MyViewable(pb.Viewable):
    def view_test(self, perspective, description):
        print("This viewpoint was %s the Avatar"%description)
        print("and we got the following perspective: %s"%perspective)


class MyRealm(object):
    implements(portal.IRealm)
    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = User(avatarID, mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.logout()


class User(pb.Avatar):
    def __init__(self, name, mind):
        self.name = name
        self.mind = mind
        self.v = MyViewable()
        mind.callRemote("takeViewable", self.v)

    def perspective_getViewable(self):
        return self.v

    def logout(self):
        self.mind = None


realm = MyRealm()
checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
checker.addUser("alice", "1234")
p = portal.Portal(realm, [checker])

reactor.listenTCP(8800, pb.PBServerFactory(p))
reactor.run()