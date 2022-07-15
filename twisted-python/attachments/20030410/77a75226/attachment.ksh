from twisted.internet import reactor
from twisted.web import static, server

# imports needed for woven guard
from twisted.internet.app import MultiService
from twisted.cred.service import Service 
from twisted.cred.authorizer import DefaultAuthorizer
from twisted.web.woven import guard

# imports needed for guard.PerspectiveWrapper subclass
from twisted.python import formmethod as fm
from twisted.web.woven import page, form
from twisted.web.util import Redirect

myTemplate = """
<html>
	<head>
	    <title>Login</title>
	</head>
	<body>
        <div model="description"></div>
	    <form action="">
	        User<br />
	        <input type="text" name="identity" model="identity" view="Input" /><br />
	        Password<br />
	        <input type="password" name="password" /><br />
	        <input type="submit" />
	    </form>
	</body>
</html>"""
        
class MyPerspectiveWrapper(guard.PerspectiveWrapper):
    def getResourceForLogin(self, request, loginMethod, model=None):
        if model is None:
            model = {"description": "", "identity": ""}
        
        retPage = page.Page(m=model, template=myTemplate)
        retPage.addSlash = 0

        return retPage
    
    def getFormProcessorForLogin(self, request, loginMethod):
        loginSignature = fm.MethodSignature(
                fm.String("identity", "",
                            "Username", ""),
                fm.Password("password", "",
                            "Password", ""))
        
        failedLogin = lambda errModel: self._ebLoginFailed(errModel, request, loginMethod)
        loggedIn = lambda m: Redirect(request.pathRef().parentRef().fullURL(request))
        
        return form.FormProcessor(loginSignature.method(loginMethod), errback=failedLogin, callback=loggedIn)
    
    def _ebLoginFailed(self, errModel, request, loginMethod):
        model = {"description": errModel.getSubmodel("description"), "identity": request.args.get("identity")[0]}
        return self.getResourceForLogin(request, loginMethod, model=model)
        
ms = MultiService("hello")
auth = DefaultAuthorizer(ms)
svc = Service("test_service", ms, auth)
myp = svc.createPerspective("test")
myp.makeIdentity("test")

unProtected = static.Data("you should never see this", "text/plain")
unProtected.putChild("", static.Data("Anyone can see me.", "text/plain"))

protectedResource = static.Data("you should never see this", "text/plain")
protectedResource.putChild("", static.Data("Only an authenticated user can see me.", "text/plain"))

# authFactory (name is unimportant) simply gets passed a perspective and should return a protected resource
authFactory = lambda p: protectedResource

pwrap = MyPerspectiveWrapper(svc, unProtected, authFactory)
swrap = guard.SessionWrapper(pwrap)
    
site = server.Site(swrap)
reactor.listenTCP(10998, site)
reactor.run()
