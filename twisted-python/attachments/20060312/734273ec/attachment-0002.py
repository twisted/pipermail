"""
    An example FTP server, with minimal user authentication.
"""

from twisted.protocols.ftp  import FTPFactory
from twisted.protocols.ftp  import FTPRealm 
from twisted.cred.portal    import Portal
from twisted.cred.checkers  import AllowAnonymousAccess
from twisted.cred.checkers  import FilePasswordDB

#
# First, set up a portal (twisted.cred.portal.Portal). This will be used
# to authenticate user logins, including anonymous logins.
#
# Part of this will be to establish the "realm" of the server - the most important
# task in this case is to establish where anonymous users will have default access
# to. In a real world scenario this would typically point to something like '/pub'
# but for this example it is pointed at the current working directory for giggles.
#
# The other important part of the portal setup is to point it to a tuple of
# credential checkers. The first of these is used to grant access to anonymous
# users and is relatively simple. The second of these is a very primitive, but
# functional, password checker. For this example I a using a plain text password
# file that has one username:password pair per line. This checker *does* provide
# a hashing interface, and one would normally want to use it instead of plain text
# storage for anything remotely resembling a 'live' network. In this case, the file
# "pass.dat" is used, and stored in the same directory as the server. BAD.
#
# pass.dat looks like this:
#
# =====================
#   jeff:bozo
#   grimmtooth:bozo2
# =====================
#
p = Portal(FTPRealm('./'), 
    (   AllowAnonymousAccess(),
        FilePasswordDB("pass.dat"),)
    )

#
# Once the portal is set up, start up the FTPFactory and pass the portal to it
# on startup. FTPFactory will start up a twisted.protocols.ftp.FTP() handler
# for each incoming OPEN request. Business as usual in Twisted land.
#
f = FTPFactory(p)

#
# You know this part. Point the reactor to port 21 coupled with the above factory,
# and start the event loop.
#
from twisted.internet import reactor
reactor.listenTCP(21, f)
reactor.run()

