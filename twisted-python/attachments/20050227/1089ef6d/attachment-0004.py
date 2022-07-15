"""
Twisted Tap-builder for the Pan Galactic Repository Service
@version: $Revision: 1.30 $
"""

__version__ = "$Revision: 1.30 $"[11:-2]
# $Source: /repo/step_testbed/PanGalactic/pangalactic/pgertap.py,v $

import os

# Twisted imports ...
from twisted.application import internet
from twisted.application.service import Application
from twisted.cred import portal
from twisted.enterprise import adbapi
from twisted.internet import ssl
from twisted.python import usage
from twisted.python import log
from twisted.spread import pb
from twisted.web import script
from twisted import web

# PanGalactic imports ...
from pangalactic.repo.pger import Pger
from pangalactic.repo.pgerxmlrpc import PgerXmlrpcService
from pangalactic.repo.pgersoap import PgerSoapService
from pangalactic.repo import pgercred

class Options(usage.Options):

    optParameters = [["webport", "p", 8080,
                      """Port number to have the web-server with
                      XML-RPC interface listen on."""],
                     ["encrypted", "e", "0",
                      "Specifies whether to use SSL."],
                     ["pbport", "b", str(pb.portno)],
                     ["home", "h", "/usr/local/pger",
                      """Home directory for PGER.  This can also be set
                      using the environment variable PGERHOME."""],
                     ["domains", "d", "",
                      """List of domains."""]]

def makeService(config):

    if config["webport"]:               # set TCP port to listen on 
        webport = int(config["webport"])

    if config["encrypted"]:             # --encrypted=0 -> no SSL
        encrypted = int(config["encrypted"])

    if config["pbport"]:
        pbport = int(config["pbport"])

    if config["home"]:
        home = config["home"]

    if config["domains"]:               # configure domains
        domains = config["domains"]
    else:
        domains = 'PanGalactic'

    app = Application('PanGalaxian')
    # TODO:  make this more elegantly configured
    pgerhub = Pger(domains=domains, encrypted=encrypted)
    pgerhub.setServiceParent(app)
    pgerchkr = pgerhub.credchkr

    ###  PGER Perspective Broker Interface  ###
    # PgerPB is temporarily disabled (until we look at what needs
    # to be changed to make it work with the new PB architecture)
        # bkr = pb.PBServerFactory(PGER)
        # pgerhub.addService(bkr)
        # application.listenTCP(pbport, bkr)

    ###  HTTP Multiplexer resource  ###
    # "mux" provides the root for the PGER HTTP resources.
    # Standard base URLs:  
    #     * Static Web:  '/'
    #     * XML-RPC:     '/RPC2'
    #     * SOAP:        '/SOAP'
    # TODO:  handle requests sent to the wrong URL gracefully.
    mux = web.resource.Resource()

    ###  PGER XML-RPC interface  ###
    xr = pgercred.XmlrpcRealm('PGER XML-RPC',
                              engine=pgerhub)
    xp = portal.Portal(xr)
    xp.registerChecker(pgerchkr)
    mux.putChild('RPC2', pgercred.BasicAuthResource(xp))

    ###  PGER SOAP interface  ###
    # TODO:  not implemented yet (just copied from XML-RPC ;)
    # mux.putChild('SOAP', PgerSoapService(pgerhub))

    ###  PGER HTTP file-upload interface  ###
    # non-browser upload interface (for direct http uploads)
    ur = pgercred.FileUploadRealm('PGER HTTP File Upload',
                                  engine=pgerhub)
    up = portal.Portal(ur)
    up.registerChecker(pgerchkr)
    mux.putChild('upload', pgercred.BasicAuthResource(up))

    ###  PGER HTTP file-upload interface  ###
    # web browser (html) upload interface
    wur = pgercred.WebUploadRealm('PGER HTTP File Upload',
                                  engine=pgerhub)
    wup = portal.Portal(wur)
    wup.registerChecker(pgerchkr)
    mux.putChild('webupload', pgercred.BasicAuthResource(wup))

    ###  PGER Static web server  ###
    sr = pgercred.StaticHttpRealm('PGER Web', 'web')
    sp = portal.Portal(sr)
    sp.registerChecker(pgerchkr)
    res = pgercred.BasicAuthResource(sp)
    res.processors = {'.rpy': script.ResourceScript}
    mux.putChild('', res)

    site = web.server.Site(mux)
    if encrypted:
        privkey = os.path.join(home, 'ssl/privkey.pem')
        certifc = os.path.join(home, 'ssl/cert.pem')
        ctx  = ssl.DefaultOpenSSLContextFactory(privkey, certifc)
        webserv = internet.SSLServer(webport, site, ctx)
    else:
        webserv = internet.TCPServer(webport, site)
    webserv.setServiceParent(pgerhub)
    return webserv



