# jasstest.tac - controlling file for a single instance jass webapp
# -*- coding: iso-8859-1 -*-
#
# author   : Werner Thie, wth
# last edit: 20.03.2009
# modhistory:
#   20.03.2009 - wth, created

import sys, os

path = os.getcwd()
sys.path.append(path)

from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import LogFile

from twisted.internet import reactor

from twisted.application import service, strports, internet

from photoserver import gRSRC, JSONFactory

application = service.Application("photoserver")
application.setComponent(ILogObserver, FileLogObserver(LogFile('photoserver.log', '/var/log', rotateLength=10000000)).emit)

gRSRC = JSONFactory()
#site = server.Site(gRSRC)
webserver = strports.service("tcp:9000", gRSRC)
webserver.setServiceParent(application)

#this main() is only used for debugging the server, this file should be run with twistd
def main():
  log.startLogging(sys.stdout)
  reactor.listenTCP(9000, gRSRC)       #start only a basic service when debugging
  reactor.run()

if __name__ == '__main__':
  main()
