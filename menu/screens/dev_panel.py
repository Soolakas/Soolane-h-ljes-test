import pygame
from menu.ui.button import UIButton
from menu.ui.label import UILabel
from upgrade_registry import UPGRADES, Rarity, RARITY_CONFIG

# ============================================
# Developer mode settings - Arendaja režiimi seaded
# ============================================
DEV_PANEL_WIDTH = 320
DEV_PANEL_HEIGHT = 500
DEV_PANEL_X = 1280 - DEV_PANEL_WIDTH - 20  # Top-right corner
DEV_PANEL_Y = 20
DEV_BUTTON_HEIGHT = 35
DEV_BUTTON_GAP = 8

# Submenu for upgrade selection
SUBMENU_WIDTH = 300
SUBMENU_HEIGHT = 400


class DevPanel:
    """Arendaja režiimi paneel - Developer mode panel for playtesting."""

    def __init__(self, sound_manager=None):
        self.active = False                    # Kas paneel on aktiivne - Is panel active
        self.sound_manager = sound_manager     # Helihaldur - Sound manager
        self.buttons = []                      # Peamised nupud - Main buttons
        self.labels = []                       # Sildid - Labels
        self._font = pygame.font.SysFont(None, 20)
        self._small_font = pygame.font.SysFont(None, 16)
        self._title_font = pygame.font.SysFont(None, 28)
        self.show_info = False                 # Kas info on kuvatud - Is info overlay shown
        self.show_submenu = False              # Kas alamenuu on avatud - Is submenu open
        self.submenu_buttons = []              # Alamenuu nupud - Submenu buttons
        self.submenu_scroll = 0                # Alamenuu kerimine - Submenu scroll
        self.invulnerable = False              # Kas mängija on haavamatu - Is player invincible
        self._build_buttons()

    def toggle(self):
        """Lülita arendaja režiim sisse/välja - Toggle dev mode on/off."""
        self.active = not self.active
        if not self.active:
            self.show_submenu = False
            self.show_info = False

    def set_callback(self, callback_name, callback):
        """Seab tagasihelistamise - Set callback for dev actions."""
        if not hasattr(self, '_callbacks'):
            self._callbacks = {}
        self._callbacks[callback_name] = callback

    def _build_buttons(self):
        """Loob arendaja paneeli nupud - Build dev panel buttons."""
        self.buttons = []
        x = DEV_PANEL_X + 15
        y = DEV_PANEL_Y + 50

        button_configs = [
            ("INVINCIBLE: OFF", self._on_toggle_invincible),
            ("GRANT UPGRADE", self._on_grant_upgrade),
            ("SHOW INFO: OFF", self._on_toggle_info),
            ("SKIP +30s", self._on_skip_30),
            ("SKIP +60s", self._on_skip_60),
            ("SKIP +5min", self._on_skip_5min),
            ("KILL ALL ENEMIES", self._on_kill_all),
            ("RESET RUN", self._on_reset),
            ("CLOSE", self._on_close),
        ]

        for text, callback in button_configs:
            btn = UIButton(text, (x, y), (DEV_PANEL_WIDTH - 30, DEV_BUTTON_HEIGHT),
                          callback=callback, font_size=18)
            if text == "CLOSE":
                btn.bg_color = (80, 40, 40)
                btn.hover_color = (110, 50, 50)
            self.buttons.append(btn)
            y += DEV_BUTTON_HEIGHT + DEV_BUTTON_GAP

    def _on_toggle_invincible(self):
        self.invulnerable = not self.invulnerable
        self.buttons[0].text = f"INVINCIBLE: {'ON' if self.invulnerable else 'OFF'}"
        if hasattr(self, '_callbacks') and 'toggle_invincible' in self._callbacks:
            self._callbacks['toggle_invincible'](self.invulnerable)

    def _on_grant_upgrade(self):
        self.show_submenu = not self.show_submenu
        if self.show_submenu:
            self._build_submenu()

    def _on_toggle_info(self):
        self.show_info = not self.show_info
        self.buttons[2].text = f"SHOW INFO: {'ON' if self.show_info else 'OFF'}"

    def _on_skip_30(self):
        if hasattr(self, '_callbacks') and 'skip_time' in self._callbacks:
            self._callbacks['skip_time'](30)

    def _on_skip_60(self):
        if hasattr(self, '_callbacks') and 'skip_time' in self._callbacks:
            self._callbacks['skip_time'](60)

    def _on_skip_5min(self):
        if hasattr(self, '_callbacks') and 'skip_time' in self._callbacks:
            self._callbacks['skip_time'](300)

    def _on_kill_all(self):
        if hasattr(self, '_callbacks') and 'kill_all' in self._callbacks:
            self._callbacks['kill_all']()

    def _on_reset(self):
        if hasattr(self, '_callbacks') and 'reset' in self._callbacks:
            self._callbacks['reset']()

    def _on_close(self):
        self.active = False
        self.show_submenu = False
        self.show_info = False

    def _build_submenu(self):
        """Loob uuenduste alamenuu - Build upgrade selection submenu."""
        self.submenu_buttons = []
        x = DEV_PANEL_X + 20
        y = DEV_PANEL_Y + 60

        # Group upgrades by rarity
        for rarity in Rarity.ALL:
            config = RARITY_CONFIG[rarity]
            rarity_upgrades = [u for u in UPGRADES if u.get("rarity") == rarity]
            if not rarity_upgrades:
                continue

            # Rarity header
            self.submenu_buttons.append({
                "type": "header",
                "text": config["label"].upper(),
                "color": config["color"],
                "rect": pygame.Rect(x, y, SUBMENU_WIDTH - 20, 25),
            })
            y += 30

            for upgrade in rarity_upgrades:
                btn = UIButton(upgrade["name"], (x, y), (SUBMENU_WIDTH - 20, 28),
                              callback=self._make_upgrade_callback(upgrade), font_size=15)
                btn.bg_color = (40, 40, 60)
                btn.hover_color = (60, 60, 90)
                self.submenu_buttons.append({"type": "button", "button": btn, "upgrade": upgrade})
                y += 32

        # Back button
        back_btn = UIButton("BACK", (x, y), (SUBMENU_WIDTH - 20, 28),
                           callback=self._on_back_from_submenu, font_size=15)
        back_btn.bg_color = (80, 40, 40)
        self.submenu_buttons.append({"type": "button", "button": back_btn, "upgrade": None})

    def _make_upgrade_callback(self, upgrade):
        """Loob tagasihelistamise uuenduse andmiseks - Create callback for granting upgrade."""
        def on_click():
            if hasattr(self, '_callbacks') and 'grant_upgrade' in self._callbacks:
                self._callbacks['grant_upgrade'](upgrade)
        return on_click

    def _on_back_from_submenu(self):
        self.show_submenu = False

    def set_upgrade_counts(self, upgrade_counts):
        """Seab uuenduste loendused kuvamiseks - Set upgrade counts for display."""
        self._upgrade_counts = upgrade_counts

    def handle_events(self, events):
        """Töötleb sisendsündmuseid - Handle input events."""
        if not self.active:
            return

        if self.show_submenu:
            for event in events:
                for item in self.submenu_buttons:
                    if item["type"] == "button":
                        item["button"].handle_event(event)
        else:
            for event in events:
                for btn in self.buttons:
                    btn.handle_event(event)

    def update(self, dt):
        """Uuendab paneeli olekut - Update panel state."""
        pass

    def draw(self, screen):
        """Joonistab arendaja paneeli - Draw dev panel."""
        if not self.active:
            return

        # Taust - Background
        panel_rect = pygame.Rect(DEV_PANEL_X, DEV_PANEL_Y, DEV_PANEL_WIDTH, DEV_PANEL_HEIGHT)
        pygame.draw.rect(screen, (20, 20, 40), panel_rect, border_radius=8)
        pygame.draw.rect(screen, (80, 80, 120), panel_rect, 2, border_radius=8)

        # Pealkiri - Title
        title_surf = self._title_font.render("DEV MODE", True, (255, 255, 100))
        title_rect = title_surf.get_rect(centerx=panel_rect.centerx, top=DEV_PANEL_Y + 10)
        screen.blit(title_surf, title_rect)

        if self.show_submenu:
            self._draw_submenu(screen)
        else:
            for btn in self.buttons:
                btn.draw(screen)

    def _draw_submenu(self, screen):
        """Joonistab alamenuu - Draw submenu."""
        panel_rect = pygame.Rect(DEV_PANEL_X + 10, DEV_PANEL_Y + 10, SUBMENU_WIDTH, SUBMENU_HEIGHT)
        pygame.draw.rect(screen, (25, 25, 50), panel_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 150), panel_rect, 2, border_radius=8)

        title_surf = self._title_font.render("GRANT UPGRADE", True, (255, 255, 100))
        title_rect = title_surf.get_rect(centerx=panel_rect.centerx, top=DEV_PANEL_Y + 20)
        screen.blit(title_surf, title_rect)

        for item in self.submenu_buttons:
            if item["type"] == "header":
                surf = self._font.render(item["text"], True, item["color"])
                screen.blit(surf, item["rect"])
            elif item["type"] == "button":
                item["button"].draw(screen)

    def draw_info_overlay(self, screen, player_stats, difficulty_manager, enemies, game_time, upgrade_counts):
        """Joonistab info ülekate - Draw info overlay."""
        if not self.active or not self.show_info:
            return

        lines = [
            "=== DEVELOPER INFO ===",
            f"Time: {difficulty_manager.get_elapsed_time()}",
            "--- Player Stats ---",
            f"Speed: {player_stats.get('speed_multiplier', 1.0):.2f}x",
            f"Fire Rate: {player_stats.get('fire_rate_multiplier', 1.0):.2f}x",
            f"Crit Chance: {player_stats.get('crit_chance', 0.0)*100:.0f}%",
            f"Accuracy: {player_stats.get('accuracy', 0)}/2",
            f"Knockback: {player_stats.get('knockback_force', 0):.0f}",
            f"Poison: {player_stats.get('poison_chance', 0.0)*100:.0f}% / {player_stats.get('poison_damage', 0.0):.1f} HP/s",
            f"Bounces: {player_stats.get('max_bounces', 0)}",
            f"Random Bullet: {player_stats.get('random_bullet_chance', 0.0)*100:.0f}%",
            f"Dashes: {player_stats.get('dash_count', 0)}",
            f"Proximity DMG: +{player_stats.get('proximity_damage_bonus', 0.0)*100:.0f}%",
            f"Cactus: {player_stats.get('cactus_armor_stacks', 0)}",
            "--- Difficulty ---",
            f"Spawn Interval: {difficulty_manager.get_spawn_interval():.1f}s",
            f"Wave Size: {difficulty_manager.get_wave_size()[0]}-{difficulty_manager.get_wave_size()[1]}",
            f"Health Bonus: +{difficulty_manager.get_enemy_health_bonus()}",
            f"Speed Multiplier: {difficulty_manager.get_enemy_speed_multiplier():.2f}x",
            f"Enemy Count: {len(enemies)}",
            "--- Upgrades Owned ---",
        ]

        # Add upgrade counts
        for upgrade_id, count in upgrade_counts.items():
            lines.append(f"  {upgrade_id}: x{count}")

        y = 50
        font = pygame.font.SysFont(None, 18)
        for line in lines:
            surf = font.render(line, True, (200, 200, 255))
            screen.blit(surf, (50, y))
            y += 20
