import twisted.spread.pb as pb

import resources

from twisted.internet import reactor
from twisted.cred import portal, checkers

def main():
    realm = resources.Server()
    checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
    checker.addUser("alice", "1234")
    p = portal.Portal(realm, [checker])

    reactor.listenTCP(8800, pb.PBServerFactory(p))
    reactor.run()

if __name__ == "__main__":
    main()
