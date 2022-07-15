from twisted.conch.ssh import transport, userauth, connection, common, keys, channel
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import sys, os, re
from subprocess import *

class SshException(Exception):
	pass

class SshClient(protocol.ClientFactory):
	'''
	Executes a remote python code
	'''
	def __init__(self, command, server, username, password = None, keyfile = os.path.expanduser('~/.ssh/id_dsa')):
		'''
		Necessary information to connect
		'''
		self.username = username
		self.password = password
		self.server = server
		self.keyfile = keyfile
		self.command = command
		self._deferer_ = defer.Deferred()
		self._transport = None
	
	def buildProtocol(self, addr):
		'''
		Create the protocol after connection
		'''
		self._transport = SshTransport(self.username, self.password, self.keyfile, self.command, self._deferer_)
		return self._transport
	
	def connect(self):
		reactor.connectTCP(self.server, 22, self)
		self._deferer_.addCallback(self.disconnectOnSuccess)
		self._deferer_.addErrback(self.disconnectOnError)
		return self._deferer_
	
	def disconnect(self):
		if self._transport is not None:
			self._transport.loseConnection()
			
	def disconnectOnError(self, failure):
		self.disconnect()
		raise failure
	
	def disconnectOnSuccess(self, result):
		self.disconnect()
		return result
	
	def clientConnectionFailed(self, connector, reason):
		'''
		When connection failed
		'''
		protocol.ClientFactory.clientConnectionFailed(self, connector, reason)
		log.err(reason)
		self._deferer_.errback(reason)
	
class SshTransport(transport.SSHClientTransport):
	
	def __init__(self, username, password, keyfile, command, _deferer_):
		'''
		Necessary info to start SSH connection
		'''
		self.username = username
		self.password = password
		self.keyfile = keyfile
		self.command = command
		self._deferer_ = _deferer_
		self.timeout = reactor.callLater(30, self.sshTransportTimeout)
	
	def verifyHostKey(self, hostKey, fingerprint):
		'''
		Check fingerprint
		'''
		self.timeout.cancel()
		return defer.succeed(1)
	
	def connectionSecure(self):
		'''
		User authentication 
		'''
		self.requestService(
			SshUserAuth(self.username, 
						self.password, 
						self.keyfile, 
						self._deferer_,
						SshConnection(self.command, self._deferer_)))

	def sshTransportTimeout(self):
		'''
		If the connection times out
		'''
		self.loseConnection()
		self._deferer_.errback(SshException('408', 'Connection timed out.'))
	
class SshUserAuth(userauth.SSHUserAuthClient):
	
	def __init__(self, username, password, keyfile, _deferer_, connection):
		'''
		User authentication
		'''
		userauth.SSHUserAuthClient.__init__(self, username, connection)
		self.keyfile = keyfile
		self.password = password
		self._deferer_ = _deferer_
	
	def getPassword(self):
		'''
		Password auth is not provided, give error
		'''
		if self.password:
			return self.password
		else:
			self.transport.sendDisconnect(transport.DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE, 'no more auths')
			self._deferer_.errback(SshException('401', 'Wrong Key / Key authentication failed'))
			return
	
	def getGenericAnswers(self, name, instruction, questions):
		'''
		Keyboard interactive password is not provided, give erro
		'''
		self.transport.sendDisconnect(transport.DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE, 'no more auths')
		self._deferer_.errback(SshException('401', 'User authentication failed'))
		return defer.fail(None)
	
	def getPublicKey(self):
		'''
		Create the public key
		'''
		if not os.path.exists(self.keyfile) or self.lastPublicKey:
			raise SshException('401', 'Auth key %s doesn\'t exist' % self.keyfile)
		
		return keys.Key.fromFile(self.keyfile + '.pub')
	
	def getPrivateKey(self):
		'''
		Create the private key
		'''
		return defer.succeed(keys.Key.fromFile(self.keyfile))

class SshConnection(connection.SSHConnection):
	
	def __init__(self, command, _deferer_, *args, **kwargs):
		'''
		Tracks the SSH connection
		'''
		connection.SSHConnection.__init__(self)
		self.command = command
		self._deferer_ = _deferer_
	
	def serviceStarted(self):
		'''
		Runs just after the authentication finished
		'''
		self.openChannel(SshChannel(self.command, self._deferer_, \
									  2**16, 2**15, conn=self))
	
	def serviceStopped(self):
		'''
		Runs if the service stopped
		'''
	
class SshChannel(channel.SSHChannel):
	name = 'session'
	
	_buffer = ''
	delimiter = '\n'
	MAX_LENGTH = 16384

	def __init__(self, command, _deferer_, *args, **kwargs):
		'''
		SSH channel parameters
		'''
		channel.SSHChannel.__init__(self, *args, **kwargs)
		self.command, self.input = command
		self._deferer_ = _deferer_
		self.success = True
		self.output = ''
	
	def openFailed(self, reason):
		self._deferer_.errback(reason)
	
	def channelOpen(self, ignoredData):
		d = self.conn.sendRequest(self, 'exec', common.NS(self.command), wantReply = True)
		d.addCallback(self._cbRequest)
	
	def _cbRequest(self, ignored):
		if self.input:
			self.write(self.input)
		self.conn.sendEOF(self)
	
	def dataReceived(self, data):
		"""
		Splits the data to lines
		"""
		lines  = (self._buffer+data).split(self.delimiter)
		self._buffer = lines.pop(-1)
		for line in lines:
			if len(line) > self.MAX_LENGTH:
				return self.lineLengthExceeded(line)
			else:
				self.lineReceived(line)
		if len(self._buffer) > self.MAX_LENGTH:
			return self.lineLengthExceeded(self._buffer)
	
	def lineReceived(self, line):
		self.output += line + self.delimiter
	
	def lineLengthExceeded(line):
		self.success = False
		self._deferer_.errback(SshException('500', 'Very long line'))
	
	def extReceived(self, dataType, data):
		print "500 Extended data:", dataType, data
	
	def closed(self):
		if self.success:
			self._deferer_.callback(self.output)

class SimpleClient(object):
	def __init__(self, host, creds):
		self._host = host
		self._creds = creds
		self._result = None
		self._success = False
	
	def _on_done(self, result):
		self._result = result
		self._success = True
		if reactor.running:
			reactor.stop()
					
	def _on_error(self, failure):
		self._result = failure.getErrorMessage()
		print 'ERROR:', self._result
		self._success = False
		if reactor.running:
			reactor.stop()
	
	def execute(self, command):
		self._client = SshClient(command, self._host, self._creds)
		d = self._client.connect()
		d.addCallback(self._on_done)
		d.addErrback(self._on_error)
		reactor.run()
		return self._success, self._result
		
if __name__ == "__main__":
	cl = SimpleClient('172.16.75.50', 'root')
	
	#first command
	s, r = cl.execute( ('python', 'print "Hello World"') )
	print 'S:', s, 'R:', r
	#second command
	s, r = cl.execute( ('python', """import os
os.system("ls /")""") )
	print 'S:', s, 'R:', r
