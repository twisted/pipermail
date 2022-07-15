application = Application('My_App')
myapp_hub = MyApp()
myapp_hub.setServiceParent(application)
myappchkr = myapp_hub.credchkr

###  HTTP Multiplexer resource  ###
# provides the root for My_App's HTTP resources.
# Base URLs:
#     * Static Web:  '/'
#     * XML-RPC:     '/RPC2'
# TODO:  handle requests sent to the wrong URL gracefully.
mux = web.resource.Resource()

###  My_App XML-RPC interface  ###
xr = myappcred.XmlrpcRealm('My_App XML-RPC',
                          engine=myapp_hub)
xp = portal.Portal(xr)
xp.registerChecker(myappchkr)
mux.putChild('RPC2', myappcred.BasicAuthResource(xp))

###  My_App Static web server  ###
sr = myappcred.StaticHttpRealm('My_App Web', 'web')
sp = portal.Portal(sr)
sp.registerChecker(myappchkr)
res = myappcred.BasicAuthResource(sp)
res.processors = {'.rpy': script.ResourceScript}
mux.putChild('', res)

webport = 8080 # or whatever
site = web.server.Site(mux)
webserv = internet.TCPServer(webport, site)
webserv.setServiceParent(myapp_hub)


