import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.state_manager import GameState


class PauseScreen(BaseScreen):
    """Mängu peatus-ekraan jätkamise, seadete ja menüüsse naasmise nuppudega.
    Pause overlay with resume, settings, and quit to menu buttons."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []                          # Nuppude nimekiri
        self._title_font = pygame.font.SysFont(None, 64)   # Pealkirja font
        self._build_buttons()

    def _build_buttons(self):
        """Loob pausiekraani nupud: jätka, seaded, menüüsse."""
        screen_w, screen_h = 1280, 720
        btn_w, btn_h = 240, 50                     # Nupu laius ja kõrgus
        btn_x = (screen_w - btn_w) / 2             # Horisontaalne tsentreerimine
        start_y = screen_h * 0.50                  # Nuppude alguse Y-koordinaat
        gap = 15                                   # Vahe nuppude vahel

        self.buttons = [
            # Jätka - naaseb mängu (pop_state eemaldab pausi oleku pinust)
            UIButton("RESUME", (btn_x, start_y), (btn_w, btn_h),
                     callback=lambda: self.state_manager.pop_state(),
                     font_size=28),
            # Seaded - avab seadete ekraani (push_state lisab uue oleku pinu otsa)
            UIButton("SETTINGS", (btn_x, start_y + btn_h + gap), (btn_w, btn_h),
                     callback=lambda: self.state_manager.push_state(GameState.SETTINGS),
                     font_size=26),
            # Menüüsse - naaseb põhimenüüsse ja lähtestab mängu
            UIButton("QUIT TO MENU", (btn_x, start_y + (btn_h + gap) * 2), (btn_w, btn_h),
                     callback=self._on_quit_to_menu,
                     font_size=26, bg_color=(80, 40, 40), hover_color=(110, 50, 50)),
        ]

    def _on_quit_to_menu(self):
        """Menüüsse naasmise nupu töötleja. Vahetab oleku menüüle ja lähtestab mängu."""
        self.state_manager.change_state(GameState.MENU)
        if hasattr(self, "_game_reset_callback"):
            self._game_reset_callback()

    def set_game_reset_callback(self, callback):
        """Seab tagasihelistamise, mida kutsutakse menüüsse naasmisel mängu lähtestamiseks."""
        self._game_reset_callback = callback

    def handle_events(self, events):
        """Töötleb kõiki sisendsündmuseid nuppude jaoks."""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        """Uuendab pausiekraani olekut. Hetkel pole vaja midagi teha."""
        pass

    def draw(self, screen):
        """Joonistab pausi ülekate: tumendatud taust, pealkiri ja nupud."""
        # Läbipaistev tumedus kiht mängu peale
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()
        title_surf = self._title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_w / 2, screen_h * 0.35))
        screen.blit(title_surf, title_rect)

        for btn in self.buttons:
            btn.draw(screen)
