#!/usr/bin/env python

"""

<song>Man of Metropolis Steals Our Hearts - Sufjan Stevens </song>
"""

from twisted.python                                   import log, logfile
from twisted.internet.defer                           import Deferred
from twisted.python.failure                           import Failure
from twisted.internet                                 import reactor
from twisted.spread                                   import pb

import stackless
import sys

flag = 1

class TwistedException(Exception):
   def __init__(self, value):
       self.value = value
       
   def __repr__(self):
       return str(self.value)


class Deferred(object):
    def __init__(self, channel):
        self.channel = channel

    def __success__(self, result):
        self.channel.send((True, result))
    
    def __failure__(self, failure):
        self.channel.send((False, failure))
    
    
class Processor(object):
    def __init__(self):
       pass
        
    
    def __callMethod__(self, method, *args, **kwargs):
        channel = stackless.channel()
        deferred = Deferred(channel)
        method(*args, **kwargs).addCallbacks(deferred.__success__, deferred.__failure__)
        status, result = channel.receive()
        if status == False:
           raise TwistedException(result)
        return result
       
       
    def calculate(self, perspective, a, b):
        return self.__callMethod__(perspective.callRemote,'calculate', a, b)
       
  
    def getRootObject(self, factory, *arg, **kwargs):
        return self.__callMethod__(factory.getRootObject, *arg, **kwargs)
        
        
        
class TestTasklet(object):
    def __init__(self, processor):
        self.processor = processor
        
    def execute(self, host, port):
        global flag
        
        factory = pb.PBClientFactory()
        log.msg("connecting")
        reactor.connectTCP(host, port, factory)
        log.msg("connected")
        
        try:
           log.msg("get")
           perspective = self.processor.getRootObject(factory)
           log.msg("got")
           print "=>", processor.calculate(perspective, 10, 20)
           flag = False
        
        except TwistedException:
            log.msg("A Twisted Exception was thrown")
            log.msg(sys.exc_info())
        

log.startLogging(sys.stdout)
processor = Processor()

# run the Twisted reactor in its own tasklet

stackless.tasklet(TestTasklet(processor).execute)('127.0.0.1', 8000)
stackless.tasklet(reactor.run)()

while (stackless.getruncount() > 1 and flag):
    stackless.schedule()