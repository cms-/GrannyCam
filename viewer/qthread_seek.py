from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QThread, SIGNAL
import urllib2, urllib2_ssl
import ssl
import sys
import collections
import time
import httplib
from functools import partial

class VideoScreen(QtGui.QGraphicsView):
    # Screen onto which the image is projected
    # View, Scene and Item rolled into one object
    def __init__(self, parent):
        super(VideoScreen, self).__init__(parent)
        self.added = False
        self._scene = QtGui.QGraphicsScene(self)
        self._photo = QtGui.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
    # Update frame set on timer call in MainWindow
    def setFrame(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self._photo.setPixmap(pixmap)
            if self.added is False:
                self.added = True
        else:
            self._photo.setPixmap(QtGui.Pixmap())


class parserThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.url = None
        self.ttl = 0
        self.exiting = False
        self.request = urllib2.build_opener(urllib2_ssl.HTTPSHandler(
           key_file='/etc/nginx/ssl/lab.key',
           cert_file='/etc/nginx/ssl/lab.crt',
            ca_certs='/home/viewer/cms_CA.crt'
            )
        )

    def run(self):
        n = self.ttl
        r = self.request

        try:
            stream = r.open(self.url)
        except:
            while True:
                time.sleep(5)
                stream = r.open(self.url)
                if stream:
                    break
        # Queue up past initial HTTP multipart header, including prefaced boundary line
               
        start = time.time()
        while not self.exiting and n > 0:
            start = time.time()
            for x in range(2):
                stream.readline()
            stream.read(16)
            jpg_len = stream.read(10).split('\r')

            for x in range(2):
                stream.readline()
            jpg = stream.read(int(jpg_len[0]))
            end = time.time()
            self.emit(QtCore.SIGNAL('updateFrame(PyQt_PyObject)'), jpg)
            print >> sys.stderr, str(end-start) + ' ' + str(sys.getsizeof(jpg))
            stream.readline()

            n -= 1

        r.close()

    
    def __del__(self):
        self.exiting = True
        self.wait()


    def parse(self, url, ttl):
        self.url = url
        self.ttl = ttl
        self.start()


class Window(QtGui.QMainWindow):

    def __init__(self, address):
        super(Window,self).__init__()
        # Init the frame image list
        self.url = "https://" + address + "/?action=stream"
        self.statusBar().hide()
        # Init the video screen
        self.screen = VideoScreen(self)
        self.setCentralWidget(self.screen)
        # Start parsing the web stream for images
        
        # Create thread Worker slot
        self.thread = parserThread()
        self.connect(self.thread, QtCore.SIGNAL('updateFrame(PyQt_PyObject)'), self.updateFrame)
        self.connect(self.thread, SIGNAL("finished()"), self.updateUi)
        #self.connect(self.thread, SIGNAL("terminated()"), self.updateUi)
        self.thread.parse(self.url, 250)

    def updateFrame(self, jpg):
        
        # Runs when signal is sent from stream thread
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(jpg)
        # Calls the VideoScreen function
        self.screen.setFrame(pixmap)

    def updateUi(self):
        self.thread.parse(self.url, 500)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window("lab")
    window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    window.setGeometry(0, 0, 1280, 720)
    window.show()
    sys.exit(app.exec_())
