import pygame


class UIPanel:
    """Konteineripaneel tausta, äärise ja lapselementidega.
    Container panel with background, border, and child elements."""

    def __init__(self, position, size, bg_color=(30, 30, 50), border_color=(80, 80, 120), border_width=2):
        self.position = pygame.Vector2(position)   # Asukoht ekraanil
        self.size = pygame.Vector2(size)           # Suurus (laius, kõrgus)
        self.bg_color = bg_color                   # Taustavärv
        self.border_color = border_color           # Äärise värv
        self.border_width = border_width           # Äärise laius
        self.children = []                         # Lapselemendid (nupud, sildid jne)

    @property
    def rect(self):
        """Tagastab paneeli ristkülikuna."""
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            int(self.size.x), int(self.size.y),
        )

    def add_child(self, child):
        """Lisab lapselemendi paneelile."""
        self.children.append(child)

    def handle_events(self, events):
        """Edastab sündmused kõigile lapselementidele."""
        for event in events:
            for child in self.children:
                if hasattr(child, "handle_event"):
                    child.handle_event(event)

    def draw(self, screen):
        """Joonistab paneeli tausta, äärise ja kõik lapselemendid."""
        rect = self.rect
        pygame.draw.rect(screen, self.bg_color, rect, border_radius=8)
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, rect, self.border_width, border_radius=8)
        for child in self.children:
            child.draw(screen)
