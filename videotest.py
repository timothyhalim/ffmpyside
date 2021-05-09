from player.Video import Viewer
from PySide2.QtWidgets import QApplication

app = QApplication([])
w = Viewer("60.mp4")
w.show()
w.stream.finished.connect(w.start)
app.exec_()

