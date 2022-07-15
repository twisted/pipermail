import sys, time, socket
from threading import Thread
import threadframe, traceback
from twisted.web2 import server, channel, static, wsgi, resource
from twisted.internet import reactor

class TwistedWebServerThread(Thread):

    def __init__(self, app):
        Thread.__init__(self, name="Twisted")
        factory = channel.HTTPFactory(server.Site(wsgi.WSGIResource(app)))
        reactor.listenTCP(8080, factory, interface="0.0.0.0")

    def run(self):
        reactor.run(installSignalHandlers=False)

def dummy_app(environ, start_response):
    out_content = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
    start_response('200 OK', [('Content-type', 'text/plain')])
    return [out_content]

#data intentionally less then content length
D = "POST /cgi-bin/minapi.py HTTP/1.0\r\n"+ \
 "Host: 127.0.0.1:8080\r\n"+\
 "Content-Type: text/xml\r\n"+\
 "Content-Length: 152\r\n"+\
 "\r\n"+\
 "<?xml version='1.0'?>\n"+\
 "<methodCall>\n"+\
 "<methodName>getStateName</methodName>\n" +\
 "<params>\n" +\
 "<param>\n" +\
 "<value><int>41</int></value>\n" #+\
# "</param>\n" +\
# "</params>\n" +\
# "</methodCall>\n"

#D = open("data.txt3", "rb").read()

def half_post():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 8080))
    s.send(D)
    s.close()

def write_server_threads():
    frames = threadframe.threadframe()
    for frame in frames:
        print '-' * 72 
        for linestr in traceback.format_stack(frame):
            print linestr

if __name__ == "__main__":
    s = TwistedWebServerThread(dummy_app)
    s.start()
    time.sleep(0.2)
    half_post()
    time.sleep(5)
    write_server_threads()