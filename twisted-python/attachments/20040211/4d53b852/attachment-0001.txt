# Twisted, the Framework of Your Internet
# Copyright (C) 2001 Matthew W. Lefkowitz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This example extends the cred.py example to use a db-based
checker.

Note:  this example assumes that PostgreSQL is installed and a
database named 'userdb' has been created.

credwithdb.py will set up the users table, populate it with a
test user, and drop the table when it exits, so it can be
modified and run again.
"""

import sys
from pyPgSQL import PgSQL

from twisted.protocols import basic
from twisted.internet import protocol
from twisted.internet import defer
from twisted.python import components
from twisted.python import failure
from twisted.python import log
from twisted.enterprise import adbapi

from twisted.cred import error
from twisted.cred import portal
from twisted.cred import checkers
from twisted.cred import credentials

schema = """
CREATE TABLE users (
    username    varchar(64) PRIMARY KEY,
    password    varchar(64)
)
"""

testdata = """
INSERT INTO users VALUES (
    'moi',
    'secret'
)
"""

class IProtocolUser(components.Interface):
    def getPrivileges(self):
        """Return a list of privileges this user has."""

    def logout(self):
        """Cleanup per-login resources allocated to this avatar"""

class User:
    __implements__ = (IProtocolUser,)
    
    def __init__(self, id):
        self.id = id

    def getPrivileges(self):
        return [1, 2, 3]

    def logout(self):
        print "Cleaning up user resources"

class Protocol(basic.LineReceiver):
    user = None
    portal = None
    avatar = None
    logout = None

    def connectionMade(self):
        self.sendLine("Login with USER <name> followed by PASS <password> or ANON")
        self.sendLine("Check privileges with PRIVS")

    def connectionLost(self, reason):
        if self.logout:
            self.logout()
            self.avatar = None
            self.logout = None
    
    def lineReceived(self, line):
        f = getattr(self, 'cmd_' + line.upper().split()[0])
        if f:
            try:
                f(*line.split()[1:])
            except TypeError:
                self.sendLine("Wrong number of arguments.")
            except:
                self.sendLine("Server error (probably your fault)")

    def cmd_USER(self, name):
        self.user = name
        self.sendLine("Alright.  Now PASS?")
    
    def cmd_PASS(self, password):
        if not self.user:
            self.sendLine("USER required before PASS")
        else:
            if self.portal:
                self.portal.login(
                    credentials.UsernamePassword(self.user, password),
                    None,
                    IProtocolUser
                ).addCallbacks(self._cbLogin, self._ebLogin
                )
            else:
                self.sendLine("DENIED")

    def cmd_PRIVS(self):
        self.sendLine("You have the following privileges: ")
        self.sendLine(" ".join(map(str, self.avatar.getPrivileges())))

    def _cbLogin(self, (interface, avatar, logout)):
        assert interface is IProtocolUser
        self.avatar = avatar
        self.logout = logout
        self.sendLine("Login successful.  Available commands: PRIVS")
    
    def _ebLogin(self, failure):
        failure.trap(error.UnauthorizedLogin)
        self.sendLine("Login denied!  Go away.")

class ServerFactory(protocol.ServerFactory):
    protocol = Protocol
    
    def __init__(self, portal):
        self.portal = portal
    
    def buildProtocol(self, addr):
        p = protocol.ServerFactory.buildProtocol(self, addr)
        p.portal = self.portal
        return p

class Realm:
    __implements__ = portal.IRealm

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = User(avatarId)
        return IProtocolUser, av, av.logout

class SimpleAdbapiPasswdDb:
    __implements__ = (checkers.ICredentialsChecker,)

    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self):
        # db setup and teardown are synchronous; no big deal.
        conn = PgSQL.connect(database='userdb')
        curs = conn.cursor()
        curs.execute(schema)
        curs.execute(testdata)
        conn.commit()
        conn.close()
        self.dbpool = adbapi.ConnectionPool('pyPgSQL.PgSQL',
                                            database='userdb')

    def teardown(self):
        conn = PgSQL.connect(database='userdb')
        curs = conn.cursor()
        curs.execute('DELETE FROM users')
        curs.execute('DROP TABLE users')
        conn.commit()
        conn.close()

    def getUser(self, username):
        res = self.dbpool.runQuery(
                  """SELECT * from users where username = %s""",
                  (username,))
        if res:
            return res
        else:
            raise KeyError(username)

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, c):
        try:
            u = self.getUser(c.username).addCallback(lambda x:
                                                   x[0].username)
            p = self.getUser(c.username).addCallback(lambda x:
                                                   x[0].password)
        except KeyError:
            return failure.Failure(error.UnauthorizedLogin())
        else:
            return p.addCallback(
                c.checkPassword).addCallback(
                self._cbPasswordMatch, u)
        return failure.Failure(error.UnauthorizedLogin())

def main():
    r = Realm()
    p = portal.Portal(r)
    c = SimpleAdbapiPasswdDb()
    p.registerChecker(c)

    f = ServerFactory(p)

    log.startLogging(sys.stdout)

    from twisted.internet import reactor
    reactor.listenTCP(4738, f)
    reactor.run()
    c.teardown()

if __name__ == '__main__':
    main()

