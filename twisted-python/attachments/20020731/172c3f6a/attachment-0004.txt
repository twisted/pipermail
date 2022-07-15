# WebConduit

from twisted.web import wmvc
from twisted.web import server
from twisted.python import components
from twisted.internet import protocol
from twisted.internet import reactor


REMOTE_ADDRESS = "lambda.moo.mud.org"
REMOTE_PORT = 8888


class IConduitSession(components.Interface):
    """
    A unique session namespace for the conduit.
    """
    def setRequest(request):
        """Set the web request object to which output written to this conduit will be sent.
        Until this is called, output will be cached; after this is called, the behavior of calling
        it again is undefined.
        """
    
    def input(arg):
        """Send input to the conduit.
        """
    
    def output(arg):
        """Send output from the conduit to the web browser.
        """


class ConduitSession(protocol.Protocol):
    __implements__ = IConduitSession
    def __init__(self, session):
        self.cached = []
        self.request = None
        reactor.clientTCP(REMOTE_ADDRESS, REMOTE_PORT, self)

    def setRequest(self, request):
        self.request = request
        for item in self.cached:
            self.output(item)

    def input(self, arg):
        self.write(arg)

    def output(self, arg):
        if self.request is None:
            self.cached.append(arg)
        else:
            arg = arg.replace("'", "\\'")
            self.request.write(arg+'<script language="JavaScript1.2">' + "top.recv('" + arg + "')</script>\r\n")

    def dataReceived(self, data):
        lines = data.split('\n')
        for line in lines:
            self.output(line.strip())

    def write(self, data):
        self.transport.write(data + '\n')


components.registerAdapter(ConduitSession, server.Session, IConduitSession)


class MWebConduit(wmvc.WModel):
    pass


class VWebConduit(wmvc.WView):
    templateFile = "conduit.html"


class CWebConduit(wmvc.WController):
    def render(self, request):
        session = request.getSession(IConduitSession)
        input = request.args.get("input", [None])[0]
        if input:
            session.input(input)
            return "<html>%s sent.</html>" % input
        output = request.args.get("output", [None])[0]
        if output:
            session.setRequest(request)
            session.output("<html>Output connected")
            # We'll never be done!
            return server.NOT_DONE_YET
        return wmvc.WController.render(self, request)


wmvc.registerViewForModel(VWebConduit, MWebConduit)
wmvc.registerControllerForModel(CWebConduit, MWebConduit)
