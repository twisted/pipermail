from twisted.spread import pb
from twisted.internet import reactor

import e

class Echoer(pb.Root):
    def remote_echo(self, st):
        print 'echoing:', st
	raise e.MyError("st=%s" % st)
        return st

if __name__ == '__main__':
    reactor.listenTCP(8789, pb.PBServerFactory(Echoer()))
    reactor.run()
