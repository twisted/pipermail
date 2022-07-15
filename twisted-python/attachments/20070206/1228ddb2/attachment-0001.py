import sha
from zope.interface import Interface, implements
from twisted.cred import portal, checkers, credentials

class IHTTPUser(Interface):
    pass

class HTTPUser(object):
    implements(IHTTPUser)

class HTTPAuthRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IHTTPUser in interfaces:
            return IHTTPUser, HTTPUser()

        raise NotImplementedError("Only IHTTPUser interface is supported")

class UserDbCredChecker:

    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, userdb):
        self.db = userdb

    def _verifyCreds(self, creds):
        """
        Verify credentials, returning the username if successful.
        """
        res = self.db.runQuery(
            """SELECT * from _passwd where _oid = %s
               and _password = %s""",
            (creds.username, 
             sha.sha(creds.password).hexdigest()))
        def succeeded(r):
            try:
                if len(r) == 1:
                    return creds.username
                elif len(r) == 0:
                    return failure.Failure(error.UnauthorizedLogin())
            except:
                # Houston, we have a problem ...
                # should probably have user notify admin
                e = 'User database appears to be borken'
                raise ValueError, e
        def failed(e):
            raise LookupError, e
        return res.addCallbacks(succeeded, failed)

    def requestAvatarId(self, c):
        if not c.username or not c.password:
            return failure.Failure(error.UnauthorizedLogin())
        return self._verifyCreds(c)

