"""
Functional test for dbchecker returning an AvatarId when given a correct set of
credentials.
"""

from twisted.cred import credentials
from twisted.internet import reactor
from dbchecker import DbChecker
from zope.interface import implements

class C:
    implements(credentials.IUsernamePassword)

    def __init__(self, u=None, p=None):
        self.username = u
        self.password = p

c = C(u='spam', p='eggs')

checker = DbChecker()

def success(userid):
    print
    print 'success:  userid = %s' % userid
    print
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = checker.requestAvatarId(c)
out.addCallbacks(success, failure)

reactor.run() # start the main loop

