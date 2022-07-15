# Credit for the approach goes to Igor Kravtchenko:
# http://twistedmatrix.com/pipermail/twisted-python/2006-August/013814.html

from twisted.python import log

################## From t.i.win32eventreactor.py
from twisted.internet import _dumbwin32proc

def upgraded_win32_spawnProcess(self, processProtocol, executable, args=(), env={}, path=None,
                                uid=None, gid=None, usePTY=0, childFDs=None, win32flags=0):
    """Spawn a process."""
    if uid is not None:
        raise ValueError("Setting UID is unsupported on this platform.")
    if gid is not None:
        raise ValueError("Setting GID is unsupported on this platform.")
    if usePTY:
        raise ValueError("PTYs are unsupported on this platform.")
    if childFDs is not None:
        raise ValueError(
            "Custom child file descriptor mappings are unsupported on "
            "this platform.")
    args, env = self._checkProcessArgs(args, env)
    return _dumbwin32proc.Process(self, processProtocol, executable, args, env, path, win32flags)

################## From t.i.posixbase
from twisted.python.runtime import platform, platformType

processEnabled = False
if platformType == 'posix':
    import process
    processEnabled = True

if platform.isWindows():
    from twisted.internet import _dumbwin32proc
    try:
        import win32process
        processEnabled = True
    except ImportError:
        win32process = None

def upgraded_posix_spawnProcess(self, processProtocol, executable, args=(), env={}, path=None,
                                 uid=None, gid=None, usePTY=0, childFDs=None, win32flags=0):
    args, env = self._checkProcessArgs(args, env)
    if platformType == 'posix':
        from twisted.internet import process
        if usePTY:
            if childFDs is not None:
                raise ValueError("Using childFDs is not supported with usePTY=True.")
            return process.PTYProcess(self, executable, args, env, path,
                                      processProtocol, uid, gid, usePTY)
        else:
            return process.Process(self, executable, args, env, path,
                                   processProtocol, uid, gid, childFDs)
    elif platformType == "win32":
        if uid is not None or gid is not None:
            raise ValueError("The uid and gid parameters are not supported on Windows.")
        if usePTY:
            raise ValueError("The usePTY parameter is not supported on Windows.")
        if childFDs:
            raise ValueError("Customizing childFDs is not supported on Windows.")

        if win32process:
            return _dumbwin32proc.Process(self, processProtocol, executable, args, env, path, win32flags)
        else:
            raise NotImplementedError, "spawnProcess not available since pywin32 is not installed."
    else:
        raise NotImplementedError, "spawnProcess only available on Windows or POSIX."

################## From t.i._dumbwin32proc.py
import os

# Win32 imports
import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32process
import win32security

import pywintypes

from zope.interface import implements
from twisted.internet.interfaces import IProcessTransport, IConsumer, IProducer

from twisted.python.win32 import quoteArguments

from twisted.internet import error
from twisted.python import failure

from twisted.internet import _pollingfile

def upgraded__init__(self, reactor, protocol, command, args, environment, path, win32flags=0):
    _pollingfile._PollingTimer.__init__(self, reactor)
    self.protocol = protocol

    # security attributes for pipes
    sAttrs = win32security.SECURITY_ATTRIBUTES()
    sAttrs.bInheritHandle = 1
    
    # create the pipes which will connect to the secondary process
    self.hStdoutR, hStdoutW = win32pipe.CreatePipe(sAttrs, 0)
    self.hStderrR, hStderrW = win32pipe.CreatePipe(sAttrs, 0)
    hStdinR,  self.hStdinW  = win32pipe.CreatePipe(sAttrs, 0)
    
    win32pipe.SetNamedPipeHandleState(self.hStdinW,
                                      win32pipe.PIPE_NOWAIT,
                                      None,
                                      None)

    # set the info structure for the new process.
    StartupInfo = win32process.STARTUPINFO()
    StartupInfo.hStdOutput = hStdoutW
    StartupInfo.hStdError  = hStderrW
    StartupInfo.hStdInput  = hStdinR
    StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES

    # Create new handles whose inheritance property is false
    pid = win32api.GetCurrentProcess()
    
    tmp = win32api.DuplicateHandle(pid, self.hStdoutR, pid, 0, 0,
                                   win32con.DUPLICATE_SAME_ACCESS)
    win32file.CloseHandle(self.hStdoutR)
    self.hStdoutR = tmp

    tmp = win32api.DuplicateHandle(pid, self.hStderrR, pid, 0, 0,
                                   win32con.DUPLICATE_SAME_ACCESS)
    win32file.CloseHandle(self.hStderrR)
    self.hStderrR = tmp
    
    tmp = win32api.DuplicateHandle(pid, self.hStdinW, pid, 0, 0,
                                   win32con.DUPLICATE_SAME_ACCESS)
    win32file.CloseHandle(self.hStdinW)
    self.hStdinW = tmp

    # Add the specified environment to the current environment - this is
    # necessary because certain operations are only supported on Windows
    # if certain environment variables are present.

    env = os.environ.copy()
    env.update(environment or {})

    cmdline = quoteArguments(args)
    # TODO: error detection here.
    def doCreate():
        self.hProcess, self.hThread, dwPid, dwTid = win32process.CreateProcess(
            command, cmdline, None, None, 1, win32flags, env, path, StartupInfo)
        
    try:
        doCreate()
    except pywintypes.error, pwte:
        if not _dumbwin32proc._invalidWin32App(pwte):
            # This behavior isn't _really_ documented, but let's make it
            # consistent with the behavior that is documented.
            raise OSError(pwte)
        else:
            # look for a shebang line.  Insert the original 'command'
            # (actually a script) into the new arguments list.
            sheb = _dumbwin32proc._findShebang(command)
            if sheb is None:
                raise OSError(
                    "%r is neither a Windows executable, "
                    "nor a script with a shebang line" % command)
            else:
                args = list(args)
                args.insert(0, command)
                cmdline = quoteArguments(args)
                origcmd = command
                command = sheb
                try:
                    # Let's try again.
                    doCreate()
                except pywintypes.error, pwte2:
                    # d'oh, failed again!
                    if _dumbwin32proc._invalidWin32App(pwte2):
                        raise OSError(
                            "%r has an invalid shebang line: "
                            "%r is not a valid executable" % (
                            origcmd, sheb))
                    raise OSError(pwte2)

    win32file.CloseHandle(self.hThread)

    # close handles which only the child will use
    win32file.CloseHandle(hStderrW)
    win32file.CloseHandle(hStdoutW)
    win32file.CloseHandle(hStdinR)

    self.closed = 0
    self.closedNotifies = 0

    # set up everything
    self.stdout = _pollingfile._PollableReadPipe(
        self.hStdoutR,
        lambda data: self.protocol.childDataReceived(1, data),
        self.outConnectionLost)

    self.stderr = _pollingfile._PollableReadPipe(
        self.hStderrR,
        lambda data: self.protocol.childDataReceived(2, data),
        self.errConnectionLost)

    self.stdin = _pollingfile._PollableWritePipe(
        self.hStdinW, self.inConnectionLost)

    for pipewatcher in self.stdout, self.stderr, self.stdin:
        self._addPollableResource(pipewatcher)

    # notify protocol
    self.protocol.makeConnection(self)

    # (maybe?) a good idea in win32er, otherwise not
    # self.reactor.addEvent(self.hProcess, self, 'inConnectionLost')

def upgradeSpawnProcess():
    from twisted.internet import _dumbwin32proc, posixbase, win32eventreactor
    
    win32eventreactor.Win32Reactor.spawnProcess = upgraded_win32_spawnProcess
    posixbase.PosixReactorBase.spawnProcess = upgraded_posix_spawnProcess
    _dumbwin32proc.Process.__init__ = upgraded__init__
