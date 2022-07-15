"""A win32 implementation of the Twisted main loop.

This requires win32all or ActivePython to be installed, as well as the
ctypes module from http://starship.python.net/crew/theller/ctypes.html

ctypes is required because win32all does not yet expose the SetTimer
and KillTimer Windows api functions.

Author: U{Thomas Heller<mailto:theller@python.net>}

"""
# win32guireactor
#
# Compared to twisted's win32eventreactor module, this module shows up
# in taskmanager with much less processor use.
# This version now also receives timer events (callLater) through
# the Windows message loop, so displaying a MessageBox in the application
# doesn't block these things.
#
# win32all doesn't expose the required SetTimer and KillTimer windows apis,
# so we must use ctypes here (but that's a feature, not a bug ;-)

from win32file import FD_READ, FD_WRITE, FD_CLOSE, FD_ACCEPT, FD_CONNECT
import win32gui, win32con
from win32file import WSAAsyncSelect
from win32event import MsgWaitForMultipleObjects, \
     WAIT_OBJECT_0, WAIT_TIMEOUT, QS_ALLINPUT, QS_ALLEVENTS

from twisted.internet import abstract, default, main, error
from twisted.python import log, threadable, failure
from twisted.internet.interfaces import IReactorFDSet
from twisted.internet.base import DelayedCall

import sys, time

# for SetTimer, KillTimer
from ctypes import windll
user32 = windll.user32

class Win32Timer(DelayedCall):
    _timerid = 0

    def __init__(self, *args, **kw):
        DelayedCall.__init__(self, *args, **kw)
        self._timerid = Win32Timer._timerid
        Win32Timer._timerid += 1

class Win32GUIReactor(default.PosixReactorBase):

    __implements__ = (default.PosixReactorBase.__implements__, IReactorFDSet)

    __hwnd = None
    __atom = None

    def __init__(self, *args, **kw):
        self.__create_window()
        self.reads = {} # maps fd to readers
        self.writes = {} # maps fd to writers
        self.timers = {} # maps timer ids to Win32Timers
        default.PosixReactorBase.__init__(self, *args, **kw)
        
    def __register_wndclass(self):
        # Register a window class to use as a message window
        wndclass = win32gui.WNDCLASS()
        wndclass.lpfnWndProc = {win32con.WM_USER: self.__wm_networkevent,
                                win32con.WM_TIMER: self.__wm_timerevent}
        wndclass.lpszClassName = "win32guireactor_wndclass%s" % id(self)
        self.__atom = win32gui.RegisterClass(wndclass)
        self.__wndclass = wndclass

    def __create_window(self):
        # Create a window which will be able to receive events
        if self.__atom is None:
            self.__register_wndclass()
        self.__hwnd = win32gui.CreateWindow(self.__atom,
                                            "win32guireactor",
                                            0,
                                            0, 0, 100, 100, 0, 0, 0, None)

    def __wm_timerevent(self, hwnd, msg, wParam, lParam):
        # This method is called if the message window receives
        # timer events
        user32.KillTimer(hwnd, wParam)
        tple = self.timers[wParam]
        tple.func(*tple.args, **tple.kw)

    def __wm_networkevent(self, hwnd, msg, wParam, lParam):
        # This method is called if the message window receives
        # network events
        code = lParam & 0xFFFF
        fd = wParam

        if code & (FD_CONNECT|FD_ACCEPT|FD_READ|FD_CLOSE):
            if not self.reads.has_key(fd):
                return
            obj = self.reads[fd]
            action = obj.doRead
        else:
            if not self.writes.has_key(fd):
                return
            obj = self.writes[fd]
            action = obj.doWrite

        closed = 0
        log.logOwner.own(fd)
        try:
            closed = action()
        except:
            closed = sys.exc_value
            log.deferr()

        if closed:
            self.removeReader(obj)
            self.removeWriter(obj)
            try:
                obj.connectionLost(failure.Failure(closed))
            except:
                log.deferr()
        log.logOwner.disown(fd)

    ################################################################

    def callLater(self, seconds, f, *args, **kw):
        now = time.time()
        tple = Win32Timer(now + seconds, f, args, kw,
                          self._cancelCallLater, self._resetCallLater)
        self.timers[tple._timerid] = tple
        delta = tple.time - now
        assert delta >= 0
        user32.SetTimer(self.__hwnd, tple._timerid, int(delta * 1000)+1, 0)
        return tple

    def _resetCallLater(self, tple):
        delta = tple.time - time.time()
        assert delta >= 0
        user32.SetTimer(self.__hwnd, tple._timerid, int(delta * 1000)+1, 0)

    def _cancelCallLater(self, tple):
        user32.KillTimer(self.__hwnd, tple._timerid)
        del self.timers[tple._timerid]

    ################################################################

    def addReader(self, reader):
        fd = reader.fileno()
        if not self.reads.has_key(fd):
            # setup notifications
            WSAAsyncSelect(fd, self.__hwnd, win32con.WM_USER,
                           FD_READ|FD_WRITE|FD_ACCEPT|FD_CONNECT|FD_CLOSE)
            self.reads[fd] = reader
            
    def removeReader(self, reader):
        fd = reader.fileno()
        if self.reads.has_key(fd):
            del self.reads[fd]
        if not self.writes.has_key(fd):
            # cancel all notifications if not also a writer
            WSAAsyncSelect(fd, self.__hwnd, win32con.WM_USER, 0)

    def addWriter(self, writer):
        fd = writer.fileno()
        if not self.writes.has_key(fd):
            # setup notifications
            WSAAsyncSelect(fd, self.__hwnd, win32con.WM_USER,
                           FD_READ|FD_WRITE|FD_ACCEPT|FD_CONNECT|FD_CLOSE)
            self.writes[fd] = writer

    def removeWriter(self, writer):
        fd = writer.fileno()
        if self.writes.has_key(fd):
            del self.writes[fd]
        if not self.reads.has_key(fd):
            # cancel all notifications, if not also a reader
            WSAAsyncSelect(fd, self.__hwnd, win32con.WM_USER, 0)

    def removeAll(self):
        # remove all selectables, and return a list of them
        result = self.reads.values() + self.writes.values()
        for reader in self.reads.values():
            self.removeReader(reader)
        for writer in self.writes.values():
            self.removeWriter(writer)
        assert not self.reads
        assert not self.writes
        return result
    
    ################################################################

    # Eventually, doIteration would be unneeded, and  mainLoop should simply
    # call win32gui.PumpMessages()
    #
    # Currently it is required, because there is some work done by
    # base.runUntilCurrent() which is not yet done here.

    def doIteration(self, timeout):
        if timeout is None:
            timeout = 5000
        else:
            timeout = int(timeout * 1000)

        val = MsgWaitForMultipleObjects([], False, timeout,
                                        QS_ALLINPUT | QS_ALLEVENTS)
        if val == WAIT_TIMEOUT:
            return
        elif val == WAIT_OBJECT_0:
            exit = win32gui.PumpWaitingMessages()
            if exit:
                self.callLater(0, self.stop)

def install():
    threadable.init(1)
    r = Win32GUIReactor()
    main.installReactor(r)
