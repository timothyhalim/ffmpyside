from PySide2.QtCore import Property, QPoint
from PySide2.QtWidgets import QApplication, QSlider, QStyleOptionSlider, QToolTip

class TimeSlider(QSlider):
    def __init__(self, *args, maxTime=1, offset=QPoint(-25, -45)):
        super(TimeSlider, self).__init__(*args)
        self.offset = offset

        self.setMaxTime(maxTime)
        self.setFixedHeight(16)
        self.style = QApplication.style()
        self.opt = QStyleOptionSlider()
        self.setMaximum(1000)

        self.valueChanged.connect(self.showTip)
        self.enterEvent = self.showTip
        self.setTipVisibility(True)

        self.setStyleSheet(self.qss())

    def setMaxTime(self, maxTime):
        self.maxTime = maxTime
        
    def setTipVisibility(self, visible):
        self.tipVisible = visible

    def setHeight(self,value): self.setFixedHeight(value)
    def getHeight(self): return self.height()
    Height = Property(int, getHeight, setHeight)

    def showTip(self, _):
        if self.isVisible() and self.tipVisible:
            self.initStyleOption(self.opt)
            rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)

            pos_local = rectHandle.topLeft() + self.offset
            pos_global = self.mapToGlobal(pos_local)
            currentms = self.maxTime * (float(self.value()) / max(self.maximum(), 1))
            currentTime = f"{int(currentms / (1000*60*60)) % 24:02d}:{int(currentms / (1000*60)) % 60:02d}:{(currentms / (1000)) % 60:04.02f} ({self.value()})"
            self.tip = QToolTip.showText(pos_global, currentTime, self)

    def qss(self):
        return """
            QSlider::handle:horizontal, QSlider::handle:vertical {
                background: #FF0000;
                border-color: transparent;
                border-radius: 8px;
                width: 16px;
                height: 16px;
            }
            QSlider::handle:horizontal {
                margin-top: -7px;
                margin-bottom: -7px;
            }
            QSlider::handle:vertical {
                margin-left: -7px;
                margin-right: -7px;
            }

            QSlider::groove:horizontal, QSlider::groove:vertical {
                border-color: transparent;
                background: transparent;
            }
            QSlider::groove:horizontal {
                height: 2px;
            }
            QSlider::groove:vertical {
                background: #aa0000;
                width: 2px;
            }

            QSlider::sub-page:horizontal, QSlider::sub-page:vertical {
                background: #aa0000;
                border-color: transparent;
            }
            QSlider::sub-page:horizontal {
                height: 2px;
            }
            QSlider::sub-page:vertical {
                background: black;
                width: 2px;
                border-radius: 1px;
            }

            QSlider::handle:horizontal:hover, QSlider::handle:vertical:hover {
                background: #FF0000;
                border-color: transparent;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal:disabled, QSlider::sub-page:vertical:disabled {
                background: #bbbbbb;
                border-color: #999999;
            }

            QSlider::add-page:horizontal:disabled, QSlider::add-page:vertical:disabled {
                background: #2a82da;
                border-color: #999999;
            }

            QSlider::handle:horizontal:disabled, QSlider::handle:horizontal:disabled {
            background: #2a82da;
            }
            """