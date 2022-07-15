from twisted.protocols import ftp
from twisted.python import usage, log, filepath, failure
from twisted.application import internet
from twisted.cred import error, portal, checkers, credentials
from twisted.internet import reactor, defer
from zope.interface import Interface, implements
"""
A simple, Mock ftpserver based on the twisted ftp plugin.
Usage:
def setUp(self):
   self.server = FtpServerFactory({ 'root': /tmp,  }).makeServer()
def tearDown(self):
   server.close()
Todo: Make a IFTPShell implementation that can take a directory structure defined as a dictionary.
"""

class MyFTPRealm:
    """
    Special ftprealm that uses the root for logged in users and /tmp for anon users.
    @type anonymousRoot: L{twisted.python.filepath.FilePath}
    @ivar anonymousRoot: Root of the filesystem to which anonymous, default /tmp
    @type : L{twisted.python.filepath.FilePath}
    @ivar anonymousRoot: Root of the filesystem to which logged in users may see
    users will be granted access.
    """
    implements(portal.IRealm)
    def __init__(self, root, anonymousRoot = "tmp"):
        self.anonymousRoot = filepath.FilePath(anonymousRoot)
        self.root = root

    def requestAvatar(self, avatarId, mind, *interfaces):

        for iface in interfaces:
            if iface is ftp.IFTPShell:
                if avatarId is checkers.ANONYMOUS:
                    avatar = ftp.FTPAnonymousShell(self.anonymousRoot)
                else:
                    avatar = ftp.FTPShell(filepath.FilePath(self.root))
                return ftp.IFTPShell, avatar, getattr(avatar, 'logout', lambda: None)
        raise NotImplementedError("Only IFTPShell interface is supported by this realm")
class FtpServerFactory(object):
    """
    Simple mock ftp server instance.
    usage:
    def setUp(self):
        port = FtpServerFactory({'root': './tmp', 'allowed_users': {'twisted':'twisted'}}).makeListner()
        # important: use the addCleanup function instead of the normal tearDown function.
        self.addCleanup(port.stopListening)
    def testSomething()
    """
    def __init__(self, config):

        f = ftp.FTPFactory()
        log.msg("Starting ftp server with root: " + config['root'])

        r = MyFTPRealm(config['root'])

        p = portal.Portal(r)
        p.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)

        if config.has_key('password-file') and config['password-file'] is not None:
            p.registerChecker(checkers.FilePasswordDB(config['password-file'], cache=True))
        if config['allowed_users'] is not None:
            p.registerChecker(checkers.InMemoryUsernamePasswordDatabaseDontUse(**config['allowed_users']))

        f.tld = config['root']
        f.userAnonymous = config.get('userAnonymous', 'anon')
        f.portal = p
        f.protocol = ftp.FTP

        self.f = f

        try:
            self.portno = 21
            #self.portno = int(config['port'])
        except KeyError:
            self.portno = 2121

    def makeListener(self):
        """
        Starts listening to a random port.
        @return: an object that provides L{IListeningPort}.
        """
        return reactor.listenTCP(0, self.f, interface="127.0.0.1")

port = FtpServerFactory({'root': './tmp', 'allowed_users': {'zozo':'zozo'},  'port': 21}).makeListener()
reactor.run()