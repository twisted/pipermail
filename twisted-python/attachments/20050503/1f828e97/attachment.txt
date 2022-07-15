import sys
import struct
import time

from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from twisted.python import log

# global flag
running = True

class SimpleMsg:
	def __init__(self): pass
	
	def pack(self):
		return struct.pack(">BBBB", 64, 65, 66, 67)


class SimpleServer(Protocol):

    def connectionMade(self):
		m = self.factory.msg()
		while running:
			self.transport.write(m.pack())
			sys.stderr.write(".")
			time.sleep(1)
		self.transport.loseConnection()

class SimpleFactory(ServerFactory):
	protocol = SimpleServer

	def __init__(self, MessageClass):
		self.msg = MessageClass


def main():
	log.startLogging(sys.stdout)
	reactor.listenTCP(5050, SimpleFactory(SimpleMsg))
	reactor.run()

if __name__ == "__main__":
	main()
