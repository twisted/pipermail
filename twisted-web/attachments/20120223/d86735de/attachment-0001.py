'''
Server tests
@author: jacekf
'''

from twisted.cred import portal, checkers, error as credError
from zope.interface import implements, Interface, Attribute
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory

class IAvatar(Interface):
    username = Attribute("""User name""")

class PasswordDictChecker:
    implements(checkers.ICredentialsChecker)
    
    def __init__(self,passwords):
        self.__passwords = passwords
        self.credentialInterfaces = (IAvatar,)
        
    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.__passwords.has_key(username):
            if credentials.password == self.__passwords[username]:
                return defer.succeed(username)
            else:
                credError.UnauthorizedLogin("Access denied")
        else:
            credError.UnauthorizedLogin("Access denied")
            
    
class TestAvatar():
    implements(IAvatar)
    
    def __init__(self,username):
        self.username = username
                
class TestRealm():
    implements(portal.IRealm)

    def __init__(self,users):
        self.__users = users
        
    def requestAvatar(self, avatarId, mind, *interfaces):
        if IAvatar in interfaces:
            logout = lambda: None
            return (IAvatar,TestAvatar(avatarId),logout)
        else:                
            raise KeyError("None of the requested interfaces are supported")

class TestResource(Resource):
    isLeaf = True
    
    def __init__(self,schema=None,filters=()):
        Resource.__init__(self)

    def render_GET(self,request):
        return "OK"
    

def run_security_app():
    passwords = {"admin":"password"}
    users = {"admin":"Administrator"}
    
    realm = TestRealm(users)
    
    p = portal.Portal(TestRealm(users),(PasswordDictChecker(passwords),))
    credentialFactory = BasicCredentialFactory("CorePost")
    resource = HTTPAuthSessionWrapper(portal, [credentialFactory])
    
    print "Running..."
    
    factory = Site(resource)
    reactor.listenTCP(8084, factory)    
    reactor.run()                       

    
if __name__ == "__main__":
    run_security_app()