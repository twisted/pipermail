
# Twisted, the Framework of Your Internet
# Copyright (C) 2001 Matthew W. Lefkowitz
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
An example of using the FTP client
"""

# Twisted imports
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.basic import FileSender
from twisted.python import usage
from twisted.internet import reactor

# Standard library imports
import string
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


# Define some callbacks
def success(response):
    print 'Success!  Got response:'
    print '---'
    if response is None:
        print None
    else:
        print string.join(response, '\n')
    print '---'

def fail(error):
    print 'Failed.  Error was:'
    print error
    from twisted.internet import reactor
    reactor.stop()


class Options(usage.Options):
    optParameters = [['host', 'h', ''],
                     ['port', 'p', 1221],
                     ['username', 'u', 'anonymous'],
                     ['password', None, 'anonumous@example.com'],
                     ['passive', None, 0],
                     ['debug', 'd', 1],
                    ]

def run():
	# Get config
	config = Options()
	config.parseOptions()
	config.opts['port'] = int(config.opts['port'])
	config.opts['passive'] = int(config.opts['passive'])
	config.opts['debug'] = int(config.opts['debug'])
	
	# Create the client
	FTPClient.debug = config.opts['debug']
	creator = ClientCreator(reactor, FTPClient, config.opts['username'],
							config.opts['password'], passive=config.opts['passive'])
	creator.connectTCP(config.opts['host'], config.opts['port']).addCallback(connectionMade)
	
	print "**** Here 1 -"
	reactor.run()
	print "- Here 2 ****"


def sendfile(consumer, fileObj):
	"""
	"""
	print "2.1 consumer, fileObject -", consumer, fileObj
	s = FileSender()
	print "2.2"
	d = s.beginFileTransfer(fileObj, consumer)
	print "2.3"
	d.addCallback(lambda _: consumer.finish())
	print "2.4"
	return d


def connectionMade(ftpClient):
	"""
	"""
	try:
		print "1.0"
		my_file = StringIO("Hello! Did this get sent to the remote side?")
		print "1.1"
		my_filename = 'myfile.txt'	
		print "1.2"
		ftpClient.pwd().addCallbacks(success, fail)
		print "1.3"
		dC, dL = ftpClient.storeFile(my_filename)
		print "1.4"
		dC.addCallback(sendfile, my_file)
		print "1.5"
		dL.addCallbacks(success, fail)
		print "1.6"
		
	except:
		print "Exception -", sys.exc_value
		reactor.stop()
		
	


# this only runs if the module was *not* imported
if __name__ == '__main__':
    run()

