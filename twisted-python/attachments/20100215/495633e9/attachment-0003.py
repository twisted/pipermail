#!/usr/bin/env python

from twisted.cred import error
from twisted.cred.credentials import IUsernameHashedPassword, IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.internet.defer import Deferred
from twisted.python import log
from twisted.enterprise import adbapi
from twisted.cred.portal import Portal, IRealm
from twisted.spread import pb
from twisted.internet import reactor
from OpenSSL import SSL
  
from zope.interface import implements

import sys

class DBCredentialsChecker(object):
    implements(ICredentialsChecker)

    def __init__(self, dbConn):
        
	self.dbConn = dbConn
        self.credentialInterfaces = (IUsernamePassword, IUsernameHashedPassword,)

    def requestAvatarId(self, credentials):
	userName = str.strip(credentials.username)
	queryStr = "SELECT username, password FROM ruser WHERE username = '%s'" % userName
        dbDeferred = self.dbConn.runQuery(queryStr)
        deferred = Deferred()
        dbDeferred.addCallbacks(self._cbAuthenticate, self._ebAuthenticate,
				callbackArgs=(credentials, deferred),
				errbackArgs=(credentials, deferred))
        return deferred

    def _cbAuthenticate(self, result, credentials, deferred):
	if len(result) == 0:
	    deferred.errback(error.UnauthorizedLogin('Username unknown'))
        else:
            username, password = result[0]
	    username = username.strip()
	    password = password.strip()
	    if credentials.checkMD5Password(password):
		deferred.callback(credentials.username)
            else:
                deferred.errback(error.UnauthorizedLogin('Password mismatch'))
    def _ebAuthenticate(self, message, credentials, deferred):
        deferred.errback(error.LoginFailed(message))

class DefinedError(pb.Error):
    pass

class RqueueAvatar(pb.Avatar):

    def setUserInfo(self, userId, userName, fullName):
	self.userId = userId
	self.userName = userName
	self.fullName = fullName

    def perspective_userInfo(self):
	return (self.userId, self.userName, self.fullName)

    def perspective_getFile(self, fileName):
	file = open(fileName, "rb")
	return file.read()

    def perspective_sendFile(self, data, fileName):
	file = open("cp-" + fileName, "wb")
	file.write(data)
	file.close()
	return fileName

    def perspective_echo(self, text):
        print 'echoing', text
	message = "%s: %s" % (self.userName, text)
        return message

    def perspective_error(self):
        raise DefinedError("exception!")

    def logout(self):
        print "logged out"


class RqueueRealm:

    implements(IRealm)

    def __init__(self, dbConn):
	self.dbConn = dbConn

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective  in interfaces:
	    userName = avatarId
            userQuery = "SELECT ruser_id, username, fullname FROM ruser WHERE username = '%s'" % userName
            deferred = self.dbConn.runQuery(userQuery)
	    return deferred.addCallback(self._gotQueryResults)
        else:
            raise NotImplementedError("Only pb.IPerspective interface is supported by this realm")

    def _gotQueryResults(self, rows):
        userId, userName, fullName = rows[0]
	userName = userName.strip()
	fullName = fullName.strip()
        self._registerLogin(userId)
	avatar = RqueueAvatar()
	avatar.setUserInfo(userId, userName, fullName)
	return pb.IPerspective, avatar, avatar.logout
    
    def _registerLogin(self, avatarId):
        "Add counter and set login flag to the user entry"
        pass

class ServerContextFactory:
    
    def getContext(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
	ctx.use_certificate_file('/etc/ssl/private/pure-ftpd.pem')
        ctx.use_privatekey_file('/etc/ssl/private/pure-ftpd.pem')
        return ctx


DB_DRIVER = "pyPgSQL.PgSQL"
DB_ARGS = {'database': 'cttc-rusers', 'user': 'postgres'}

def main():
    #log.startLogging(sys.stdout)

    connection = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)
    realm = RqueueRealm(connection)
    checkers = (DBCredentialsChecker(connection),)
    portal = Portal(realm, checkers)
    reactor.listenSSL(2323, pb.PBServerFactory(portal), ServerContextFactory())

if __name__ == "__main__":
    reactor.callWhenRunning(main)
    reactor.run()

