import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "music_volume": 0.7,
    "sfx_volume": 0.8,
    "fullscreen": False,
    "resolution": [1280, 720],
    "show_fps": False,
    "particle_quality": "high",
    "key_bindings": {
        "move_up": "w",
        "move_down": "s",
        "move_left": "a",
        "move_right": "d",
    },
}


class GameSettings:
    """Manages game settings with persistent JSON storage."""

    def __init__(self):
        self._data = dict(DEFAULT_SETTINGS)
        self.load()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    @property
    def music_volume(self):
        return self._data["music_volume"]

    @music_volume.setter
    def music_volume(self, value):
        self._data["music_volume"] = value

    @property
    def sfx_volume(self):
        return self._data["sfx_volume"]

    @sfx_volume.setter
    def sfx_volume(self, value):
        self._data["sfx_volume"] = value

    @property
    def fullscreen(self):
        return self._data["fullscreen"]

    @fullscreen.setter
    def fullscreen(self, value):
        self._data["fullscreen"] = value

    @property
    def resolution(self):
        return tuple(self._data["resolution"])

    @resolution.setter
    def resolution(self, value):
        self._data["resolution"] = list(value)

    @property
    def show_fps(self):
        return self._data["show_fps"]

    @show_fps.setter
    def show_fps(self, value):
        self._data["show_fps"] = value

    @property
    def particle_quality(self):
        return self._data["particle_quality"]

    @particle_quality.setter
    def particle_quality(self, value):
        self._data["particle_quality"] = value

    @property
    def key_bindings(self):
        return self._data["key_bindings"]

    @key_bindings.setter
    def key_bindings(self, value):
        self._data["key_bindings"] = value

    def load(self):
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
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._data, f, indent=2)
