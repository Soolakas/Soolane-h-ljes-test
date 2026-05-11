from enum import Enum


class GameState(Enum):
    """Mängu olekute loetelu - kõik võimalikud ekraanid/olekud."""
    MENU = "menu"          # Põhimenüü
    PLAYING = "playing"    # Aktiivne mäng
    PAUSED = "paused"      # Mäng on peatatud
    SETTINGS = "settings"  # Seadete ekraan
    UPGRADES = "upgrades"  # Püsivõimenduste ekraan (menüü)
    UPGRADE_SELECTION = "upgrade_selection"  # Uuenduse valik mängu ajal
    GAME_OVER = "game_over" # Mängu lõpp


class StateManager:
    """Haldab mängu olekute vahetusi pinupõhise navigeerimissüsteemiga.
    Manages game state transitions with a stack-based navigation system."""

    def __init__(self):
        self._current_state = GameState.MENU    # Praegune aktiivne olek
        self._state_stack = [GameState.MENU]    # Olekute pinu (stack)
        self._listeners = []                    # Kuulajad, keda teavitatakse oleku muutmisel

    @property
    def current_state(self):
        """Tagastab praeguse aktiivse oleku."""
        return self._current_state

    def change_state(self, new_state):
        """Vahetab täielikult oleku - tühjendab pinu ja seab uue oleku.
        Kasutatakse peamenüüsse või mängu naasmisel."""
        self._state_stack = [new_state]
        self._current_state = new_state
        self._notify_listeners()

    def push_state(self, new_state):
        """Lisab uue oleku pinu otsa (nt paus või seaded).
        Võimaldab hiljem pop_state abil tagasi minna."""
        self._state_stack.append(new_state)
        self._current_state = new_state
        self._notify_listeners()

    def pop_state(self):
        """Eemaldab viimase oleku pinust ja naaseb eelmise juurde.
        Kasutatakse pausist või seadetest tagasi minnes."""
        if len(self._state_stack) > 1:
            self._state_stack.pop()
            self._current_state = self._state_stack[-1]
            self._notify_listeners()

    def add_listener(self, callback):
        """Lisab kuulaja, keda teavitatakse iga oleku muutuse korral."""
        self._listeners.append(callback)

    def remove_listener(self, callback):
        """Eemaldab kuulaja nimekirjast."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        """Teavitab kõiki kuulajaid oleku muutusest."""
        for listener in self._listeners:
            listener(self._current_state)
