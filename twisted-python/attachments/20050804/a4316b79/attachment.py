from twisted.protocols.telnet import Telnet
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
class TelnetProtocol(Telnet):
	buffer = ''
	def makeConnection(self, transport):
		print "Making a connection"
		Telnet.makeConnection(self, transport)
	def connectionMade(self):
		self.lines=[]
		print "Connection made"
		Telnet.connectionMade(self)
	def dataReceived(self, data):
		print "Data recived"
		self.buffer+=data
		print self.buffer
		if self.buffer == '':
			print "nic nie ma"
			self.transport.loseConnection()
		Telnet.dataReceived(self, data)         
	def connectionLost(self, reason):
		self.alive = False
		print "connection lost, %s" % reason
		Telnet.connectionLost(self, reason)
	def telnet_User(self, user):
		user="mkl"
		print "user"
		Telnet.telnet_User(self, user)
	def telnet_Password(self, paswd):
		paswd="some_password"
		print "password"
		self.loggedIn()
		Telnet.telnet_Password(self, paswd)
	def loggedIn(self):
		print "udalo sie zalogowac"
		Telnet.loggedIn(self)
#-------------------------#
class MyFactory(ClientFactory):
	protocol = TelnetProtocol
	def startedConnecting(self, connector):
		#self.makeConnection()
		#connector.connect()
		pass # we could connector.stopConnecting()
	def clientConnectionLost(self, connector, raeason):
		print "Connection lost reconecting"
		connector.connect() # reconnect
	def clientConnectionFailed(self, connector, reason):
		print "connection failed"
		reactor.stop()
#-------------------------------------#
if __name__=="__main__":
	from twisted.internet import reactor
	HOST='192.168.130.1'
	port=23
	c=reactor.connectTCP(HOST, port, MyFactory())
	reactor.run()
#-------------------------------------