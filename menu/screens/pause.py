import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.state_manager import GameState


class PauseScreen(BaseScreen):
    """Pause overlay with resume, settings, and quit to menu buttons."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []
        self._title_font = pygame.font.SysFont(None, 64)
        self._build_buttons()

    def _build_buttons(self):
        screen_w, screen_h = 1280, 720
        btn_w, btn_h = 240, 50
        btn_x = (screen_w - btn_w) / 2
        start_y = screen_h * 0.50
        gap = 15

        self.buttons = [
            UIButton("RESUME", (btn_x, start_y), (btn_w, btn_h),
                     callback=lambda: self.state_manager.pop_state(),
                     font_size=28),
            UIButton("SETTINGS", (btn_x, start_y + btn_h + gap), (btn_w, btn_h),
                     callback=lambda: self.state_manager.push_state(GameState.SETTINGS),
                     font_size=26),
            UIButton("QUIT TO MENU", (btn_x, start_y + (btn_h + gap) * 2), (btn_w, btn_h),
                     callback=self._on_quit_to_menu,
                     font_size=26, bg_color=(80, 40, 40), hover_color=(110, 50, 50)),
        ]

    def _on_quit_to_menu(self):
        self.state_manager.change_state(GameState.MENU)
        if hasattr(self, "_game_reset_callback"):
            self._game_reset_callback()

    def set_game_reset_callback(self, callback):
        self._game_reset_callback = callback

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()
        title_surf = self._title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_w / 2, screen_h * 0.35))
        screen.blit(title_surf, title_rect)

        for btn in self.buttons:
            btn.draw(screen)
