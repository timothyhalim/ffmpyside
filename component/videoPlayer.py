import datetime
import numpy as np

from PySide2.QtCore import QThread, QTimer, Qt, Signal
from PySide2.QtGui import QImage, QPainter, QPixmap
from PySide2.QtWidgets import QApplication, QWidget

import ffmpeg 

class Stream(QThread):
    packet = Signal(object)

    def __init__(self, file, codec='video', bit=24, parent=None) -> None:
        super().__init__(parent=parent)
        self.setStackSize(0)
        self.file = file
        self.codec = codec
        self.bit = bit
        self.imageFormat = {
            8 : {"np" : np.uint8, 'rgb' : 'gray', "ch": 1, "qt" :  QImage.Format_Grayscale8}, # Gray Scale
            24 : {"np" : np.uint8, 'rgb' : 'rgb24', "ch": 3, "qt" : QImage.Format_RGB888}, # RGB 8Bit
            32 : {"np" : np.uint8, 'rgb' : 'rgba', "ch": 4, "qt": QImage.Format_RGBA8888_Premultiplied,} # RGBA 8Bit
        }
        self.currentFormat = self.imageFormat[bit]

        probe = ffmpeg.probe(file)
        self.info = next((stream for stream in probe['streams'] if stream['codec_type'] == self.codec), None)
        frames = int(eval(self.info['nb_frames'])) if 'nb_frames' in self.info else 1
        duration = float(eval(self.info['duration'])) if 'duration' in self.info else 1
        width = int(self.info['width'])
        height = int(self.info['height'])
        fps = frames/duration
        pix_fmt = self.info['pix_fmt']
        self.metadata = {
            "format" : pix_fmt,
            "width" : width,
            "height" : height,
            "duration" : duration,
            "frameCount" : frames,
            "fps" : fps,
            "bit" : self.bit
        }

    def run(self):
        if self.codec == "video":
            packetSize = self.metadata['height'] * self.metadata['width'] * self.currentFormat['ch'] 
            stream = (
                ffmpeg
                .input(self.file)
                .output('pipe:', format='rawvideo', pix_fmt=self.currentFormat['rgb'])
                .run_async(pipe_stdout=True)
            )
            
            while stream.poll() is None:
                packet = stream.stdout.read(packetSize)
                try:
                    frame = np.frombuffer(packet, self.currentFormat['np']).reshape([self.metadata['height'], self.metadata['width'], 3])
                    self.packet.emit(frame)
                    stream.stdout.flush()
                except:
                    pass

class Image(QWidget):
    frameChanged = Signal(int)
    frameCountChanged = Signal(int)
    stateChanged = Signal(str)
    ratioChanged = Signal(float)
    fpsChanged = Signal(float)

    def __init__(self, file, bit, parent=None):
        super(Image, self).__init__(parent=parent)

        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)
        
        self.buffer = []
        self.frame = -1
        self.setFrame(0)

        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.draw)

    def addStream(self, stream):
        self.buffer.append(stream)

    def finishedStreaming(self):
        print("Finished")

    def setStream(self, file, bit=24):
        self.stream = Stream(file, bit=bit, parent=self)
        self.stream.packet.connect(self.addStream)
        self.stream.finished.connect(self.finishedStreaming)
        self.stream.start()

        self.fpsChanged.emit(self.stream.metadata['fps'])
        self.ratioChanged.emit(self.stream.metadata['width']/self.stream.metadata['height'])
        self.frameCountChanged.emit(self.stream.metadata['frameCount']-1)

    def setFrame(self, frame):
        if len(self.buffer) <= 0: return
        if frame >= len(self.buffer): frame = len(self.buffer)-1
        if frame == self.frame: return
        if frame >= self.stream.metadata['frameCount']: frame = self.stream.metadata['frameCount']-1
        self.frame = frame
        self.frameChanged.emit(self.frame)
        image = QImage(self.buffer[self.frame], self.stream.metadata['width'], self.stream.metadata['height'], self.stream.currentFormat['qt'])
        self.pixmap = QPixmap(image)
    
        self.update()

    def draw(self):
        delta = (datetime.datetime.now() - self.startTime).total_seconds()
        frame = int((delta/self.stream.metadata['duration']) * self.stream.metadata['frameCount'])
        self.setFrame(frame)
        if self.frame >= self.stream.metadata['frameCount'] or delta >= self.stream.metadata['duration']:
            self.timer.stop()

    def paintEvent(self, event):
        if hasattr(self, "pixmap"):
            painter = QPainter()
            painter.begin(self)
            painter.drawPixmap(self.rect(), self.pixmap)
            painter.end()

    def start(self):
        self.startTime = datetime.datetime.now()
        self.frame = -1
        self.timer.start()
        
    def stop(self):
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication([])
    w = Image("60.mp4", 24, 500)
    w.show()
    app.exec_()