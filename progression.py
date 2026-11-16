
import json
import os
from pathlib import Path


class Progression:
    def __init__(self):
        folder = Path(
            os.getenv("LOCALAPPDATA") or Path.home()
        ) / "DeskBug"

        self.save_file = folder / "progress.json"
        self.level = 1
        self.xp = 0

        self.load()

    def required_xp(self):
        return 50 + (self.level - 1) * 25

    def stage(self):
        if self.level >= 10:
            return "Yetiskin"
        if self.level >= 5:
            return "Genc"
        return "Yavru"

    def add_xp(self, amount):
        if amount <= 0:
            return False

        self.xp += amount
        leveled_up = False

        while self.xp >= self.required_xp():
            self.xp -= self.required_xp()
            self.level += 1
            leveled_up = True

            print(
                f"WEBBY SEVIYE ATLADI! "
                f"Yeni seviye: {self.level}"
            )

        self.save()
        return leveled_up

    def save(self):
        try:
            self.save_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            data = {
                "level": self.level,
                "xp": self.xp
            }

            temp = self.save_file.with_suffix(".tmp")
            temp.write_text(
                json.dumps(data, indent=4),
                encoding="utf-8"
            )
            temp.replace(self.save_file)

        except OSError as error:
            print("XP kayit hatasi:", error)

    def load(self):
        if not self.save_file.exists():
            return

        try:
            data = json.loads(
                self.save_file.read_text(
                    encoding="utf-8"
                )
            )

            self.level = max(
                1, int(data.get("level", 1))
            )
            self.xp = max(
                0, int(data.get("xp", 0))
            )

        except (OSError, ValueError, TypeError) as error:
            print("XP yuklenemedi:", error)
