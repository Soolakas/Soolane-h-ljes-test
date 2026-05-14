import pygame
from menu.screens.base_screen import BaseScreen
from upgrade_registry import RARITY_CONFIG

# ============================================
# Uuenduste valiku kaardi seaded - Upgrade card configuration
# ============================================
CARD_WIDTH = 300          # Kaardi laius - Card width
CARD_HEIGHT = 350         # Kaardi kõrgus - Card height
CARD_GAP = 30             # Vahe kaartide vahel - Gap between cards
BORDER_WIDTH = 4          # Äärise laius - Border width
HEAL_BUTTON_WIDTH = 350   # Tervise nupu laius - Heal button width (sideways card)
HEAL_BUTTON_HEIGHT = 300  # Tervise nupu kõrgus - Heal button height


class UpgradeCard:
    """Uuenduse kaart nupuna - Upgrade card as a clickable button."""

    def __init__(self, upgrade, position, size, callback):
        """Algustab uuenduse kaardi.
        
        Args:
            upgrade (dict): Uuenduse dictionary - Upgrade dictionary.
            position (tuple): (x, y) asukoht ekraanil - Screen position.
            size (tuple): (width, height) suurus - Card size.
            callback (function): Tagasihelistamine klikkimisel - Click callback.
        """
        self.upgrade = upgrade
        self.position = pygame.Vector2(position)
        self.size = pygame.Vector2(size)
        self.callback = callback
        self._hovered = False
        self._font_title = pygame.font.SysFont(None, 32)
        self._font_desc = pygame.font.SysFont(None, 22)
        self._font_rarity = pygame.font.SysFont(None, 20)

    @property
    def rect(self):
        """Tagastab kaardi ristkülikuna - Returns card as a Rect."""
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            int(self.size.x), int(self.size.y),
        )

    def handle_event(self, event):
        """Töötleb hiire sündmuse - Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, screen):
        """Joonistab uuenduse kaardi - Draw the upgrade card."""
        rect = self.rect
        rarity = self.upgrade.get("rarity", "common")
        config = RARITY_CONFIG.get(rarity, RARITY_CONFIG["common"])

        # Taustavärv - Background color
        bg_color = (35, 35, 55)
        if self._hovered:
            bg_color = (50, 50, 75)

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)

        # Rariteedi ääris - Rarity border
        border_color = config["border"]
        pygame.draw.rect(screen, border_color, rect, BORDER_WIDTH, border_radius=8)

        # Rariteedi silt - Rarity label
        rarity_text = self._font_rarity.render(config["label"].upper(), True, config["color"])
        rarity_rect = rarity_text.get_rect(centerx=rect.centerx, top=rect.y + 12)
        screen.blit(rarity_text, rarity_rect)

        # Uuenduse nimi - Upgrade name
        name_text = self._font_title.render(self.upgrade["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(centerx=rect.centerx, top=rarity_rect.bottom + 10)
        screen.blit(name_text, name_rect)

        # Kirjeldus (pakitud mitmele reale) - Description (wrapped)
        desc_font = self._font_desc
        desc_text = self.upgrade.get("description", "")
        self._draw_wrapped_text(screen, desc_text, desc_font, (180, 180, 200),
                                rect.centerx, name_rect.bottom + 15, rect.width - 40)

    def _draw_wrapped_text(self, screen, text, font, color, center_x, start_y, max_width):
        """Joonistab teksti mitmele reale - Draw text wrapped across multiple lines."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_surf = font.render(test_line, True, color)
            if test_surf.get_width() > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        y = start_y
        for line in lines:
            surf = font.render(line, True, color)
            rect = surf.get_rect(centerx=center_x, top=y)
            screen.blit(surf, rect)
            y += rect.height + 4


class HealButton:
    """Tervise taastamise nupp - Heal button as a clickable button."""

    def __init__(self, position, size, callback):
        """Algustab tervise nupu.
        
        Args:
            position (tuple): (x, y) asukoht ekraanil - Screen position.
            size (tuple): (width, height) suurus - Button size.
            callback (function): Tagasihelistamine klikkimisel - Click callback.
        """
        self.position = pygame.Vector2(position)
        self.size = pygame.Vector2(size)
        self.callback = callback
        self._hovered = False
        self._font_title = pygame.font.SysFont(None, 36)
        self._font_desc = pygame.font.SysFont(None, 24)

    @property
    def rect(self):
        """Tagastab nupu ristkülikuna - Returns button as a Rect."""
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            int(self.size.x), int(self.size.y),
        )

    def handle_event(self, event):
        """Töötleb hiire sündmuse - Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, screen, heal_amount):
        """Joonistab tervise nupu - Draw the heal button."""
        rect = self.rect

        # Taustavärv - Background color (green tint for healing)
        bg_color = (30, 55, 35)
        if self._hovered:
            bg_color = (45, 75, 50)

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)

        # Roheline ääris - Green border
        border_color = (50, 180, 80)
        pygame.draw.rect(screen, border_color, rect, BORDER_WIDTH, border_radius=8)

        # Pealkiri - Title
        title_text = self._font_title.render("RESTORE HEALTH", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=rect.centerx, top=rect.y + 30)
        screen.blit(title_text, title_rect)

        # Tervise kogus - Heal amount
        amount_text = self._font_title.render(f"+{heal_amount} HP", True, (80, 255, 120))
        amount_rect = amount_text.get_rect(centerx=rect.centerx, top=title_rect.bottom + 20)
        screen.blit(amount_text, amount_rect)

        # Kirjeldus - Description
        desc_text = f"Restores {heal_amount} health points"
        desc_font = self._font_desc
        self._draw_wrapped_text(screen, desc_text, desc_font, (150, 220, 170),
                                rect.centerx, amount_rect.bottom + 20, rect.width - 40)

    def _draw_wrapped_text(self, screen, text, font, color, center_x, start_y, max_width):
        """Joonistab teksti mitmele reale - Draw text wrapped across multiple lines."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_surf = font.render(test_line, True, color)
            if test_surf.get_width() > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        y = start_y
        for line in lines:
            surf = font.render(line, True, color)
            rect = surf.get_rect(centerx=center_x, top=y)
            screen.blit(surf, rect)
            y += rect.height + 4


class UpgradeSelectionScreen(BaseScreen):
    """Uuenduste valiku ekraan - Upgrade selection screen.
    
    Kuvab kolm uuendust mängijale valimiseks.
    Shows three upgrade choices for the player to select from.
    """

    def __init__(self, state_manager, settings, upgrade_manager):
        """Algustab uuenduste valiku ekraani.
        
        Args:
            state_manager: Olekuhaldur - State manager.
            settings: Mängu seaded - Game settings.
            upgrade_manager: Uuenduste haldur - Upgrade manager.
        """
        super().__init__(state_manager, settings)
        self.upgrade_manager = upgrade_manager
        self.cards = []                       # Uuenduse kaardid - Upgrade cards
        self._heal_button = None              # Tervise nupp - Heal button
        self._title_font = pygame.font.SysFont(None, 56)
        self._subtitle_font = pygame.font.SysFont(None, 28)
        self._on_upgrade_selected = None      # Tagasihelistamine - Callback
        self._on_heal = None                  # Tervise tagasihelistamine - Heal callback
        self._time_without_hit = 0.0          # Aeg ilma tabamuseta - Time without hit
        self._time_spent_alive = 0.0          # Kulutatud aeg - Time spent alive
        self._selection_cooldown = 0.5        # Valiku viivitus sekundites - Selection delay in seconds
        self._cooldown_remaining = 0.0        # Järelejäänud viivitus - Remaining cooldown
        self._build_ui()

    def reset_cooldown(self):
        """Lähtesta valiku viivitus - Reset selection cooldown (called when choices are generated)."""
        self._cooldown_remaining = self._selection_cooldown

    def set_time_without_hit(self, time_val):
        """Seab aja ilma tabamuseta - Set time without hit for display."""
        self._time_without_hit = time_val

    def set_time_spent_alive(self, time_val):
        """Seab kulutatud aja - Set time spent alive for display."""
        self._time_spent_alive = time_val

    def set_callback(self, callback):
        """Seab tagasihelistamise uuenduse valimisel - Set upgrade selection callback."""
        self._on_upgrade_selected = callback

    def set_heal_callback(self, callback):
        """Seab tervise taastamise tagasihelistamise - Set heal callback."""
        self._on_heal = callback

    def _get_heal_amount(self):
        """Arvuta tervise kogus aja põhjal - Calculate heal amount based on time spent alive."""
        total_seconds = int(self._time_spent_alive)
        if total_seconds >= 150:
            return 4
        elif total_seconds >= 120:
            return 3
        elif total_seconds >= 90:
            return 2
        else:
            return 1

    def _build_ui(self):
        """Loob uuenduse kaardid ja tervise nupu - Build upgrade cards and heal button."""
        choices = self.upgrade_manager.pending_choices
        if not choices:
            self.cards = []
            self._heal_button = None
            return

        screen_w, screen_h = 1280, 720

        # Arvuta kaartide asukohad - Calculate card positions
        total_width = len(choices) * CARD_WIDTH + (len(choices) - 1) * CARD_GAP
        start_x = (screen_w - total_width) / 2
        card_y = (screen_h - CARD_HEIGHT) / 2 - 30

        self.cards = []
        for idx, upgrade in enumerate(choices):
            card_x = start_x + idx * (CARD_WIDTH + CARD_GAP)
            card = UpgradeCard(
                upgrade,
                (card_x, card_y),
                (CARD_WIDTH, CARD_HEIGHT),
                callback=self._make_callback(idx),
            )
            self.cards.append(card)

        # Loo tervise nupp kaartide alla - Create heal button below cards
        heal_x = (screen_w - HEAL_BUTTON_WIDTH) / 2
        heal_y = card_y + CARD_HEIGHT + 30
        self._heal_button = HealButton(
            (heal_x, heal_y),
            (HEAL_BUTTON_WIDTH, HEAL_BUTTON_HEIGHT),
            callback=self._make_heal_callback(),
        )

    def _make_callback(self, index):
        """Loob tagasihelistamise konkreetse kaardi jaoks - Create callback for a specific card."""
        def on_click():
            if self._on_upgrade_selected:
                self._on_upgrade_selected(index)
        return on_click

    def _make_heal_callback(self):
        """Loob tagasihelistamise tervise nupu jaoks - Create callback for heal button."""
        def on_click():
            if self._on_heal:
                self._on_heal()
        return on_click

    def handle_events(self, events):
        """Töötleb sisendsündmuseid - Handle input events."""
        # Ignore events during cooldown - prevents accidental clicks
        if self._cooldown_remaining > 0:
            return
        for event in events:
            for card in self.cards:
                card.handle_event(event)
            if self._heal_button:
                self._heal_button.handle_event(event)

    def update(self, dt):
        """Uuendab ekraani olekut - Update screen state."""
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= dt

    def draw(self, screen):
        """Joonistab valiku ekraani - Draw the selection screen."""
        # Läbipaistev tumedus kiht - Transparent dark overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()

        # Pealkiri - Title
        title_surf = self._title_font.render("CHOOSE AN UPGRADE", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_w / 2, screen_h * 0.15))
        screen.blit(title_surf, title_rect)

        # Aeg elus - Time spent alive
        alive_total_seconds = int(self._time_spent_alive)
        alive_minutes = alive_total_seconds // 60
        alive_seconds = alive_total_seconds % 60
        alive_text = f"Time spent alive: {alive_minutes}:{alive_seconds:02d}"
        alive_surf = self._subtitle_font.render(alive_text, True, (200, 200, 230))
        alive_rect = alive_surf.get_rect(center=(screen_w / 2, title_rect.bottom + 15))
        screen.blit(alive_surf, alive_rect)

        # Kuva viivituse indikaator - Show cooldown indicator
        if self._cooldown_remaining > 0:
            wait_text = f"Choosing... {self._cooldown_remaining:.1f}s"
            wait_surf = self._subtitle_font.render(wait_text, True, (255, 200, 50))
            wait_rect = wait_surf.get_rect(center=(screen_w / 2, alive_rect.bottom + 20))
            screen.blit(wait_surf, wait_rect)

        # Kaardid - Cards
        for card in self.cards:
            card.draw(screen)

        # Tervise nupp - Heal button
        if self._heal_button:
            heal_amount = self._get_heal_amount()
            self._heal_button.draw(screen, heal_amount)
