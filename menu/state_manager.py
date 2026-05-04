from enum import Enum


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    SETTINGS = "settings"
    UPGRADES = "upgrades"
    GAME_OVER = "game_over"


class StateManager:
    """Manages game state transitions with a stack-based navigation system."""

    def __init__(self):
        self._current_state = GameState.MENU
        self._state_stack = [GameState.MENU]
        self._listeners = []

    @property
    def current_state(self):
        return self._current_state

    def change_state(self, new_state):
        self._state_stack = [new_state]
        self._current_state = new_state
        self._notify_listeners()

    def push_state(self, new_state):
        self._state_stack.append(new_state)
        self._current_state = new_state
        self._notify_listeners()

    def pop_state(self):
        if len(self._state_stack) > 1:
            self._state_stack.pop()
            self._current_state = self._state_stack[-1]
            self._notify_listeners()

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        for listener in self._listeners:
            listener(self._current_state)
