from twisted.internet import stdio, reactor
from twisted.protocols import basic
from twisted.web import client

class WebCheckerCommandProtocol(basic.LineReceiver):
    delimiter = '\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    def connectionMade(self):
        self.sendLine("Web checker console. Type 'help' for help.")

    def lineReceived(self, line):
        if not line: return
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]
        try:
            method = getattr(self, 'do_' + command)
            method(*args)
        except AttributeError, e:
            self.sendLine('Error: no such command.')
        except Exception, e:
            self.sendLine('Error: ' + str(e))            

    def do_help(self, command=None):
        "help [command]: List commands, or show help on the given command"
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Valid commands: " +" ".join(commands))

    def do_quit(self):
        "quit: Quit this session"
        self.sendLine('Goodbye.')
        # stop the reactor, only because this is meant to be run in Stdio.
        # if using with Telnet, use self.transport.loseConnection() instead.
        reactor.stop()
            
    def do_check(self, url):
        "check <url>: Attempt to download the given web page"
        client.getPage(url).addCallback(
            self.__checkSuccess).addErrback(
            self.__checkFailure)

    def __checkSuccess(self, pageData):
        self.sendLine("Success: got %i bytes." % len(pageData))

    def __checkFailure(self, failure):
        self.sendLine("Failure: " + failure.getErrorMessage())

if __name__ == "__main__":
    stdio.StandardIO(WebCheckerCommandProtocol())
    reactor.run()
