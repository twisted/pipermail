import weakref

import resources
from twisted.internet import reactor

def main():
    c = resources.Client(reactor)
    c.connect()
    reactor.run()

if __name__ == "__main__":
    main()
