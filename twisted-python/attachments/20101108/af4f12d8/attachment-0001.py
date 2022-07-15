class Task (object):
    def __init__ (self, args):
        self.args = args
        self.pid = None
    def __repr__ (self):
        return str(self.args)+str(self.pid)
    

