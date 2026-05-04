import pygame


class UIPanel:
    """Container panel with background, border, and child elements."""

    def __init__(self, position, size, bg_color=(30, 30, 50), border_color=(80, 80, 120), border_width=2):
        self.position = pygame.Vector2(position)
        self.size = pygame.Vector2(size)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.children = []

    @property
    def rect(self):
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            int(self.size.x), int(self.size.y),
        )

    def add_child(self, child):
        self.children.append(child)

    def handle_events(self, events):
        for event in events:
            for child in self.children:
                if hasattr(child, "handle_event"):
                    child.handle_event(event)

    def draw(self, screen):
        rect = self.rect
        pygame.draw.rect(screen, self.bg_color, rect, border_radius=8)
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, rect, self.border_width, border_radius=8)
        for child in self.children:
            child.draw(screen)
