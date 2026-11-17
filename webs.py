"""Bounded silk construction and progression rewards."""
from behavior import edge_key
from persistence import log

def connect_web(self, icon):
    # Ilk ikon agin baslangic noktasi
    if self.last_anchor is None:
        self.last_anchor = icon
        log.debug("%s", " ".join(str(value) for value in ("Ilk ag noktasi:", icon["name"],)))
        return

    if self.last_anchor is icon:
        return

    start = self.last_anchor
    end = icon

    # Ayni iki ikon arasina tekrar ag kurma
    key = edge_key(start, end)

    for edge in self.web_edges:
        if edge["key"] == key:
            self.last_anchor = icon
            return

    self.web_edges.append({
        "start": start,
        "end": end,
        "key": key
    })

    if len(self.web_edges) > self.max_web_edges:
        self.web_edges.pop(0)

    log.debug("%s", " ".join(str(value) for value in ("AG ORULDU:", start["name"], "->", end["name"],)))

    self.last_anchor = icon

    # Yeni ag baglantisi = 10 XP
    leveled_up = self.progression.add_xp(10)

    log.debug("%s", " ".join(str(value) for value in (f"XP: {self.progression.xp}/"
        f"{self.progression.required_xp()} | "
        f"Seviye: {self.progression.level}",)))

    if leveled_up and hasattr(self, "pet_panel"):
        self.pet_panel.message.setText(
            f"Webby reached level {self.progression.level}!"
        )


