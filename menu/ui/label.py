import pygame


class UILabel:
    """Staatiline tekstisilt. Static text label."""

    def __init__(self, text, position, font_size=24, color=(255, 255, 255), center=False):
        self.text = text                              # Kuvatav tekst
        self.position = pygame.Vector2(position)       # Asukoht ekraanil
        self.font_size = font_size                     # Teksti suurus
        self.color = color                             # Teksti värv
        self.center = center                           # Kas tekst on tsentreeritud
        self._font = pygame.font.SysFont(None, font_size)

    def set_text(self, text):
        """Uuendab sildi teksti."""
        self.text = text

    def draw(self, screen):
        """Joonistab tekstisildi antud pinnale."""
        text_surf = self._font.render(self.text, True, self.color)
        if self.center:
            rect = text_surf.get_rect(center=(int(self.position.x), int(self.position.y)))
        else:
            rect = text_surf.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        screen.blit(text_surf, rect)
