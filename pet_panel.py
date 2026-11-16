
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSystemTrayIcon,
    QMenu
)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QAction
)

import json
import os
from pathlib import Path


class PetPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DeskBug - Webby")
        self.setFixedSize(360, 420)

        self.save_folder = (
            Path(os.getenv("LOCALAPPDATA") or Path.home())
            / "DeskBug"
        )
        self.save_file = self.save_folder / "pet_data.json"

        self.load_state()

        self.setStyleSheet("""
            QWidget {
                background-color: #20212B;
                color: #F5F5F5;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QLabel#title {
                font-size: 23px;
                font-weight: bold;
                color: #C5A7FF;
            }

            QPushButton {
                background-color: #353549;
                border: 1px solid #55556A;
                border-radius: 8px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #51456D;
            }

            QProgressBar {
                border: none;
                border-radius: 6px;
                background: #383846;
                height: 15px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #9B7BEA;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("WEBBY")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Seviye 1 | Yavru Orumcek")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)


        # XP ve seviye sistemi
        self.progression = None

        self.level_label = QLabel("Seviye 1 | Yavru")
        self.level_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.level_label)

        self.xp_bar = QProgressBar()
        self.xp_bar.setRange(0, 50)
        self.xp_bar.setValue(0)
        self.xp_bar.setFormat("0 / 50 XP")

        layout.addWidget(self.xp_bar)

        # XP degisikliklerini panelde guncelle
        self.xp_timer = QTimer(self)
        self.xp_timer.timeout.connect(
            self.update_progression
        )
        self.xp_timer.start(500)


        # Ihtiyac cubuklari
        self.food_bar = QProgressBar()
        self.energy_bar = QProgressBar()
        self.happiness_bar = QProgressBar()

        layout.addWidget(QLabel("Tokluk"))
        layout.addWidget(self.food_bar)

        layout.addWidget(QLabel("Enerji"))
        layout.addWidget(self.energy_bar)

        layout.addWidget(QLabel("Mutluluk"))
        layout.addWidget(self.happiness_bar)

        buttons = QHBoxLayout()

        feed_button = QPushButton("Besle")
        sleep_button = QPushButton("Uyut")
        love_button = QPushButton("Sev")

        buttons.addWidget(feed_button)
        buttons.addWidget(sleep_button)
        buttons.addWidget(love_button)

        layout.addLayout(buttons)

        self.message = QLabel("Webby masaustunu kesfediyor...")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message)

        feed_button.clicked.connect(self.feed)
        sleep_button.clicked.connect(self.sleep)
        love_button.clicked.connect(self.love)

        self.update_bars()

        # Her 60 saniyede ihtiyaclar azalir
        self.needs_timer = QTimer(self)
        self.needs_timer.timeout.connect(self.update_needs)
        self.needs_timer.start(60000)

    
    def load_state(self):
        # Ilk acilista varsayilan degerler
        self.food = 85
        self.energy = 75
        self.happiness = 90

        if not self.save_file.exists():
            return

        try:
            with open(
                self.save_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            self.food = max(
                0, min(100, int(data.get("food", 85)))
            )
            self.energy = max(
                0, min(100, int(data.get("energy", 75)))
            )
            self.happiness = max(
                0, min(100, int(data.get("happiness", 90)))
            )

            print("Webby'nin kaydi yuklendi!")

        except (OSError, ValueError, TypeError) as error:
            print("Kayit okunamadi:", error)

    def save_state(self):
        data = {
            "food": self.food,
            "energy": self.energy,
            "happiness": self.happiness
        }

        try:
            self.save_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            temporary = self.save_file.with_suffix(".tmp")

            with open(
                temporary,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(data, file, indent=4)

            temporary.replace(self.save_file)

        except OSError as error:
            print("Kayit hatasi:", error)


    def set_progression(self, progression):
        self.progression = progression
        self.update_progression()

    def update_progression(self):
        if self.progression is None:
            return

        level = self.progression.level
        xp = self.progression.xp
        required = self.progression.required_xp()
        stage = self.progression.stage()

        self.level_label.setText(
            f"Seviye {level} | {stage}"
        )

        self.xp_bar.setRange(0, required)
        self.xp_bar.setValue(min(xp, required))

        self.xp_bar.setFormat(
            f"{xp} / {required} XP"
        )


    def update_bars(self):
        self.food_bar.setValue(self.food)
        self.energy_bar.setValue(self.energy)
        self.happiness_bar.setValue(self.happiness)

        self.food_bar.setFormat(f"{self.food}/100")
        self.energy_bar.setFormat(f"{self.energy}/100")
        self.happiness_bar.setFormat(
            f"{self.happiness}/100"
            
        )
        
        self.save_state()

    def feed(self):
        self.food = min(100, self.food + 20)
        self.message.setText("Webby yemegini yedi!")
        self.update_bars()

    def sleep(self):
        self.energy = min(100, self.energy + 25)
        self.message.setText("Webby biraz dinlendi!")
        self.update_bars()

    def love(self):
        self.happiness = min(
            100, self.happiness + 15
        )
        self.message.setText("Webby mutlu oldu!")
        self.update_bars()

    def update_needs(self):
        self.food = max(0, self.food - 1)
        self.energy = max(0, self.energy - 1)
        self.happiness = max(
            0, self.happiness - 1
        )
        self.update_bars()

    def open_panel(self):
        self.show()
        self.raise_()
        self.activateWindow()


def create_tray_icon():
    # Disaridan resim dosyasi gerektirmeyen ikon
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(
        QPainter.RenderHint.Antialiasing
    )

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#9975EA"))
    painter.drawEllipse(10, 10, 44, 44)

    painter.setBrush(QColor("white"))
    painter.drawEllipse(22, 25, 8, 9)
    painter.drawEllipse(35, 25, 8, 9)

    painter.setBrush(QColor("#20212B"))
    painter.drawEllipse(25, 28, 3, 4)
    painter.drawEllipse(38, 28, 3, 4)

    painter.end()
    return QIcon(pixmap)


def setup_pet_tray(app):
    panel = PetPanel()
    icon = create_tray_icon()

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("DeskBug - Webby")

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background: #252532;
            color: white;
            padding: 6px;
        }
        QMenu::item {
            padding: 8px 22px;
        }
        QMenu::item:selected {
            background: #51456D;
        }
    """)

    open_action = QAction("Webby'yi Ac", menu)
    open_action.triggered.connect(panel.open_panel)
    menu.addAction(open_action)

    menu.addSeparator()

    quit_action = QAction("DeskBug'dan Cik", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    def tray_clicked(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            panel.open_panel()

    tray.activated.connect(tray_clicked)
    tray.show()

    # Referanslari koru
    tray.pet_menu = menu
    tray.pet_panel = panel

    return panel, tray
