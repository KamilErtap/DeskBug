
import sys
import math
import random
import signal
import ctypes

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QCursor

from desktop_icons import get_desktop_icons
from pet_panel import setup_pet_tray
from progression import Progression
from persistence import data_directory, read_json, write_json, configure_logging, close_logging, log
from state import Settings, PetState
from behavior import turn_towards, step_towards
from webs import connect_web
from graphics import draw_webs, draw_home, draw_spider



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

        self.settings = Settings.load()
        self.state = PetState.load()
        self.heading = -90.0
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
        self.sleep_requested = False
        self.sleep_frames = 0

        # Kayitli yuvayi yukle
        self.load_home()

        self.choose_target()


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spider)
        self.timer.start(30)

    
    def load_home(self):
        self.home_file = data_directory() / "home.json"
        self.home_name = read_json(self.home_file).get("home_name")
        self.home_icon = next((icon for icon in self.desktop_icons if icon['name'] == self.home_name), None)
        if self.home_name is None and self.desktop_icons:
            self.home_icon = random.choice(self.desktop_icons)
            self.home_name = self.home_icon['name']
            write_json(self.home_file, {'home_name': self.home_name})

    def refresh_environment(self):
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())
        self.x = max(20, min(self.width()-20, self.x))
        self.y = max(20, min(self.height()-20, self.y))
        old_target = self.current_icon['name'] if self.current_icon else None
        old_anchor = self.last_anchor['name'] if self.last_anchor else None
        self.load_icons()
        self.load_home()
        icons = {icon['name']: icon for icon in self.desktop_icons}
        self.web_edges = [dict(edge, start=icons[edge['start']['name']], end=icons[edge['end']['name']])
                          for edge in self.web_edges
                          if edge['start']['name'] in icons and edge['end']['name'] in icons]
        self.last_anchor = icons.get(old_anchor)
        self.current_icon = icons.get(old_target)
        if self.current_icon:
            self.target_x, self.target_y = self.current_icon['x'], self.current_icon['y']
        else:
            self.choose_target()

    def apply_settings(self):
        self.settings.save()
        self.setVisible(self.settings.pet_visible)
        self.update()

    def request_sleep(self):
        self.sleep_requested = True
        self.rest_frames = 0
        if self.home_icon is None:
            self.sleeping = True
        self.pet_panel.message.setText("Returning to the nest for a little rest." if self.home_icon else "Resting here until a nest is available.")
        self.pet_panel.update_bars()

    def load_icons(self):
        try:
            raw_icons = get_desktop_icons()
        except Exception as error:
            log.exception("Desktop icon scan failed")
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

        log.debug("Found %s icons", len(self.desktop_icons))

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

            log.debug("%s", " ".join(str(value) for value in ("Yeni hedef:", self.current_icon["name"],)))

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

    connect_web = connect_web

    def get_pet_stats(self):
        return self.state.food, self.state.energy, self.state.happiness

    def update_sleep(self):
        if not self.sleeping:
            return False

        self.sleep_frames += self.frame_scale

        # Yaklasik 3 saniyede bir enerji kazan
        if self.sleep_frames >= 100:
            self.sleep_frames = 0

            self.state.energy = min(100, self.state.energy + 5)
            self.state.save()
            if hasattr(self, 'pet_panel'):
                self.pet_panel.update_bars()
                self.pet_panel.message.setText("Webby is sleeping peacefully…")
            if self.state.energy >= 60:
                self.sleeping = False
                self.sleep_requested = False
                if hasattr(self, 'pet_panel'):
                    self.pet_panel.message.setText("Rested and ready to explore.")
                self.choose_target()

        self.update()
        return True



    def update_spider(self):
        interval = 120 if self.sleeping or self.rest_frames > 0 or not self.settings.pet_visible else 30
        self.timer.setInterval(interval)
        self.frame_scale = interval / 30
        motion_scale = self.frame_scale * self.settings.animation_speed / 100


        # Webby uyuyorsa hareket etmesin
        if self.update_sleep():
            return

        # Enerji azsa yuvasina donsun
        food, energy, happiness = self.get_pet_stats()

        if (energy <= 20 or self.sleep_requested) and self.home_icon is None:
            self.sleeping = True
            self.sleep_frames = 0
            return

        if (energy <= 20 or self.sleep_requested) and self.home_icon is not None:
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
                        "Tucked into the nest. Sweet dreams, Webby."
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
            self.scared_frames = max(0, self.scared_frames - self.frame_scale)

            # Fareden uzaklasma yonu
            if mouse_distance > 0.01:
                vx = dx_mouse / mouse_distance
                vy = dy_mouse / mouse_distance
            else:
                vx, vy = 1, 0

            self.x = max(
                20,
                min(self.width() - 20, self.x + vx * 5 * motion_scale)
            )

            self.y = max(
                20,
                min(self.height() - 20, self.y + vy * 5 * motion_scale)
            )

            self.heading = turn_towards(self.heading, math.degrees(math.atan2(vy, vx)))
            self.animation += 0.3 * motion_scale
            self.update()
            return

        if self.rest_frames > 0:
            self.rest_frames = max(0, self.rest_frames - self.frame_scale)
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

            self.heading = turn_towards(self.heading, math.degrees(math.atan2(dy, dx)))
            self.x, self.y = step_towards(self.x, self.y, self.target_x, self.target_y, current_speed * motion_scale)
            self.animation += 0.22 * motion_scale


        self.update()

    draw_webs = draw_webs
    draw_home = draw_home
    draw_spider = draw_spider

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.draw_webs(painter)
        self.draw_home(painter)
        self.draw_spider(painter)

        painter.end()


def main():
    configure_logging()
    # Qt 6 enables per-monitor high-DPI support before creating native windows.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    app = QApplication(sys.argv)
    app.setApplicationName("DeskBug")
    app.setQuitOnLastWindowClosed(False)
    spider = Spider()
    pet_panel, tray = setup_pet_tray(app, spider)
    spider.pet_panel = pet_panel
    pet_panel.set_progression(spider.progression)
    spider.apply_settings()

    refresh_timer = QTimer(spider)
    refresh_timer.timeout.connect(spider.refresh_environment)
    refresh_timer.start(60000)
    def watch_screen(screen):
        screen.availableGeometryChanged.connect(lambda *_: spider.refresh_environment())
        screen.logicalDotsPerInchChanged.connect(lambda *_: spider.refresh_environment())
    def screen_added(screen):
        watch_screen(screen)
        spider.refresh_environment()
    app.screenAdded.connect(screen_added)
    app.screenRemoved.connect(lambda *_: spider.refresh_environment())
    app.primaryScreenChanged.connect(lambda *_: spider.refresh_environment())
    for screen in app.screens():
        watch_screen(screen)

    shortcut_timer = QTimer(spider)
    def check_exit_shortcut():
        if sys.platform == 'win32':
            user32 = ctypes.windll.user32
            if all(user32.GetAsyncKeyState(key) & 0x8000 for key in (0x11,0x12,0x51)):
                app.quit()
    shortcut_timer.timeout.connect(check_exit_shortcut)
    shortcut_timer.start(100)

    def shutdown():
        spider.timer.stop()
        refresh_timer.stop()
        shortcut_timer.stop()
        pet_panel.needs_timer.stop()
        pet_panel.xp_timer.stop()
        spider.state.save()
        spider.progression.save()
        spider.settings.save()
        tray.hide()
        spider.close()
        log.info("DeskBug shut down cleanly")
        close_logging()
    app.aboutToQuit.connect(shutdown)
    log.info("DeskBug started")
    try:
        return app.exec()
    except KeyboardInterrupt:
        app.quit()
        return 0

if __name__ == '__main__':
    sys.exit(main())
