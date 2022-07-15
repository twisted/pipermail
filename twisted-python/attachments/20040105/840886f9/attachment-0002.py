"""Provides Security for network connections"""

from twisted.spread import pb
from twisted.python import components
from twisted.cred import error
from twisted.cred.credentials import IUsernameHashedPassword, IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.internet.defer import Deferred
from pyPgSQL.PgSQL import *    

class DBCredentialsChecker:
    """This class checks the credentials of incoming connections
    against a user table in a database"""
    __implements__ = ICredentialsChecker
    
    def __init__(self, runQuery, userTableName='user', usernameField='username', passwordField='password',
                 customCheckFunc=None, caseSensitiveUsernames=False, caseSensitivePasswords=True):
        """
        @type runQuery: Callable that takes arguments as follows: (sqlStr, *args, **kwargs)
        @param runQuery: This will be called to get the info from the db. The code is written
        for PyPgSQL so it expects the callable to automatically quote params. The function should return a
        deferred just like twisted.enterprice.adbapi.ConnectionPool.runQuery. In fact if you're using
        PyPgSQL, just create a twisted.enterprice.adbapi.ConnectionPool instance and pass it's
        runQuery method here.
        
        @type userTableName: C{str}
        @param userTableName: This is the name of the table in the database that contains
        the usernames and passwords
        
        @type usernameField: C{str}
        @param usernameField: This is the name of the field in the above table that contains
        the username (id) of the entity attempting to log in (authenticate)
        
        @type passwordField: C{str}
        @param passwordField: This is the name of the field in the above table that contains
        the password (shared secret) of the entity attempting to log in (authenticate)
        
        @type customCheckFunc: Callable that takes the following params: (username, suppliedPass, dbPass)
        and returns a boolean
        @param customCheckFunc: Use this if the passwords in the db are stored as hashes. We'll just call this,
        so you can do the checking yourself.
        
        @type caseSensitiveUsernames: C{bool}
        @param caseSensitiveUsernames: If true requires that every letter in 'credentials.username'
        is exactly the same case as the it's counterpart letter in the database.

        @type caseSensitivePasswords: C{bool}
        @param caseSensitivePasswords: If true requires that every letter in 'credentials.password'
        is exactly the same case as the it's counterpart letter in the database.
        This is only relevent if 'customCheckFunc' is emtpy.
        """
        self.runQuery = runQuery
        self.userTableName = userTableName
        self.usernameField = usernameField
        self.passwordField = passwordField        
        self.caseSensitiveUsernames = caseSensitiveUsernames
        self.caseSensitiveUsernames = caseSensitiveUsernames
        self.customCheckFunc = customCheckFunc
        # We can't support hashed password credentials if we only have a hash in the DB
        if customCheckFunc:
            self.credentialInterfaces = (IUsernamePassword,)
        else:
            self.credentialInterfaces = (IUsernamePassword, IUsernameHashedPassword,)
    
    def requestAvatarId(self, credentials):
        """Authenticates the kiosk against the database"""
        # Check that the credentials instance implements at least one of our interfaces
        for interface in self.credentialInterfaces:
            if components.implements(credentials, interface): break
        else: raise UnhandledCredentials()
        # Make up our sql
        if self.caseSensitiveUsernames:
            sql = 'SELECT %s, %s FROM %s WHERE lower(%s) = lower(%s))' % (self.usernameField,
                self.passwordField, self.userTableName, self.usernameField)
        else:
            sql = 'SELECT %s, %s FROM %s WHERE %s = %%s' % (self.usernameField,
                self.passwordField, self.userTableName, self.usernameField)
        # Ask the database for the username and password
        db_deferred = self.runQuery(sql, credentials.username)
        # Setup our deferred result
        deferred = Deferred()
        db_deferred.addCallbacks(self._cbAuthenticate, self._ebAuthenticate,
                callbackArgs=(credentials, deferred),
                errbackArgs=(credentials, deferred))
        return deferred

    def _cbAuthenticate(self, result, credentials, deferred):
        """Checks to see if authentication was good. Called once the info has been retrieved from the DB"""
        if len(result) == 0:
            deferred.errback(error.UnauthorizedLogin('Username unknown')) # Username not found in db
        else:
            username, password = result[0]
            if self.customCheckFunc:
                # Let the owner do the checking 
                if self.customCheckFunc(username, credentials.password, password): deferred.callback(credentials.username)
                else: deferred.errback(error.UnauthorizedLogin('Password mismatch'))
            else:
                # It's up to us or the credentials object to do the checking now
                if components.implements(credentials, IUsernameHashedPassword):
                    # Let the hashed password checker do the checking
                    if credentials.checkPassword(password): deferred.callback(credentials.username)
                    else: deferred.errback(error.UnauthorizedLogin('Password mismatch'))
                elif components.implements(credentials, IUsernamePassword):
                    # Compare the passwords, deciging whether or not to use case sensitivity
                    if self.caseSensitivePasswords: passOk = password.lower() == credentials.password.lower()
                    else: passOk = password == credentials.password
                    # See if they match
                    if passOk: deferred.callback(credentials.username)
                    else: deferred.errback(error.UnauthorizedLogin('Password mismatch'))
                else: deferred.errback(error.UnhandledCredentials()) # OK, we don't know how to check this

    def _ebAuthenticate(self, message, credentials, deferred):
        """The database lookup failed for some reason"""
        deferred.errback(error.LoginFailed(message))