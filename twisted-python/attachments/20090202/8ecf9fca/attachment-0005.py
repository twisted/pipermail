#!/usr/bin/env python

"""
GoodBPELProcessor.py
Andrew Francis
January 31th, 2009

Track down error in Python 2.6.1/Twisted 8.2
This version should work

<song> Hardcore UFOs -Guided By Voices </song>
"""


import stackless
import time
import sys

from twisted.internet                                 import defer
from twisted.python.failure                           import Failure
from twisted.internet                                 import reactor
from twisted.web                                      import client
from twisted.web                                      import http
from twisted.python                                   import log, logfile
from twisted.internet                                 import task

from BufferedChannel                                  import BufferedChannel

REQUEST_ERROR = -1
REPLY_ERROR = -1
OKAY = 200

MAX_PROCESSES = 2

__DEBUG__ = False


class GoodProcessor(object):
    def __init__(self):
        return


    def tick(self):
        print "tick"
        stackless.schedule()


    def startNetworking(self):
        """
        run the Twisted Reactor in its own tasklet
        also run a task that makes the Twisted Reactor yield to the Stackless 
	scheduler
        """
        l = task.LoopingCall(self.tick)
        l.start(.01)
        reactor.run()


if __name__ == "__main__":
   processor = GoodProcessor()
   stackless.tasklet(processor.startNetworking)() 
   stackless.run()
