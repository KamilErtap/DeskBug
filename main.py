
import sys
import math
import random
import signal
import ctypes
import json
from pathlib import Path
import os

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QCursor

from desktop_icons import get_desktop_icons
from pet_panel import setup_pet_tray
from progression import Progression


DEBUG_TARGETS = False


class Spider(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())

        self.x = self.width() / 2
        self.y = self.height() / 2

        self.target_x = self.x
        self.target_y = self.y

        self.speed = 2.2
        self.animation = 0

        self.rest_frames = 0
        self.scared_frames = 0

        # Masaustu ikonlari
        self.desktop_icons = []
        self.current_icon = None

        # Orumcek agi
        self.last_anchor = None
        self.web_edges = []
        self.max_web_edges = 25

        # Gelisim sistemi
        self.progression = Progression()
    
        self.load_icons()

        self.home_icon = None
        self.sleeping = False
        self.sleep_frames = 0

        # Kayitli yuvayi yukle
        self.load_home()

        self.choose_target()


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spider)
        self.timer.start(30)

    
    def load_home(self):
        save_folder = Path(
            os.getenv("LOCALAPPDATA") or Path.home()
        ) / "DeskBug"

        self.home_file = save_folder / "home.json"

        saved_name = None

        # Daha once secilen yuvayi oku
        if self.home_file.exists():
            try:
                data = json.loads(
                    self.home_file.read_text(
                        encoding="utf-8"
                    )
                )
                saved_name = data.get("home_name")
            except (OSError, ValueError) as error:
                print("Yuva kaydi okunamadi:", error)

        # Kayitli ikonu bul
        self.home_icon = None

        if saved_name is not None:
            for icon in self.desktop_icons:
                if icon["name"] == saved_name:
                    self.home_icon = icon
                    break

        # Kayitli yuva yoksa yeni bir tane sec
        if self.home_icon is None and self.desktop_icons:
            self.home_icon = random.choice(
                self.desktop_icons
            )

        # Secimi kaydet
        if self.home_icon is not None:
            try:
                save_folder.mkdir(
                    parents=True,
                    exist_ok=True
                )

                self.home_file.write_text(
                    json.dumps(
                        {
                            "home_name":
                                self.home_icon["name"]
                        },
                        indent=4,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                print(
                    "Webby'nin yuvasi:",
                    self.home_icon["name"]
                )

            except OSError as error:
                print("Yuva kaydedilemedi:", error)


    def load_icons(self):
        try:
            raw_icons = get_desktop_icons()
        except Exception as error:
            print("Ikon okuma hatasi:", error)
            raw_icons = []

        self.desktop_icons = []

        scale = QApplication.primaryScreen().devicePixelRatio()

        for icon in raw_icons:
            # Test ettigimiz %125 ekran duzeltmesi
            x = icon["x"] / scale - self.geometry().x()
            y = icon["y"] / scale - self.geometry().y()

            if 0 <= x < self.width() and 0 <= y < self.height():
                self.desktop_icons.append({
                    "name": icon["name"],
                    "x": x,
                    "y": y
                })

        print(
            f"{len(self.desktop_icons)} ikon bulundu."
        )

    def choose_target(self):
        if self.desktop_icons:
            candidates = [
                icon for icon in self.desktop_icons
                if icon is not self.last_anchor
            ]

            if not candidates:
                candidates = self.desktop_icons

            self.current_icon = random.choice(candidates)

            self.target_x = self.current_icon["x"]
            self.target_y = self.current_icon["y"]

            print("Yeni hedef:", self.current_icon["name"])

        else:
            self.current_icon = None
            margin = 35

            self.target_x = random.uniform(
                margin,
                max(margin, self.width() - margin)
            )

            self.target_y = random.uniform(
                margin,
                max(margin, self.height() - margin)
            )

    def connect_web(self, icon):
        # Ilk ikon agin baslangic noktasi
        if self.last_anchor is None:
            self.last_anchor = icon
            print("Ilk ag noktasi:", icon["name"])
            return

        if self.last_anchor is icon:
            return

        start = self.last_anchor
        end = icon

        # Ayni iki ikon arasina tekrar ag kurma
        edge_key = frozenset(
            (id(start), id(end))
        )

        for edge in self.web_edges:
            if edge["key"] == edge_key:
                self.last_anchor = icon
                return

        self.web_edges.append({
            "start": start,
            "end": end,
            "key": edge_key
        })

        if len(self.web_edges) > self.max_web_edges:
            self.web_edges.pop(0)

        print(
            "AG ORULDU:",
            start["name"],
            "->",
            end["name"]
        )

        self.last_anchor = icon

        # Yeni ag baglantisi = 10 XP
        leveled_up = self.progression.add_xp(10)

        print(
            f"XP: {self.progression.xp}/"
            f"{self.progression.required_xp()} | "
            f"Seviye: {self.progression.level}"
        )

        if leveled_up and hasattr(self, "pet_panel"):
            self.pet_panel.message.setText(
                f"Webby seviye {self.progression.level} oldu!"
            )

    
    def get_pet_stats(self):
        # Panel bagli degilse varsayilan degerler
        if not hasattr(self, "pet_panel"):
            return 85, 75, 90

        return (
            self.pet_panel.food,
            self.pet_panel.energy,
            self.pet_panel.happiness
        )

    
    def update_sleep(self):
        if not self.sleeping:
            return False

        self.sleep_frames += 1

        # Yaklasik 3 saniyede bir enerji kazan
        if self.sleep_frames >= 100:
            self.sleep_frames = 0

            if hasattr(self, "pet_panel"):
                panel = self.pet_panel

                panel.energy = min(
                    100, panel.energy + 5
                )

                panel.update_bars()

                panel.message.setText(
                    "Webby yuvasinda uyuyor..."
                )

                # Enerjisi dolunca uyan
                if panel.energy >= 60:
                    self.sleeping = False

                    panel.message.setText(
                        "Webby uyandi!"
                    )

                    self.choose_target()

        self.update()
        return True



    def update_spider(self):


        # Webby uyuyorsa hareket etmesin
        if self.update_sleep():
            return

        # Enerji azsa yuvasina donsun
        food, energy, happiness = self.get_pet_stats()

        if energy <= 20 and self.home_icon is not None:
            self.current_icon = self.home_icon
            self.target_x = self.home_icon["x"]
            self.target_y = self.home_icon["y"]
            self.rest_frames = 0

            # Yuvaya ulasti mi?
            home_distance = math.hypot(
                self.x - self.target_x,
                self.y - self.target_y
            )

            if home_distance < 4:
                self.x = self.target_x
                self.y = self.target_y

                self.sleeping = True
                self.sleep_frames = 0

                if hasattr(self, "pet_panel"):
                    self.pet_panel.message.setText(
                        "Webby yuvasinda uykuya daldi!"
                    )

                self.update()
                return


        mouse = self.mapFromGlobal(QCursor.pos())

        dx_mouse = self.x - mouse.x()
        dy_mouse = self.y - mouse.y()

        mouse_distance = math.hypot(
            dx_mouse, dy_mouse
        )

        # Fare cok yakindaysa kac
        if 0 < mouse_distance < 100:
            self.scared_frames = 35
            self.rest_frames = 0

        if self.scared_frames > 0:
            self.scared_frames -= 1

            # Fareden uzaklasma yonu
            if mouse_distance > 0.01:
                vx = dx_mouse / mouse_distance
                vy = dy_mouse / mouse_distance
            else:
                vx, vy = 1, 0

            self.x = max(
                20,
                min(self.width() - 20, self.x + vx * 5)
            )

            self.y = max(
                20,
                min(self.height() - 20, self.y + vy * 5)
            )

            self.animation += 0.3
            self.update()
            return

        if self.rest_frames > 0:
            self.rest_frames -= 1
            self.update()
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y

        distance = math.hypot(dx, dy)

        
        if distance < 4:
            self.x = self.target_x
            self.y = self.target_y

            food, energy, happiness = self.get_pet_stats()

            # Mutluysa daha fazla ag orer
            web_chance = 0.25 + happiness * 0.007

            if self.current_icon is not None:
                if random.random() < web_chance:
                    self.connect_web(self.current_icon)

            # Enerjisi dustukce daha cok dinlenir
            rest_chance = 0.15 + (100 - energy) * 0.007

            if random.random() < rest_chance:
                self.rest_frames = random.randint(
                    30, 130
                )

            self.choose_target()
        
        else:
            food, energy, happiness = self.get_pet_stats()

            # Tokluk ve enerji hareketi etkiler
            food_factor = 0.55 + food / 200
            energy_factor = 0.55 + energy / 200

            current_speed = self.speed * food_factor * energy_factor

            # Tamamen hareketsiz kalmasin
            current_speed = max(0.45, current_speed)

            step = min(current_speed, distance)

            self.x += dx / distance * step
            self.y += dy / distance * step

            self.animation += 0.22


        self.update()

    def draw_webs(self, painter):
        painter.save()

        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Tamamlanmis ag baglantilari
        painter.setPen(
            QPen(QColor(160, 205, 240, 170), 1.5)
        )

        for edge in self.web_edges:
            start = edge["start"]
            end = edge["end"]

            painter.drawLine(
                int(start["x"]),
                int(start["y"]),
                int(end["x"]),
                int(end["y"])
            )

        # Orumcek yururken iplik cekiyor
        if (
            self.last_anchor is not None
            and self.current_icon is not None
            and self.last_anchor is not self.current_icon
            and self.scared_frames == 0
        ):
            painter.setPen(
                QPen(QColor(190, 220, 255, 130), 1)
            )

            painter.drawLine(
                int(self.last_anchor["x"]),
                int(self.last_anchor["y"]),
                int(self.x),
                int(self.y)
            )

        painter.restore()

    def draw_targets(self, painter):
        if not DEBUG_TARGETS:
            return

        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 220, 100, 130))

        for icon in self.desktop_icons:
            painter.drawEllipse(
                int(icon["x"]) - 5,
                int(icon["y"]) - 5,
                10, 10
            )

        painter.restore()

    
    def draw_home(self, painter):
        if self.home_icon is None:
            return

        painter.save()

        x = self.home_icon["x"]
        y = self.home_icon["y"]

        painter.translate(x, y)

        # Kozanin dis halkasi
        painter.setPen(
            QPen(QColor(183, 156, 255, 120), 1.5)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawEllipse(-30, -25, 60, 50)
        painter.drawEllipse(-24, -20, 48, 40)

        # Ipek iplikleri
        painter.setPen(
            QPen(QColor(190, 205, 255, 100), 1)
        )

        for i in range(8):
            angle = (2 * math.pi * i) / 8

            outer_x = math.cos(angle) * 30
            outer_y = math.sin(angle) * 25

            painter.drawLine(
                0, 0,
                int(outer_x),
                int(outer_y)
            )

        # Uyurken koza hafif parlar
        if self.sleeping:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(160, 120, 255, 40)
            )
            painter.drawEllipse(-23, -19, 46, 38)

        painter.restore()


    def draw_spider(self, painter):
        painter.save()


        if self.sleeping:
            painter.setPen(
                QPen(QColor("#B79CFF"), 2)
            )

            painter.drawText(
                int(self.x + 17),
                int(self.y - 25),
                "Zzz"
            )


        bob = math.sin(self.animation) * 2
        painter.translate(self.x, self.y + bob)


        # Seviyeye gore fiziksel buyume
        level = self.progression.level

        if level < 5:
            # Yavru
            size = 0.85 + (level - 1) * 0.05

        elif level < 10:
            # Genc
            size = 1.10 + (level - 5) * 0.07

        else:
            # Yetiskin
            size = 1.50 + min(level - 10, 10) * 0.04

        painter.scale(size, size)


        angle = math.degrees(
            math.atan2(
                self.target_y - self.y,
                self.target_x - self.x
            )
        )

        painter.rotate(angle)

        color = QColor("#292929")

        if self.scared_frames > 0:
            color = QColor("#7B3FE4")

        painter.setPen(QPen(color, 3))

        # Sekiz hareketli bacak
        for side in (-1, 1):
            for i in range(4):
                wave = math.sin(
                    self.animation + i * 1.5
                ) * 4

                painter.drawLine(
                    side * 7,
                    i * 2 - 3,
                    int(side * (20 + i * 3)),
                    int((i - 1) * 6 + wave)
                )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(-13, -12, 26, 24)

        painter.setBrush(QColor("white"))
        painter.drawEllipse(-7, -5, 5, 5)
        painter.drawEllipse(2, -5, 5, 5)

        painter.setBrush(QColor("black"))
        painter.drawEllipse(-5, -4, 2, 2)
        painter.drawEllipse(4, -4, 2, 2)

        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.draw_webs(painter)
        self.draw_targets(painter)
        self.draw_home(painter)
        self.draw_spider(painter)

        painter.end()


signal.signal(
    signal.SIGINT,
    signal.default_int_handler
)

app = QApplication(sys.argv)

# Panel kapaninca ana uygulama kapanmasin
app.setQuitOnLastWindowClosed(False)

spider = Spider()
spider.show()

# Pet paneli ve sistem tepsisi
pet_panel, tray = setup_pet_tray(app)

# Orumcek pet degerlerini okuyabilsin
spider.pet_panel = pet_panel
pet_panel.set_progression(spider.progression)

signal_timer = QTimer()
signal_timer.timeout.connect(lambda: None)
signal_timer.start(100)

user32 = ctypes.windll.user32


def check_exit_shortcut():
    ctrl = user32.GetAsyncKeyState(0x11) & 0x8000
    alt = user32.GetAsyncKeyState(0x12) & 0x8000
    q = user32.GetAsyncKeyState(0x51) & 0x8000

    if ctrl and alt and q:
        app.quit()


shortcut_timer = QTimer()
shortcut_timer.timeout.connect(check_exit_shortcut)
shortcut_timer.start(50)

try:
    sys.exit(app.exec())
except KeyboardInterrupt:
    app.quit()
    sys.exit(0)
