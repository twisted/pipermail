'''Testing a way to embed IPython in a twisted app without using threads.
(seems to work on Py25/WinXP, twisted2.5 patched with #2157, IPython0.8.0)

twisted.internet.stdio is responsible for getting user input.
An implementation of the LineReceiver protocol passes received lines
to a custom subclass of the IPython shell (main raw_input call removed).

No readline behaviour is available.
(But IPython still sets up readline and uses it for colour printing.)

TODO:
    integrate readline functionality: two possibilities

    1) Change pyreadline so that it can be called back by t.i.stdio for
       all things except waiting for input (i.e. completion, key bindings, ...)
       This would mean no further changes to IPython, which would still
       be using pyreadline directly.
       (or use a GNU readline callback interface: a t.i.stdio-alike would be
       polling/selecting for input, but then call readline to actually consume it.)
    2) Build a readline compatible interface for t.i.stdio
       (only the parts for setting up completeres, key bindings, ...)
       and make the IPython subclass use that instead of pyreadline

As there is a lot of pasted IPython code including comments, I added
##### multi-hash comments and
docstrings explaining the rearrangements.

:author: strank
'''

__docformat__ = "restructuredtext en"

import sys
import __builtin__

from twisted.internet import reactor, stdio
from twisted.protocols import basic
from IPython.Shell import IPShellEmbed
from IPython.iplib import InteractiveShell, ultraTB
from IPython.ipmaker import make_IPython


def main():
    ###### this is what we want:
    reactor.callWhenRunning(startTwistedStdioShell)
    ###### because this blocks the reactor while IPython is active:
    #reactor.callWhenRunning(startIPShell)
    reactor.run()


def startIPShell():
    '''The non-twisted-friendly way of embedding IPython.'''
    some_recognisable_local = 'WAGAWAGA' # gets exposed in Shell
    ipshell = IPShellEmbed([],
                           banner='Standard IPython called from twisted (blocking)',
                           exit_msg='Leaving Interpreter, back to program.')
    ipshell('***Called from top level. '
            'Hit Ctrl-D to exit interpreter and continue program.')
    reactor.stop()


def startTwistedStdioShell():
    '''On Windows, this only works with a patched twisted,
    because twisted.internet.stdio in twisted2.5 is unix only,
    see ticket #2157.
    '''
    some_recognisable_local = 'WAGAWAGA' # does not get exposed
    # because ipshell is only called later in ShellProtocol.connectionMade
    ipshell = TwistedIPShellEmbed([],
                                  banner='IPython embedded in a Twisted application',
                                  exit_msg='Leaving Interpreter, back to program.')
    sp = ShellProtocol(ipshell, '***Called from top level. ')
    #sp.setRawMode()
    stdio.StandardIO(sp)


class TwistedIPShellEmbed(IPShellEmbed):
    '''Same as superclass, BUT:
    __init__ is duplicated, with a single difference:
        The actual IP shell_class is set to our own subclass.
    __call__ is split into two methods for setup / teardown.
    '''

    def __init__(self,argv=None,banner='',exit_msg=None,rc_override=None,
                 user_ns=None):
        """Note that argv here is a string, NOT a list."""
        self.set_banner(banner)
        self.set_exit_msg(exit_msg)
        self.set_dummy_mode(0)
        # sys.displayhook is a global, we need to save the user's original
        # Don't rely on __displayhook__, as the user may have changed that.
        self.sys_displayhook_ori = sys.displayhook
        # save readline completer status
        try:
            #print 'Save completer',sys.ipcompleter  # dbg
            self.sys_ipcompleter_ori = sys.ipcompleter
        except:
            pass # not nested with IPython
        self.IP = make_IPython(argv,rc_override=rc_override,
                               embedded=True,
                               user_ns=user_ns,
                               ###### HERE IS THE DIFFERENCE  -- StefanRank
                               shell_class=TwistedInteractiveShell)
        # copy our own displayhook also
        self.sys_displayhook_embed = sys.displayhook
        # and leave the system's display hook clean
        sys.displayhook = self.sys_displayhook_ori
        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultraTB.FormattedTB(color_scheme = self.IP.rc.colors,
                                             mode = self.IP.rc.xmode,
                                             call_pdb = self.IP.rc.pdb)
        self.restore_system_completer()

    def __call__(self,header='',local_ns=None,global_ns=None,dummy=None):
        # Set global subsystems (display,completions) to our values
        sys.displayhook = self.sys_displayhook_embed
        if self.IP.has_readline:
            self.IP.set_completer()
        if self.banner and header:
            format = '%s\n%s\n'
        else:
            format = '%s%s\n'
        banner =  format % (self.banner,header)
        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        ###### STOP HERE, THIS embed_mainloop DOESN'T BLOCK, RETURN THE SHELL --StefanRank
        return self.IP.embed_mainloop(banner,local_ns,global_ns,stack_depth=1)

    def teardown(self):
        ###### call the code that would have been called at the end of IP.embed_mainloop:
        self.IP.teardown()
        ###### This is the code formerly known as: the end of __call__:
        if self.exit_msg:
            print self.exit_msg
        # Restore global systems (display, completion)
        sys.displayhook = self.sys_displayhook_ori
        self.restore_system_completer()


class TwistedInteractiveShell(InteractiveShell):
    '''Subclassing to remove raw_input call and provide a callback interface.
    Copy-pasted and split up code of embed_mainloop, interact, raw_input.
    '''

    def embed_mainloop(self,header='',local_ns=None,global_ns=None,stack_depth=0):
        # Get locals and globals from caller
        if local_ns is None or global_ns is None:
            call_frame = sys._getframe(stack_depth).f_back
            if local_ns is None:
                local_ns = call_frame.f_locals
            if global_ns is None:
                global_ns = call_frame.f_globals
        self.user_global_ns = global_ns
        local_varnames = local_ns.keys()
        self.user_ns.update(local_ns)
        if local_ns is None and global_ns is None:
            self.user_global_ns.update(__main__.__dict__)
        self.set_completer_frame()
        self.add_builtins()
        self.interact(header)
        return self ###### needed for later calls, interact is now non-blocking

    def teardown(self):
        '''This is the code formerly known as: the end of interact and embed_mainloop.'''
        ##### from interact:
        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1
        ##### from embed_mainloop:
        # now, purge out the user namespace from anything we might have added
        # from the caller's local namespace
        ###### local_varnames not accessible any more,
        ###### should probably be saved... (TODO)
        ###delvar = self.user_ns.pop
        ###for var in local_varnames:
        ###    delvar(var,None)
        # and clean builtins we may have overridden
        self.clean_builtins()

    def interact(self, banner=None):
        ###### HERE IT GETS HAIRY: code copied from self.interact(header)
        if self.exit_now:
            # batch run -> do not interact
            return ###### This does not make any sense now, since we are non-blocking
        cprt = 'Type "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write(banner)
        more = 0
        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1
        self.promptForLine(more)
        return self

    def promptForLine(self, more):
        '''New method. To be called before waiting for the next line.'''
        prompt = ''
        ###### THIS NEEDED TO BE UNTANGLED: originally a while loop in self.interact
        # exit_now is set by a call to %Exit or %Quit
        if not self.exit_now:
            if more:
                prompt = self.hooks.generate_prompt(True)
                if self.autoindent:
                    self.readline_startup_hook(self.pre_readline)
            else:
                prompt = self.hooks.generate_prompt(False)
            ####### code from self.raw_input:
            self.set_completer()
            ####### write the prompt here, writing it in the LineReceiver
            ####### with sendLine messes up the colouring
            self.write(prompt)
        ####### raw_input BEGONE!!!
        ####### unfortunately all the exception handling in self.interact is also gone.
        ####### return and wait for a call to useLine

    def useLine(self, line, continue_prompt=False):
        '''New method. To be called with a new received line.'''
        ####### code from self.raw_input:
        if line.strip():
            if continue_prompt:
                self.input_hist_raw[-1] += '%s\n' % line
                if self.has_readline: # and some config option is set?
                    try:
                        histlen = self.readline.get_current_history_length()
                        newhist = self.input_hist_raw[-1].rstrip()
                        self.readline.remove_history_item(histlen-1)
                        self.readline.replace_history_item(histlen-2,newhist)
                    except AttributeError:
                        pass # re{move,place}_history_item are new in 2.4.
            else:
                self.input_hist_raw.append('%s\n' % line)
        try:
            lineout = self.prefilter(line,continue_prompt)
        except:
            # blanket except, in case a user-defined prefilter crashes, so it
            # can't take all of ipython with it.
            self.showtraceback()
            lineout = ''
        ###### CODE FROM INTERACT AGAIN:
        more = self.push(lineout)
        if (self.SyntaxTB.last_syntax_error and
            self.rc.autoedit_syntax):
            self.edit_syntax_error()
        self.promptForLine(more)
        ###### indicate if we want to quit
        return not self.exit_now


class ShellProtocol(basic.LineReceiver):
    delimiter = '\n' # does not work with '\r\n' on Windows...
                     # this might be an issue with the #2157 patches?

    def __init__(self, ipshell, banner):
        self.ipshell = ipshell
        self.banner = banner

    def connectionMade(self):
        #self.sendLine("Yay, type something!")
        # locals here are available in the shell:
        # (but in practice the locals of the ShellProtocol() call site
        # would be more interesting.)
        another_strange_local = 'hubabuba'
        from twisted.internet import reactor
        self.sheller = self.ipshell(self.banner
                + '\n  quit.....quits via LineReceiver,'
                + '\n  exit()...quits via IPython,'
                + '\n  pause....test pausing the LineReceiver')

    def lineReceived(self, line):
        if line == 'quit':
            self.sendLine('OK quitting')
            self.transport.loseConnection()
            return
        if line == 'pause':
            self.sendLine('OK pausing for 2 seconds')
            self.pauseProducing()
            self.clearLineBuffer()
            # still receives keys typed during the pause,
            # no matter how many clearLineBuffer()s, I use.
            # might be a feature of Windows cmd... ?
            def restart():
                self.clearLineBuffer()
                self.resumeProducing()
                self.clearLineBuffer()
            reactor.callLater(2, restart)
            return
        #self.sendLine("Echo: " + line)
        if not self.sheller.useLine(line): # processes line, prints output and next prompt
            self.sendLine("IPython wants to quit")
            self.transport.loseConnection()
        #self.transport.write("Yay, type more!")

    #def rawDataReceived(self, data):
    #    self.sendLine('RawEcho: ' + str(data))
    #    self.transport.write("Yay, type more!")

    def connectionLost(self, reason):
        try:
            self.ipshell.teardown()
        except IOError:
            pass # is raised by IPython code when you type quit
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()


if __name__ == '__main__':
    main()
