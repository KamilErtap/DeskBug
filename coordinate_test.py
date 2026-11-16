
import sys
import ctypes

from ctypes import wintypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]

app = QApplication(sys.argv)

screen = app.primaryScreen()
print("Ekran boyutu:", screen.geometry())
print("Olceklendirme:", screen.devicePixelRatio())

print("\nMouse'u masaustundeki bir ikonun")
print("ORTASINA getirip Enter'a bas.")
input()

qt_pos = QCursor.pos()

win_pos = POINT()
ctypes.windll.user32.GetCursorPos(
    ctypes.byref(win_pos)
)

print("\n--- KOORDINAT TESTI ---")
print("PySide6 X:", qt_pos.x())
print("PySide6 Y:", qt_pos.y())
print("Windows X:", win_pos.x)
print("Windows Y:", win_pos.y)
print("----------------------")
