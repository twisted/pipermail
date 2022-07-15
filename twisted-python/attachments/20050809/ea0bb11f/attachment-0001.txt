"""
Emulation of Python's interactive interpreter that lives in harmony
with Twisted's reactor.
"""


from twisted.python import threadable
threadable.init()

from twisted.internet import reactor, defer, threads
from code import InteractiveConsole as _InteractiveConsole
import sys


class TwistedInteractiveConsole(_InteractiveConsole):
    """Closely emulate the behavior of the interactive Python interpreter,
    but run from within Twisted's reactor!
    """

    def __init__(self, locals=None, filename="<console>"):
        """Constructor.

        The optional locals argument will be passed to the
        InteractiveInterpreter base class.

        The optional filename argument should specify the (file)name
        of the input stream; it will show up in tracebacks.

        """
        _InteractiveConsole.__init__(self, locals, filename)

    def interact(self, banner=None, stopReactor=False):
        """Closely emulate the interactive Python console.

        The optional banner argument specify the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current class name in parentheses (so as not
        to confuse this with the real interpreter -- since it's so
        close!).

        The optional stopReactor argument indicates whether to stop
        the Twisted reactor when the user exits the interpreter (^Z).

        """
        self.stopReactor = stopReactor
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write("%s\n" % str(banner))
        reactor.callLater(0, self._startInteraction)

    def _startInteraction(self, more=False):
        if more:
            prompt = sys.ps2
        else:
            prompt = sys.ps1
        d = defer.maybeDeferred(self.raw_input, prompt)
        d.addCallbacks(self._processInput, self._processInputError)

    def _processInput(self, line):
        more = self.push(line)
        reactor.callLater(0, self._startInteraction, more)

    def _processInputError(self, failure):
        failure.trap(EOFError)
        self.write("\n")
        if bool(self.stopReactor):
            reactor.stop()

    def raw_input(self, prompt=""):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        The base implementation uses the built-in function
        raw_input(); a subclass may replace this with a different
        implementation.

        """
        return threads.deferToThread(raw_input, prompt)


def interact(banner=None, readfunc=None, local=None, stopReactor=False):
    """Closely emulate the interactive Python interpreter.

    This is a backwards compatible interface to the InteractiveConsole
    class.  When readfunc is not specified, it attempts to import the
    readline module to enable GNU readline if it is available.

    Arguments (all optional, all default to None):

    banner -- passed to InteractiveConsole.interact()
    readfunc -- if not None, replaces InteractiveConsole.raw_input()
    local -- passed to InteractiveInterpreter.__init__()
    stopReactor -- passed to InteractiveConsole.interact()

    """
    console = TwistedInteractiveConsole(local)
    if readfunc is not None:
        console.raw_input = readfunc
    else:
        try:
            import readline
        except ImportError:
            pass
    console.interact(banner, stopReactor)


if __name__ == '__main__':
    reactor.callWhenRunning(interact, stopReactor=True)
    reactor.run()
