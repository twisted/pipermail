#---------------------#
#Client Side Protocol #
#---------------------#
from twisted.protocols.telnet import Telnet
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor, task, defer, threads
import telnetlib as tln
from twisted.python import threadable
threadable.init()

import logging, thread

class TelnetProtocol(Telnet):
	buffer = ''
	global ciag
	licznik = 0
	
	def makeConnection(self, transport):
		print "Making a connection"
		Telnet.makeConnection(self, transport)
		
	def connectionMade(self):
		print "Connection made"
#		self.log.info("telnet_protocol connected")
		Telnet.connectionMade(self)
		
	def connectionLost(self, reason):
#		self.log.debug("Connection lost: %s", reason)
		print "connection lost, %s" % reason
		Telnet.connectionLost(self, reason)

	def dataReceived(self, data):
		print "Data recived"
		ciag=""
		self.buffer+=data
		f=open("new.txt","a+")
		print self.buffer
		f.write(self.buffer)
		odp = self.responseFunct(data)
		self.write(odp)
		if self.buffer == '':
			print "nic nie ma"
			self.transport.loseConnection()
		if ("login:" in  data) and ("Last login:" not in data):
			print "wchodze 4"
			# here i take a username from USE CASE
			self.telnet_User()
			print "wychodze 4"
		if "Password:" in  data:
			print "wchodze 5"
			# here i take a password from USE CASE
			self.telnet_Password()
			print "wychodze 5"
		try:
			print "try 1"
			if "[mkl@julia mkl]$" in data:
				self.telnet_Check_OK(data)
				print "try 2"
			else:
				print "else 1"
				self.telnet_Check_DENY() 
				print "else 2"
				pass
		except:
			pass
	
	def responseFunct(self, buffer):
		response = ""
		print "funkcja in"
		f = open("dlugosc.txt","a+")
		length = len(buffer)# buffer - string
		response_buffer=""
		for i in range(length/3):
			# every seqence I should RESponse, should begin from IAC - \xff (255)
			# i dont get a terminal type
			sequence=buffer[0+(i*3):3+(i*3)]
			f.write("seq:"+sequence)
			if sequence.count(tln.IAC):
				f.write("<-: YES\n")
				if sequence.count(tln.DO) and sequence.count(tln.SNDLOC):
					response = tln.IAC + tln.DO + tln.SNDLOC
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.DO) and sequence.count(tln.BINARY):
					response = tln.IAC + tln.WILL + tln.BINARY
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.DO) and sequence.count(tln.ECHO):
					response = tln.IAC + tln.WILL + tln.ECHO
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.DO) and sequence.count(tln.SGA):
					response = tln.IAC + tln.WILL + tln.SGA
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.WILL) and sequence.count(tln.BINARY):
					response = tln.IAC + tln.DO + tln.BINARY
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.WILL) and sequence.count(tln.ECHO):
					response = tln.IAC + tln.DO + tln.ECHO
					f.write("RES:"+str(response)+"\n")
				elif sequence.count(tln.WILL) and sequence.count(tln.SGA):
					response = tln.IAC + tln.DO + tln.SGA
					f.write("RES:"+str(response)+"\n")
				elif tln.DO in sequence or tln.DONT in sequence:
					response = tln.IAC + tln.WONT + sequence[2]
					f.write("RES:"+str(response)+"\n")
				elif tln.WILL in sequence or tln.WONT in sequence:
					response = tln.IAC + tln.DONT + sequence[2]
					f.write("RES:"+str(response)+"\n")
			else:
				f.write("\n")
			response_buffer +=response
		print "funkcja out"
		return response_buffer

	def telnet_User(self, user="mkl"):
		print "user1"
		self.transport.write(user+"\n\r")
		print "user2"
		
	def telnet_Password(self, paswd="Kznjsnm"):
		print "pass1"
		self.transport.write(paswd+"\n\r")
		print "pass2"
	
	def loggedIn(self):
		# i know that user succesfuly login
		f=open("zewn.txt","w")
		f.write("logged In")
		print "logged In"
			
	def telnet_Check_OK(self, data):
		if "[mkl@julia mkl]$" in data:
			print "wchodze spr log"
			f=open("new.txt","a+")
			f.write("udalo sie zalogowac")
			print "wychodze spr log"
		pass

	def telnet_Check_DENY(self):
		print "zly user we"
		f=open("new.txt","a+")
		f.write("zly user - nie udalo sie zalogowac")
		print "zly user wy"	
		self.tansport.loseConnection()
		reactor.stop()
	
	def telnet_KeepAlive(self):
		print "KA 1"
		self.write("pwd\n\r")
		print "KA 2"
	
	def telnet_Command(self, command="pwd"):
		print "comm1"
		self.write(command+"\r\n")
		f.write(command)
		print "comm2"
#-------------------------#
# Client Side Factories 2 #
#-------------------------#

class MyFactory(ClientFactory):
	protocol = TelnetProtocol
	
	def startedConnecting(self, connector):
		#self.makeConnection()
		#connector.connect()
		pass # we could connector.stopConnecting()
	
	def clientConnectionLost(self, connector, reason):
		print "Connection lost reconecting %s" % reason
		reactor.stop()
#		connector.connect() # reconnect
	
	def clientConnectionFailed(self, connector, reason):
		print "connection failed %s" % reason
		reactor.stop()
	
#-------------------------------------#
# Connection API			 #
#-------------------------------------#
if __name__=="__main__":
	def telnet_KeepAlive2():
		print "keeping alive 1"
		tel = TelnetProtocol()
		#tel.telnet_KeepAlive()
		print "keeping alive 2"	
	
	HOST='127.0.0.1'
	port=2323
	l = task.LoopingCall(telnet_KeepAlive2)
	l.start(5.0)
	reactor.connectTCP(HOST, port, MyFactory())
	reactor.run()