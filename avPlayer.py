
from PySide2.QtCore import QAbstractAnimation, QEvent, QPoint, QPropertyAnimation, QTimer, Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QAction, QApplication, QFileDialog, QGraphicsOpacityEffect, QHBoxLayout, QMenu, QPushButton, QSlider, QVBoxLayout, QWidget

import os
from datetime import datetime, timedelta

from component.AudioContainer import Sound
from component.VideoContainer import VideoContainer
from component.ButtonIcon import ButtonIcon
from component.TimeSlider import TimeSlider

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

class MediaPlayer(VideoContainer):
    def __init__(self, file, bit=24, trim=None, parent=None):
        super(MediaPlayer, self).__init__(parent=parent)
        
        self.resourcePath = os.path.normpath(os.path.join(fileDir, "resource")).replace("\\", "/")

        self.audio = Sound(file, trim, self)
        for w in [self.audio]:
            w.setFocusProxy(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        
        self.onTop = False
        self.visible = False
        self.isPaused = False
        self.lastMove = datetime.now()

        self.setupWidget()
        self.setupRightClick()
        self.setupSignal()
        
        self.setStream(file, bit)

    def setupWidget(self):
        # Top
        self.pinBtn = ButtonIcon(icon=f"{self.resourcePath}/pin.svg", iconsize=15)
        self.pinBtn.setCheckable(True)
        self.closeBtn = ButtonIcon(icon=f"{self.resourcePath}/cancel.svg", iconsize=15)
        self.topLayout = QHBoxLayout()
        self.topLayout.setContentsMargins(5,5,5,5)
        self.topLayout.addWidget(self.pinBtn)
        self.topLayout.addStretch()
        self.topLayout.addWidget(self.closeBtn)

        # Middle
        self.playBtn = ButtonIcon(icon=f"{self.resourcePath}/play.svg", iconsize=100)
        self.volumeSlider = QSlider(Qt.Vertical, self)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(100)
        self.volumeBtn = ButtonIcon(icon=f"{self.resourcePath}/speaker.svg", iconsize=15)
        self.volumeLayout = QVBoxLayout()
        self.volumeLayout.setContentsMargins(0,0,0,0)
        for w in (self.volumeSlider, self.volumeBtn):
            self.volumeLayout.addWidget(w)
        
        self.playLayout = QHBoxLayout()
        self.playLayout.addStretch()
        self.playLayout.addWidget(self.playBtn)
        self.playLayout.addStretch()
        self.playLayout.addLayout(self.volumeLayout)

        # Bottom
        self.addBtn = ButtonIcon(icon=f"{self.resourcePath}/plus.svg", iconsize=15)
        self.timeSlider = TimeSlider(Qt.Horizontal, self)
        self.volumeSlider.setStyleSheet(self.timeSlider.qss())
        self.repeatBtn = ButtonIcon(icon=f"{self.resourcePath}/replay.svg", iconsize=15)
        self.listBtn = ButtonIcon(icon=f"{self.resourcePath}/list.svg", iconsize=15)
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setContentsMargins(0,0,0,0)
        self.bottomLayout.addWidget(self.addBtn)
        self.bottomLayout.addWidget(self.listBtn)
        self.bottomLayout.addWidget(self.timeSlider)
        self.bottomLayout.addWidget(self.repeatBtn)
        
        self.layout().addLayout(self.topLayout)
        self.layout().addStretch()
        self.layout().addLayout(self.playLayout)
        self.layout().addStretch()
        self.layout().addLayout(self.bottomLayout)

        self.visibilityTimer = QTimer()
        self.visibilityTimer.setInterval(50)
        self.visibilityTimer.timeout.connect(self.toggleCursor)
        self.visibilityTimer.start()

        self.opacFX = []
        for w in (self.pinBtn, self.closeBtn, self.playBtn, self.volumeSlider, self.volumeBtn, self.addBtn, self.repeatBtn, self.listBtn):
            w.setFocusProxy(self)
            fx = QGraphicsOpacityEffect(w)
            fx.setOpacity(0)
            w.setGraphicsEffect(fx)
            self.opacFX.append(fx)
        
        for w in self.cornerGrips:
            w.setFocusProxy(self)
            fx = QGraphicsOpacityEffect(w)
            fx.setOpacity(0)
            w.setGraphicsEffect(fx)
            self.opacFX.append(fx)

        self.timeSlider.setHeight(1)
        self.timeSlider.setFocusProxy(self)

    def setupRightClick(self):
        self.popMenu = QMenu(self)
        self.openAct = QAction('Open File', self)
        self.fullAct = QAction('Fullscreen', self)
        self.atopAct = QAction('Pin on Top', self)
        self.listAct = QAction('Playlist', self)
        self.helpAct = QAction('Help', self)
        self.exitAct = QAction('Exit', self)

        for act in (self.openAct, self.fullAct, self.listAct, self.helpAct):
            self.popMenu.addAction(act)
        self.popMenu.addSeparator()
        self.popMenu.addAction(self.exitAct)

        # Initial 
        self.fullAct.setCheckable(True)
        self.listAct.setCheckable(True)

        # Temp
        self.listAct.setDisabled(True)
        self.helpAct.setDisabled(True)

    def setupSignal(self):
        # Controller 
        self.closeBtn.clicked.connect(self.close)
        self.playBtn.clicked.connect(self.togglePlay)
        self.volumeSlider.valueChanged.connect(self.setVolume)
        self.addBtn.clicked.connect(self.openFile)
        self.timeSlider.sliderMoved.connect(self.seek)
        self.pinBtn.clicked.connect(self.toggleOnTop)

        # Player
        self.stateChanged.connect(self.onStateChanged)
        self.frameCountChanged.connect(self.onFrameCountChanged)
        self.frameChanged.connect(self.onFrameChanged)

        # Right click
        self.openAct.triggered.connect(self.openFile)
        self.fullAct.triggered.connect(self.toggleFullscreen)
        self.exitAct.triggered.connect(self.close)

    def event(self, event):
        if event.type() == QEvent.Type.Enter:
            self.lastMove = datetime.now()
            self.toggleVisibility(True)
        elif event.type() == QEvent.Type.Leave:
            self.lastMove = datetime.now() - timedelta(seconds=5)
            self.toggleVisibility(False)
        return super(MediaPlayer, self).event(event)

    def mousePressEvent(self, event):
        self.lastButton = event.button()
        if event.button() == Qt.MouseButton.LeftButton:
            self.lastClick = datetime.now()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.startFrame = self.timeSlider.value()
            self.startPos = event.pos()

        super(MediaPlayer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "startPos"):
                if (datetime.now() - self.lastClick).microseconds/1000 < 300:
                    self.start()

        elif event.button() == Qt.MouseButton.RightButton:
            self.onRightClick(event.pos())
            
        elif self.lastButton == Qt.MouseButton.MiddleButton:
            if hasattr(self, "startPos"): delattr(self, "startPos")
            if hasattr(self, "startFrame"): delattr(self, "startFrame")

        super(MediaPlayer, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.lastMove = datetime.now()
        self.toggleVisibility(True)
        if self.lastButton == Qt.MouseButton.MiddleButton:
            if hasattr(self, "startFrame"):
                self.pause()
                
                delta = event.pos()-self.startPos
                percent = delta.x()/self.width()
                
                m = self.timeSlider.maximum()
                final = int(self.startFrame+(percent*m))
                
                self.timeSlider.setValue(final)
                self.seek()

        super(MediaPlayer, self).mouseMoveEvent(event)

    def wheelEvent(self, event):
        increment = int(self.volumeSlider.maximum() / 10)
        if (event.angleDelta().y()) > 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()+increment)
        elif (event.angleDelta().y()) < 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()-increment)
        return super(MediaPlayer, self).wheelEvent(event)

    def dropEvent(self, event):
        self.drawDrag = False
        self.update()
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            self.createMedia(url)
            self.play()
        elif event.mimeData().hasText():
            url =  event.mimeData().text()
            if os.path.isfile(url):
                self.createMedia(url)
                self.play()
    
    def keyPressEvent(self, event):
        self.lastMove = datetime.now()
        self.toggleVisibility(True)
        if event.key() in [Qt.Key_Left, Qt.Key_A, Qt.Key_Less, Qt.Key_Comma]:
            self.pause()
            self.timeSlider.setValue(self.timeSlider.value()-1)
            self.seek()
        elif event.key() in [Qt.Key_Right, Qt.Key_D, Qt.Key_Greater, Qt.Key_Period]:
            self.pause()
            self.timeSlider.setValue(self.timeSlider.value()+1)
            self.seek()
        elif event.key() in [Qt.Key_Up, Qt.Key_Plus]:
            self.volumeSlider.setValue(self.volumeSlider.value()+5)
        elif event.key() in [Qt.Key_Down, Qt.Key_Minus]:
            self.volumeSlider.setValue(self.volumeSlider.value()-5)
        elif event.key() in [Qt.Key_Space]:
            self.start()
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_O]:
            self.openFile()
        elif event.key() in [Qt.Key_F11, Qt.Key_F]:
            self.toggleFullscreen()
        elif event.key() in [Qt.Key_Tab, Qt.Key_L]:
            print("Open Playlist")
        elif event.key() in [Qt.Key_Slash, Qt.Key_Question]:
            print("Open Help")
        elif event.key() in [Qt.Key_Menu]:
            self.onRightClick(QPoint(0,0))
        elif event.key() in [Qt.Key_Escape]:
            self.close()
        elif QKeySequence(event.key()+int(event.modifiers())) == QKeySequence("Ctrl+V"):
            url = QApplication.clipboard().text()
            self.createMedia(url)
            self.play()

        return super(MediaPlayer, self).keyPressEvent(event)

    def opacityAnimation(self, end, duration, callback):
        anims = []
        for fx in self.opacFX:
            ani = QPropertyAnimation(fx, b"opacity")
            ani.setStartValue(fx.opacity())
            ani.setEndValue(end)
            a = max(fx.opacity(), end)
            i = min(fx.opacity(), end)
            ani.setDuration((a-i)*duration)
            ani.stateChanged.connect(callback)
            anims.append(ani)
        return anims

    def heightAnimation(self, target, height, duration, callback):
        ani = QPropertyAnimation(target, b"Height")
        ani.setStartValue(target.getHeight())
        ani.setEndValue(height)
        a = max(target.getHeight(), height)
        i = min(target.getHeight(), height)
        ani.setDuration((a-i)/a*duration)
        return ani

    def toggleWidget(self, state):
        if (self.sender().endValue() > 0 and state == QAbstractAnimation.State.Running) :
            self.sender().targetObject().parent().show()
        elif (self.sender().endValue() <= 0 and state == QAbstractAnimation.State.Stopped) :
            self.sender().targetObject().parent().hide()

    def toggleVisibility(self, visible=True):
        if self.visible == visible:
            return
        self.visible = visible
        if visible:
            self.setCursor(Qt.ArrowCursor)
            
        self.move(self.pos().x(), self.pos().y())

        self.anims = self.opacityAnimation(1 if visible else 0, 300, self.toggleWidget)
        self.anims += [self.heightAnimation(w, 20 if visible else 1, 300, self.toggleWidget) for w in (self.addBtn, self.timeSlider, self.listBtn, self.repeatBtn)]
        for a in self.anims:
            a.start()

        self.timeSlider.setTipVisibility(visible)

    def toggleOnTop(self):
        self.onTop = not self.onTop
        print("On Top", self.onTop)
        # self.setWindowFlag(Qt.WindowStaysOnBottomHint,self.onTop) 
        # self.update()

    def toggleCursor(self):
        if (datetime.now() - self.lastMove).seconds >= 5 :
            self.setCursor(Qt.BlankCursor)
            self.toggleVisibility(False)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.toggleVisibility(True)

    def togglePlay(self, event=None):
        print(self.state)
        if self.state in ["Idle", "Stopped", "Paused", "Buffering"]:
            self.start()
            self.audio.start()
        elif self.state == "Playing":
            self.pause()
            self.audio.pause()

    def onFrameCountChanged(self, frames):
        # self.timeSlider.setMaxTime(frames)
        self.timeSlider.setMaximum(frames)
        self.audio.setFrameCount(frames)

    def onFrameChanged(self, frame):
        self.timeSlider.setValue(frame)

    def onStateChanged(self, state):
        if state == 'NothingSpecial':
            return
        elif state == 'Opening':
            return
        elif state == 'Buffering':
            return
        elif state == 'Playing':
            self.playBtn.changeIcon(f"{self.resourcePath}/pause.svg")
        elif state == 'Paused':
            self.playBtn.changeIcon(f"{self.resourcePath}/play.svg")
        elif state == 'Stopped':
            self.playBtn.changeIcon(f"{self.resourcePath}/replay.svg")
            mediaPath = self.media.get_mrl()
            self.createMedia(mediaPath)
            self.pause()
            self.slide(.99)
            
        elif state == 'Ended':
            self.timeSlider.setValue(self.timeSlider.maximum())
        elif state == 'Error':
            return

    def onRightClick(self, point):
        self.fullAct.setChecked(self.isFullScreen())
        self.popMenu.exec_(self.mapToGlobal(point))   

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie", fileDir, "All (*.*)")
        if fileName != '':
            self.createMedia(fileName)
            self.play()
    
    def setVolume(self):
        normalize = self.volumeSlider.value() / self.volumeSlider.maximum()
        self.audio.setVolume(normalize)
        
    def seek(self, frame=None):
        if frame is None: frame = self.timeSlider.value()
        self.setFrame(frame)
        self.audio.seek(frame)

app = QApplication([])
w = MediaPlayer("60.mp4")
w.show()
app.exec_()