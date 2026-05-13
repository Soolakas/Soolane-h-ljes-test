import pygame
from menu.screens.base_screen import BaseScreen
from menu.ui.button import UIButton
from menu.ui.label import UILabel
from menu.ui.slider import UISlider
from menu.state_manager import GameState


class SettingsScreen(BaseScreen):
    """Seadete ekraan kuva, juhtelementide ja lähtestamise nuppudega.
    Settings screen with display, controls, and reset settings button."""

    def __init__(self, state_manager, settings, screen=None, sound_manager=None):
        """Algustab seadete ekraani.
        
        Args:
            state_manager: Olekuhaldur ekraanivahetuste jaoks
            settings: Mängu seadete objekt
            screen: Pygame ekraanipind (täisekraani ja resolutsiooni muutmiseks)
            sound_manager: SoundManager instance for volume control
        """
        super().__init__(state_manager, settings)
        self.screen = screen                    # Pygame ekraanipind kuva muutuste jaoks
        self.sound_manager = sound_manager      # Helihaldur helitugevuse juhtimiseks
        self.buttons = []                        # Nuppude nimekiri
        self.labels = []                         # Siltide nimekiri
        self.sliders = []                        # Liugurite nimekiri
        self._title_font = pygame.font.SysFont(None, 48)  # Pealkirja font
        self._build_ui()

    def _build_ui(self):
        """Loob kõik seadete ekraani elemendid õige paigutusega.
        Kasutab tegelikku ekraani suurust, et paneel jääks alati keskele.
        Kõik elemendid mahuvad paneeli sisse ilma kattumisteta."""
        # Kasutab tegelikku ekraani suurust (oluline pärast resolutsiooni muutust)
        if self.screen is not None:
            screen_w, screen_h = self.screen.get_size()
        else:
            screen_w, screen_h = 1280, 720

        panel_w = 500                              # Paneeli laius (kitsam, et mahub paremini)
        panel_x = (screen_w - panel_w) / 2         # Horisontaalne tsentreerimine
        panel_y = 30                               # Ülemine marginaal
        panel_h = 560                              # Paneeli kõrgus

        # Salvestame paneeli asukoha joonistamiseks
        self._panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        content_x = panel_x + 30                   # Sisu vasakpoolne marginaal
        y = panel_y + 65                           # Sisu alguse Y-koordinaat (pealkirja all)

        # ============================================
        # Kuva seaded - Display section
        # ============================================
        self.labels.append(UILabel("DISPLAY", (content_x, y), font_size=26))
        y += 32

        # Täisekraani sisse/välja nupp
        fs_text = "Fullscreen: ON" if self.settings.fullscreen else "Fullscreen: OFF"
        self._fullscreen_btn = UIButton(
            fs_text,
            (content_x, y), (220, 38),
            callback=self._toggle_fullscreen,
            font_size=20
        )
        self.buttons.append(self._fullscreen_btn)
        y += 50

        # Resolutsiooni valik (tsükliline nupp)
        self._resolutions = [(1280, 720), (1920, 1080), (800, 600)]
        current_res = self.settings.resolution
        self._res_btn = UIButton(
            f"Resolution: {current_res[0]}x{current_res[1]}",
            (content_x, y), (260, 38),
            callback=self._cycle_resolution,
            font_size=20
        )
        self.buttons.append(self._res_btn)
        y += 60

        # ============================================
        # Juhtelemendid - Controls section
        # ============================================
        self.labels.append(UILabel("CONTROLS", (content_x, y), font_size=26))
        y += 32

        # Kuvab praegused klahvide seaded
        bindings = self.settings.key_bindings
        control_y = y
        for action, key in bindings.items():
            # Teisendab action nime loetavaks (nt "move_up" -> "Move Up")
            label_text = f"{action.replace('_', ' ').title()}: {key.upper()}"
            self.labels.append(UILabel(label_text, (content_x, control_y), font_size=20, color=(180, 180, 200)))
            control_y += 28
        y = control_y + 45

        # ============================================
        # Audio seaded - Audio section
        # ============================================
        self.labels.append(UILabel("AUDIO", (content_x, y), font_size=26))
        y += 32

        self._sfx_volume_slider = UISlider(
            (content_x, y),
            width=280,
            value=self.settings.sfx_volume,           # Algne väärtus salvestatud seadetest - Initial value from saved settings
            label="SFX Volume",                       # Heliefektide helitugevuse silt - SFX volume label
            callback=self._on_sfx_volume_changed,     # Tagasihelistamine helitugevuse muutmisel - Callback on volume change
        )
        self.sliders.append(self._sfx_volume_slider)  # Lisa liugurite nimekirja - Add to sliders list
        y += 60

        # ============================================
        # Lähtesta seaded - Reset Settings button
        # ============================================
        # Tagasi-nupp - viib põhimenüüsse
        self.buttons.append(
            UIButton("BACK", (content_x, y), (100, 38),
                     callback=lambda: self.state_manager.change_state(GameState.MENU),
                     font_size=20)
        )

        # Lähtesta-nupp - taastab vaikeväärtused
        self.buttons.append(
            UIButton("RESET", (content_x + 115, y), (100, 38),
                     callback=self._reset_settings,
                     font_size=20, bg_color=(80, 40, 40), hover_color=(110, 50, 50))
        )

    def _on_sfx_volume_changed(self, value):
        """Uuendab heliefektide helitugevust reaalajas.
        Updates sound effects volume in real-time.
        
        Args:
            value (float): Uus helitugevus 0.0 kuni 1.0.
                New volume from 0.0 to 1.0.
        """
        self.settings.sfx_volume = value
        if self.sound_manager:
            self.sound_manager.set_volume(value)

    def _toggle_fullscreen(self):
        """Vahetab täisekraani režiimi sisse ja välja.
        Kasutab pygame.display.toggle_fullscreen() ekraani režiimi muutmiseks."""
        self.settings.fullscreen = not self.settings.fullscreen

        # Rakendab täisekraani muutuse pygame-s
        if self.screen is not None:
            pygame.display.toggle_fullscreen()

        # Salvestab seadme automaatselt
        self.settings.save()

        # Ehitab ekraani uuesti üles, et paneel jääks keskele uuel ekraanil
        self.labels.clear()
        self.buttons.clear()
        self.sliders.clear()
        self._build_ui()

    def _cycle_resolution(self):
        """Vahetab resolutsiooni järgmisele väärtusele ringiga.
        Kasutab pygame.display.set_mode() uue resolutsiooni rakendamiseks.
        Säilitab täisekraani oleku - kui on täisekraanil, jääb ka peale muutust."""
        current = self.settings.resolution
        idx = (self._resolutions.index(current) + 1) % len(self._resolutions) if current in self._resolutions else 0
        new_res = self._resolutions[idx]
        self.settings.resolution = new_res

        # Rakendab uue resolutsiooni pygame-s
        # Oluline: kui on täisekraanil, tuleb lippu säilitada,
        # sest set_mode() lähtestab ekraani ja eemaldab täisekraani muidu
        if self.screen is not None:
            flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
            pygame.display.set_mode(new_res, flags)

        # Salvestab seadme automaatselt
        self.settings.save()

        # Ehitab ekraani uuesti üles, et paneel jääks keskele uuel ekraanil
        self.labels.clear()
        self.buttons.clear()
        self.sliders.clear()
        self._build_ui()

    def _reset_settings(self):
        """Lähtestab kõik seaded vaikeväärtustele ja rakendab need."""
        self.settings.reset()

        # Rakenda resolutsioon - Apply resolution
        if self.screen is not None:
            new_res = self.settings.resolution
            flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
            self.screen = pygame.display.set_mode(new_res, flags)

        # Rakenda helitugevus - Apply volume
        if self.sound_manager:
            self.sound_manager.set_volume(self.settings.sfx_volume)

        # Ehitab ekraani täielikult uuesti üles uute seadete ja keskmise paneeliga
        self.labels.clear()
        self.buttons.clear()
        self.sliders.clear()
        self._build_ui()

    def handle_events(self, events):
        """Töötleb kõiki sisendsündmuseid nuppude ja liugurite jaoks."""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)
            for slider in self.sliders:
                slider.handle_event(event)

    def update(self, dt):
        """Uuendab seadete ekraani olekut. Hetkel pole vaja midagi teha."""
        pass

    def draw(self, screen):
        """Joonistab seadete ekraani: taust, paneel, pealkiri, sildid ja nupud."""
        screen.fill((15, 15, 25))

        panel_rect = self._panel_rect
        # Paneeli taust
        pygame.draw.rect(screen, (25, 25, 45), panel_rect, border_radius=8)
        # Paneeli ääris
        pygame.draw.rect(screen, (60, 60, 100), panel_rect, 2, border_radius=8)

        # Pealkiri "SETTINGS"
        title_surf = self._title_font.render("SETTINGS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(panel_rect.centerx, panel_rect.y + 32))
        screen.blit(title_surf, title_rect)

        # Joonistab kõik sildid, liugurid ja nupud
        for label in self.labels:
            label.draw(screen)
        for slider in self.sliders:
            slider.draw(screen)
        for btn in self.buttons:
            btn.draw(screen)
