#!/usr/bin/env python

# Simple telnet daemon demo by David McNab
# run it, then type 'telnet localhost 2000' to try it out

from twisted.internet import reactor, protocol

import twisted.protocols.telnet

class mytelnetd(twisted.protocols.telnet.Telnet):
    """hacked-up ircd"""

    def telnet_Command(self, command):
        print "got command: %s" % command
        self.write("You entered: %s\r\n" % command)
        return 'Command'

    def _X_telnet_User(self, user):
        print "User %s wants to log in" % user
        return 'Password'

    def checkUserAndPass(self, user, passwd):
        print "user=%s, passwd=%s" % (user, passwd)
        if passwd != 'cream':
            print dir(self)
            print "bad password"
            return False
        return True

def main():
    """This runs the protocol on port 8000"""
    mytelnetdF = protocol.ServerFactory()
    mytelnetdF.protocol = mytelnetd
    reactor.listenTCP(2000, mytelnetdF)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    print "Point your telnet client to port 2000 to try this demo"
    print "any username accepted, password is 'cream'"
    main()
