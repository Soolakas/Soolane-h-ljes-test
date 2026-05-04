import math
import os
import pygame


BACKGROUND = (2, 3, 14)
GRID_COLOR = (10, 70, 95)
GRID_ACCENT = (28, 160, 190)
PLAYER_COLOR = (80, 245, 255)
PROJECTILE_COLOR = (255, 235, 70)
PLAYER_SHEET_PATH = os.path.join("assets", "imported", "tiny-spaceships", "tinyShip3.png")
PLAYER_SHEET_COLUMNS = 5
PLAYER_SHEET_ROWS = 2
TRAIL_FRAME_DIR = os.path.join("assets", "imported", "pixel-fire-trail")
_asset_cache = {}


def _screen_pos(world_pos, camera_offset):
    return (
        int(world_pos.x - camera_offset.x),
        int(world_pos.y - camera_offset.y),
    )


def _dim(color, amount):
    return tuple(max(0, min(255, int(channel * amount))) for channel in color)


def _asset_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)


def _load_player_sprite():
    if "player_sprite" not in _asset_cache:
        sheet = pygame.image.load(_asset_path(PLAYER_SHEET_PATH)).convert_alpha()
        frame_width = sheet.get_width() // PLAYER_SHEET_COLUMNS
        frame_height = sheet.get_height() // PLAYER_SHEET_ROWS
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), pygame.Rect(0, 0, frame_width, frame_height))
        _asset_cache["player_sprite"] = frame

    return _asset_cache["player_sprite"]


def _trail_frame_number(filename):
    stem = os.path.splitext(filename)[0]
    if "_" not in stem:
        return -1
    return int(stem.rsplit("_", 1)[1])


def _crop_visible(surface):
    bounds = surface.get_bounding_rect()
    if bounds.width == 0 or bounds.height == 0:
        return surface

    cropped = pygame.Surface(bounds.size, pygame.SRCALPHA)
    cropped.blit(surface, (0, 0), bounds)
    return cropped


def _load_trail_frames():
    if "trail_frames" not in _asset_cache:
        frame_dir = _asset_path(TRAIL_FRAME_DIR)
        frame_names = [
            name for name in os.listdir(frame_dir)
            if name.lower().endswith(".png") and "_" in name
        ]
        frame_names.sort(key=_trail_frame_number)
        _asset_cache["trail_frames"] = [
            pygame.transform.rotate(_crop_visible(
                pygame.image.load(os.path.join(frame_dir, name)).convert_alpha()
            ), 90)
            for name in frame_names
        ]

    return _asset_cache["trail_frames"]


def _draw_glow_line(surface, color, start, end, width=2):
    start = (int(start[0]), int(start[1]))
    end = (int(end[0]), int(end[1]))
    pygame.draw.line(surface, _dim(color, 0.18), start, end, width + 10)
    pygame.draw.line(surface, _dim(color, 0.35), start, end, width + 5)
    pygame.draw.line(surface, color, start, end, width)


def draw_background(surface, camera_offset):
    surface.fill(BACKGROUND)

    width = surface.get_width()
    height = surface.get_height()
    grid_size = 96
    accent_size = grid_size * 4
    offset_x = int(-camera_offset.x % grid_size)
    offset_y = int(-camera_offset.y % grid_size)
    accent_x = int(-camera_offset.x % accent_size)
    accent_y = int(-camera_offset.y % accent_size)

    for x in range(offset_x - grid_size, width + grid_size, grid_size):
        pygame.draw.line(surface, _dim(GRID_COLOR, 0.55), (x, 0), (x, height), 1)
    for y in range(offset_y - grid_size, height + grid_size, grid_size):
        pygame.draw.line(surface, _dim(GRID_COLOR, 0.55), (0, y), (width, y), 1)

    for x in range(accent_x - accent_size, width + accent_size, accent_size):
        pygame.draw.line(surface, _dim(GRID_ACCENT, 0.35), (x, 0), (x, height), 1)
    for y in range(accent_y - accent_size, height + accent_size, accent_size):
        pygame.draw.line(surface, _dim(GRID_ACCENT, 0.35), (0, y), (width, y), 1)


def draw_projectile(surface, projectile, camera_offset):
    pos = projectile["pos"]
    vel = projectile["vel"]
    if vel.length() == 0:
        return

    direction = vel.normalize()
    head = pygame.Vector2(_screen_pos(pos, camera_offset))
    tail = head - direction * 20
    _draw_glow_line(surface, PROJECTILE_COLOR, tail, head, 3)


def draw_player_trail(surface, trail, current_pos, lifetime, camera_offset, width):
    if not trail:
        return

    frames = _load_trail_frames()
    if not frames:
        return

    points = [(pygame.Vector2(_screen_pos(pos, camera_offset)), age) for pos, age in trail]
    points.append((pygame.Vector2(_screen_pos(current_pos, camera_offset)), 0.0))
    frame_offset = int(pygame.time.get_ticks() / 60)

    for segment_idx, ((start, start_age), (end, end_age)) in enumerate(zip(points, points[1:])):
        segment = end - start
        length = segment.length()
        if length < 2:
            continue

        fade = max(0.0, 1 - ((start_age + end_age) * 0.5) / lifetime)
        frame = frames[(frame_offset + segment_idx) % len(frames)]
        scaled = pygame.transform.smoothscale(frame, (max(6, int(length + 10)), width * 3))
        scaled.set_alpha(int(165 * fade))
        angle = -math.degrees(math.atan2(segment.y, segment.x))
        rotated = pygame.transform.rotate(scaled, angle)
        midpoint = (start + end) * 0.5
        rect = rotated.get_rect(center=(int(midpoint.x), int(midpoint.y)))
        surface.blit(rotated, rect)


def draw_health_square(surface, x, y, size, filled):
    color = (255, 70, 95) if filled else (22, 30, 48)
    outline = (255, 150, 165) if filled else (65, 95, 120)
    rect = pygame.Rect(x, y, size, size)

    if filled:
        pygame.draw.rect(surface, _dim(color, 0.22), rect.inflate(10, 10), 2)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, outline, rect, 2)


def draw_player_sprite(surface, pos, angle, radius, camera_offset, invulnerable=False):
    sprite = _load_player_sprite()
    target_height = radius * 3.0
    scale = target_height / sprite.get_height()
    rotated = pygame.transform.rotozoom(sprite, -angle, scale)

    if invulnerable and int(pygame.time.get_ticks() / 120) % 2 == 0:
        rotated.set_alpha(95)
    else:
        rotated.set_alpha(255)

    center = _screen_pos(pos, camera_offset)
    rect = rotated.get_rect(center=center)
    surface.blit(rotated, rect)
