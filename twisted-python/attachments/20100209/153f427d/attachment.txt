#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from zope.interface import implements
from twisted.internet import reactor
from twisted.internet.interfaces import IReadDescriptor

class inputFile(object):
    implements(IReadDescriptor)

    def __init__(self, filename):
        self.filename = filename
        self.filedes = os.open(filename, os.O_RDONLY | os.O_NONBLOCK)
        reactor.addReader(self)

    def fileno(self):
        return self.filedes

    def connectionLost(self, reason):
        raise reason

    def logPrefix(self):
        return 'inputFile'

    def doRead(self):
        reactor.removeReader(self)
        os.close(self.filedes)
        self.filedes = -1
        reactor.stop()

if __name__ == '__main__':
    r = inputFile('/etc/group')
    reactor.addReader(r)
    reactor.run()
