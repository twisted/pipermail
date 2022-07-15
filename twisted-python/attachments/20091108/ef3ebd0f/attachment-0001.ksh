# Copyright (c) 2009 Ziga Seilnacht. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE FREEBSD PROJECT ''AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE FREEBSD PROJECT OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import sys
import msvcrt

try:
    import win32con
    import win32process
    import win32security
    import win32service
except ImportError:
    win32process = None

from twisted.python import win32



def getPythonArgs():
    """
    Return the list of command line args that were used to start
    the current Python interpreter and were not stored in C{sys.argv}.

    These are the options that control the Python interpreter itself,
    like the Python executable, optimization level, warning filters,
    division behaviour and literal string handling.
    """
    args = [sys.executable]
    for warnoption in sys.warnoptions:
        args.append("-W")
        args.append(warnoption)
    if type(1 / 2) is not int:
        args.append("-Qnew")
    if type("") is not str:
        args.append("-U")
    if not __debug__:
        if getPythonArgs.__doc__ is None:
            args.append("-OO")
        else:
            args.append("-O")
    return args



def daemonize():
    args = [os.path.abspath(__file__)] + sys.argv
    executable = sys.executable
    cmdline = win32.quoteArguments(getPythonArgs() + args)
    inherit = False
    priority = win32process.GetPriorityClass(win32process.GetCurrentProcess())
    flags = (win32process.CREATE_BREAKAWAY_FROM_JOB | # session leader
             win32process.CREATE_NEW_PROCESS_GROUP |  # group leader
             win32process.DETACHED_PROCESS |          # no controlling terminal
             priority)
    info = win32process.STARTUPINFO()
    win32process.CreateProcess(executable, cmdline, None, None,
                               inherit, flags, None, None, info)
    # Do what exec* functions do, let the OS do the cleanup.
    os._exit(0)



def daemonize2():
    args = [sys.argv[1], "--nodaemon"] + sys.argv[2:]
    executable = sys.executable
    cmdline = win32.quoteArguments(getPythonArgs() + args)
    inherit = True
    priority = win32process.GetPriorityClass(win32process.GetCurrentProcess())
    flags = (win32process.CREATE_NO_WINDOW | # create an invisible console
             win32process.CREATE_NEW_PROCESS_GROUP | # group leader
             priority)
    attributes = win32security.SECURITY_ATTRIBUTES()
    attributes.bInheritHandle = True
    station = win32service.CreateWindowStation(None, 0,
                                               win32con.GENERIC_READ |
                                               win32con.GENERIC_WRITE,
                                               attributes)
    station.SetProcessWindowStation()
    sname = win32service.GetUserObjectInformation(station,
                                                  win32service.UOI_NAME)
    dname = str(os.getpid())
    desktop = win32service.CreateDesktop(dname, 0,
                                         win32con.GENERIC_READ |
                                         win32con.GENERIC_WRITE,
                                         attributes)
    desktop.SetThreadDesktop()
    null = os.open("NUL", os.O_RDWR)
    handle = msvcrt.get_osfhandle(null)
    info = win32process.STARTUPINFO()
    info.lpDesktop = "%s\\%s" % (sname, dname)
    info.dwFlags = win32process.STARTF_USESTDHANDLES
    info.hStdInput = info.hStdOutput = info.hStdError = handle
    win32process.CreateProcess(executable, cmdline, None, None,
                               inherit, flags, None, None, info)
    # Same as above, exit as fast as posible.
    os._exit(0)



if __name__ == "__main__":
    daemonize2()
