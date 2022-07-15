from twisted.internet import app, reactor
from twisted.web import server, resource

class SimpleService(app.ApplicationService):
    def startService(self):
        self.serviceRunning = 1
        print "%s: Started." % self.serviceName
        reactor.callLater(0, self.printHello)

    def printHello(self):
        print "Hello from %s." % self.serviceName
        self.nextCall = reactor.callLater(1, self.printHello)

    def stopService(self):
        self.serviceRunning = 0
        if hasattr(self, 'nextCall'): 
            self.nextCall.cancel()
            del(self.nextCall)
        print "%s: Stopped." % self.serviceName

class ServiceWebManager(resource.Resource):
    isLeaf = 1

    def __init__(self, app):
        self.app = app

    def render(self, request):
        serviceName = request.args.get('service', [''])[0]
        action = request.args.get('action', [''])[0]
        if serviceName:
            service = self.app.getServiceNamed(serviceName)
            if action == 'Start':
                service.startService()
            else:
                service.stopService()
            request.redirect('/')
        else:
            for s in self.app.services.keys():
                if self.app.getServiceNamed(s).serviceRunning:
                    action = 'Stop'
                else:
                    action = 'Start'
                request.write("""
                <form method='post'>
                <input type='hidden' name='service' value='%s' />%s
                <input type='submit' name='action' value='%s'>
                </form>
                """ % (s, s, action))
        return ""

myApp = app.Application("Test App")
SimpleService("Service 1", myApp)
SimpleService("Service 2", myApp)
website = server.Site(ServiceWebManager(myApp))
myApp.listenTCP(8008, website)
myApp.run(save=0)
