#!/usr/bin/env python

"""
ToyProcessor.py
Andrew Francis
April 3rd, 2008

The purpose of this programme is to illustrate the techniques
used in the presentation "Adventures in Stackless Python / Twisted Integration"

<song>Dead Letter and the Infinite - Wintersleep </song> 
"""


import stackless
import time
import sys

from twisted.internet.defer                           import Deferred
from twisted.python.failure                           import Failure
from twisted.internet                                 import reactor
from twisted.web                                      import client
from twisted.web                                      import http
from twisted.python                                   import log, logfile
from twisted.internet                                 import task

RECEIVE_RESPONSE = 0
REPLY_RESPONSE = 1
INVOKE_RESPONSE = 2
WAIT_RESPONSE = 3

REQUEST_ERROR = -1
REPLY_ERROR = -1


      
__DEBUG__ = False


class CorrelationNotFound:
    def __init__(self, data):
        self.data = data


class Request(object):
    pass


class Response(object):
    pass


"""
run the Twisted Reactor in its own tasklet
also run a task that makes the Twisted Reactor yield to the Stackless scheduler
"""
def twistedReactor():
    l = task.LoopingCall(stackless.schedule)
    l.start(.01)
    reactor.run()


class InvokeResponse(Response):
    def __init__(self, requestId, message, isError = False):
        self.type = INVOKE_RESPONSE
        self.requestId = requestId
        self.message = message
        self.isError = isError
        return


class ReceiveResponse(Response):
    def __init__(self, path, message, channel):
        self.type = RECEIVE_RESPONSE
        self.path = path
        self.message = message
        self.channel = channel
        return


class ReplyRequest(Request):
    def __init__(self, requestId, message, isError = False):
        self.requestId = requestId
        self.message = message
        self.isError = isError


class ReplyResponse(Response):
    def __init__(self, requestId, isError = False):
        self.type = REPLY_RESPONSE
        self.requestId = requestId
        self.isError = isError
        return


class WaitResponse(Response):
    def __init__(self, requestId):
        self.type = WAIT_RESPONSE
        self.requestId = requestId
        return


"""
Process corresponds to a WS-BPEL process
"""
class Process(object):
    def __init__(self, url, messageExchange):
        self.url = url
        self.messageExchange = messageExchange
        self.scopeId = Process.processor.__generateScope__()
        self.replyMessage = "<html><head></head><body>hello world from process " + str(self.scopeId) + "</body></html>"
        return


    def execute(self):
        log.msg("Process " + str(self.scopeId) + " started")
        self.processor.receive(self.scopeId, self.url, self.messageExchange, self.__class__)
        result = self.processor.invoke("http://localhost")
        self.processor.reply(self.scopeId, self.messageExchange, self.replyMessage)
        return        

    
class AlarmProcess(object):
    def __init__(self, period):
        self.period = period
        self.scopeId = Process.processor.__generateScope__()
        return


    def execute(self):
        log.msg("Process " + str(self.scopeId) + " started")
        while (1):
            self.processor.wait(self.scopeId, self.period)
            #result = self.processor.invoke("http://localhost")
            log.msg("Tick")
        return      

"""
Correlations are used to match incoming messages to the corresponding receive 
activities
"""

class Correlation(object):
    def __init__(self, path, messageExchange, requestId):
        self.path = path
        self.messageExchange = messageExchange
        self.requestId = requestId
        self.aChannel = None
        return


    def __eq__(self, other):
        return self.path == other


    def __repr__(self):
        return self.path + " " + "requestId: " + str(self.requestId) + " " + self.messageExchange


    def getChannel(self):
        return self.aChannel


    def setChannel(self, channel):
        self.aChannel = channel

    channel = property(getChannel, setChannel)


class ToyProcessor(object):
    def __init__(self, channel):
        self.responseChannel = channel
        self.requestId = -1
        self.scopeId = 0
        self.requestTable = {}
        self.correlations = []
        self.messageExchangeStates = {}
        self.flag = True
        return


    """
    level 0 calls
    """

    def createProcess(self, factory, *args,**kwargs):
        stackless.tasklet(factory(*args, **kwargs).execute)()


    def invoke(self, url):
        return self.__processRequest__(self.__invokeRequest__, url, self.responseChannel)


    def receive(self, eventScope, url, messageExchange, factory):
        result = self.__processRequest__(self.__receiveRequest__, eventScope, url, messageExchange)

        # and create a new daemon
        if factory != None:
            log.msg("creating replacement daemon")
            self.createProcess(factory, url, messageExchange)
        return result

    def reply(self, eventScope, messageExchange, message):
        self.__processRequest__(self.__replyRequest__, eventScope, messageExchange, message)


    def wait(self, eventScope, period):
        self.__processRequest__(self.__waitRequest__, eventScope, period)

    """
    level 1 calls
    """

    def __rewrite__(self, scope, messageExchange):
        return str(scope) + ":" + messageExchange


    def __processRequest__(self, callable, *args, **kwargs):
        channel = stackless.channel()
        requestId = self.__addRequest__(channel)
        callable(requestId, *args, **kwargs)
        result = channel.receive()
        self.__deleteRequest__(requestId)
        return result


    def __processResponse__(self, response):
        try:
            if response.type == RECEIVE_RESPONSE:
                requestId, message = self.__receiveResponse__(response)
            elif response.type == REPLY_RESPONSE:
                requestId, message = self.__replyResponse__(response)
            elif response.type == INVOKE_RESPONSE:
                requestId, message = self.__invokeResponse__(response)
            elif response.type == WAIT_RESPONSE:
                requestId, message = self.__waitResponse__(response)
            else:
                log.message("something funny has happened " + str(requestId))
                print response
                reactor.stop

            if requestId != REQUEST_ERROR:
                self.requestTable[requestId].send(message)
        except:
            log.msg(sys.exc_info())


    def __generateScope__(self):
        self.scopeId += 1
        return self.scopeId


    def __addRequest__(self, channel):
        self.requestId = self.requestId + 1
        self.requestTable[self.requestId] = channel
        return self.requestId


    def __deleteRequest__(self, requestId):
        del self.requestTable[requestId]
        return     


    def __invokeRequest__(self, requestId, url, responseChannel):
        log.msg("INVOKE_REQUEST Started " + str(requestId) + " " + url)
        Connection(requestId, responseChannel).connect(url)
        log.msg("INVOKE_REQUEST Finished " + str(requestId))


    def __invokeResponse__(self, response):
        log.msg("INVOKE_RESPONSE Started " + str(response.requestId))
        return response.requestId, response.message


    def __receiveRequest__(self, requestId, scope, path, messageExchange):
        log.msg("__RECEIVE_REQUEST___ STARTED " + str(requestId) + " pid:" + str(scope))
        self.__addCorrelation__(requestId, path, self.__rewrite__(scope, messageExchange))
        log.msg("__RECEIVE_REQUEST__ FINISHED__" + str(requestId) + " pid:" + str(scope))


    def __receiveResponse__(self, response):
        log.msg("RECEIVE_RESPONSE STARTED")
        try:
            correlation = self.__removeCorrelation__(response.path)
            self.messageExchangeStates[correlation.messageExchange] = response.channel

        except CorrelationNotFound, E:
            response.channel.send(ReplyRequest(None,"<html><head><body>Path not found</body></html>",True))
            return REQUEST_ERROR, None
        else:                          
            log.msg("RECEIVE_RESPONSE ENDED " + str(correlation.requestId))
            return correlation.requestId, response.message


    def __replyRequest__(self, requestId, scope, messageExchange, message):
        log.msg("REPLY_REQUEST STARTED")
        newMessageExchange = self.__rewrite__(scope, messageExchange)
        channel = self.messageExchangeStates[newMessageExchange]
        del self.messageExchangeStates[newMessageExchange]
        log.msg("REPLY_REQUEST SENDING MESSAGE")
        channel.send(ReplyRequest(requestId, message))
        log.msg("REQUEST_REQUEST FINISHED")
        return


    def __replyResponse__(self, response):
        return response.requestId, None


    def __waitRequest__(self, requestId, scope, period):
        def alarm(requestId):
            self.responseChannel.send(WaitResponse(requestId))
        reactor.callLater(period, alarm, requestId)


    def __waitResponse__(self, response):
        return response.requestId, None


    def __addCorrelation__(self, requestId, path, messageExchange): 
        log.msg("entering __addCorrelation__")
        self.correlations.append(Correlation(path, messageExchange, requestId))
        log.msg("exiting __addCorrelation__")


    def __removeCorrelation__(self, path):
        try:
            log.msg("Looking for correlation =>" + path)
            i = self.correlations.index(path)
            print "found =>", self.correlations[i]
        except ValueError:
            raise CorrelationNotFound(path)
        return self.correlations.pop(i)   


    def execute(self):
        while (self.flag):
            log.msg("processor - waiting for message")
            self.__processResponse__(self.responseChannel.receive())

"""
level 2
"""
class MyRequestHandler(http.Request):

    """
    it is necessary to run the body of the request handler in its own tasklet
    as to prevent the entire reactor from blocking on a channel
    """
    def process(self):
        stackless.tasklet(self.doWork)()

    def doWork(self):
        channel = stackless.channel()
        receiveRequest = ReceiveResponse(self.path, self.content.read(), channel)
        MyRequestHandler.responseChannel.send(receiveRequest)
        log.msg("REQUEST HANDLER WAITING ON CHANNEL")
        reply = channel.receive()

        if reply.isError:
            self.setResponseCode(http.NOT_FOUND)
            theReplyId = REPLY_ERROR
        else:
            theReplyId = reply.requestId
            
        self.write(reply.message.encode("utf-8"))
        self.finish()
        
        log.msg("REQUEST HANDLER WRITING REPLY " + str(theReplyId))
        MyRequestHandler.responseChannel.send(ReplyResponse(theReplyId))
        log.msg("REQUEST HANDLER COMPLETED " + str(theReplyId))
        return

    
class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

    
class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp    

    
class Connection(object):
    def __init__(self, requestId, channel):
        self.channel = channel
        self.requestId = requestId

    def __handleConnection__(self, result):
        log.msg("INVOKE RESPONSE " + str(self.requestId))
        self.channel.send(InvokeResponse(self.requestId, result))


    def __handleError__(self, failure):
        self.channel.send(InvokeResponse(self.requestId, failure, True))


    def connect(self, url):
        client.getPage(url).addCallback(self.__handleConnection__).addErrback(self.__handleError__)
            
            

if __name__ == "__main__":
    
    log.startLogging(sys.stdout)
    log.msg("test starting Solution")
    log.msg("test starting now")

    """
    responses are send on a channel shared by Twisted and the ToyProcessor
    """
    responseChannel = stackless.channel()
    processor = ToyProcessor(responseChannel)
    MyRequestHandler.responseChannel = responseChannel
    MyRequestHandler.processor = processor

    #make all Process instances inherit a processor
    #should create an abstract Process
    Process.processor = processor
    AlarmProcess.processor = processor

    """
    okay start the processor    
    """
    stackless.tasklet(processor.execute)()

    """
    okay, let us run some processes
    """ 
    
    for i in range(0,1000):
        processor.createProcess(Process, "/" + str(i), "message" + str(i))
            
    processor.createProcess(AlarmProcess, 10)

    
    """
    and create a HTTP server
    """
    reactor.listenTCP(8000, MyHttpFactory())

    stackless.tasklet(twistedReactor)()

    while (stackless.getruncount() > 1):
        stackless.schedule()

    log.msg("programme has abnormally terminated?")
   