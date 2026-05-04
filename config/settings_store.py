import json
import os

# Seadete faili nimi - Settings file name
SETTINGS_FILE = "settings.json"

# Vaikimisi seaded, kui faili ei eksisteeri või on vigane
DEFAULT_SETTINGS = {
    "music_volume": 0.7,      # Muusika helitugevus (tulevikuks, hetkel kasutusel pole)
    "sfx_volume": 0.8,        # Heliefektide helitugevus (tulevikuks, hetkel kasutusel pole)
    "fullscreen": False,       # Täisekraani režiim
    "resolution": [1280, 720], # Ekraani resolutsioon
    "key_bindings": {          # Klahvide seaded
        "move_up": "w",
        "move_down": "s",
        "move_left": "a",
        "move_right": "d",
    },
}


class GameSettings:
    """Haldab mängu seadeid püsiva JSON salvestusega."""

    def __init__(self):
        self._data = dict(DEFAULT_SETTINGS)
        self.load()

    def get(self, key, default=None):
        """Tagastab seadme väärtuse võtme järgi."""
        return self._data.get(key, default)

    def set(self, key, value):
        """Seab seadme väärtuse."""
        self._data[key] = value

    @property
    def music_volume(self):
        """Muusika helitugevus (tulevikuks)."""
        return self._data["music_volume"]

    @music_volume.setter
    def music_volume(self, value):
        self._data["music_volume"] = value

    @property
    def sfx_volume(self):
        """Heliefektide helitugevus (tulevikuks)."""
        return self._data["sfx_volume"]

    @sfx_volume.setter
    def sfx_volume(self, value):
        self._data["sfx_volume"] = value

    @property
    def fullscreen(self):
        """Täisekraani režiim."""
        return self._data["fullscreen"]

    @fullscreen.setter
    def fullscreen(self, value):
        self._data["fullscreen"] = value

    @property
    def resolution(self):
        """Ekraani resolutsioon."""
        return tuple(self._data["resolution"])

    @resolution.setter
    def resolution(self, value):
        self._data["resolution"] = list(value)

    @property
    def key_bindings(self):
        """Klahvide seaded."""
        return self._data["key_bindings"]

    @key_bindings.setter
    def key_bindings(self, value):
        self._data["key_bindings"] = value

    def load(self):
        """Laeb seaded failist. Kui faili pole või on vigane, kasutab vaikimisi seadeid."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                for key in DEFAULT_SETTINGS:
                    if key in saved:
                        self._data[key] = saved[key]
            except (json.JSONDecodeError, IOError):
                self._data = dict(DEFAULT_SETTINGS)

    def save(self):
        """Salvestab seaded faili."""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def reset(self):
        """Lähtestab kõik seaded vaikeväärtustele ja salvestab need."""
        self._data = dict(DEFAULT_SETTINGS)
        self.save()
