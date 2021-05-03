import datetime
import numpy as np

from PySide2.QtCore import QTimer
from PySide2.QtGui import QImage, QPainter, QPixmap
from PySide2.QtWidgets import QApplication, QWidget

import ffmpeg 

def streamVideo(file, bit=8, trim=None):
    format = {
        8 : {"np" : np.uint8, 'rgb' : 'gray', "ch": 1}, # Gray Scale
        24 : {"np" : np.uint8, 'rgb' : 'rgb24', "ch": 3}, # RGB 8Bit
        32 : {"np" : np.uint8, 'rgb' : 'rgba', "ch": 4} # RGBA 8Bit
    }
    if not bit in format.keys(): raise ("{bit}-Bit number not supported yet. Currently only 8-Bit (Grayscale), 24-Bit (RGB), 32-Bit(RGBA)")
    
    probe = ffmpeg.probe(file)

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    
    if video_stream:
        frames = int(eval(video_stream['nb_frames'])) if 'nb_frames' in video_stream else 1
        duration = float(eval(video_stream['duration'])) if 'duration' in video_stream else 1
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        fps = frames/duration
        pix_fmt = video_stream['pix_fmt']

        if trim:
            trim = min(frames, trim)
            duration = trim / frames * duration
        else:
            trim = frames

        vout, _ = (
            ffmpeg
            .input(file)
            .output('pipe:', format='rawvideo', pix_fmt=format[bit]['rgb'], vframes=trim)
            .run(capture_stdout=True)
            # .run_async()
        )

        stream = (
            np
            .frombuffer(vout, format[bit]['np'])
            .reshape([-1, height, width, format[bit]['ch']])
        )

        frames = stream.shape[0]
        metadata = {
            "format" : pix_fmt,
            "width" : width,
            "height" : height,
            "duration" : duration,
            "frameCount" : frames,
            "fps" : fps,
            "bit" : bit
        }
        return stream, metadata

class Image(QWidget):
    def __init__(self, file, bit, trim=None, parent=None):
        super(Image, self).__init__(parent=parent)

        self.stream, self.info = streamVideo(file, bit, trim)
        
        self.frame = -1
        
        self.imageFormat = {
            8 :  QImage.Format_Grayscale8,
            24 :  QImage.Format_RGB888,
            32:  QImage.Format_RGBA8888_Premultiplied,
            # 64:  QImage.Format_RGBA64_Premultiplied
        }

        image = QImage(self.stream[0], self.info['width'], self.info['height'], self.imageFormat[self.info['bit']])
        self.pixmap = QPixmap(image)

        self.setFixedHeight(self.info['height'])
        self.setFixedWidth(self.info['width'])
        
        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.draw)

        
    def mouseReleaseEvent(self, event):
        self.frame = -1
        self.startTime = datetime.datetime.now()
        self.timer.start()

    def draw(self):
        delta = (datetime.datetime.now() - self.startTime).total_seconds()
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
        
    def stop(self):
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication([])
    w = Image("60.mp4", 24, 500)
    w.show()
    app.exec_()