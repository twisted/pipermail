#! /usr/bin/env python

import unbuffered
import warnings
warnings.filterwarnings("ignore", "the FCNTL module is deprecated; please use fcntl")
warnings.filterwarnings("ignore", "the TERMIOS module is deprecated; please use termios")

import os
import sys
import servicemanager
import win32serviceutil
import win32service
import win32api

from twisted.internet import reactor
from twisted.python import log, logfile

def sighandler(sig):
    print "received signal %s" % (sig,)
    return True

win32api.SetConsoleCtrlHandler(sighandler, True)


class NBService(win32serviceutil.ServiceFramework):
    _svc_name_ = ""
    _svc_display_name_ = ""
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.args = args

    def slog(self, x):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            x,
            (self._svc_name_, '')
            )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        try:
            self.slog(servicemanager.PYS_SERVICE_STOPPING)
        except Exception, err:
            print "Error while trying to log service event in SvcStop: %s" %(err,)
            
        from twisted.internet import reactor
        reactor.callFromThread(reactor.stop)

    # SvcStop only gets triggered when the user explictly stops (or restarts)
    # the service. To shut the service down cleanly when Windows is shutting
    # down, we also need to hook SvcShutdown.
    SvcShutdown = SvcStop

    def SvcDoRun(self):
        self.slog(servicemanager.PYS_SERVICE_STARTING,)
        reactor.callLater(0.0, self.slog, servicemanager.PYS_SERVICE_STARTED)

        oldrun = reactor.run
        def reactor_run():
            return oldrun(installSignalHandlers=False)
        reactor.run = reactor_run
        
        try:
            self.main()
            try:
                self.slog(servicemanager.PYS_SERVICE_STOPPED)
            except Exception, err:
                print "Error while trying to log service event in SvcDoRun: %s" %(err,)
            
            print "done"
            print "-"*70
        except Exception, err:
            print "FATAL ERROR:", err
            import traceback
            traceback.print_exc()
            raise

def usage(s=None):
    if s:
        print "nbsvc: error parsing command line: %s" % (s,)
        print

    print "Usage:"
    print "nbsvc install NAME CMD [ARG1...]"
    print "    register service with service manager"
    print
    print "nbsvc remove NAME"
    print "    unregister service at service manager"
    print
    print "nbsvc start NAME"
    print "    start registered service"
    print
    print "nbsvc stop"
    print "    stop running service"
    print
    sys.exit(10)


class Main(object):
    def __init__(self): 
        self.evtsrc_dll = os.path.abspath(servicemanager.__file__)      
        self.klass = NBService
        
        #if servicemanager.RunningAsService():
        # return
        
        if len(sys.argv)<3:
            usage()

        cmd = sys.argv[1]
        name = sys.argv[2]
        args = sys.argv[3:]

        self.name = name
        self.args = args
        self.klass._svc_name_ = name
        self.klass._svc_display_name_ = name

        try:
            m=getattr(self, "cmd_"+cmd)
        except AttributeError:
            usage("unknown command '%s'" % cmd)
        m(args)

    def cmd_install(self, args):
        assert getattr(sys, 'frozen', False), "must be run in frozen mode"
        arg0 = os.path.basename(args[0])
        if arg0.lower().endswith('.exe'):
            arg0 = arg0[:-4]
        args[0] = arg0
        __import__('__main__%s__' % arg0)
        
        k=self.klass

        win32serviceutil.InstallService(None,
                                        serviceName=k._svc_name_,
                                        displayName=k._svc_display_name_,
                                        startType=win32service.SERVICE_AUTO_START,
                                        exeName=sys.executable,
                                        exeArgs='run %s %s' % (self.name, " ".join(['"%s"' % x for x in args])),
                                        )
        sys.exit(0)


    def cmd_stop(self, arg):
        win32serviceutil.StopService(self.klass._svc_name_)

    def cmd_remove(self, arg):
        win32serviceutil.RemoveService(self.klass._svc_name_)

    def cmd_start(self, arg):
        win32serviceutil.StartService(self.klass._svc_name_)

    def cmd_run(self, arg):
        #log.startLogging(open(r"c:\log.txt", 'wb'))
        sys.argv[1:] = arg[1:]
        k=self.klass
        iname = "__main__%s__" % (arg[0],)
        
        def main(self):
            __import__(iname).main()
            
            
        k.main = main # __import__(iname).main
                
        servicemanager.Initialize(k._svc_name_, self.evtsrc_dll)
        servicemanager.PrepareToHostSingle(k)
        servicemanager.StartServiceCtrlDispatcher()

if __name__=='__main__':
    Main()
