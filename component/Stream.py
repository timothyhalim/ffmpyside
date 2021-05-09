import numpy as np
from PySide2.QtCore import QThread, Signal
from PySide2.QtGui import QImage

import ffmpeg

class Stream(QThread):
    packet = Signal(object)

    def __init__(self, file, codec, parent=None) -> None:
        super(Stream, self).__init__(parent=parent)
        self.file = file
        self.codec = codec

        probe = ffmpeg.probe(file)
        self.info = next((stream for stream in probe['streams'] if stream['codec_type'] == self.codec), None)

class VideoStream(Stream):
    def __init__(self, file, bit=24, parent=None) -> None:
        super().__init__(file, codec="video", parent=parent)

        self.bit = bit
        self.imageFormat = {
            8 : {"np" : np.uint8, 'rgb' : 'gray', "ch": 1, "qt" :  QImage.Format_Grayscale8}, # Gray Scale
            24 : {"np" : np.uint8, 'rgb' : 'rgb24', "ch": 3, "qt" : QImage.Format_RGB888}, # RGB 8Bit
            32 : {"np" : np.uint8, 'rgb' : 'rgba', "ch": 4, "qt": QImage.Format_RGBA8888_Premultiplied,} # RGBA 8Bit
        }

        if self.info:
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
            self.currentFormat = self.imageFormat[self.bit]

    def run(self):
        packetSize = self.metadata['height'] * self.metadata['width'] * self.currentFormat['ch'] 
        stream = (
            ffmpeg
            .input(self.file)
            .output(
                'pipe:', 
                format='rawvideo', 
                pix_fmt=self.currentFormat['rgb']
            )
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

class AudioStream(Stream):
    def __init__(self, file, parent=None) -> None:
        super().__init__(file, codec="audio", parent=parent)

        self.audioFormat = {
            8  : {'np':np.int8, 'data':"u8"},
            16 : {'np':np.int16, 'data':"s16le"},
            32 : {'np':np.int32, 'data':"s32le"}
        }

        if self.info:
            print(self.info)
            channels = int(self.info['channels'])
            samplerate = int(self.info['sample_rate'])
            duration = float(eval(self.info['duration']))
            duration_ts = self.info['duration_ts']
            frames = int(self.info['nb_frames'])
            audio_codec = self.info.get('codec_name')
            if (self.info.get('sample_fmt') == 'fltp' and audio_codec in ['mp3', 'mp4', 'aac', 'webm', 'ogg']):
                bit = 16
            else:
                bit = self.info['bits_per_sample']

            self.metadata = {
                "codec" : audio_codec,
                "channels" : channels,
                "duration" : duration,
                "frames" : frames,
                "totalbit" : duration_ts*channels,
                "samplerate" : samplerate,
                "bit" : bit
            }
            self.currentFormat = self.audioFormat[bit]

    def run(self):
        packetSize = self.metadata['samplerate'] * self.metadata['channels']
        stream = (
            ffmpeg
            .input(self.file)
            .output(
                'pipe:', 
                format=self.currentFormat['data'], 
                acodec=f"pcm_{self.currentFormat['data']}", 
                ac=self.metadata['channels']
            )
            .run_async(pipe_stdout=True)
        )
        
        while stream.poll() is None:
            packet = stream.stdout.read(packetSize)
            try:
                frame = np.frombuffer(packet, dtype=self.currentFormat["np"])
                self.packet.emit(frame)
                stream.stdout.flush()
            except:
                pass


