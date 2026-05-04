import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.state_manager import GameState


class MainMenuScreen(BaseScreen):
    """Main menu screen with title, play, settings, upgrades, and exit buttons."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []
        self._title_font = pygame.font.SysFont(None, 80)
        self._subtitle_font = pygame.font.SysFont(None, 28)
        self._quit_requested = False
        self._build_buttons()

    def _build_buttons(self):
        screen_w, screen_h = 1280, 720
        btn_w, btn_h = 280, 55
        btn_x = (screen_w - btn_w) / 2
        start_y = screen_h * 0.55
        gap = 15

        self.buttons = [
            UIButton("PLAY", (btn_x, start_y), (btn_w, btn_h),
                     callback=lambda: self.state_manager.change_state(GameState.PLAYING),
                     font_size=30),
            UIButton("SETTINGS", (btn_x, start_y + btn_h + gap), (btn_w, btn_h),
                     callback=lambda: self.state_manager.change_state(GameState.SETTINGS),
                     font_size=28),
            UIButton("UPGRADES", (btn_x, start_y + (btn_h + gap) * 2), (btn_w, btn_h),
                     callback=lambda: self.state_manager.change_state(GameState.UPGRADES),
                     font_size=28),
            UIButton("EXIT", (btn_x, start_y + (btn_h + gap) * 3), (btn_w, btn_h),
                     callback=self._on_exit_clicked,
                     font_size=28, bg_color=(80, 40, 40), hover_color=(110, 50, 50)),
        ]

    def _on_exit_clicked(self):
        self._quit_requested = True

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((15, 15, 25))
        self._draw_background_decorations(screen)

        screen_w, screen_h = screen.get_size()

        title_surf = self._title_font.render("GEOMETRY BATTLES", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_w / 2, screen_h * 0.22))
        screen.blit(title_surf, title_rect)

        subtitle = self._subtitle_font.render("A geometric arena shooter", True, (150, 150, 180))
        sub_rect = subtitle.get_rect(center=(screen_w / 2, screen_h * 0.32))
        screen.blit(subtitle, sub_rect)

        for btn in self.buttons:
            btn.draw(screen)

    def _draw_background_decorations(self, screen):
        screen_w, screen_h = screen.get_size()
        center = (screen_w / 2, screen_h * 0.38)
        import math
        for i in range(8):
            angle = math.radians(45 * i + 22.5)
            radius = 200
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            pygame.draw.circle(screen, (40, 40, 60), (x, y), 3, 2)
        for i in range(8):
            angle = math.radians(45 * i + 22.5)
            radius = 200
            x1 = center[0] + radius * math.cos(angle)
            y1 = center[1] + radius * math.sin(angle)
            angle2 = math.radians(45 * ((i + 1) % 8) + 22.5)
            x2 = center[0] + radius * math.cos(angle2)
            y2 = center[1] + radius * math.sin(angle2)
            pygame.draw.line(screen, (30, 30, 50), (x1, y1), (x2, y2), 1)

    def is_quit_requested(self):
        return self._quit_requested
