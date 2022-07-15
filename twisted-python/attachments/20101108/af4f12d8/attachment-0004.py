import xmlrpclib
import time
import cPickle

class Task (object):
    def __init__ (self, args):
        self.args = args
        self.pid = None
    def __repr__ (self):
        return str(self.args)+str(self.pid)
    
s = xmlrpclib.Server('http://localhost:7080/')
s.queue (['sleep', '4'])
s.queue (['sleep', '15'])
s.queue (['sleep', '15'])
s.queue (['sleep', '15'])
s.queue (['sleep', '15'])
s.queue (['sleep', '15'])
active_tasks, queued_tasks, stopped_tasks = cPickle.loads (s.get_tasks())
sleepy = active_tasks[0].pid
s.suspend (sleepy)
time.sleep(5)
s.go (sleepy)


