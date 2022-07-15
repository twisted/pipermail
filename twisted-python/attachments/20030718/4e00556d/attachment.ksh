#!/usr/bin/env python
from twisted.internet import reactor
from twisted.internet.app import Application
from twisted.web import static, server, script

def main():
	"""Run the xml rpc server.
	"""
	app = Application("CafeMonitor")

	root = static.File("./")
	root.processors = {
		'.rpy': script.ResourceScript,
		}

	app.listenTCP(
		port=20808,
		factory=server.Site(root),
		interface="localhost"
	)
	print("Web Frontend - <%s:%s>." % ("localhost", "20808"))
	app.run(0)
	
if __name__ == '__main__':
	main()
	
