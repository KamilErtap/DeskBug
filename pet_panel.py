
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSystemTrayIcon,
    QMenu, QCheckBox, QSlider
)

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from state import PetState, Settings
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QAction
)



class PetPanel(QWidget):
    def __init__(self, spider=None):
        super().__init__()

        self.setWindowTitle("DeskBug - Webby")
        self.spider = spider
        self.state = spider.state if spider else PetState.load()
        self.settings = spider.settings if spider else Settings.load()
        self.setFixedWidth(344)

        self.setStyleSheet("""
            QWidget {
                background-color: #1d1b23;
                color: #ece7f0;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QLabel#title {
                font-size: 28px;
                font-weight: bold;
                color: #c4aedb;
            }

            QPushButton {
                background-color: #302a3b;
                border: 1px solid #494051;
                border-radius: 8px;
                padding: 9px;
            }
            QPushButton:pressed {
                background-color: #61506d;
            }
            QCheckBox { spacing: 8px; }
            QSlider::groove:horizontal { height: 4px; background: #39313f; }
            QSlider::handle:horizontal { width: 12px; margin: -4px 0; background: #c4aedb; border-radius: 6px;
            }

            QPushButton:hover {
                background-color: #45384f;
            }

            QProgressBar {
                border: none;
                border-radius: 6px;
                background: #302b38;
                height: 15px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #a58abd;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("Webby")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("YOUR LITTLE DESKTOP COMPANION")
        subtitle.setStyleSheet("color: #9d91aa; font-size: 10px; letter-spacing: 1px;")
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

        layout.addWidget(QLabel("Nourishment"))
        layout.addWidget(self.food_bar)

        layout.addWidget(QLabel("Energy"))
        layout.addWidget(self.energy_bar)

        layout.addWidget(QLabel("Happiness"))
        layout.addWidget(self.happiness_bar)

        buttons = QHBoxLayout()

        feed_button = QPushButton("Feed")
        sleep_button = QPushButton("Rest")
        love_button = QPushButton("Pet")

        buttons.addWidget(feed_button)
        buttons.addWidget(sleep_button)
        buttons.addWidget(love_button)

        layout.addLayout(buttons)

        self.message = QLabel("A quiet little life among your icons.")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(36)
        self.message.setStyleSheet("color: #b5a7bf; font-size: 12px;")
        layout.addWidget(self.message)
        settings_label = QLabel("DESKTOP ATMOSPHERE")
        settings_label.setStyleSheet("color: #9d91aa; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(settings_label)
        self.pet_toggle = QCheckBox("Show Webby")
        self.web_toggle = QCheckBox("Silk and nest")
        self.pet_toggle.setChecked(self.settings.pet_visible)
        self.web_toggle.setChecked(self.settings.web_visible)
        toggles = QHBoxLayout()
        toggles.addWidget(self.pet_toggle)
        toggles.addWidget(self.web_toggle)
        layout.addLayout(toggles)
        self.speed_label = QLabel()
        layout.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50,150)
        self.speed_slider.setSingleStep(10)
        self.speed_slider.setValue(self.settings.animation_speed)
        self.speed_slider.setAccessibleName("Animation speed")
        layout.addWidget(self.speed_slider)
        self.pet_toggle.toggled.connect(self.change_settings)
        self.web_toggle.toggled.connect(self.change_settings)
        self.speed_slider.valueChanged.connect(self.change_settings)
        self.speed_label.setText(f"Animation pace · {self.settings.animation_speed}%")

        feed_button.clicked.connect(self.feed)
        sleep_button.clicked.connect(self.sleep)
        love_button.clicked.connect(self.love)

        self.bar_animations = {}
        self.update_bars()

        # Her 60 saniyede ihtiyaclar azalir
        self.needs_timer = QTimer(self)
        self.needs_timer.timeout.connect(self.update_needs)
        self.needs_timer.start(60000)

    
    @property
    def food(self): return self.state.food
    @food.setter
    def food(self, value): self.state.food = value
    @property
    def energy(self): return self.state.energy
    @energy.setter
    def energy(self, value): self.state.energy = value
    @property
    def happiness(self): return self.state.happiness
    @happiness.setter
    def happiness(self, value): self.state.happiness = value

    def save_state(self):
        self.state.save()

    def change_settings(self, *_):
        self.settings.pet_visible = self.pet_toggle.isChecked()
        self.settings.web_visible = self.web_toggle.isChecked()
        self.settings.animation_speed = self.speed_slider.value()
        self.speed_label.setText(f"Animation pace · {self.settings.animation_speed}%")
        self.settings.save()
        if self.spider:
            self.spider.apply_settings()

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
            f"Level {level}  ·  {stage}"
        )

        self.xp_bar.setRange(0, required)
        self.xp_bar.setValue(min(xp, required))

        self.xp_bar.setFormat(
            f"{xp} / {required} XP"
        )


    def update_bars(self):
        for bar, value in ((self.food_bar,self.food), (self.energy_bar,self.energy), (self.happiness_bar,self.happiness)):
            animation = self.bar_animations.get(bar)
            if animation:
                animation.stop()
            if bar.value() < 0 or not self.isVisible():
                bar.setValue(value)
            else:
                if animation is None:
                    animation = QPropertyAnimation(bar, b"value", self)
                    animation.setDuration(240)
                    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                    self.bar_animations[bar] = animation
                animation.setStartValue(bar.value())
                animation.setEndValue(value)
                animation.start()

        self.food_bar.setFormat(f"{self.food}/100")
        self.energy_bar.setFormat(f"{self.energy}/100")
        self.happiness_bar.setFormat(
            f"{self.happiness}/100"
            
        )
        
        self.save_state()

    def feed(self):
        self.food = min(100, self.food + 20)
        self.message.setText("A small meal, happily received.")
        self.update_bars()

    def sleep(self):
        if self.spider:
            self.spider.request_sleep()
        else:
            self.message.setText("Webby is resting.")

    def love(self):
        self.happiness = min(
            100, self.happiness + 15
        )
        self.message.setText("Webby feels a little more loved.")
        self.update_bars()

    def update_needs(self):
        self.state.decay()
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

    painter.setBrush(QColor("#1d1b23"))
    painter.drawEllipse(25, 28, 3, 4)
    painter.drawEllipse(38, 28, 3, 4)

    painter.end()
    return QIcon(pixmap)


def setup_pet_tray(app, spider=None):
    panel = PetPanel(spider)
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
            background: #45384f;
        }
    """)

    open_action = QAction("Visit Webby", menu)
    open_action.triggered.connect(panel.open_panel)
    menu.addAction(open_action)

    menu.addSeparator()

    quit_action = QAction("Quit DeskBug", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    def tray_clicked(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            panel.open_panel()

    tray.activated.connect(tray_clicked)
    tray.show()
    if not QSystemTrayIcon.isSystemTrayAvailable():
        panel.open_panel()

    # Referanslari koru
    tray.pet_menu = menu
    tray.pet_panel = panel

    return panel, tray
