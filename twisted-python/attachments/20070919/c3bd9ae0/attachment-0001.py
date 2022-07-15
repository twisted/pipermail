from twisted.application import service
from twisted.internet import defer, utils
from twisted.python import log



class ProcessExecutionService(service.Service):


    maxActive = 5


    def __init__(self, maxActive=None):
        if maxActive is not None:
            self.maxActive = maxActive
        self.queue = defer.DeferredQueue()


    def getProcessOutput(self, *a, **k):
        return self.enqueue(utils.getProcessOutput, a, k)


    def getProcessValue(self, *a, **k):
        return self.enqueue(utils.getProcessValue, a, k)


    def startService(self):
        for i in range(self.maxActive):
            self.queue.get().addCallback(self.execute)


    def enqueue(self, callable, args, kwargs):
        d = defer.Deferred()
        self.queue.put((d, callable, args, kwargs))
        return d


    def execute(self, queueItem):

        def processNext(result):
            self.queue.get().addCallback(self.execute)
            return result

        d, callable, args, kwargs = queueItem
        callable(*args, **kwargs).addBoth(processNext).chainDeferred(d)
        



if __name__ == '__main__':

    import random, sys
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    execService = ProcessExecutionService()

    def finished(result, count):
        print "finished: sleep %d, result=%s" % (count, result)

    for i in range(10):
        delay = int(random.random()*5)
        d = execService.getProcessValue(sys.executable,
            args=["-c" "import time; time.sleep(%d)"%delay])
        d.addCallback(finished, delay)

    reactor.callLater(0, execService.startService)
    reactor.run()

