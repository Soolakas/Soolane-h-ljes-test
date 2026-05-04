import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.ui.label import UILabel
from menu.ui.slider import UISlider
from menu.state_manager import GameState


class SettingsScreen(BaseScreen):
    """Full settings screen with audio, display, controls, and gameplay sections."""

    def __init__(self, state_manager, settings):
        super().__init__(state_manager, settings)
        self.buttons = []
        self.sliders = []
        self.labels = []
        self._title_font = pygame.font.SysFont(None, 52)
        self._section_font = pygame.font.SysFont(None, 30)
        self._value_labels = {}
        self._build_ui()

    def _build_ui(self):
        screen_w, screen_h = 1280, 720
        panel_w = 600
        panel_x = (screen_w - panel_w) / 2
        panel_y = 30
        panel_h = screen_h - 60

        self._panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        self.buttons.append(
            UIButton("BACK", (panel_x + 20, panel_y + 10), (100, 40),
                     callback=lambda: self.state_manager.change_state(GameState.MENU),
                     font_size=22)
        )

        self.buttons.append(
            UIButton("SAVE", (panel_x + panel_w - 120, panel_y + 10), (100, 40),
                     callback=self._save_settings,
                     font_size=22)
        )

        content_x = panel_x + 40
        y = panel_y + 70

        self.labels.append(UILabel("AUDIO", (content_x, y), font_size=28))
        y += 35

        self._music_slider = UISlider(
            (content_x, y), panel_w - 80, self.settings.music_volume,
            label="Music Volume", font_size=20
        )
        self.sliders.append(self._music_slider)
        y += 55

        self._sfx_slider = UISlider(
            (content_x, y), panel_w - 80, self.settings.sfx_volume,
            label="SFX Volume", font_size=20
        )
        self.sliders.append(self._sfx_slider)
        y += 70

        self.labels.append(UILabel("DISPLAY", (content_x, y), font_size=28))
        y += 35

        self._fullscreen_btn = UIButton(
            "Fullscreen: OFF" if not self.settings.fullscreen else "Fullscreen: ON",
            (content_x, y), (220, 38),
            callback=self._toggle_fullscreen,
            font_size=20
        )
        self.buttons.append(self._fullscreen_btn)
        y += 50

        resolutions = [(1280, 720), (1920, 1080), (800, 600)]
        current_res = self.settings.resolution
        res_idx = resolutions.index(current_res) if current_res in resolutions else 0
        self._res_btn = UIButton(
            f"Resolution: {current_res[0]}x{current_res[1]}",
            (content_x, y), (260, 38),
            callback=lambda: self._cycle_resolution(resolutions),
            font_size=20
        )
        self.buttons.append(self._res_btn)
        self._resolutions = resolutions
        y += 70

        self.labels.append(UILabel("CONTROLS", (content_x, y), font_size=28))
        y += 35

        bindings = self.settings.key_bindings
        control_y = y
        for action, key in bindings.items():
            label_text = f"{action.replace('_', ' ').title()}: {key.upper()}"
            self.labels.append(UILabel(label_text, (content_x, control_y), font_size=20, color=(180, 180, 200)))
            control_y += 28
        y = control_y + 35

        self.labels.append(UILabel("GAMEPLAY", (content_x, y), font_size=28))
        y += 35

        fps_text = "ON" if self.settings.show_fps else "OFF"
        self._fps_btn = UIButton(
            f"Show FPS: {fps_text}",
            (content_x, y), (200, 38),
            callback=self._toggle_fps,
            font_size=20
        )
        self.buttons.append(self._fps_btn)
        y += 50

        qualities = ["low", "medium", "high"]
        current_quality = self.settings.particle_quality
        self._quality_btn = UIButton(
            f"Particle Quality: {current_quality.title()}",
            (content_x, y), (280, 38),
            callback=lambda: self._cycle_quality(qualities),
            font_size=20
        )
        self.buttons.append(self._quality_btn)

    def _toggle_fullscreen(self):
        self.settings.fullscreen = not self.settings.fullscreen
        self._fullscreen_btn.text = "Fullscreen: ON" if self.settings.fullscreen else "Fullscreen: OFF"

    def _cycle_resolution(self, resolutions):
        current = self.settings.resolution
        idx = (resolutions.index(current) + 1) % len(resolutions) if current in resolutions else 0
        new_res = resolutions[idx]
        self.settings.resolution = new_res
        self._res_btn.text = f"Resolution: {new_res[0]}x{new_res[1]}"

    def _toggle_fps(self):
        self.settings.show_fps = not self.settings.show_fps
        fps_text = "ON" if self.settings.show_fps else "OFF"
        self._fps_btn.text = f"Show FPS: {fps_text}"

    def _cycle_quality(self, qualities):
        current = self.settings.particle_quality
        idx = (qualities.index(current) + 1) % len(qualities) if current in qualities else 0
        new_quality = qualities[idx]
        self.settings.particle_quality = new_quality
        self._quality_btn.text = f"Particle Quality: {new_quality.title()}"

    def _save_settings(self):
        self.settings.music_volume = self._music_slider.value
        self.settings.sfx_volume = self._sfx_slider.value
        self.settings.save()

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)
            for slider in self.sliders:
                slider.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((15, 15, 25))

        panel_rect = self._panel_rect
        pygame.draw.rect(screen, (25, 25, 45), panel_rect, border_radius=8)
        pygame.draw.rect(screen, (60, 60, 100), panel_rect, 2, border_radius=8)

        title_surf = self._title_font.render("SETTINGS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(panel_rect.centerx, panel_rect.y + 35))
        screen.blit(title_surf, title_rect)

        for label in self.labels:
            label.draw(screen)
        for btn in self.buttons:
            btn.draw(screen)
        for slider in self.sliders:
            slider.draw(screen)
