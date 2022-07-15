# $Id: pgercred.py,v 1.11 2004/08/09 02:22:57 waterbug Exp $
"""
Authentication and credential management for PGER.
@version: $Revision: 1.11 $
"""
__version__ = "$Revision: 1.11 $"[11:-2]

import sys
import sha

from twisted.cred import error
from twisted.cred import portal
from twisted.cred import checkers
from twisted.cred import credentials
from twisted.python import components
from twisted.python import failure
from twisted.python import log
from twisted.web import resource
from twisted.web import server
from twisted.web import static

from pangalactic.repo.pgerxmlrpc    import PgerXmlrpcService
from pangalactic.repo.pgerupload    import FileUploadService
from pangalactic.repo.pgerwebupload import WebUploadResource


class AvatarResource(resource.Resource):

    __implements__ = resource.IResource

    def __init__(self, userid, realm=''):
        self.userid = userid
        self.realm = realm

    def logout(self):
        pass


class HttpRealm:

    __implements__ = portal.IRealm

    def __init__(self, name=''):
        self.name = name

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = AvatarResource(id=avatarId,
                            realm=self.name)
        return resource.IResource, av, av.logout


class XmlrpcAvatar(PgerXmlrpcService):

    __implements__ = resource.IResource

    def __init__(self, userid, realm='', engine=None):
        PgerXmlrpcService.__init__(self, engine=engine,
                                   userid=userid)
        self.userid = userid
        self.realm = realm

    def logout(self):
        pass


class XmlrpcRealm:

    __implements__ = portal.IRealm

    def __init__(self, name='', engine=None):
        self.name = name
        self.engine = engine

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = XmlrpcAvatar(userid=avatarId,
                          realm=self.name,
                          engine=self.engine)
        return resource.IResource, av, av.logout


class FileUploadAvatar(FileUploadService):

    __implements__ = resource.IResource

    def __init__(self, userid, realm='HTTP File Upload', engine=None):
        FileUploadService.__init__(self, 
                                   engine=engine,
                                   userid=userid)
        self.userid = userid
        self.realm = realm

    def logout(self):
        pass


class FileUploadRealm:

    __implements__ = portal.IRealm

    def __init__(self, name='HTTP File Upload', engine=None):
        self.name = name
        self.engine = engine

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = FileUploadAvatar(userid=avatarId,
                              realm=self.name,
                              engine=self.engine)
        return resource.IResource, av, av.logout


class WebUploadAvatar(WebUploadResource):

    __implements__ = resource.IResource

    def __init__(self, userid, realm='Web File Upload', engine=None):
        WebUploadResource.__init__(self, 
                                   engine=engine,
                                   userid=userid)
        self.userid = userid
        self.realm = realm

    def logout(self):
        pass


class WebUploadRealm:

    __implements__ = portal.IRealm

    def __init__(self, name='Web File Upload', engine=None):
        self.name = name
        self.engine = engine

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = WebUploadAvatar(userid=avatarId,
                              realm=self.name,
                              engine=self.engine)
        return resource.IResource, av, av.logout


class StaticAvatarResource(static.File):

    __implements__ = resource.IResource

    def __init__(self, root, *args, **kw):
        static.File.__init__(self, root, *args, **kw)

    def logout(self):
        pass


class StaticHttpRealm:

    __implements__ = portal.IRealm

    def __init__(self, name='', root=''):
        self.name = name
        self.root = root

    def requestAvatar(self, avatarId, mind, *interfaces):
        av = StaticAvatarResource(self.root)
        return resource.IResource, av, av.logout


class UserDbCredChecker:

    __implements__ = (checkers.ICredentialsChecker,)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, userdb):
        self.db = userdb

    def _verifyCreds(self, creds):
        """
        Verify credentials, returning the username if successful.
        """
        res = self.db.runQuery(
            """SELECT * from _passwd where _pgef_oid = %s
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


class BasicAuthResource:
    """
    A resource requiring http basic authentication.
    """

    __implements__ = resource.IResource
    isLeaf = True

    def __init__(self, portal):
        self.portal = portal
        self.httpRealm = portal.realm.name

    def render(self, request):
        username, password = request.getUser(), request.getPassword()
        creds = credentials.UsernamePassword(username, password)
        d = self.portal.login(creds, None, resource.IResource)
        def cb((_, r, logout)):
            request.notifyFinish().addBoth(lambda _: logout())
            result = resource.getChildForRequest(r, request).render(request)
            if result != server.NOT_DONE_YET:
                request.write(result)
                request.finish()
        def eb(f):
            try:
                f.trap(error.LoginFailed,
                       error.UnauthorizedLogin)
                log.msg('BasicAuth error: %s' % f)
                request.setResponseCode(401)
                request.setHeader("www-authenticate",
                                  'Basic realm="%s"' % self.httpRealm)
                request.finish()
            except:
                log.msg('Error during auth: %s' % f)
                request.finish()
        d.addCallbacks(callback=cb,errback=eb)
        d.addErrback(log.err)
        return server.NOT_DONE_YET




