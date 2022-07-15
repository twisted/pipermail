import os
from twisted.cred import credentials, checkers, error
from twisted.enterprise import adbapi
from twisted.python import failure
from zope.interface import implements
from pysqlite2 import dbapi2


class DbChecker:
    """
    A simple checker with a database backend.
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self):
        # remove userdb file if there's one from last run
        if os.path.exists('userdb'):
            os.remove('userdb')
        # create a new auth database
        con = dbapi2.connect('userdb')
        cur = con.cursor()
        cur.executescript("""
            create table users
                (
                  userid      varchar(20),
                  passwd      varchar(20)
                );
            insert into users (userid, passwd) values ('spam', 'eggs');""")
        cur.close()
        self.db = adbapi.ConnectionPool('pysqlite2.dbapi2',
                                        'userdb')

    def _verifyCreds(self, creds):
        """
        Verify credentials, returning username if successful.
        """
        res = self.db.runQuery(
            """SELECT * from users where userid = ? and passwd = ?""",
            (creds.username, creds.password))
        def succeeded(r):
            if len(r) == 1:
                return creds.username
            elif len(r) == 0:
                return failure.Failure(error.UnauthorizedLogin())
        def failed(e):
            raise LookupError, e
        return res.addCallbacks(succeeded, failed)

    def requestAvatarId(self, c):
        if not c.username or not c.password:
            return failure.Failure(error.UnauthorizedLogin())
        return self._verifyCreds(c)


