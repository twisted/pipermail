import functools

class TestDescriptor(object):
    
    def __init__(self, func):
        self.instances = set()
        self._func = func
    
    def __get__(self, inst, cls):
        if inst is None:
            return self
        print("TD %d (%s.%s) accessed by %s: id=%d"%(id(self), cls,
            self._func.__name__, inst, id(inst)))
        if inst in self.instances:
            print("has already seen %d"%id(inst))
        else:
            self.instances.add(inst)
        return functools.partial(self._func, inst)

