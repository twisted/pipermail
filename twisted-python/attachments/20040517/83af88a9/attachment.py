from twisted.internet import reactor

def _runUntilCurrentNew():
    """
    If twcs is active, call it before calling the original
    reactor.runUntilCurrent method.
    """
    if reactor.twcs:
        p = reactor.twcs
        reactor.twcs = None
        p()
    _runUntilCurrentOld()

def _timeoutNew():
    """
    If twcs is active, return 0;
    otherwise use the original reactor.timeout to
    calculate the return value.
    """
    if reactor.twcs:
        return 0
    return _timeoutOld()


_runUntilCurrentOld = reactor.runUntilCurrent
_timeoutOld = reactor.timeout

def fastcalltwcs(self):
    reactor.twcs = self

_lastcall = None
reactor.twcs = None

def calltwcs(self):
    global _lastcall
    if _lastcall is None or not _lastcall.active():
        _lastcall = reactor.callLater(0, self)

def _patchCallLater():
    # replace reactor.runUntilCurrent with _runUntilCurrentNew
    reactor.runUntilCurrent = _runUntilCurrentNew
    reactor.poll = None
    # replace reactor.timeout with _timeoutNew
    reactor.timeout=_timeoutNew
    global calltwcs
    calltwcs = fastcalltwcs

class whenNoDelayedCalls:
    """
    I check for when there are no delayed calls and twcs is not active.
    By default, I stop the reactor.

    I'm only useful when you are not using sockets, asynchronous I/O,
    or service threads. ;-(
    """
    def __init__(self,granularity=1.0,func=reactor.stop):
        """
        granularity tells me how often I need to run, in seconds:
        func is the callable to be invoked when I think the reactor is idle.
        """
        self.func=func
        self.granularity=granularity
        reactor.callLater(granularity,self)

    def __call__(self):
        c = len(reactor.getDelayedCalls())
        if c or reactor.twcs:
            reactor.callLater(self.granularity,self)
        else:
            self.func()

def pollLoop(granularity=.2,func=reactor.stop):
    """
    I run the reactor until there are no more delayed calls
    and twcs is inactive.

    I'm a weak equivilent of invoking (a modified) asyncore poll loop.
    But I should not be used in programs which use sockets, asynchronous I/O or
    service threads.
    """
    whenNoDelayedCalls(granularity,func)
    reactor.run()


class CSList:
    """
    Manages a list of functions to be called.

    (Specificly adopted for Twisted)
    """
    
    def __init__(self):
        self.oldLst=[]
        self.newLst=[]
        self.count=0

    def empty(self):
        """
        Returns True when both the new and old cs lists are empty.
        """
        return len(self.oldLst)==self.count and len(self.newLst)==0

    def enter(self,func):
        """
        Adds a callable object, func, to the new cs list.
        """
        calltwcs(self)
        self.newLst.append(func)

    def __call__(self):
        """
        Copies the new cs list to the old cs list,
        empties the new cs list,
        and then calls every item in the old cs list.

        When a function is called, it is dropped from the cs list.
        If the function is to be called repeatedly, it must re-enter
        itself on the cs list.
        """
        if not len(self.newLst):
            return
        self.oldLst=self.newLst
        self.newLst=[]
        while self.count<len(self.oldLst):
            func=self.oldLst[self.count]
            self.count+=1
            func()
        self.count=0
        self.oldLst=[]
        if len(self.newLst):
            calltwcs(self)

    def cancel(self,func):
        """
        Removes func from the cs list.
        """
        try:
            self.newLst.remove(func)
        except:
            i=self.oldLst.index(func,self.count)
            del self.oldLst[i]

class CompStrm:
    """
    Base class for computational streams.

    (Specificly adopted for Twisted)
    """
    
    def __init__(self,returnTo=None):
        """
        Creates the cs iterator object by calling the cs generator method.

        The returnTo parameter is an invoking computational stream.
        """
        self.csi=self.cs()
        self.returnTo=returnTo
        self.pollDelay=.1

    def run(self):
        """
        Enters the computational stream in CSList.
        """
        if self.returnTo:
            self.returnTo.run()
        else:
            self.csList.enter(self)

    def __call__(self):
        """
        Execute the next part of the computational stream.
        """
        try:
            more=self.csi.next()
            if more:
                self.csList.enter(self)
        except StopIteration:
            pass

    def startPoll(self):
        """
        Enter the poll method in PollList.
        """
        self.pollEvent=reactor.callLater(self.pollDelay,self.poll)

    def cancelPoll(self):
        """
        Remove the poll method from PollList.
        """
        self.pollEvent.cancel()

    def startTimer(self,delay,timeoutFunc):
        """
        Schedule timeoutFunc to be called in delay seconds.

        Returns the schedule event used by cancelTimer.
        """
        return reactor.callLater(delay,timeoutFunc)

    def cancelTimer(self,timerEvent):
        """
        Cancel timerEvent.
        """
        timerEvent.cancel()

    def poll(self):
        """
        An optional method, to be implemented in a subclass,
        poll is called after startPoll is called.
        """
        raise NotImplementedError("to be implemented in subclass")

    def cs(self):
        """
        A generator method, to be implemented in a subclass.
        This method must contain at least one yield statement.
        """
        raise NotImplementedError("must be implemented in subclass")

    def eval(self,csClass):
        """
        Creates an instance of csClass, passing self as the invoking
        computational stream.

        This method is useful when one computational stream invokes another:

            cs=self.eval(csClass)
            for i in cs.csi:
                yield i
        """
        return csClass(returnTo=self)

CompStrm.csList=CSList()

