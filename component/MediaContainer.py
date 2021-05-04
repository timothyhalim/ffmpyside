import sys
import os
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QLabel, QVBoxLayout, QWidget

from .FrameWidget import FrameWidget

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

pyVersion = float(f"{sys.version_info[0]}.{sys.version_info[1]}")
vlcdir = os.path.normpath(os.path.join(fileDir, "..", "vlc"))
if not os.path.isdir(vlcdir):
    vlcdir = os.path.normpath(os.path.join(os.getcwd(), "vlc"))

if pyVersion >= 3.8:
    os.add_dll_directory(vlcdir)
else:
    if not vlcdir in sys.path:
        sys.path.append(vlcdir)
    os.environ['PYTHON_VLC_MODULE_PATH'] = vlcdir
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.normpath(os.path.join(vlcdir, "libvlc.dll"))
    os.chdir(vlcdir)
    
import vlc

class MediaContainer(FrameWidget):
    stateChanged = Signal(str)
    lengthChanged = Signal(int)
    timeChanged = Signal(float)
    fpsChanged = Signal(float)

    def __init__(self, parent=None, controller=None):
        super(MediaContainer, self).__init__(parent)

        self.mediaContainer = QLabel()
        self.mediaContainer.setStyleSheet("background:black;")
        self.mediaContainer.setAttribute(Qt.WA_TranslucentBackground, False)
        self.mediaContainer.setObjectName("Video")
        self.vlc = vlc.Instance()
        self.mediaPlayer = self.vlc.media_player_new()
        self.mediaPlayer.set_hwnd(int(self.mediaContainer.winId()))
        self.eventManager = self.mediaPlayer.event_manager()
        self.media = None
        self.setFocusPolicy(Qt.NoFocus)
        self.mediaContainer.setFocusPolicy(Qt.NoFocus)

        self.eventManager.event_attach(vlc.EventType.MediaPlayerNothingSpecial, self._onStateChanged, 'NothingSpecial')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerOpening, self._onStateChanged, 'Opening')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self._onStateChanged, 'Buffering')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self._onStateChanged, 'Playing')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self._onStateChanged, 'Paused')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerStopped, self._onStateChanged, 'Stopped')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEndReached, self._onStateChanged, 'Ended')
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._onStateChanged, 'Error')

        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self._onBuffer)

        self.eventManager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self._onPlayerLengthChanged)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self._onTimeChanged)

        hbox = QVBoxLayout(self)
        hbox.setContentsMargins(self.gripSize,self.gripSize,self.gripSize,self.gripSize)
        hbox.addWidget(self.mediaContainer)
        self.setLayout(hbox)

        
        self._isOnTop = False

        if controller:
            self.setController(controller)

    def setController(self, controller):
        self.controller = controller
        self.controller.setParent(self)
        # self.setFocusProxy(self.controller)

    def show(self):
        super(MediaContainer, self).show()
        if hasattr(self, "controller"):
            self.controller.show()

    def close(self):
        if hasattr(self, "controller"):
            self.controller.close()
        return super(MediaContainer, self).close()

    def resizeEvent(self, event):
        super(MediaContainer, self).resizeEvent(event)
        if hasattr(self, "controller"):
            self.resizeController()

    def onTop(self, state):
        self._isOnTop = state
        self.setWindowFlag(Qt.WindowStaysOnTopHint, state) 

    def isOnTop(self):
        return self._isOnTop

    def resizeController(self):
        self.controller.move(self.pos().x()+(self.gripSize)+1, self.pos().y()+(self.gripSize)+1)
        self.controller.resize(self.width()-(self.gripSize*2)-2, self.height()-(self.gripSize*2)-2)
        self.controller.activateWindow()

    def createMedia(self, mediaPath):
        self.media = self.vlc.media_new(mediaPath)
        self.media.parse()
        self.mediaPlayer.set_media(self.media)

        if self.mediaPlayer.video_get_height() > 0:
            self.setRatio(self.mediaPlayer.video_get_width()/self.mediaPlayer.video_get_height())
        self._onFPSChanged()

        self.metadata = {
            'duration' : self.media.get_duration(),
            'frames' : int(self.media.get_duration()/1000*self.fps)
        }

    def _onFPSChanged(self):
        self.fps = self.mediaPlayer.get_fps()
        self.fpsChanged.emit(self.fps)

    def _onStateChanged(self, event, state):
        self.state = state
        if self.state == "Playing":
            self.media.parse()
            self._onPlayerLengthChanged(None)
        self.stateChanged.emit(state)

    def _onBuffer(self, event):
        ...
        # print(dir(event))
        # print(vars(event))
        # print(event.getBuffering())

    def _onPlayerLengthChanged(self, event):
        self.media = self.mediaPlayer.get_media()
        if self.media:
            self.lengthChanged.emit(self.media.get_duration())

    def _onTimeChanged(self, event):
        self.time = self.getPosition()
        self.timeChanged.emit(min(self.time+(0.03*self.time), 1))
    
    def isPlaying(self):
        return self.mediaPlayer.is_playing()

    def play(self):
        if self.media:
            print("Playing", self.media.get_mrl())
            self.mediaPlayer.play()
        
    def pause(self):
        if self.isPlaying() and self.mediaPlayer.can_pause():
            self.mediaPlayer.pause()

    def setPosition(self, pos):
        if self.mediaPlayer.is_seekable():
            pos = max(min(pos, 1), 0)
            self.mediaPlayer.set_position(pos)

    def getPosition(self):
        return self.mediaPlayer.get_position()

    def setVolume(self, volume):
        self.mediaPlayer.audio_set_volume(volume)

    def stop(self):
        self.mediaPlayer.stop()
