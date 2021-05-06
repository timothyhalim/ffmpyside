import numpy as np
from datetime import datetime
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import QByteArray, QTimer, Signal
from PySide2.QtMultimedia import QAudioFormat, QAudioOutput

import ffmpeg 

def streamAudio(file, trim=None):
    probe = ffmpeg.probe(file)

    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    
    if audio_stream:
        channels = int(audio_stream['channels'])
        samplerate = int(audio_stream['sample_rate'])
        duration = float(eval(audio_stream['duration']))
        frames = int(audio_stream['nb_frames'])
        audio_codec = audio_stream.get('codec_name')
        if (audio_stream.get('sample_fmt') == 'fltp' and audio_codec in ['mp3', 'mp4', 'aac', 'webm', 'ogg']):
            bit = 16
        else:
            bit = audio_stream['bits_per_sample']

        audioFormat = {
            8  : {'np':np.int8, 'codec':"u8"},
            16 : {'np':np.int16, 'codec':"s16le"},
            32 : {'np':np.int32, 'codec':"s32le"}
        }

        aout, _ = (
            ffmpeg
            .input(file)
            .output('pipe:', format=audioFormat[bit]["codec"], acodec=f"pcm_{audioFormat[bit]['codec']}", ac=channels)
            .run(capture_stdout=True)
        )

        stream = (
            np
            .frombuffer(aout, dtype=audioFormat[bit]["np"])
        )

        ticks = stream.shape[0]
        metadata = {
            "codec" : audio_codec,
            "channels" : channels,
            "duration" : duration,
            "frames" : frames,
            "bitcount" : ticks,
            "samplerate" : samplerate,
            "bit" : bit,
        }
        return stream, metadata

class Sound(QWidget):
    stateChanged = Signal(str)

    def __init__(self, file, trim=None, parent=None):
        super(Sound, self).__init__(parent=parent)
        self.stream, self.info = streamAudio(file, trim)
        self.__dict__.update(self.info)
        
        aformat = QAudioFormat()
        aformat.setSampleRate(self.samplerate)
        aformat.setChannelCount(self.channels)
        aformat.setSampleSize(self.bit)
        aformat.setCodec("audio/pcm") 
        aformat.setByteOrder(QAudioFormat.LittleEndian)
        aformat.setSampleType(QAudioFormat.SignedInt)

        self.output = QAudioOutput(format=aformat)
        self.output.setBufferSize(self.samplerate * self.channels)
        
        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.addToBuffer)

        self.setFrameCount(1)
        self.setState("Idle")

    def setFrameCount(self, frameCount):
        self.frameCount = frameCount
        self.setBitPerFrame()

    def addToBuffer(self):
        delta = (datetime.now() - self.startTime).total_seconds()
        free = self.output.bytesFree()
        if free > 0:
            self.buffer.write(self.data)
            self.data.remove(0, free)
        if delta >= self.duration: self.stop()

    def start(self):
        if self.state == "Paused":
            self.startTime = datetime.now()-self.pausedSecond
            elapsed = int(self.pausedSecond.total_seconds() / self.info['duration'] * len(self.stream))
            self.data = QByteArray(self.stream[elapsed:].tobytes())
        else:
            self.data = QByteArray(self.stream.tobytes())
            self.startTime = datetime.now()

        self.buffer = self.output.start()
        self.timer.start()
        
    def stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def setState(self, state):
        self.state = state
        self.stateChanged.emit(self.state)

    def setVolume(self, vol):
        self.output.setVolume(vol)

    def pause(self, event=None):
        self.timer.stop()
        self.output.stop()
        self.pausedSecond = (datetime.now() - self.startTime)
        self.setState("Paused")

    def setBitPerFrame(self):
        bufferSize = self.samplerate * self.channels
        self.output.setBufferSize(bufferSize)
        
        split = len(self.stream)/self.frameCount
        n = max(1, int(split))
        start = 0
        self.bpf = []
        for i in range(0, self.frameCount):
            end = int(start + n)
            self.bpf.append(QByteArray(self.stream[start:end].tobytes()))
            start = end
        count = 0
        for x in self.bpf:
            for y in self.bpf:
                count += 1

    def seek(self, frame):
        if frame >= len(self.bpf): frame = len(self.bpf)-1
        self.buffer.write(self.bpf[frame])

if __name__ == "__main__":
    app = QApplication([])
    w = Sound("60.mp4")
    w.show()
    app.exec_()
