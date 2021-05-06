from PySide2.QtCore import QPoint, QRect, QSize,Qt
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import QSizeGrip, QWidget

class SideGrip(QWidget):
    def __init__(self, parent, edge):
        QWidget.__init__(self, parent)
        if edge == Qt.LeftEdge:
            self.setCursor(Qt.SizeHorCursor)
            self.resizeFunc = self.resizeLeft
        elif edge == Qt.TopEdge:
            self.setCursor(Qt.SizeVerCursor)
            self.resizeFunc = self.resizeTop
        elif edge == Qt.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
            self.resizeFunc = self.resizeRight
        else:
            self.setCursor(Qt.SizeVerCursor)
            self.resizeFunc = self.resizeBottom
        self.mousePos = None

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width)
        window.setGeometry(geo)

    def resizeTop(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() - delta.y())
        geo = window.geometry()
        geo.setTop(geo.bottom() - height)
        window.setGeometry(geo)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() + delta.x())
        window.resize(width, window.height())

    def resizeBottom(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() + delta.y())
        window.resize(window.width(), height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            self.resizeFunc(delta)

    def mouseReleaseEvent(self, event):
        self.mousePos = None

class FrameWidget(QWidget):
    def __init__(self, parent=None):
        super(FrameWidget, self).__init__(parent)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)

        self._gripSize = 1
        self.initialGrip = self._gripSize
        self.sideGrips = [
            SideGrip(self, Qt.LeftEdge), 
            SideGrip(self, Qt.TopEdge), 
            SideGrip(self, Qt.RightEdge), 
            SideGrip(self, Qt.BottomEdge), 
        ]
        self.cornerGrips = [QSizeGrip(self) for i in range(4)]

        self.drawDrag = False
        self.lastButton = Qt.MouseButton.NoButton
        self.setRatio(1280/720)

    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = size
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.gripSize, self.gripSize,
            -self.gripSize, -self.gripSize)

        corner = 10

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top()+corner, self.gripSize, inRect.height()-corner)
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left()+corner, 0, inRect.width()-corner, self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(), 
            inRect.top()+corner, self.gripSize, inRect.height()-corner)
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize+corner, inRect.top() + inRect.height(), 
            inRect.width()-corner, self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QRect(outRect.topLeft(), inRect.topLeft()+QPoint(corner,corner)))
        # top right
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()+QPoint(-corner,corner)).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QRect(outRect.bottomRight(), inRect.bottomRight()+QPoint(-corner,-corner)).normalized())
        # bottom left
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()+QPoint(corner,-corner)).normalized())

    def setRatio(self, ratio=None):
        if ratio:
            self.ratio = ratio
        newSize = self.keepRatio(self.size())
        if newSize:
            self.resize(self.keepRatio(self.size()))

    def keepRatio(self, size):
        newHeight = size.width()/self.ratio
        newHeight -= newHeight%1
        newHeight += 1
        if self.height() == newHeight:
            return
        return QSize(size.width(), newHeight)

    def resizeEvent(self, event):
        if event.size() == event.oldSize():
            return
        else:
            newSize = self.keepRatio(event.size())
            if newSize:
                self.resize(newSize)
        
        self.updateGrips()

    def mousePressEvent(self, event):
        self.lastButton = event.button()
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.pos()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "startPos"): delattr(self, "startPos")

    def mouseMoveEvent(self, event):
        if self.lastButton == Qt.MouseButton.LeftButton:
            if not self.isFullScreen():
                if hasattr(self, "startPos"):
                    delta = event.pos()-self.startPos
                    self.move(self.pos()+delta)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggleFullscreen()

    def dragEnterEvent(self, event):
        self.drawDrag = True
        self.update()
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        self.drawDrag = False
        self.update()

    def dropEvent(self, event):
        self.drawDrag = False
        self.update()

    def paintEvent(self, event):
        if self.drawDrag:
            s = self.size()
            qp = QPainter()
            qp.begin(self)
            qp.setRenderHint(QPainter.Antialiasing, True)

            pen = QPen(Qt.white, 5)
            pen.setCapStyle(Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(Qt.transparent)

            outerWidth = s.width()-60
            outerHeight = s.height()-60

            ow = int(s.width()/2-outerWidth/2)
            oh = int(s.height()/2-outerHeight/2)
            qp.drawRoundedRect(ow, oh, outerWidth, outerHeight, 5, 5)
            
            qp.setBrush(Qt.white)
            thickness = 12
            length = 50
            roundness = thickness/2

            vS = int(s.width()/2-thickness/2)
            vE = int(s.height()/2-length/2)
            qp.drawRoundedRect(vS, vE, thickness, length, roundness, roundness)
            hS = int(s.width()/2-length/2)
            hE = int(s.height()/2-thickness/2)
            qp.drawRoundedRect(hS, hE, length, thickness, roundness, roundness)

            qp.end()

    def showNormal(self):
        self.setGripSize(self.initialGrip)
        self.update()
        return super(FrameWidget, self).showNormal()

    def showFullScreen(self) -> None:
        self.initialGrip = self.gripSize
        self.setGripSize(0)
        self.update()
        return super(FrameWidget, self).showFullScreen()

    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
