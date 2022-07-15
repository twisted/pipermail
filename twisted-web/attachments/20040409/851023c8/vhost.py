from nevow import rend

import string

class NameVirtualHost(rend.Page):
    """I am a resource which represents named virtual hosts. 
       And these are my obligatory comments
    """
    
    default = None
    
    def __init__(self):
        """Initialize. - Do you really need me to tell you that?
        """
        
        rend.Page.__init__(self)
        self.hosts = {}

    def addHost(self, name, resrc):
        """Add a host to this virtual host. - The Fun Stuff(TM)
            
        This associates a host named 'name' with a resource 'resrc'

            nvh.addHost('nevow.com', nevowDirectory)
            nvh.addHost('divmod.org', divmodDirectory)
            nvh.addHost('twistedmatrix.com', twistedMatrixDirectory)

        I told you that was fun.
        """
        
        self.hosts[name] = resrc

    def removeHost(self, name):
        """Remove a host. :(
        """
        del self.hosts[name]

    def _getResourceForRequest(self, request):
        """(Internal) Get the appropriate resource for the request
            
            TODO:
                Fail nicely when the host doesn't exist AND no default is set.
        """
        
        hostHeader = request.getHeader('host')
        
        if hostHeader == None:
            return self.default
        else:
            host = hostHeader.split(':')[0].lower()

        return self.hosts.get(host, self.default)

    def locateChild(self, request, segments):
        """It's a NameVirtualHost, do you know where your children are?
        
        This uses locateChild magic so you don't have to mutate the request.
        """
        resrc = self._getResourceForRequest(request)
        return resrc, segments

