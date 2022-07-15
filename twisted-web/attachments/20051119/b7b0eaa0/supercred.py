import random

from zope.interface import implements, Interface, Attribute
from Crypto.PublicKey import RSA

from twisted.protocols import basic
from twisted.internet import defer, stdio, reactor
from twisted.cred import portal

class IDemonstration(Interface):
    name = Attribute("The name of this avatar")

class DemonstrationAvatar(object):
    def __init__(self, name):
        self.name = name

class DemonstrationRealm(object):
    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is IDemonstration:
                return IDemonstration, DemonstrationAvatar(avatarId), reactor.stop
        raise NotImplementedError()

class IDemonstrationCredentials(Interface):
    def getUsername():
        pass

    def setUsername():
        pass

    def nextChallenge():
        pass

    def setResponse():
        pass

    def verifyChallengeResponse():
        pass

class DemonstrationChecker(object):

    credentialInterfaces = (IDemonstrationCredentials,)

    def __init__(self, secretDatabase):
        self.keys = secretDatabase

    def requestAvatarId(self, creds):
        d = creds.getUsername()
        d.addCallback(self.gotUsername, creds)
        return d

    def gotUsername(self, username, creds):
        creds.setPrivateKey(self.keys[username])
        d = creds.verifyChallengeResponse()
        d.addCallback(self.verified, username)
        return d

    def verified(self, result, username):
        if result:
            return username
        raise ecred.UnauthorizedLogin()

class DemonstrationCredentials(object):
    implements(IDemonstrationCredentials)

    waitingForUsername = None
    waitingForPrivateKey = None
    waitingForAuthentication = None

    username = None
    privateKey = None
    authenticated = False

    def __init__(self, phases):
        self.phases = phases
        self.challengesLeft = phases
        self.challenges = []
        self.responses = []

    def getUsername(self):
        if self.username is not None:
            return defer.succeed(self.username)
        self.waitingForUsername = defer.Deferred()
        return self.waitingForUsername

    def nextChallenge(self):
        if self.username is None:
            return defer.succeed("USERNAME")

        if self.privateKey is None:
            self.waitingForPrivateKey = defer.Deferred()
            self.waitingForPrivateKey.addCallback(lambda ign: self.nextChallenge())
            return self.waitingForPrivateKey
        if self.challengesLeft:
            self.challengesLeft -= 1
            self.challenges.append(str(random.random()))
            return defer.succeed(self.privateKey.encrypt(self.challenges[-1], random.randrange(2 ** 32)))
        return defer.succeed(None)

    def setPrivateKey(self, pkey):
        self.privateKey = pkey
        if self.waitingForPrivateKey is not None:
            d, self.waitingForPrivateKey = self.waitingForPrivateKey, None
            d.callback(None)

    def setResponse(self, resp):
        if self.username is None:
            self.username = resp
            if self.waitingForUsername is not None:
                d, self.waitingForUsername = self.waitingForUsername, None
                d.callback(resp)
        else:
            self.responses.append(resp)
            if len(self.responses) == self.phases:
                self.checkResponse()

    def checkResponse(self):
        if self.responses == self.challenges:
            self.correct = True
        else:
            self.correct = False
        self.authenticated = True
        if self.waitingForAuthentication is not None:
            d, self.waitingForAuthentication = self.waitingForAuthentication, None
            d.callback(self.correct)

    def verifyChallengeResponse(self):
        if self.authenticated:
            return defer.succeed(self.correct)
        self.waitingForAuthentication = defer.Deferred()
        return self.waitingForAuthentication

class ComplexAuthenticationProtocol(basic.LineReceiver):
    from os import linesep as delimiter
    state = None

    def __init__(self, portal):
        self.portal = portal

    def connectionMade(self):
        creds = DemonstrationCredentials(3)
        self.creds = creds
        self.state = 'authing'
        d = self.creds.nextChallenge()
        d.addCallback(self.sendChallenge)
        self.portal.login(creds, None, IDemonstration).addCallbacks(self.loggedIn, self.loginFailed)

    def lineReceived(self, line):
        getattr(self, 'state_' + self.state)(line)

    def loggedIn(self, (i, a, l)):
        self.avatar = a
        self.logout = l
        self.state = 'authed'
        self.transport.write('GREAT JOB: ')

    def loginFailed(self, err):
        self.sendLine('ACCESS DENIED')
        self.transport.loseConnection()
        reactor.callLater(0, reactor.stop)

    def state_authed(self, line):
        self.sendLine(self.avatar.name + '> ' + line)

    def connectionLost(self, reason):
        if self.state == 'authed':
            self.avatar = None
            self.logout()

    def state_authing(self, line):
        self.creds.setResponse(line)
        d = self.creds.nextChallenge()
        d.addCallback(self.sendChallenge)

    def sendChallenge(self, challenge):
        if challenge is None:
            # Cycle is complete, wait for portal.login()
            # Deferred to fire.
            self.transport.write('AUTHENTICATING...')
            return
        self.transport.write("AUTH %r: " % (challenge,))

def main():
    r = DemonstrationRealm()
    c = DemonstrationChecker({
            "exarkun": RSA.construct((
                    161859819151819697098254488452824564010217320876817821541898950013341404364938401540928478590407075283248536244195214627226564129026378628713469358115556366932798572246155146009693612210610619147184316601341319915404987601523926979999190949843548551482325311823684520186363883408904082828455778237782407401107L,
                    65537L))})

    p = portal.Portal(r, [c])
    stdio.StandardIO(ComplexAuthenticationProtocol(p))
    reactor.run()

if __name__ == '__main__':
    main()
