import sys, traceback
import json
from twisted.internet import reactor, task, defer, threads
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver


class CustomLineReceiverProtocol(LineReceiver):
	delimiter = b':==:'

class ServiceListener(CustomLineReceiverProtocol):
	def connectionMade(self):
		print('    protocol connectionMade')
		self.factory.activeClients.append(self)

	def connectionLost(self, reason):
		print('    protocol connectionLost')
		self.factory.removeClient(self)

	def lineReceived(self, line):
		print('    protocol lineReceived: {}'.format(line))

	def constructAndSendData(self, action):
		message = {'action': action}
		jsonMessage = json.dumps(message)
		msg = jsonMessage.encode('utf-8')
		print('    protocol constructAndSendData: {}'.format(msg))
		self.sendLine(msg)

class ServiceFactory(ServerFactory):
	protocol = ServiceListener

	def __init__(self):
		print('factory constructor')
		super().__init__()
		self.activeClients = []
		self.loopingHealthUpdates = task.LoopingCall(self.enterSystemHealthCheck)
		self.loopingHealthUpdates.start(15)

	def removeClient(self, client):
		print('  factory removeClient')
		self.activeClients.remove(client)

	def enterSystemHealthCheck(self):
		print('  factory enterSystemHealthCheck')
		threadHandle = threads.deferToThread(self.sendHealthRequest)
		return threadHandle

	def sendHealthRequest(self):
		if len(self.activeClients) <= 0:
			print('  factory sendHealthRequest: no active clients to talk to')
		else:
			for client in self.activeClients:
				print('  factory sendHealthRequest: requesting from client...')
				client.constructAndSendData('healthRequest')

if __name__ == '__main__':
	try:
		reactor.listenTCP(51841, ServiceFactory(), interface='127.0.0.1')
		reactor.run()
	except:
		stacktrace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print('clientWrapper exception: {}'.format(stacktrace))
	print('exiting')
	sys.exit(0)
