import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.ui.label import UILabel
from menu.state_manager import GameState


class UpgradesScreen(BaseScreen):
    """Uuenduste ekraan (koht tulevastele püsivõimendustele).
    Placeholder upgrades screen ready for future implementation."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []                          # Nuppude nimekiri
        self.labels = []                           # Siltide nimekiri
        self._title_font = pygame.font.SysFont(None, 64)   # Pealkirja font
        self._subtitle_font = pygame.font.SysFont(None, 32) # Alapealkirja font
        self._build_ui()

    def _build_ui(self):
        """Loob uuenduste ekraani elemendid: tagasi-nupp, pealkiri ja 'tulekul' tekst."""
        screen_w, screen_h = 1280, 720

        # Tagasi-nupp - viib põhimenüüsse
        self.buttons.append(
            UIButton("BACK", (30, 20), (100, 40),
                     callback=lambda: self.state_manager.change_state(GameState.MENU),
                     font_size=22)
        )

        # Pealkiri ja tulekul teade
        self.labels.append(
            UILabel("UPGRADES", (screen_w / 2, screen_h * 0.3), font_size=56, center=True)
        )
        self.labels.append(
            UILabel("Coming Soon", (screen_w / 2, screen_h * 0.42), font_size=32, center=True, color=(180, 180, 200))
        )
        self.labels.append(
            UILabel("Permanent upgrades will be available here.", (screen_w / 2, screen_h * 0.50), font_size=24, center=True, color=(120, 120, 150))
        )

    def handle_events(self, events):
        """Töötleb kõiki sisendsündmuseid nuppude jaoks."""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        """Uuendab ekraani olekut. Hetkel pole vaja midagi teha."""
        pass

    def draw(self, screen):
        """Joonistab uuenduste ekraani: taust, sildid ja nupud."""
        screen.fill((15, 15, 25))

        for label in self.labels:
            label.draw(screen)
        for btn in self.buttons:
            btn.draw(screen)
