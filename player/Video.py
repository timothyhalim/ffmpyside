from PySide2.QtCore import Signal
from PySide2.QtGui import QImage, QPainter, QPixmap

from component.Stream import VideoStream
from component.ElapsedTimer import ElapsedTimer
from component.FrameWidget import FrameWidget

class Viewer(FrameWidget):
    frameChanged = Signal(int)
    frameCountChanged = Signal(int)
    stateChanged = Signal(str)
    ratioChanged = Signal(float)
    fpsChanged = Signal(float)

    def __init__(self, file=None, parent=None):
        super(Viewer, self).__init__(parent=parent)
        
        self.setAcceptDrops(True)

        self.memoryLimit = 0
        self.buffer = []
        self.frame = 0
        self.setFrame(0)
        self.setState("Idle")

        self.timer = ElapsedTimer(self)
        self.timer.timeout.connect(self.draw)
        if file:
            self.setStream(file)

    def setState(self, state):
        self.state = state
        self.stateChanged.emit(self.state)

    def setStream(self, file, bit=24):
        self.stream = VideoStream(file, bit=bit, parent=self)
        self.stream.packet.connect(self.addToBuffer)
        self.stream.finished.connect(self.finishedStreaming)
        self.stream.start()
        self.setState("Buffering")

        self.setRatio(self.stream.metadata['width']/self.stream.metadata['height'])
        self.fpsChanged.emit(self.stream.metadata['fps'])
        self.frameCountChanged.emit(self.stream.metadata['frameCount']-1)

    def addToBuffer(self, stream):
        self.buffer.append(stream)

    def finishedStreaming(self):
        if self.state == "Buffering":
            self.setState("Idle")

    def setFrame(self, frame):
        if len(self.buffer) <= 0: return
        if frame == self.frame: return
        if frame >= len(self.buffer): self.pause(); return
        if frame >= self.stream.metadata['frameCount']: frame = self.stream.metadata['frameCount']-1
        self.frame = frame
        self.frameChanged.emit(self.frame)
        image = QImage(self.buffer[self.frame], self.stream.metadata['width'], self.stream.metadata['height'], self.stream.currentFormat['qt'])
        self.pixmap = QPixmap(image)

        self.update()

    def draw(self):
        secsElapsed = self.timer.elapsed.total_seconds()
        percentage = secsElapsed/self.stream.metadata['duration']
        frame = int(percentage * self.stream.metadata['frameCount'])
        self.setFrame(frame)
        if self.frame >= self.stream.metadata['frameCount'] or secsElapsed >= self.stream.metadata['duration']:
            self.stop()

    def paintEvent(self, event):
        if hasattr(self, "pixmap"):
            painter = QPainter()
            painter.begin(self)
            painter.drawPixmap(self.rect(), self.pixmap)
            painter.end()
        super(Viewer, self).paintEvent(event)

    def start(self):
        if not self.timer.isActive():
            self.timer.start()
        self.setState("Playing")
        
    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
        self.setState("Stopped")

    def pause(self, event=None):
        if self.timer.isActive():
            self.timer.stop()
        self.setState("Paused")

