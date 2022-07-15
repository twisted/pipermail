from PyQt4.QtGui import QApplication, QKeyEvent, QPainter, QImage
import cv2
import sys

print 'args:', sys.argv
video = None
if len(sys.argv) > 2:
    print 'start video:', sys.argv[2]
    video = cv2.VideoWriter( sys.argv[2] + '.avi',  cv2.cv.CV_FOURCC('M','J','P','G'), 24, (1024, 768),True)

from PyQt4.QtWebKit import QWebView, QWebPage, QWebSettings

class MaybeVideo(QApplication):
    
    # you may need
    def spoof_hit_enter(self, receiver):
        print 'spoof'
        super(MaybeVideo, self).notify(receiver, QKeyEvent(QEvent.KeyPress, Qt.Key_Enter, Qt.NoModifier)) 
        super(MaybeVideo, self).notify(receiver, QKeyEvent(QEvent.KeyRelease, Qt.Key_Enter, Qt.NoModifier))         

    painter = QPainter()    
    events = []
    ready = False
        
    def notify(self, receiver, event):        
        if MaybeVideo.ready and isinstance(receiver, QWebView) and not MaybeVideo.painter.isActive() and video is not None:
            try:             
                #print 'clip screenshot'   
                image = QImage(QSize(1024, 768), QImage.Format_RGB32)                
                MaybeVideo.painter.begin(image)
                MaybeVideo.painter.setRenderHint(QPainter.Antialiasing, True)            
                MaybeVideo.painter.setRenderHint(QPainter.TextAntialiasing, True)            
                MaybeVideo.painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                MaybeVideo.painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                receiver.page().mainFrame().render(MaybeVideo.painter)            
                image.save("temp.jpg", "jpg")                                    
                video.write( cv2.imread('temp.jpg'))
                MaybeVideo.painter.end()
            except Exception as e:
                print e
        if event.type() == QEvent.SockAct:            
            MaybeVideo.ready = True                                
        elif not event.type() in MaybeVideo.events:
            #print 'new type', receiver, event.type(), QEvent.User
            MaybeVideo.events.append(event.type())
        else:
            pass      
        return super(MaybeVideo, self).notify(receiver, event)

app = MaybeVideo([])

import qt4reactor
qt4reactor.install()

from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import QEvent, Qt, QSize, QUrl

from twisted.internet import reactor

import signal

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkCookieJar

class MaybeVideoWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.web_page = QWebPage()
        
        print self.web_page.settings()        
                
        self.web_page.setNetworkAccessManager(QNetworkAccessManager())        
        self.web_page.networkAccessManager().setCookieJar(QNetworkCookieJar())                
        self.resize(QSize(1024, 768))
        
        web_view = QWebView()        
        web_view.resize(QSize(1024, 768))
        web_view.settings().setAttribute(QWebSettings.AutoLoadImages, True)
        web_view.settings().setAttribute(QWebSettings.JavascriptEnabled, True)        
        web_view.settings().setAttribute(QWebSettings.JavaEnabled, False)        
        web_view.settings().setAttribute(QWebSettings.JavascriptCanOpenWindows, False)        
        web_view.settings().setAttribute(QWebSettings.PluginsEnabled, True)        
        
        self.web_page.setView(web_view)
        self.setCentralWidget(web_view)
        self.setWindowTitle('MaybeVideo')
        
                        
        
        self.web_page.view().urlChanged.connect(self._page_url_change)
        self.web_page.loadStarted.connect(self._page_start)
        self.web_page.loadProgress.connect(self._page_progress)
        self.web_page.loadFinished.connect(self._page_finished)        

    def go(self, url):
        #print 'go:', url
        self.web_page.view().load(QUrl(url))    

    def _page_progress(self, percent):
        #print 'page progress', percent
        pass

    def _page_start(self):
        #print 'page start'
        pass
    
    def _page_finished(self, ok):
        #print 'page finished:', str(ok)
        pass

    def _page_url_change(self, url):
        print '_url_change:', str(url.toString())            
    
mvw = MaybeVideoWindow()    

def end(ign, ign2):
    print 'stopping'
    reactor.stop()

def start():     
    mvw.show()
    if len(sys.argv) > 1:
        mvw.go('http://' + sys.argv[1] )
    else:
        mvw.go('http://www.google.com')

print 'start'    
signal.signal(signal.SIGINT, end)
reactor.callLater(2, start)
reactor.run()
