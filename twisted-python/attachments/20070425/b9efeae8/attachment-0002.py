#!/usr/bin/env python
"""
TestProcessor.py
April 24th, 2007

The purpose of this programme is to suspend a request handler,
make a series of calls involving deferreds, and resume the
request handler. This test does not work.

The main tasklet makes a series of synchronous
API calls : the first is to wait for a http request. The second
is to get a web page. The last is to send a http reply.

Under the hood, a tasklet "the processor" suspends and resumes
tasklets waiting for IO events.

The programme works fine for:

def execute(self):
    self.processor.getWebPage()

(the programme will just run)

and

def execute(self):
    self.processor.getHttpRequest()
    self.processor.sendHttpResponse()

(use a HTML form with method POST)

However when 

def execute(self):
    self.processor.getHttpRequest()
    self.processor.getWebPage()
    self.processor.sendHttpResponse()

combination are done, something bad happens and the programme
ends pre-maturely

"""

from twisted.internet.defer                           import Deferred
from twisted.python.failure                           import Failure
from twisted.internet                                 import reactor
from twisted.web                                      import client
from twisted.web                                      import http
import stackless
import pdb
import time
import sys

MESSAGE = {0 : "client_response",
           1 : "receive_response",
           2 : "reply_response" }

CLIENT_RESPONSE = 0
RECEIVE_RESPONSE = 1
REPLY_RESPONSE = 2

message = """<html><head></head><body>hello world</body></html>"""


def pump():
    while (1):
      stackless.schedule()
    
    
class Response(object):
    def __init_(self):
        return


class Request(object):
    def __init__(self):
        return
    
"""
run Twisted in its own tasklet
"""
def twistedReactor():
    reactor.run()


"""
a housekeeping data structure to hide how tasklets are
suspended and resumed. For now, we use channels. Not sure
how easy it is to replace this with capture/remove/insert
"""
class Activity(object):
    def __init__(self):
        self.channel = stackless.channel()
        return

    def __repr__(self):
        return str(self.channel.__reduce__())
    
    def resume(self, response):
        self.channel.send(response)
            
    def suspend(self):
        print "[suspending]"
        return self.channel.receive()
    



"""
The Twisted Web server
"""
class Server(object):
    
    """
    Twisted sends network events to the processor via
    a channel
    """
    def execute(self, port, requestChannel):
        MyRequestHandler.requestChannel = requestChannel
        reactor.listenTCP(port, MyHttpFactory())
        return


class MyRequestHandler(http.Request):
    
    def process(self):
            
        print "request handler :", stackless.getcurrent()    
        myChannel = stackless.channel()
        
        response = Response()
        response.type = RECEIVE_RESPONSE
        response.path = self.path
        response.channel = myChannel
        response.body = self.content
        
        """
        send information back to the processor about the
        HTTP request. Include a private channel so the
        processor can send back a reply
        """
        MyRequestHandler.requestChannel.send(response)
        
        """
        send the reply to the client
        """
        reply = myChannel.receive()
        self.write(reply.message)
        self.finish()
        
        """
        tell the processor that request handler has
        finished
        """
        ack = Response()
        ack.type = REPLY_RESPONSE
        ack.body = None
        ack.requestId = reply.requestId
        
        MyRequestHandler.requestChannel.send(ack)
        return
        
        
class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler
    
    
class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp
    
    
"""
The ClientConnection represents a deferred Twisted call
"""
class ClientConnection(object):
    
    """
    include a requestId so the processor can associate completed
    messages with outstanding requests
    """
    def __init__(self, channel, address, requestId):
        self.address = address
        self.channel = channel
        self.requestId = requestId
        return
    
    def __handleResponse__(self, pageData):
        print "__handleResponse__ started"
        
        print "deferred tasklet :", stackless.getcurrent()
        
        response = Response()
        response.requestId = self.requestId
        response.type = CLIENT_RESPONSE
        response.body = pageData
        
        self.channel.send(response)
        print "__handleResponse__ finished"
        return
    
    #ignore errors for now
    def __handleError__(self, failure):
        print "__handleError__"
        return
    
    def connect(self):
        client.getPage(self.address).addCallback(self.__handleResponse__).addErrback(self.__handleError__)     
        return


"""
The TestTasklet makes a series of calls to the processor
"""
class TestTasklet(object):
    def __init__(self, processor):
        self.processor = processor
        return
    
    """
    note - don't care about what is returned.
    """
    def execute(self):
        try:
            """
            the processor ensures that one call must
            complete before the other starts. Besides
            they all run in the same tasklet.
            """
            self.processor.getHttpRequest("/")
            response = self.processor.getWebPage('http://localhost')
            self.processor.sendHttpResponse(message)
        except  :
            print sys.exc_info()
        return


class TestProcessor(object):
    
    def __init__(self, channel):
        self.flag = True
        self.channel = channel
        self.tasklets = {}
        self.requests = {}
        self.requestId = 0
        self.serverChannel = None
        self.receiveActivity = None
        return
    
    
    """
    just return the tasklet associated with the getHttpRequest()
    """
    def __match__(self):
        return self.receiveActivity
    
    
    def __getTaskletEntry__(self):
        tasklet = stackless.getcurrent()
        if not self.tasklets.has_key(tasklet):
            self.tasklets[tasklet] = Activity()
        return self.tasklets[tasklet]
           
           
    #associate a request with a tasklet
    #for now don't worry about set_atomic
    def __addRequest__(self, activity):
        self.requestId = self.requestId + 1
        print "[requestId " + str(self.requestId) + "]"
        self.requests[self.requestId] = activity
        return self.requestId
           
           
    #get a request       
    def __getRequest__(self, requestId):
        print "[resuming request " + str(requestId) + "]"
        return self.requests[requestId]
    
           
    def __removeRequest__(self, requestId):
        del self.requests[requestId]
           
           
    """
    API 
    """
    def getHttpRequest(self, path):
        print "getHttpRequest started"
        #pdb.set_trace()
        activity = self.__getTaskletEntry__()
        requestId = self.__addRequest__(activity)
        self.receiveActivity = (requestId, activity)
        result = activity.suspend()
        self.serverChannel = result.channel
        self.__removeRequest__(requestId)
        print "getHttpRequest finished"
        return result
    
    
    def getWebPage(self, address):
        print "getWebPage started"
        #pdb.set_trace()
        activity = self.__getTaskletEntry__()
        requestId = self.__addRequest__(activity)
        ClientConnection(self.channel, address, requestId).connect()
        result = activity.suspend()
        self.__removeRequest__(requestId)
        print "getWebPage finished"
        return result
    
    
    def sendHttpResponse(self, message):
        print "sendHttpResponse started"
        activity = self.__getTaskletEntry__()
        requestId = self.__addRequest__(activity)
        request = Request()
        request.message = message
        request.requestId = requestId
        self.serverChannel.send(request)
        result = activity.suspend()
        self.__removeRequest__(requestId)
        print "sendHttpResponse finished"
        return 
    
    
    """
    Event processing 
    """
    def processEvents(self):
        while (self.flag):
            response = self.channel.receive()
            
            if response.type == RECEIVE_RESPONSE:
                """
                for now just blindly match any HTTP request
                """
                requestId, activity = self.__match__()
                response.requestId = requestId
            
            """
            get the tasklet associated with the event
            and resume it, giving it a result in the process
            """
            activity = self.__getRequest__(response.requestId)
            activity.resume(response)
            
        print "finished processing"    
        return
    
try:    
    print "test starting"    
    channel = stackless.channel()
    #stackless.tasklet(pump)()
    processor = TestProcessor(channel)
    print "processor", stackless.tasklet(processor.processEvents)()
    print "TaskTasklet", stackless.tasklet(TestTasklet(processor).execute)()
    print "Server", stackless.tasklet(Server().execute)(8000, channel)
    print "reactor tasklet: ", stackless.tasklet(twistedReactor)()
except:
    print sys.exc_info()
    reactor.stop()
    
"""
should run indefinitely
"""
while (stackless.getruncount() > 1):
    stackless.schedule()

print "this is the channel count and blocked tasklets:", channel.__reduce__()

print "dump request table"

for activityObject in processor.requests.values():
    print activityObject

print "dump RH channel"
print processor.receiveActivity