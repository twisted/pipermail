import os, sys

authfile = os.path.expanduser ('~/.garlic/auth')
db = None
port = 8081

from twisted.cred import portal, checkers, credentials
from twisted.spread import pb
from twisted.internet import reactor
from twisted.web import static, server
from twisted.cred import checkers, portal

from twisted.python import log
log.startLogging (sys.stderr)

class Avatar (pb.Avatar):

    def __init__ (self, uid):

        self.id = uid
        return

Anonymous = Avatar ('')


class User (Avatar):

    def __init__ (self, uid, db):

        self.id = uid
        self.db = db

        return


class Realm:
    
    """A simple implementor of cred's IRealm."""

    __implements__ = portal.IRealm

    def __init__ (self, db):

        self.db = db
        return
    
    
    def requestAvatar (self, avatarId, mind, *interfaces):

        if User not in interfaces:
            raise NotImplementedError ("no supported interface")
            
        return (pb.IPerspective, User (avatarId, self.db), lambda : None)



def pw_hash (user, proposed, actual):

    parts = actual.split ('$', 3)

    salt = '$'.join (parts [:3])
    
    return crypt.crypt (proposed, salt)


check = checkers.FilePasswordDB (authfile, hash = pw_hash)

remote_portal = portal.Portal (Realm (db))
remote_portal.registerChecker (check)

from twisted.spread import pb

reactor.listenTCP (port, pb.PBServerFactory (remote_portal))

reactor.run ()
