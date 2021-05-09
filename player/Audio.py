from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from PySide2.QtCore import QByteArray, Qt, Signal
from PySide2.QtMultimedia import QAudioFormat, QAudioOutput

from component.Stream import AudioStream
from component.ElapsedTimer import ElapsedTimer
from component.TooltipSlider import TooltipSlider
from component.ButtonIcon import ButtonIcon

class Speaker(QWidget):
    timeChanged = Signal(float)
    durationChanged = Signal(float)
    stateChanged = Signal(str)

    def __init__(self, file, horizontal=True, parent=None):
        super(Speaker, self).__init__(parent=parent)
        if horizontal:
            QVBoxLayout(self)
            orientation=Qt.Vertical
        else:
            QHBoxLayout(self)
            orientation=Qt.Horizontal
        self.layout().setContentsMargins(0,0,0,0)
        self.volumeSlider = TooltipSlider(orientation=orientation)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(100)
        self.volumeSlider.valueChanged.connect(self.setVolume)
        self.volumeBtn = ButtonIcon(icon="speaker.svg", iconsize=15)
        self.volumeBtn.clicked.connect(self.toggleMute)
        for w in (self.volumeSlider, self.volumeBtn):
            self.layout().addWidget(w)
            
        self.mute = False
        self.memoryLimit = 0
        self.setState("Idle")

        self.timer = ElapsedTimer(self)
        self.timer.timeout.connect(self.speak)
        if file:
            self.setStream(file)

    def setState(self, state):
        self.state = state
        self.stateChanged.emit(self.state)

    def setStream(self, file, bit=24):
        self.stream = AudioStream(file, parent=self)
        self.stream.packet.connect(self.addToBuffer)
        self.stream.finished.connect(self.finishedStreaming)
        self.stream.start()
        self.setState("Buffering")
        
        audioFormat = QAudioFormat()
        audioFormat.setSampleRate(self.stream.metadata['samplerate'])
        audioFormat.setChannelCount(self.stream.metadata['channels'])
        audioFormat.setSampleSize(self.stream.metadata['bit'])
        audioFormat.setCodec("audio/pcm") 
        audioFormat.setByteOrder(QAudioFormat.LittleEndian)
        audioFormat.setSampleType(QAudioFormat.SignedInt)

        self.output = QAudioOutput(format=audioFormat)
        self.output.setBufferSize(self.stream.metadata['samplerate'] * self.stream.metadata['channels'])
        self.device = self.output.start()
        self.data = []
        self.buffer = QByteArray()

        self.durationChanged.emit(self.stream.metadata['duration'])

    def addToBuffer(self, stream):
        self.data.append(stream)
        self.buffer.append(QByteArray(stream.tobytes()))

    def finishedStreaming(self):
        if self.state == "Buffering":
            self.setState("Idle")

    def setFrameCount(self, frameCount):
        # Split bits to framecount so there will be audio during seek
        self.frameCount = frameCount
        
        split = self.stream.metadata['totalbit']/self.frameCount
        increment = max(1, int(split))
        start = 0
        self.bitPerFrame = []
        while start < len(self.data):
            end = int(start + increment)
            self.bitPerFrame.append(QByteArray(self.data[start:end].tobytes()))
            start = end

    def toggleMute(self):
        if not self.mute:
            self.unmute = self.volumeSlider.value()
            self.volumeSlider.setValue(0)
        else:
            self.volumeSlider.setValue(self.unmute)
            self.unmute = self.volumeSlider.maximum()
        self.mute = not self.mute

    def speak(self):
        free = self.output.bytesFree()
        if free > 0:
            self.device.write(self.buffer)
            self.buffer.remove(0, free)
        if self.timer.elapsed.total_seconds() >= self.stream.metadata['duration']: self.stop()

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

    def setVolume(self, vol):
        self.output.setVolume(vol)

    def seek(self, frame):
        if frame >= len(self.bitPerFrame): frame = len(self.bitPerFrame)-1
        self.device.write(self.bitPerFrame[frame])
