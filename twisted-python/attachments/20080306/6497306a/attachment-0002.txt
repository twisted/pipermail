from twisted.internet import reactor, protocol, defer, threads
from twisted.protocols import basic

ip = [] # i plan to save any ip connected to this server in this variable
message = "" # this is a variable that store any message from client

class MovementProtocol(basic.LineReceiver):


    def __init__(self):
        self.deferred = defer.Deferred() # for a later development

    def lineReceived(self, line):
        if line == "quit":
            self.sendLine("Goodbye.")
            self.transport.loseConnection( )
        else:
            if line == "right":
                message = "server :" + line
                self.sendLine(message)  # i think this is the problem
                print "data %s sent" % line
            elif line == "left":
                message = "server :" + line
                self.sendLine(message)
                print "data %s sent" % line
            elif line == "up":
                message = "server :" + line
                self.sendLine(message)
                print "data %s sent" % line
            elif line == "down":
                message = "server :" + line
                self.sendLine(message)
                print "data %s sent" % line
            else:
                print "accepting data: %s" % line
                ip.append(line)

    #def PeriodicClientCheck(self):
        

class MovementServerFactory(protocol.ServerFactory):

    protocol  = MovementProtocol



if __name__ == "__main__":
    port = 5001
    print "server run at port %i" % port

    reactor.listenTCP(port, MovementServerFactory( ))
    reactor.run( )