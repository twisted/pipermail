import sys

from twisted.python import log
from twisted.internet import ssl, protocol, reactor

log.startLogging(sys.stdout)

f = protocol.ReconnectingClientFactory()
f.protocol = protocol.Protocol

reactor.connectSSL('localhost', 12345, f, ssl.ClientContextFactory())
reactor.run()
