# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
from twisted.spread.util import FilePager

from twisted.internet.defer import Deferred
from pbecho import FilePageWriter

def _do_page(page_receiver,
             input_filename):
    d = Deferred()
    fp = open(input_filename,
              'r')
    pager = FilePager(page_receiver,
                      fp,
                      fp=fp,
                      deferred=d)
    return d

def connected(perspective):
    perspective.callRemote('save_file', 'output').addCallback(_do_page, 
                                                              'pbecho.py')
    print "Connected."

factory = pb.PBClientFactory()
reactor.connectTCP("localhost", pb.portno, factory)
factory.login(UsernamePassword("guest", "guest")).addCallback(connected)

#reactor.callLater(.7, lambda : reactor.stop())

reactor.run()
