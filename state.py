"""UI-independent needs and presentation preferences."""
from dataclasses import dataclass, asdict
from persistence import data_directory, read_json, write_json

def bounded(value, default, low=0, high=100):
    try:
        return max(low, min(high, int(value)))
    except (ValueError, TypeError, OverflowError):
        return default

@dataclass
class PetState:
    food: int = 85
    energy: int = 75
    happiness: int = 90

    @classmethod
    def load(cls, path=None):
        data = read_json(path or data_directory() / 'pet_data.json')
        return cls(*(bounded(data.get(key), default) for key, default in [('food',85), ('energy',75), ('happiness',90)]))

    def save(self, path=None):
        return write_json(path or data_directory() / 'pet_data.json', asdict(self))

    def decay(self):
        for key in ('food', 'energy', 'happiness'):
            setattr(self, key, max(0, getattr(self, key) - 1))

@dataclass
class Settings:
    animation_speed: int = 100
    web_visible: bool = True
    pet_visible: bool = True

    @classmethod
    def load(cls, path=None):
        data = read_json(path or data_directory() / 'settings.json')
        return cls(bounded(data.get('animation_speed'),100,50,150),
                   data.get('web_visible') if isinstance(data.get('web_visible'), bool) else True,
                   data.get('pet_visible') if isinstance(data.get('pet_visible'), bool) else True)

    def save(self, path=None):
        return write_json(path or data_directory() / 'settings.json', asdict(self))
