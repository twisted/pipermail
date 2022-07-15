from twisted.internet import reactor
from twisted.spread import pb

class Client():
    def __init__( self ):
        def got_controller( remoteController ):
            self.remoteController = remoteController
            d = self.remoteController.callRemote("addQuitCallback", self.quit)
            d.addErrback(err_controller)
       
        def err_controller( e ):
            print "ERROR: value:", e.value
            print "ERROR: type: ", e.type
            e.value=None
            e.type=None
            reactor.stop()

        print "client: initializing"
        factory = pb.PBClientFactory()
        reactor.connectTCP( "localhost", 8800, factory )     
        factory.getRootObject().addCallbacks( got_controller, err_controller )
        
    def quit(self):
        print "client: quit"
        reactor.callLater(1, reactor.stop)

if __name__ == "__main__":
    client = Client()
    reactor.run()
    
