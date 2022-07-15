"""
Win32 process support.
"""

# Twisted imports
from twisted.internet import abstract, main, win32

# System imports
import win32api
import win32pipe
import win32file
import win32process
import win32security
import win32con
import win32event
import pywintypes
import msvcrt
import os
import sys
import threading
import Queue
import string


class Process(abstract.FileDescriptor):
    """A process that integrates with the Twisted event loop."""
    
    buffer = ''
    
    def __init__(self, command, args, environment, path):
        # security attributes for pipes
        sAttrs = win32security.SECURITY_ATTRIBUTES()
        sAttrs.bInheritHandle = 1

        # create pipes
        hStdin_r,  self.hStdin_w  = win32pipe.CreatePipe(sAttrs, 0)
        self.hStdout_r, hStdout_w = win32pipe.CreatePipe(sAttrs, 0)
        self.hStderr_r, hStderr_w = win32pipe.CreatePipe(sAttrs, 0)

        # set the info structure for the new process.
        StartupInfo = win32process.STARTUPINFO()
        StartupInfo.hStdInput  = hStdin_r
        StartupInfo.hStdOutput = hStdout_w
        StartupInfo.hStdError  = hStderr_w
        StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES
        # Mark doesn't support wShowWindow yet.
        # StartupInfo.dwFlags = StartupInfo.dwFlags | win32process.STARTF_USESHOWWINDOW
        # StartupInfo.wShowWindow = win32con.SW_HIDE
        
        # Create new output read handles and the input write handle. Set
        # the inheritance properties to FALSE. Otherwise, the child inherits
        # the these handles; resulting in non-closeable handles to the pipes
        # being created.
        pid = win32api.GetCurrentProcess()

        tmp = win32api.DuplicateHandle(
            pid,
            self.hStdin_w,
            pid,
            0,
            0,     # non-inheritable!!
            win32con.DUPLICATE_SAME_ACCESS)
        # Close the inhertible version of the handle
        win32file.CloseHandle(self.hStdin_w)
        self.hStdin_w = tmp
        
        tmp = win32api.DuplicateHandle(
            pid,
            self.hStdout_r,
            pid,
            0,
            0,     # non-inheritable!
            win32con.DUPLICATE_SAME_ACCESS)
        # Close the inhertible version of the handle
        win32file.CloseHandle(self.hStdout_r)
        self.hStdout_r = tmp
        
        tmp = win32api.DuplicateHandle(
            pid,
            self.hStderr_r,
            pid,
            0,
            0,     # non-inheritable!
            win32con.DUPLICATE_SAME_ACCESS)
        # Close the inhertible version of the handle
        win32file.CloseHandle(self.hStderr_r)
        self.hStderr_r = tmp
        
        # start the process.
        print "creating process"
        cmdline = "%s %s" % (command, string.join(args, ' '))
        hProcess, hThread, dwPid, dwTid = win32process.CreateProcess(
                None,   # program
                cmdline,# command line
                None,   # process security attributes
                None,   # thread attributes
                1,      # inherit handles, or USESTDHANDLES won't work.
                        # creation flags. Don't access the console.
                0,      # Don't need anything here.
                        # If you're in a GUI app, you should use
                        # CREATE_NEW_CONSOLE here, or any subprocesses
                        # might fall victim to the problem described in:
                        # KB article: Q156755, cmd.exe requires
                        # an NT console in order to perform redirection.. 
                environment,   # new environment
                path,          # new directory
                StartupInfo)
        # normally, we would save the pid etc. here...
        print "process created"
        # Child is launched. Close the parents copy of those pipe handles
        # that only the child should have open.
        # You need to make sure that no handles to the write end of the
        # output pipe are maintained in this process or else the pipe will
        # not close when the child process exits and the ReadFile will hang.
        win32file.CloseHandle(hStderr_w)
        win32file.CloseHandle(hStdout_w)
        win32file.CloseHandle(hStdin_r)

        self.outQueue = Queue.Queue()
        self.closed = 0
        self.stdoutClosed = 0
        self.stderrClosed = 0
        
        threading.Thread(target=self.doWrite).start()
        win32.addEvent(self.hStdout_r, self, self.doReadOut)
        win32.addEvent(self.hStderr_r, self, self.doReadErr)
    
    def write(self, data):
        """Write data to the process' stdin."""
        self.outQueue.put(data)
    
    def closeStdin(self):
        """Close the process' stdin."""
        self.outQueue.put(None)
    
    def connectionLost(self):
        """Will be called twice, by the stdout and stderr threads."""
        if not self.closed:
            win32.removeEvent(self.hStdout_r)
            win32.removeEvent(self.hStderr_r)
            abstract.FileDescriptor.connectionLost(self)
            print "connection lost"
            self.closed = 1
            self.closeStdin()
            win32file.CloseHandle(self.hStdout_r)
            win32file.CloseHandle(self.hStderr_r)
    
    def doWrite(self):
        """Runs in thread."""
        while 1:
            data = self.outQueue.get()
            if data == None:
                break
            try:
                win32file.WriteFile(self.hStdin_w, data, None)
            except win32api.error:
                break
        
        win32file.CloseHandle(self.hStdin_w)
    
    def doReadOut(self):
        """Runs in thread."""
        try:
            hr, data = win32file.ReadFile(self.hStdout_r, 8192, None)
        except win32api.error:
            self.stdoutClosed = 1
            if self.stderrClosed:
                return main.CONNECTION_LOST
            else:
                return
        self.handleChunk(data)
    
    def doReadErr(self):
        """Runs in thread."""
        try:
            hr, data = win32file.ReadFile(self.hStderr_r, 8192, None)
        except win32api.error:
            self.stderrClosed = 1
            if self.stdoutClosed:
                return main.CONNECTION_LOST
            else:
                return
        self.handleError(data)
    

    
if __name__ == '__main__':
    win32.install()
    
    def printer(x):
        print "Got", repr(x)
    
    exe = win32api.GetModuleFileName(0)
    print exe
    p = Process(exe, ['-u', 'processtest.py'], None, None)
    print "ok, made process object"
    p.handleChunk = printer
    p.handleError = printer
    p.write("hello, world")
    p.closeStdin()
    main.run()
