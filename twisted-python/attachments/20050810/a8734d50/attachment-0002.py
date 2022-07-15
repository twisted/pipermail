#---------------------#
#Client Side Protocol #
#---------------------#
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
		f=open("new.txt","w")
		print self.buffer
		f.write(self.buffer)
		if self.buffer == '':
			self.transport.loseConnection()
		if data == "\xff\xfd\x18\xff\xfd\x20\xff\xfd\x23\xff\xfd\x27":
			self.write("\xff\xfc\x18\xff\xfc\x20\xff\xfc\x23\xff\xfc\x27")
		if data == "\xff\xfb\x03\xff\xfd\x01\xff\xfd\x1f\xff\xfb\x05\xff\xfd\x21":
			self.write("\xff\xfd\x03\xff\xfb\x01\xff\xfc\x1f\xff\xfe\x05\xff\xfc\x21")
			#self.processLine(data)
		if "Red Hat" in data:
#		if data == "\xff\xfe\x01\xff\xfb\x01"+"Red Hat Linux release 8.0 (Psyche)\r\nKernel 2":
			self.write("\xff\xfc\x01\xff\xfd\x01")
		
		if "login:" in  data:
			self.telnet_User("user")
		
		if "Password:" in  data
			self.telnet_Password("password")
		
#		Telnet.dataReceived(self, data)
		
		
	def connectionLost(self, reason):
		self.alive = False
		print "connection lost, %s" % reason
		Telnet.connectionLost(self, reason)
	
	def telnet_User(self, user):
		print "user1"
		user="user\n\r"
#		self.username=user
#		print self.user
		self.write(user)
		print "user2"
#		Telnet.telnet_User(self, user)
		
	def telnet_Password(self, paswd):
		print "pass1"
		paswd="password\n\r"
		self.write(paswd)
#		self.write("\n\r")
		print "telnet_Password"
#		Telnet.telnet_Password(self, paswd)
		
		
	def loggedIn(self):
		print "login in succesful"
		Telnet.loggedIn(self)
	
	
	def write(self, data):
		print data
		Telnet.write(self, data)
	'''
	def processLine(self, linie):
		print line
		Telnet.processLinie(self, line)	
	
	def processChunk(self, chunk):
		print self.chunk
		Telnet.processChunk(self, chunk)
	'''
#-------------------------#
# Client Side Factories 2 #
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
		print "connection failed %s" % reason
		reactor.stop()
	
#-------------------------------------#
#Connection API						  #
#-------------------------------------#
if __name__=="__main__":
	from twisted.internet import reactor
	HOST='127.0.0.1'
	port=23
#	tn = telnetlib.Telnet(HOST)
	reactor.connectTCP(HOST, port, MyFactory())
	reactor.run()
#-------------------------------------