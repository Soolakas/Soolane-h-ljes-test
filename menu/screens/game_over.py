import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.state_manager import GameState


class GameOverScreen(BaseScreen):
    """Mängu lõpu ekraan tulemuse, aja ja uuesti mängimise/menüü nuppudega.
    Game over screen with final score, time, and restart/menu buttons."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []                          # Nuppude nimekiri
        self.labels = []                           # Siltide nimekiri (tulemus ja aeg)
        self._title_font = pygame.font.SysFont(None, 72)   # Pealkirja font
        self._score_font = pygame.font.SysFont(None, 36)    # Tulemuse font
        self._score_value = 0                      # Lõpptulemus
        self._time_value = "0:00"                  # Mängu kestus
        self._build_buttons()

    def set_game_stats(self, score, time_str):
        """Seab mängu statistika (tulemus ja aeg) ja ehitab sildid uuesti."""
        self._score_value = score
        self._time_value = time_str
        self._rebuild_labels()

    def _build_buttons(self):
        """Loob mängu lõpu ekraani nupud: uuesti mängida ja põhimenüü."""
        screen_w, screen_h = 1280, 720
        btn_w, btn_h = 240, 50                     # Nupu laius ja kõrgus
        btn_x = (screen_w - btn_w) / 2             # Horisontaalne tsentreerimine
        start_y = screen_h * 0.65                  # Nuppude alguse Y-koordinaat
        gap = 15                                   # Vahe nuppude vahel

        self.buttons = [
            # Uuesti mängida - lähtestab mängu ja alustab otsast
            UIButton("PLAY AGAIN", (btn_x, start_y), (btn_w, btn_h),
                     callback=self._on_play_again,
                     font_size=28),
            # Põhimenüü - naaseb tagasi menüü ekraanile
            UIButton("MAIN MENU", (btn_x, start_y + btn_h + gap), (btn_w, btn_h),
                     callback=lambda: self.state_manager.change_state(GameState.MENU),
                     font_size=26),
        ]

    def _on_play_again(self):
        """Uuesti mängimise nupu töötleja. Vahetab oleku mängimisele ja lähtestab mängu."""
        self.state_manager.change_state(GameState.PLAYING)
        if hasattr(self, "_restart_callback"):
            self._restart_callback()

    def set_restart_callback(self, callback):
        """Seab tagasihelistamise, mida kutsutakse uuesti mängimisel mängu lähtestamiseks."""
        self._restart_callback = callback

    def _rebuild_labels(self):
        """Loob tulemuse ja aja sildid uuesti vastavalt mängu statistikale."""
        screen_w, screen_h = 1280, 720
        self.labels = [
            {
                "text": f"Final Score: {self._score_value}",
                "pos": (screen_w / 2, screen_h * 0.48),
            },
            {
                "text": f"Time: {self._time_value}",
                "pos": (screen_w / 2, screen_h * 0.55),
            },
        ]

    def handle_events(self, events):
        """Töötleb kõiki sisendsündmuseid nuppude jaoks."""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        """Uuendab ekraani olekut. Hetkel pole vaja midagi teha."""
        pass

    def draw(self, screen):
        """Joonistab mängu lõpu ekraani: tumendatud taust, pealkiri, tulemus, aeg ja nupud."""
        # Läbipaistev tumedus kiht mängu peale
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()

        # Pealkiri "GAME OVER" punases
        title_surf = self._title_font.render("GAME OVER", True, (255, 80, 80))
        title_rect = title_surf.get_rect(center=(screen_w / 2, screen_h * 0.30))
        screen.blit(title_surf, title_rect)

        # Lõpptulemus ja mängu kestus
        for label_info in self.labels:
            text_surf = self._score_font.render(label_info["text"], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=label_info["pos"])
            screen.blit(text_surf, text_rect)

        for btn in self.buttons:
            btn.draw(screen)
