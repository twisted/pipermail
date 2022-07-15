# System imports
from OpenSSL import SSL

# sibling imports
import tcp

class Client(tcp.Client):
    """I am an SSL client.
    """
    def createContext(self):
        """
        Create a SSL context. Subclasses may want to override.
        """
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)

    def createInternetSocket(self):
        """(internal) create an SSL socket
        """
        sock = tcp.Client.createInternetSocket(self)
        return SSL.Connection(self.ctx, sock)

class Port(tcp.Port):
    """I am an SSL server.
    """
    def createContext(self):
        """
        Create a SSL context. Subclasses may want to override.
        """
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.use_certificate_file('server.pem')
        self.ctx.use_privatekey_file('server.pem')
    
    def createInternetSocket(self):
        """(internal) create an SSL socket
        """
        sock = tcp.Port.createInternetSocket(self)
        return SSL.Connection(self.ctx, sock)
