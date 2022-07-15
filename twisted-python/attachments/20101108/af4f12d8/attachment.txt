from twisted.internet import protocol, reactor
from twisted.web import xmlrpc, server
from twisted.application import service, internet
import os, signal
import cPickle
from task import Task

class MyPP(protocol.ProcessProtocol):
    def __init__ (self, task):
        self.task = task
    ## def processExited(self, reason):
    ##     print "processExited, status %d" % (reason.value.exitCode,)
    def processEnded(self, reason):
        print "processEnded, task %s, status %s, exit %s, signal %s" % (self.task, reason.value.status, reason.value.exitCode, reason.value.signal)
        active_tasks.remove(self.task)
        schedule()
        
active_tasks = []
queued_tasks = []
stopped_tasks = []

n_cpu = 2

def schedule ():
    free = n_cpu - len(active_tasks)
    if free > 0 and len(queued_tasks) != 0:
        new_task = queued_tasks.pop(0)
        active_tasks.append(new_task)
        if new_task.pid:
            os.kill (new_task.pid, signal.SIGCONT)
            print 'continued:', new_task
        else:
            args = new_task.args
            pp = MyPP(new_task)
            ##r = reactor.spawnProcess(pp, args[0], args, {}, childFDs={0:0, 1:1, 2:2})
            r = reactor.spawnProcess(pp, args[0], args, {})
            #r.transport.closeStdin()
            new_task.pid = r.pid
            print 'started:', new_task
    print 'schedule: active:', active_tasks, 'queued:', queued_tasks, 'stopped:', stopped_tasks, 'ready:'

class Spawner(xmlrpc.XMLRPC):
    """An example object to be published."""

    def xmlrpc_queue(self, args):
        queued_tasks.append (Task (args))
        schedule()
        return True

    def xmlrpc_kill(self, pid, sig):
        task = filter (lambda t: t.pid == pid, active_tasks)
        assert (task != [])
        print 'kill:', task[0]
        os.kill (task[0].pid, sig)
        return True

    def xmlrpc_suspend(self, pid):
        task = filter (lambda t: t.pid == pid, active_tasks)
        assert (task != [])
        print 'suspend:', task[0]
        os.kill (task[0].pid, signal.SIGSTOP)
        active_tasks.remove (task[0])
        stopped_tasks.append (task[0])
        schedule()
        return True
    
    def xmlrpc_go(self, pid):
        task = filter (lambda t: t.pid == pid, stopped_tasks)
        assert (task != [])
        print 'continue:', task[0]
        stopped_tasks.remove (task[0])
        queued_tasks.insert (0, task[0])
        schedule()
        return True
    
    def xmlrpc_get_tasks(self):
        print 'get_tasks:', str ((active_tasks, queued_tasks, stopped_tasks))
        return cPickle.dumps ((active_tasks, queued_tasks, stopped_tasks))
    
application = service.Application("Demo application")

spawn_server = server.Site (Spawner ())

service = internet.TCPServer(7080, spawn_server)
service.setServiceParent(application)

