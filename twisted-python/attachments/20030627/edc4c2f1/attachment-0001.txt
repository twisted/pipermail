from twisted.web import server, resource, static, server, script
from twisted.web.woven import page
from twisted.internet import reactor


root = static.File(".")
root.ignoreExt(".rpy")
root.processors = {'.rpy': script.ResourceScript}

site = server.Site(root)
reactor.listenTCP(8888, site)
reactor.run()
