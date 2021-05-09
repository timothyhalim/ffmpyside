from datetime import datetime, timedelta
from PySide2.QtCore import QTimer

class ElapsedTimer(QTimer):
    def __init__(self, parent=None):
        super(ElapsedTimer, self).__init__(parent=parent)
        self.setInterval(1)
        self.reset()
    
    def increment(self):
        self.elapsed = datetime.now() - self.startTime

    def reset(self):
        self.elapsed = timedelta(seconds=0)
    
    def start(self):
        self.startTime = datetime.now() - self.elapsed
        self.timeout.connect(self.increment)
        return super().start()