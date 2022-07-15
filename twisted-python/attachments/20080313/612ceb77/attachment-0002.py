import sys
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import Protocol, ClientCreator

class DemuxServer(Protocol):
    def dataReceived(self, data):
        [header, slave_name, content] = data.split ('///', 2)
        f_clients = self.factory.demux.f_clients
        if (header == "PING"):
            project_name = content 
            if (not f_clients[project_name,slave_name].connected):
                reactor.connectTCP("localhost", f_clients[project_name,slave_name].server_port, f_clients[project_name,slave_name])
                f_clients[project_name,slave_name].protocol.server_protocol = self
                f_clients[project_name,slave_name].connected = True
        else:
            project_name = header
            f_clients[project_name,slave_name].protocol.transport.write(content)
                            
class DemuxServerFactory(ServerFactory):
    def buildProtocol(self, addr):        
        p = DemuxServer()        
        p.factory = self
        return p
    
class DemuxClient(Protocol):
    server_protocol = None

    def dataReceived(self, data):
        if self.server_protocol is not None:
            self.server_protocol.transport.write(data)

class DemuxClientFactory(ClientFactory):
    protocol =  None
    connected = False

    def buildProtocol(self, addr):
        return self.protocol

class Demux:
    listen_port = None
    f_clients = {} #indexed by project_name:slave_name
    f_server = None

    def __init__(self, projectlist, slavelist, listen_port):
        n=0
        for line in file(projectlist):
            n=n+1
            arr=line.split()
            project_name = arr[0]
            for slave_name in slavelist:
                self.f_clients[project_name,slave_name] = DemuxClientFactory()
                self.f_clients[project_name,slave_name].server_port = int(arr[1])
                self.f_clients[project_name,slave_name].connected = False
                self.f_clients[project_name,slave_name].protocol = DemuxClient()                
        self.f_server = DemuxServerFactory()
        self.f_server.demux = self
        self.listen_port = listen_port
        reactor.listenTCP(self.listen_port, self.f_server)
        
class MuxServer(Protocol):
    def dataReceived(self, data):
        self.mux.f_client.protocol.transport.write(self.mux.project_name+"///"+self.mux.slave_name+"///"+data)

class MuxServerFactory(ServerFactory):
    protocol = None
    
    def buildProtocol(self, addr):
        reactor.connectTCP(self.mux.host, self.mux.host_port, self.mux.f_client)
        return self.protocol
        
class MuxClient(Protocol):
    def connectionMade(self):
        self.transport.write("PING///"+self.mux.slave_name+"///"+self.mux.project_name)        
 
    def dataReceived(self, data):
        self.mux.f_server.protocol.transport.write(data)
        
class MuxClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return self.protocol

class Mux:
    f_server = None
    f_client = None
    host = None
    host_port = None
    listen_port = None
    project_name = None
    slave_name = None
    
    def __init__(self, host, host_port, listen_port, project_name, slave_name):
        self.host = host
        self.host_port = host_port
        self.project_name = project_name
        self.listen_port = listen_port
        self.slave_name = slave_name
        self.f_client = MuxClientFactory()
        self.f_client.mux = self
        self.f_client.protocol = MuxClient()
        self.f_client.protocol.mux = self
        self.f_server = MuxServerFactory()
        self.f_server.mux = self
        self.f_server.protocol = MuxServer()
        self.f_server.protocol.mux = self
        self.f_client.protocol.server_protocol = self.f_server.protocol
        reactor.listenTCP(listen_port, self.f_server)      
        
