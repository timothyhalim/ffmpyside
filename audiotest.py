from player.Audio import Speaker
from PySide2.QtWidgets import QApplication

app = QApplication([])
w = Speaker("60.mp4")
w.show()
w.stream.finished.connect(w.start)
app.exec_()

