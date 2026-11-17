from persistence import data_directory, read_json, write_json, log
from state import bounded

class Progression:
    def __init__(self, save_file=None):
        self.save_file = save_file or data_directory() / 'progress.json'
        self.level = 1
        self.xp = 0
        self.load()

    def required_xp(self):
        return 50 + (self.level - 1) * 25

    def stage(self):
        return 'Adult' if self.level >= 10 else 'Young spider' if self.level >= 5 else 'Spiderling'

    def add_xp(self, amount):
        if amount <= 0:
            return False
        self.xp += amount
        leveled = False
        while self.xp >= self.required_xp():
            self.xp -= self.required_xp()
            self.level += 1
            leveled = True
            log.info('Webby reached level %s', self.level)
        self.save()
        return leveled

    def save(self):
        write_json(self.save_file, {'level': self.level, 'xp': self.xp})

    def load(self):
        data = read_json(self.save_file)
        self.level = bounded(data.get('level'), 1, 1, 1000000)
        self.xp = bounded(data.get('xp'), 0, 0, 1000000000)
