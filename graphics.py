"""Painter-only artwork; no simulation or filesystem side effects."""
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QPainterPath, QRadialGradient

def silk(painter, start, end, alpha=85):
    path = QPainterPath(QPointF(start['x'], start['y']))
    dx, dy = end['x']-start['x'], end['y']-start['y']
    sag = min(22, math.hypot(dx,dy)*0.055)
    path.quadTo(QPointF((start['x']+end['x'])/2, (start['y']+end['y'])/2+sag), QPointF(end['x'],end['y']))
    painter.setPen(QPen(QColor(211,201,229,alpha),0.85))
    painter.drawPath(path)

def draw_webs(self, painter):
    if not self.settings.web_visible:
        return
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for edge in self.web_edges:
        silk(painter, edge['start'], edge['end'])
    if self.last_anchor is not None and self.current_icon is not None and self.last_anchor is not self.current_icon and not self.scared_frames:
        silk(painter,self.last_anchor,{'x':self.x,'y':self.y},55)
    painter.restore()

def draw_home(self, painter):
    if self.home_icon is None or not self.settings.web_visible:
        return
    painter.save()
    painter.translate(self.home_icon['x'],self.home_icon['y'])
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for ring in range(5):
        path = QPainterPath()
        for i in range(49):
            a = i*math.tau/48
            radius = 14 + ring*3.7 + math.sin(a*5+ring)*1.2
            point = QPointF(math.cos(a)*radius,math.sin(a)*radius*0.78)
            if i == 0: path.moveTo(point)
            else: path.lineTo(point)
        painter.setPen(QPen(QColor(199,181,226,55+ring*9),0.7))
        painter.drawPath(path)
    for i in range(9):
        a = i*math.tau/9
        painter.drawLine(QPointF(math.cos(a)*11,math.sin(a)*9),QPointF(math.cos(a)*31,math.sin(a)*24))
    if self.sleeping:
        gradient = QRadialGradient(0,0,26)
        gradient.setColorAt(0,QColor(176,151,211,40))
        gradient.setColorAt(1,QColor(176,151,211,0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QRectF(-28,-24,56,48))
    painter.restore()

def draw_spider(self, painter):
    painter.save()
    painter.translate(self.x,self.y)
    level = self.progression.level
    size = 0.85+(level-1)*0.05 if level<5 else 1.10+(level-5)*0.07 if level<10 else 1.50+min(level-10,10)*0.04
    painter.scale(size,size)
    painter.rotate(self.heading+90)
    moving = not self.sleeping and not self.rest_frames
    phase = self.animation
    painter.setBrush(Qt.BrushStyle.NoBrush)
    pen = QPen(QColor('#766780') if not self.scared_frames else QColor('#aa8dc4'),2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    for side in (-1,1):
        for i in range(4):
            wave = math.sin(phase+i*1.8+side)*2.5 if moving else 0
            path = QPainterPath(QPointF(side*6,-5+i*3))
            path.quadTo(QPointF(side*(15+i),-15+i*8+wave),QPointF(side*(22-abs(i-1)*2),-17+i*11+wave))
            painter.drawPath(path)
    painter.setPen(QPen(QColor('#aa91bb'),0.7))
    gradient = QRadialGradient(-4,3,18)
    gradient.setColorAt(0,QColor('#72607e'))
    gradient.setColorAt(1,QColor('#322e3c'))
    painter.setBrush(gradient)
    painter.drawEllipse(QRectF(-11,-1,22,24))
    painter.setBrush(QColor('#51465e'))
    painter.drawEllipse(QRectF(-9,-12,18,17))
    painter.setPen(Qt.PenStyle.NoPen)
    for x in (-4.3,4.3):
        if self.sleeping:
            painter.setPen(QPen(QColor('#ded5e7'),1.4))
            painter.drawLine(QPointF(x-2,-5),QPointF(x+2,-5))
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            painter.setBrush(QColor('#f0e9f5'))
            painter.drawEllipse(QRectF(x-3,-8,6,7))
            painter.setBrush(QColor('#292333'))
            painter.drawEllipse(QRectF(x-1.5,-7,3,4))
            painter.setBrush(QColor('#ffffff'))
            painter.drawEllipse(QRectF(x-0.7,-7,1.4,1.4))
    painter.setBrush(QColor(207,153,178,110))
    painter.drawEllipse(QRectF(-8,-2,4,2))
    painter.drawEllipse(QRectF(4,-2,4,2))
    painter.restore()
