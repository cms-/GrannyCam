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
    # Screen onto which the image is projected.
    # View, Scene and Item rolled into one object.
    def __init__(self, parent):
        super(VideoScreen, self).__init__(parent)
        self.added = False
        self._scene = QtGui.QGraphicsScene(self)
        self._photo = QtGui.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        # We're doing a full screen window, so we don't need scrollbars.
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # Paint the background nice and black
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

    def setFrame(self, pixmap=None):
        # First check to see if we have a valid QPixmap before attemping to update.
        if pixmap and not pixmap.isNull():
            # Set the VideoScreen's scene's Pixmap object to the image signaled from the worker thread.
            self._photo.setPixmap(pixmap)
            # Ensure the Pixmap object is flagged as added to the scene.
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
        # Queue up past initial HTTP multipart header, including prefaced boundary line.
               
        start = time.time()
        while not self.exiting and n > 0:
            start = time.time()
            
            # Skip ahead two lines.
            for x in range(2):
                stream.readline()
            # Skip ahead 16 bytes.
            stream.read(16)
            # Acquire the MIME size output from the HTTP header.
            jpg_len = stream.read(10).split('\r')
            # Skip ahead two more lines
            for x in range(2):
                stream.readline()
            # Read jpg_len bytes from the rest of the stream.
            jpg = stream.read(int(jpg_len[0]))
            end = time.time()
            # Send the Window's updateFrame function the jpg data for decoding.
            self.emit(QtCore.SIGNAL('updateFrame(PyQt_PyObject)'), jpg)
            print >> sys.stderr, str(end-start) + ' ' + str(sys.getsizeof(jpg))
            stream.readline()
            # 
            n -= 1

        r.close()

    
    def __del__(self):
        # This is the Pythonic function that is bound to Qt thread deconstructor.
        # The exiting condition is set to ensure the thread is not reused.
        self.exiting = True
        self.wait()


    def parse(self, url, ttl):
        # Thread entrance function that sets the initial conditions.
        # (url from which to fetch images & number of images before exiting.)
        self.url = url
        self.ttl = ttl
        self.start()


class Window(QtGui.QMainWindow):

    def __init__(self, address):
        super(Window,self).__init__()
        # Set the URL from which to stream JPEG image data.
        self.url = "https://" + address + "/?action=stream"
        self.statusBar().hide()
        # Create a VideoScreen object onto which the JPEG frames will be displayed.
        self.screen = VideoScreen(self)
        # Ensure our screen is front and center (down in front, please).
        self.setCentralWidget(self.screen)
        
        # Creates a JPEG stream parser thread object.
        self.thread = parserThread()
        # Defines a thread signal to be summoned when image data is available.
        self.connect(self.thread, QtCore.SIGNAL('updateFrame(PyQt_PyObject)'), self.updateFrame)
        # Run the updateUI() function when the thread is finished.
        self.connect(self.thread, SIGNAL("finished()"), self.updateUi)
        #self.connect(self.thread, SIGNAL("terminated()"), self.updateUi)
        # Start the parsing thread, 250 frames will be processed until thread is recycled.
        self.thread.parse(self.url, 250)

    def updateFrame(self, jpg):
        
        # Runs when signal is sent from stream thread.
        # Create a QPixmap object.
        pixmap = QtGui.QPixmap()
        # Decode data from thread as jpg.
        pixmap.loadFromData(jpg)
        # Calls the VideoScreen function to render the QPixmap image.
        self.screen.setFrame(pixmap)

    def updateUi(self):
        self.thread.parse(self.url, 500)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window("lab")

    # Set app full screen. Received video frames will be resized to fit.
    window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    # Running on a 720p monitor.
    window.setGeometry(0, 0, 1280, 720)
    window.show()
    sys.exit(app.exec_())
