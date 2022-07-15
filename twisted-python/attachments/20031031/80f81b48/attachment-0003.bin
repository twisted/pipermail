#!/usr/local/bin/python
"""RatControl Windows NT Service
"""
import win32serviceutil, win32service

class RatControlService(win32serviceutil.ServiceFramework):
    """RatControl Windows NT Service"""

    _svc_name_ = "RatControlService"
    _svc_display_name_ = "RatControl Server"

    def SvcDoRun(self):
        from twisted.internet import win32eventreactor
        win32eventreactor.install()
        from twisted.internet import reactor        

        from ratcontrol import config, server
        f = file(config.logFile, 'a')
        from twisted.python.log import startLogging
        from twisted.application.app import startApplication
        startLogging(f)
        startApplication(server.application, 0)
        reactor.run()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        from twisted.internet import reactor
        reactor.stop()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(RatControlService)
