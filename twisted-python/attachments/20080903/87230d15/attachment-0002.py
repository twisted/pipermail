# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

from zope.interface import implements

from twisted.spread import pb
from twisted.cred.portal import IRealm

from twisted.spread.pb import Referenceable

class FilePageWriter(Referenceable):
    """ A Pager-receiver that writes to a file. """
    def __init__(self,
                 file_name,
                 deferred=None):
        self.file_name = file_name
        self.fobj = open(file_name,
                         'w')
        self.deferred = deferred

    def remote_gotPage(self,
                       page):
        self.fobj.write(page)

    def remote_endedPaging(self):
        self.close()

    def close(self):
        if not self.fobj.closed:
            self.fobj.close()
        if self.deferred:
            self.deferred.callback("done")

class SimplePerspective(pb.Avatar):
    def logout(self):
        print self, "logged out"

    def perspective_save_file(self, 
                              file_name):
        fpw = FilePageWriter(file_name)
        return fpw

class SimpleRealm:
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            avatar = SimplePerspective()
            return pb.IPerspective, avatar, avatar.logout 
        else:
            raise NotImplementedError("no interface")


if __name__ == '__main__':
    from twisted.internet import reactor
    from twisted.cred.portal import Portal
    from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
    portal = Portal(SimpleRealm())
    checker = InMemoryUsernamePasswordDatabaseDontUse()
    checker.addUser("guest", "guest")
    portal.registerChecker(checker)
    reactor.listenTCP(pb.portno, pb.PBServerFactory(portal))
    reactor.run()
