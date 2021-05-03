
from audioPlayer import Sound
from videoPlayer import Image

from PySide2.QtWidgets import QApplication, QPushButton, QWidget

class MediaPlayer(QWidget):
    def __init__(self, file, bit, trim, parent=None):
        super(MediaPlayer, self).__init__(parent=parent)
        
        self.audio = Sound(file, trim, self)
        self.video = Image(file, bit, trim, self)

        self.btn = QPushButton(self)
        self.btn.clicked.connect(self.start)

    def start(self):
        self.audio.start()
        self.video.start()

    def stop(self):
        self.audio.stop()
        self.video.stop()

    def show(self):
        return super().show()

app = QApplication([])
w = MediaPlayer("60.mp4", 24, 500)
w.show()
app.exec_()