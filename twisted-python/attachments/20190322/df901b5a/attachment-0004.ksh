import os, sys, traceback
import json, time, datetime, psutil
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, task, defer, threads
from contextlib import suppress

class CustomLineReceiverProtocol(LineReceiver):
	delimiter = b':==:'

class ServiceClientProtocol(CustomLineReceiverProtocol):
	def connectionMade(self):
		print('    protocol connectionMade')
		self.factory.connectedClient = self
		self.factory.clientConnectionMade()

	def lineReceived(self, line):
		dataDict = json.loads(line)
		if dataDict.get('action') == 'healthRequest':
			self.factory.enterSimulateJob()

	def connectionLost(self, reason):
		print('    protocol connectionLost')
		self.factory.connectedClient = None
	
	def constructAndSendData(self, action, content):
		message = {}
		message['action'] = action
		message['content'] = content
		jsonMessage = json.dumps(message)
		msg = jsonMessage.encode('utf-8')
		print('    protocol constructAndSendData: {}'.format(msg))
		self.sendLine(msg)

class ServiceClientFactory(ReconnectingClientFactory):
	continueTrying = True

	def __init__(self):
		print('factory constructor')
		self.connectedClient = None
		self.health = {}
		self.loopingSystemHealth = task.LoopingCall(self.enterSystemHealthCheck)
		self.loopingSystemHealth.start(10)
		self.numPortsChanged = False
		self.disconnectedOnPurpose = False
		super().__init__()

	def buildProtocol(self, addr):
		print('  factory buildProtocol')
		self.resetDelay()
		protocol = ServiceClientProtocol()
		protocol.factory = self
		return protocol

	def clientConnectionLost(self, connector, reason):
		print('  factory clientConnectionLost: reason: {}'.format(reason))
		# if self.disconnectedOnPurpose:
		# 	## Hack to keep reactor alive
		# 	print('  factory clientConnectionLost: increasing numPorts')
		# 	self.numPorts += 1
		# 	self.numPortsChanged = True
		# 	self.disconnectedOnPurpose = False
		print('  ... simulate client going idle before attempting restart...')
		time.sleep(5)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		print('  factory clientConnectionLost: end.\n')

	def clientConnectionMade(self):
		print('  factory clientConnectionMade: starting numPorts: {}'.format(self.numPorts))
		# if self.numPortsChanged :
		# 	## Resetting from hacked value
		# 	print('  factory clientConnectionMade: decreasing numPorts')
		# 	self.numPorts -= 1
		# 	self.numPortsChanged = False
		print('  factory clientConnectionMade: finished numPorts: {}'.format(self.numPorts))
		print('  ..... pausing for <CTRL><C> test')
		time.sleep(3)

	def cleanup(self):
		print('factory cleanup: calling loseConnection')
		if self.connectedClient is not None:
			self.connectedClient.transport.loseConnection()
			self.disconnectedOnPurpose = True

	def stopFactory(self):
		print('stopFactory')
		self.stopTrying()
		with suppress(Exception):
			self.loopingSystemHealth.stop()
		print('stopFactory end.')

	def enterSimulateJob(self):
		print('  factory enterSimulateJob')
		threadHandle = threads.deferToThread(self.simulateJob)
		return threadHandle

	def simulateJob(self):
		print('  factory simulateJob: starting job')
		time.sleep(2)
		self.connectedClient.constructAndSendData('jobResponse', self.health)
		
		print('  factory simulateJob: finished job... time to reset the client (diconnect/re-initialize)...')
		self.cleanup()

	def enterSystemHealthCheck(self):
		print('  factory enterSystemHealthCheck')
		threadHandle = threads.deferToThread(self.getSystemHealth)
		return threadHandle

	def getSystemHealth(self):
		print('  factory getSystemHealth')
		try:
			currentTime = time.time()
			process = psutil.Process(os.getpid())
			startTime = process.create_time()
			self.health = {
				'processCpuPercent': process.cpu_percent(),
				'processMemory': process.memory_full_info().uss,
				'processRunTime': int(currentTime-startTime)
			}
			print('  factory getSystemHealth: system health: {}'.format(self.health))
		except:
			exception = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			print('  factory getSystemHealth: exception: {}'.format(exception))


if __name__ == '__main__':
	try:
		connector = reactor.connectTCP('127.0.0.1', 51841, ServiceClientFactory(), timeout=300)
		reactor.run()
	except:
		stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print('clientWrapper exception: {}'.format(stacktrace))
	print('exiting')
	sys.exit(0)
