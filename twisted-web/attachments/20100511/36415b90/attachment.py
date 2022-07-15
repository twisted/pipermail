from twisted.web import server, resource
from twisted.internet import reactor,threads
from twisted.python.util import println
from twisted.web.server import NOT_DONE_YET

class DelayedResource(resource.Resource):
    	isLeaf = True

	def _responseFinished(self,d):
		print "in response Finished ! " ,d

	def _delayedRender(self, request):
		from time import sleep
        	request.write("<html><body>Sorry to keep you waiting.</body></html>")
		request.finish()

	def error(self,err):
		print "err " , err

	def blockingError(self,err):
		print "In blocking error"

	def blockingProcess (self,request):
	 	from time import sleep
		print "Blocking ..."
		sleep(30)
		print "About to write"
		request.write("In blocking handler")
		request.finish()	
		print "wrote"


	def render_GET(self, request):
		d2=threads.deferToThread(self.blockingProcess,request)
		d2.addErrback(self.blockingError)
		d = request.notifyFinish()
		d.addErrback(self.error)
		return server.NOT_DONE_YET

site = server.Site(DelayedResource())
reactor.listenTCP(8080,site,interface="192.168.0.10")
reactor.run()
