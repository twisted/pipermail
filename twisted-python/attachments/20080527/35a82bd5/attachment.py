from twisted.internet import wxreactor
wxreactor.install()

import time
import sys
import wx
import getpass

from twisted.conch.ssh import common, channel, connection, userauth, keys
from twisted.internet import defer, reactor
from twisted.conch.client import connect, options, default

################################################################
### Conch connection stuff
###############################################################
class SSHClient(object):
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.password = password
        self.user = user

        self.options = options.ConchOptions()
        self.options['user'] = user
        self.options['port'] = port
        self.options.identitys = ['~/.ssh/id_rsa', '~/.ssh/id_dsa']
        #self.options.conns = ['direct'] # if not set to direct, it uses unix which fails in windows?

    def connect(self):
        print 'doing connect'
        key = default.verifyHostKey
        
        conn = connection.SSHConnection()

        print 'creating auth'
        auth = SSHUserAuth(self.user, self.password, self.options, conn)

        # clear password
        self.password = None

        print 'calling connect'
        dfr = connect.connect(self.host, self.port, self.options, key, auth)
        dfr.addCallback(self.on_connect, conn)

        print 'done with connect'
        return dfr

    def on_connect(self, results, conn):
        print 'on_connect callback'
        # pass the connection instance back up
        return conn

class SSHUserAuth(default.SSHUserAuthClient):
    def __init__(self, user, password, options, conn):
        print 'new sshuserauth'
        default.SSHUserAuthClient.__init__(self, user, options, conn)
        self.password = password
        self.failCount = 0
    
    def getPassword(self, prompt = None):
        print 'get password'
        return defer.succeed(self.password)

    def ssh_USERAUTH_FAILURE(self, packet):
        print 'failure', packet
        self.failCount += 1
        if self.failCount > 5: # it fails a few times before trying the password?
            print 'too many failures'
            raise Exception('Error logging in. Please check password')
            return
        print 'try again'
        userauth.SSHUserAuthClient.ssh_USERAUTH_FAILURE(self, packet)

class BaseCommandChannel(channel.SSHChannel):
    '''Base class for different channel types.'''
    name = 'session'

    def __init__(self, deferred, localWindow = 0, localMaxPacket = 0, remoteWindow = 0, remoteMaxPacket = 0, conn = None, data = None, avatar = None):
        channel.SSHChannel.__init__(self, localWindow, localMaxPacket, remoteWindow, remoteMaxPacket, conn, data, avatar)
        self.deferred = deferred

        self.error = False
        self.errorMsg = ''

    def openFailed(self, reason):
        self.deferred.errback(reason)

    def channelOpen(self, ignoredData):
        self.data = ''

    def dataReceived(self, data):
        self.data += data

    def extReceived(self, dataType, data):
        self.error = True
        self.errorMsg += data

    def closed(self):
        self.loseConnection()
        if self.error:
            self.deferred.errback(IOError(self.errorMsg))
        else:
            self.deferred.callback(self.data)

class RawCommandChannel(BaseCommandChannel):
    '''Simple class to run a command on the remote machine.'''
    name = 'session'

    def __init__(self, command, deferred, localWindow = 0, localMaxPacket = 0, remoteWindow = 0, remoteMaxPacket = 0, conn = None, data = None, avatar = None):
        BaseCommandChannel.__init__(self, deferred, localWindow, localMaxPacket, remoteWindow, remoteMaxPacket, conn, data, avatar)
        self.command = command

    def channelOpen(self, ignoredData):
        self.data = ''

        d = self.conn.sendRequest(self, 'exec', common.NS(str(self.command)), wantReply = 1)


#####################################################
## wx stuff
#####################################################
class TestApp(wx.App):
    def OnInit(self):
        self.connection = None

        # create a window and add some text and buttons
        self.frame = wx.Frame(None, wx.NewId(), 'WX Conch Test')
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        self.frame.Bind(wx.EVT_CLOSE, self.onExit)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # status text
        self.txt = wx.StaticText(self.frame, wx.NewId(), 'Connecting ...')
        sizer.Add(self.txt, 1, wx.EXPAND)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(hSizer, 0, wx.EXPAND)

        # input command text
        self.inputTxt = wx.TextCtrl(self.frame, wx.NewId())
        self.btn = wx.Button(self.frame, wx.NewId(), 'Run Command')
        self.btn.Disable()
        self.btn.Bind(wx.EVT_BUTTON, self.runCmd)

        hSizer.Add(self.inputTxt, 1)
        hSizer.Add(self.btn, 0)

        self.frame.SetSizerAndFit(sizer)

        ## DEBUG TIMERS ##
        # print out the time ever second to see where things
        #  are hanging.  the First is done using twisted's
        #  callLater, and the second is using a wx.Timer
        #  the wx.Timer always calls ever second, while the
        #  twisted callLater seems to hang up

        # start printing to see when twisted hangs up
        self.printLog()

        # start a wx timer to see if it continues
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.printLog2)
        self.timer.Start(1000)

        return True

    def connect(self, host, user, password):
        # start connecting to the machine through ssh
        print 'making connection'
        client = SSHClient(host, 22, user, password)
        print 'calling connect'
        dfr = client.connect()
        print 'setting up callbacks'
        dfr.addCallback(self.onConnected)
        dfr.addErrback(self.onError)
        print 'done'

    def onExit(self, evt):
        reactor.stop()

    def onConnected(self, connection):
        self.txt.SetLabel('Connected')
        self.connection = connection
        self.btn.Enable()

    def onRanCmd(self, results):
        print 'results are', results
        self.txt.SetLabel(str(results))

    def onError(self, error):
        print 'Error:', error.getErrorMessage()
        print error.getTraceback()

    def runCmd(self, evt):
        '''run the command specified by the user'''
        cmd = self.inputTxt.GetValue()
        if self.connection is None or cmd is None or cmd.strip() == '':
            return

        dfr = defer.Deferred()
        channel = RawCommandChannel(cmd, dfr, 2 ** 16, 2 ** 15, self.connection)
        dfr.addCallback(self.onRanCmd)
        dfr.addErrback(self.onError)
        
        self.connection.openChannel(channel)

    def printLog(self):
        print 'twisted:', time.ctime()
        reactor.callLater(1, self.printLog)

    def printLog2(self, evt):
        print 'wx     :', time.ctime()

# create a new app
app = TestApp()

# sleep for 2 seconds
time.sleep(2)

# get the connection info from the user
print 'Enter the host to connect to --> ',
host = sys.stdin.readline().strip()
print 'Enter your username --> ',
user = sys.stdin.readline().strip()
password = getpass.getpass()

# connect to the host
app.connect(host, user, password)
reactor.registerWxApp(app)
reactor.run()
