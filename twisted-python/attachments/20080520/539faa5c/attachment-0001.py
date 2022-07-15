from twisted.internet import reactor
from twisted.spread import pb

class Server(pb.Root):
    def remote_addQuitCallback(self, callback):
        print "server: got callback, calling in 2 seconds"
        self.quitCallback = callback
        reactor.callLater(2, self.quitCallback)

if __name__ == "__main__":
    server = Server()    
    reactor.listenTCP(8800, pb.PBServerFactory(server))
    reactor.run()
    
