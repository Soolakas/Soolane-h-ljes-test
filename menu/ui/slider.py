import pygame


class UISlider:
    """Lohistatav liugur arvväärtuste muutmiseks. Draggable slider for adjusting numeric values."""

    def __init__(
        self,
        position,
        width,
        value,
        min_val=0.0,
        max_val=1.0,
        label="",
        callback=None,
        track_color=(60, 60, 80),
        fill_color=(100, 100, 180),
        handle_color=(200, 200, 255),
        text_color=(255, 255, 255),
        font_size=20,
    ):
        self.position = pygame.Vector2(position)   # Asukoht ekraanil
        self.width = width                           # Liuguririba laius
        self.value = value                           # Praegune väärtus
        self.min_val = min_val                       # Minimaalne väärtus
        self.max_val = max_val                       # Maksimaalne väärtus
        self.label = label                           # Sildi tekst (nt "Music Volume")
        self.callback = callback                     # Funktsioon, mida kutsutakse väärtuse muutmisel
        self.track_color = track_color               # Riba taustavärv
        self.fill_color = fill_color                 # Täidetud osa värv
        self.handle_color = handle_color             # Nupu (käepideme) värv
        self.text_color = text_color                 # Teksti värv
        self.font_size = font_size                   # Teksti suurus
        self._dragging = False                       # Kas kasutaja parasjagu lohistab
        self._font = pygame.font.SysFont(None, font_size)
        self._handle_radius = 8                      # Käepideme raadius
        self._track_height = 10                      # Riba kõrgus

    @property
    def _track_rect(self):
        """Tagastab liuguririba ristkülikuna."""
        return pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.width,
            self._track_height,
        )

    def _value_to_x(self):
        """Teisendab praeguse väärtuse ekraani X-koordinaadiks."""
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.position.x + ratio * self.width

    def _x_to_value(self, x):
        """Teisendab X-koordinaadi tagasi väärtuseks."""
        ratio = (x - self.position.x) / self.width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def handle_event(self, event):
        """Töötleb hiire sündmuse. Tagastab True, kui liugurit muudeti."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_x = self._value_to_x()
            handle_rect = pygame.Rect(
                int(handle_x - self._handle_radius),
                int(self.position.y - self._handle_radius + self._track_height / 2),
                self._handle_radius * 2,
                self._handle_radius * 2,
            )
            if handle_rect.collidepoint(event.pos):
                self._dragging = True
                return True
            if self._track_rect.collidepoint(event.pos):
                self.value = self._x_to_value(event.pos[0])
                self._dragging = True
                if self.callback:
                    self.callback(self.value)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self.value = self._x_to_value(event.pos[0])
            if self.callback:
                self.callback(self.value)
            return True
        return False

    def draw(self, screen):
        """Joonistab liuguri: riba, täidetud osa, käepideme ja sildi."""
        track = self._track_rect
        pygame.draw.rect(screen, self.track_color, track, border_radius=5)

        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        fill_rect = pygame.Rect(track.x, track.y, fill_width, track.height)
        if fill_width > 0:
            pygame.draw.rect(screen, self.fill_color, fill_rect, border_radius=5)

        handle_x = self._value_to_x()
        handle_y = self.position.y + self._track_height / 2
        pygame.draw.circle(screen, self.handle_color, (int(handle_x), int(handle_y)), self._handle_radius)

        if self.label:
            value_text = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            display = f"{self.label}: {value_text}"
            text_surf = self._font.render(display, True, self.text_color)
            screen.blit(text_surf, (track.x, track.y - self.font_size - 4))
