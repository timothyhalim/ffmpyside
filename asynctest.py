from datetime import datetime
import ffmpeg
import numpy as np
from pprint import pprint
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtGui import QImage, QPainter, QPixmap

class Frame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.stream = []
        self.pixmap = QPixmap()
        
    def show(self):
        super().show()
        
        probe = ffmpeg.probe(file)
        pprint(probe)

        videoInfo = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if videoInfo:
            self.setInfo(videoInfo)

    def setInfo(self, info):
        frames = int(eval(info['nb_frames'])) if 'nb_frames' in info else 1
        duration = float(eval(info['duration'])) if 'duration' in info else 1
        width = int(info['width'])
        height = int(info['height'])
        fps = frames/duration
        pix_fmt = info['pix_fmt']
        self.info = {
            "format" : pix_fmt,
            "width" : width,
            "height" : height,
            "duration" : duration,
            "frameCount" : frames,
            "fps" : fps,
            "bit" : bit
        }

        pixformat = {
            8 : {"np" : np.uint8, 'rgb' : 'gray', "ch": 1}, # Gray Scale
            24 : {"np" : np.uint8, 'rgb' : 'rgb24', "ch": 3}, # RGB 8Bit
            32 : {"np" : np.uint8, 'rgb' : 'rgba', "ch": 4} # RGBA 8Bit
        }

        
        vsync = (
            ffmpeg
            .input(file)
            .output('pipe:', format='rawvideo', pix_fmt=pixformat[bit]['rgb'])
            .run_async(pipe_stdout=True)
        )
        
        packetSize = height * width * pixformat[bit]['ch'] 
        while vsync.poll() is None:
            packet = vsync.stdout.read(packetSize)
            try:
                p = np.frombuffer(packet, pixformat[bit]['np']).reshape([height, width, 3])
                self.addStream(p)
            except:
                pass

    def addStream(self, stream):
        self.stream.append(stream)
        self.start()

    def draw(self):
        delta = (datetime.now() - self.startTime).total_seconds()
        frame = int((delta/self.info['duration']) * self.info['frameCount'])
        if frame == self.frame: return
        self.frame = frame
        if self.frame >= self.info['frameCount'] or delta >= self.info['duration']:
            self.timer.stop()
            image = QImage(self.stream[self.info['frameCount']-1], self.info['width'], self.info['height'], self.imageFormat[self.info['bit']])
            self.pixmap = QPixmap(image)
            self.update()
            return
        print("v----", delta)
        image = QImage(self.stream[self.frame], self.info['width'], self.info['height'], self.imageFormat[self.info['bit']])
        self.pixmap = QPixmap(image)
    
        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(self.rect(), self.pixmap)
        painter.end()

    def start(self):
        self.startTime = datetime.datetime.now()
        self.timer.start()
        image = QImage(self.stream[0], self.info['width'], self.info['height'], self.imageFormat[self.info['bit']])
        self.pixmap = QPixmap(image)

file = "60.mp4"
bit = 24
app = QApplication([])
frame = Frame()
frame.show()
app.exec_()

