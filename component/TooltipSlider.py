from PySide2.QtCore import Property, QPoint, Qt
from PySide2.QtWidgets import QApplication, QSlider, QStyleOptionSlider, QToolTip

import os

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

class TooltipSlider(QSlider):
    def __init__(self, *args, orientation=Qt.Horizontal, maxTime=1, offset=QPoint(-25, -45)):
        super(TooltipSlider, self).__init__(*args)

        self.resourcePath = os.path.normpath(os.path.join(fileDir, "icons")).replace("\\", "/")

        self.hover = False
        self.offset = offset
        
        self.style = QApplication.style()
        self.opt = QStyleOptionSlider()

        self.setMaxTime(maxTime)
        self.setMaximum(1000)
        self.setTipVisibility(True)
        self.setOrientation(orientation)
        self.setSize(16)
        self.setStyleSheet(self.qss())
        self.toolTipForm = 'f"{int(percentage / (1000*60*60)) % 24:02d}:{int(percentage / (1000*60)) % 60:02d}:{(percentage / (1000)) % 60:04.02f} ({self.value()})"'
        
        self.valueChanged.connect(self.showTip)

    def setMaxTime(self, maxTime):
        self.maxTime = maxTime
        
    def setTipVisibility(self, visible):
        self.tipVisible = visible

    def setSize(self, value):
        if self.orientation == Qt.Horizontal:
            self.setHeight(value)
        else:
            self.setWidth(value)

    def getSize(self):
        if self.orientation == Qt.Horizontal:
            self.getHeight()
        else:
            self.getWidth()

    def setHeight(self,value): self.setFixedHeight(value)
    def getHeight(self): return self.height()
    Height = Property(int, getHeight, setHeight)

    def setWidth(self,value): self.setFixedWidth(value)
    def getWidth(self): return self.width()
    Width = Property(int, getWidth, setWidth)

    def setOrientation(self, orientation=Qt.Horizontal):
        return super().setOrientation(orientation)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.hover = True
        self.showTip(True)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.hover = False

    def showTip(self, _):
        if self.isVisible() and self.tipVisible and self.hover:
            self.initStyleOption(self.opt)
            rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)

            posLocal = rectHandle.topLeft() + self.offset
            posGlobal = self.mapToGlobal(posLocal)
            percentage = self.maxTime * (float(self.value()) / max(self.maximum(), 1))
            tooltipFormat = eval(self.toolTipForm)
            self.tip = QToolTip.showText(posGlobal, tooltipFormat, self)

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