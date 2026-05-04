import pygame


class UIButton:
    """Korduvkasutatav nupp, millel on hiire kohaloleku ja klikkimise visuaalsed olekud.
    Reusable clickable button with hover and click visual states."""

    def __init__(
        self,
        text,
        position,
        size,
        callback,
        font_size=28,
        bg_color=(50, 50, 70),
        hover_color=(70, 70, 100),
        text_color=(255, 255, 255),
        border_color=(120, 120, 160),
        border_width=2,
    ):
        self.text = text                          # Nupu tekst
        self.position = pygame.Vector2(position)   # Asukoht ekraanil
        self.size = pygame.Vector2(size)           # Suurus (laius, kõrgus)
        self.callback = callback                   # Funktsioon, mida kutsutakse klikkimisel
        self.font_size = font_size                 # Teksti suurus
        self.bg_color = bg_color                   # Taustavärv
        self.hover_color = hover_color             # Värv kui hiir on nupu kohal
        self.text_color = text_color               # Teksti värv
        self.border_color = border_color           # Äärise värv
        self.border_width = border_width           # Äärise laius
        self._hovered = False                      # Kas hiir on nupu kohal
        self._font = pygame.font.SysFont(None, font_size)

    @property
    def rect(self):
        """Tagastab nupu ristkülikuna (Pygame Rect)."""
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            int(self.size.x), int(self.size.y),
        )

    def handle_event(self, event):
        """Töötleb sündmuse. Tagastab True, kui nuppu klikiti."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, screen):
        """Joonistab nupu antud pinnale."""
        color = self.hover_color if self._hovered else self.bg_color
        rect = self.rect
        pygame.draw.rect(screen, color, rect, border_radius=6)
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, rect, self.border_width, border_radius=6)
        text_surf = self._font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def update_size(self, new_size):
        """Uuendab nupu suurust."""
        self.size = pygame.Vector2(new_size)
