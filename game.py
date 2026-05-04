import pygame
import math
import random

from enemy import Enemy
from spawn_manager import SpawnManager
from difficulty_manager import DifficultyManager
from vfx_manager import VFXManager
from menu.state_manager import StateManager, GameState
from menu.screens.main_menu import MainMenuScreen
from menu.screens.settings import SettingsScreen
from menu.screens.upgrades import UpgradesScreen
from menu.screens.pause import PauseScreen
from menu.screens.game_over import GameOverScreen
from config.settings_store import GameSettings

# ============================================
# pygame setup - Pygame seadistus
# ============================================
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

# ============================================
# Settings and state manager
# ============================================
settings = GameSettings()
state_manager = StateManager()

# ============================================
# Map configuration - Kaardi seaded
# ============================================
WORLD_SIZE = 3000
MAP_INSET = 300

center = WORLD_SIZE / 2
apothem = (WORLD_SIZE - 2 * MAP_INSET) / 2

map_vertices = []
for i in range(8):
    angle = math.radians(45 * i + 22.5)
    x = center + apothem * math.cos(angle)
    y = center + apothem * math.sin(angle)
    map_vertices.append((x, y))

# ============================================
# Screens
# ============================================
main_menu_screen = MainMenuScreen(state_manager, settings)
settings_screen = SettingsScreen(state_manager, settings)
upgrades_screen = UpgradesScreen(state_manager, settings)
pause_screen = PauseScreen(state_manager, settings)
game_over_screen = GameOverScreen(state_manager, settings)

screens = {
    GameState.MENU: main_menu_screen,
    GameState.SETTINGS: settings_screen,
    GameState.UPGRADES: upgrades_screen,
    GameState.PAUSED: pause_screen,
    GameState.GAME_OVER: game_over_screen,
}

# ============================================
# Camera - Kaamera seaded
# ============================================
camera_offset = pygame.Vector2(0, 0)

# ============================================
# Game state variables
# ============================================
player_pos = pygame.Vector2(center, center)
player_radius = 15
player_angle = 0
target_angle = 0
rotation_speed = 8
player_max_health = 7
player_health = player_max_health
player_invulnerable_timer = 0.0
player_invulnerable_duration = 1.0
game_over = False

player_velocity = pygame.Vector2(0, 0)
player_acceleration = 1200
player_drag = 4.0
speed_power_multiplier = 1.7
speed_power_timer = 0.0

projectiles = []
projectile_speed = 700
projectile_radius = 8

shoot_cooldown = 0.25
shoot_timer = 0
multi_shot_timer = 0.0
multi_shot_projectile_count = 3
multi_shot_spread = 18
rapid_fire_timer = 0.0
rapid_fire_multiplier = 2.0

powerups = []
powerup_radius = 13
powerup_drop_chance = 0.14
powerup_lifetime = 12.0
powerup_duration = 8.0
POWERUP_TYPES = {
    "multi_shot": {
        "color": (255, 210, 60),
        "label": "M",
    },
    "speed": {
        "color": (70, 220, 255),
        "label": "S",
    },
    "rapid_fire": {
        "color": (255, 110, 210),
        "label": "R",
    },
}

score = 0

enemies = []

difficulty_manager = DifficultyManager()
spawn_manager = SpawnManager(map_vertices, (center, center), difficulty_manager)

vfx_manager = VFXManager()

TRAIL_LIFETIME = 0.5
TRAIL_INTERVAL = 0.02
trail_timer = 0
trail = []

game_time = 0


def init_game():
    """Initialize all game variables to their starting values."""
    global player_pos, player_angle, target_angle, player_health, player_invulnerable_timer
    global game_over, player_velocity, shoot_timer, multi_shot_timer
    global speed_power_timer, rapid_fire_timer, projectiles, powerups, score
    global enemies, trail_timer, trail, game_time

    player_pos = pygame.Vector2(center, center)
    player_angle = 0
    target_angle = 0
    player_health = player_max_health
    player_invulnerable_timer = 0.0
    game_over = False

    player_velocity = pygame.Vector2(0, 0)
    shoot_timer = 0
    multi_shot_timer = 0.0
    speed_power_timer = 0.0
    rapid_fire_timer = 0.0

    projectiles = []
    powerups = []
    score = 0
    enemies = []

    trail_timer = 0
    trail = []
    game_time = 0

    difficulty_manager.elapsed_time = 0.0
    spawn_manager.spawn_timer = 0.0
    vfx_manager.particles = []


def reset_game():
    """Reset game state when returning to playing from menus."""
    init_game()


pause_screen.set_game_reset_callback(reset_game)
game_over_screen.set_restart_callback(reset_game)


# ============================================
# Utility functions - Abifunktsioonid
# ============================================

def point_in_polygon(point, vertices):
    x, y = point
    inside = False
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        if ((y1 > y) != (y2 > y)):
            xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
            if xinters > x:
                inside = not inside
    return inside


def clamp_to_map(pos, vertices, radius):
    if point_in_polygon((pos.x, pos.y), vertices):
        return pos

    min_dist = float('inf')
    closest = pos
    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            dist = math.hypot(pos.x - x1, pos.y - y1)
            if dist < min_dist:
                min_dist = dist
                closest = pygame.Vector2(x1, y1)
            continue
        t = max(0, min(1, ((pos.x - x1) * dx + (pos.y - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        dist = math.hypot(pos.x - proj_x, pos.y - proj_y)
        if dist < min_dist:
            min_dist = dist
            closest = pygame.Vector2(proj_x, proj_y)

    if min_dist > 0:
        dir_vec = pygame.Vector2(closest.x - pos.x, closest.y - pos.y).normalize()
        return closest + dir_vec * radius
    return pos


def spawn_powerup(world_pos):
    if random.random() > powerup_drop_chance:
        return

    powerup_type = random.choice(list(POWERUP_TYPES.keys()))
    powerups.append({
        "pos": pygame.Vector2(world_pos),
        "type": powerup_type,
        "age": 0.0,
    })


def create_projectile(spawn_pos, direction):
    return {
        "pos": pygame.Vector2(spawn_pos),
        "vel": direction * projectile_speed
    }


def apply_powerup(powerup_type):
    global multi_shot_timer, speed_power_timer, rapid_fire_timer

    if powerup_type == "multi_shot":
        multi_shot_timer = powerup_duration
    elif powerup_type == "speed":
        speed_power_timer = powerup_duration
    elif powerup_type == "rapid_fire":
        rapid_fire_timer = powerup_duration


def draw_health_square(surface, x, y, size, filled):
    color = (255, 70, 95) if filled else (80, 80, 80)
    outline = (255, 120, 135) if filled else (120, 120, 120)
    rect = pygame.Rect(x, y, size, size)

    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, outline, rect, 2)


def render_game_screen():
    screen.fill("black")

    pygame.draw.polygon(screen, "white", [(v[0] - camera_offset.x, v[1] - camera_offset.y) for v in map_vertices], 3)

    for enemy_unit in enemies:
        enemy_unit.draw(screen, camera_offset)

    powerup_font = pygame.font.SysFont(None, 22)
    for powerup in powerups:
        config = POWERUP_TYPES[powerup["type"]]
        screen_pos = (
            int(powerup["pos"].x - camera_offset.x),
            int(powerup["pos"].y - camera_offset.y),
        )
        pulse = 1 + 0.12 * math.sin(pygame.time.get_ticks() * 0.008)
        radius = int(powerup_radius * pulse)
        pygame.draw.circle(screen, config["color"], screen_pos, radius, 2)
        label = powerup_font.render(config["label"], True, config["color"])
        label_pos = (
            screen_pos[0] - label.get_width() / 2,
            screen_pos[1] - label.get_height() / 2,
        )
        screen.blit(label, label_pos)

    trail_radius = int(player_radius * 0.35)
    for pos, age in trail:
        screen_pos = (pos.x - camera_offset.x, pos.y - camera_offset.y)
        alpha = int(150 * (1 - age / TRAIL_LIFETIME))
        trail_surf = pygame.Surface((trail_radius * 2, trail_radius * 2))
        trail_surf.set_colorkey((0, 0, 0))
        trail_surf.set_alpha(alpha)
        pygame.draw.circle(trail_surf, (255, 255, 255), (trail_radius, trail_radius), trail_radius)
        screen.blit(trail_surf, (screen_pos[0] - trail_radius, screen_pos[1] - trail_radius))

    arrow_points = [
        (0, -player_radius),
        (-player_radius * 0.5, player_radius * 0.3),
        (0, player_radius * 0.5),
        (player_radius * 0.5, player_radius * 0.3),
    ]

    arrow_surface = pygame.Surface((player_radius * 2, player_radius * 2), pygame.SRCALPHA)
    arrow_surface_points = [
        (p[0] + player_radius, p[1] + player_radius) for p in arrow_points
    ]
    arrow_alpha = 180
    if player_invulnerable_timer > 0 and int(pygame.time.get_ticks() / 120) % 2 == 0:
        arrow_alpha = 80
    pygame.draw.polygon(arrow_surface, (255, 255, 255, arrow_alpha), arrow_surface_points)
    rotated_arrow = pygame.transform.rotate(arrow_surface, -player_angle)
    screen_x = player_pos.x - camera_offset.x - rotated_arrow.get_width() / 2
    screen_y = player_pos.y - camera_offset.y - rotated_arrow.get_height() / 2
    screen.blit(rotated_arrow, (screen_x, screen_y))

    for projectile in projectiles:
        end_pos = projectile["pos"] + projectile["vel"].normalize() * 15
        start_screen = (projectile["pos"].x - camera_offset.x, projectile["pos"].y - camera_offset.y)
        end_screen = (end_pos.x - camera_offset.x, end_pos.y - camera_offset.y)
        pygame.draw.line(screen, "yellow", start_screen, end_screen, 3)

    vfx_manager.draw(screen, camera_offset)

    health_size = 24
    health_gap = 8
    health_width = player_max_health * health_size + (player_max_health - 1) * health_gap
    health_x = screen.get_width() / 2 - health_width / 2
    for health_idx in range(player_max_health):
        square_x = int(health_x + health_idx * (health_size + health_gap))
        draw_health_square(screen, square_x, 10, health_size, health_idx < player_health)

    font = pygame.font.SysFont(None, 28)
    time_text = font.render(f"Time: {difficulty_manager.get_elapsed_time()}", True, (255, 255, 255))
    screen.blit(time_text, (10, 10))
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 38))

    active_powerups = []
    if multi_shot_timer > 0:
        active_powerups.append(f"Multi: {multi_shot_timer:.1f}s")
    if speed_power_timer > 0:
        active_powerups.append(f"Speed: {speed_power_timer:.1f}s")
    if rapid_fire_timer > 0:
        active_powerups.append(f"Fire Rate: {rapid_fire_timer:.1f}s")

    for idx, powerup_text in enumerate(active_powerups):
        rendered = font.render(powerup_text, True, (255, 255, 255))
        screen.blit(rendered, (10, 66 + idx * 26))


def update_game_logic():
    global player_pos, player_angle, target_angle, player_health, player_invulnerable_timer
    global game_over, player_velocity, shoot_timer, multi_shot_timer
    global speed_power_timer, rapid_fire_timer, projectiles, powerups, score
    global enemies, trail_timer, trail, game_time

    multi_shot_timer = max(0.0, multi_shot_timer - dt)
    speed_power_timer = max(0.0, speed_power_timer - dt)
    rapid_fire_timer = max(0.0, rapid_fire_timer - dt)
    player_invulnerable_timer = max(0.0, player_invulnerable_timer - dt)

    keys = pygame.key.get_pressed()
    input_dir = pygame.Vector2(0, 0)

    if not game_over and keys[pygame.K_w]:
        input_dir.y -= 1
    if not game_over and keys[pygame.K_s]:
        input_dir.y += 1
    if not game_over and keys[pygame.K_a]:
        input_dir.x -= 1
    if not game_over and keys[pygame.K_d]:
        input_dir.x += 1

    if input_dir.length() > 0:
        input_dir = input_dir.normalize()
        current_acceleration = player_acceleration
        if speed_power_timer > 0:
            current_acceleration *= speed_power_multiplier
        player_velocity += input_dir * current_acceleration * dt

    player_velocity *= (1 - player_drag * dt)

    player_pos += player_velocity * dt

    player_pos = clamp_to_map(player_pos, map_vertices, player_radius)

    move_dir = player_velocity
    if move_dir.length() > 0:
        move_dir_normalized = move_dir.normalize()
        target_angle = pygame.Vector2(0, -1).angle_to(move_dir_normalized)

    angle_diff = target_angle - player_angle
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    if abs(angle_diff) > 0.5:
        player_angle += math.copysign(min(abs(angle_diff), rotation_speed * dt * 60), angle_diff)

    shoot_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()

    if not game_over and mouse_buttons[0] and shoot_timer <= 0:
        world_mouse = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
        direction = world_mouse - player_pos

        if direction.length() != 0:
            direction = direction.normalize()

            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            if multi_shot_timer > 0:
                middle_index = (multi_shot_projectile_count - 1) / 2
                for shot_index in range(multi_shot_projectile_count):
                    spread_angle = (shot_index - middle_index) * multi_shot_spread
                    shot_direction = direction.rotate(spread_angle)
                    projectiles.append(create_projectile(spawn_pos, shot_direction))
            else:
                projectiles.append(create_projectile(spawn_pos, direction))
            current_shoot_cooldown = shoot_cooldown
            if rapid_fire_timer > 0:
                current_shoot_cooldown /= rapid_fire_multiplier
            shoot_timer = current_shoot_cooldown

    old_positions = []
    for projectile in projectiles:
        old_positions.append(pygame.Vector2(projectile["pos"]))
        projectile["pos"] += projectile["vel"] * dt

    for i, projectile in enumerate(projectiles):
        if not point_in_polygon((projectile["pos"].x, projectile["pos"].y), map_vertices):
            vfx_manager.spawn_hit_effect(old_positions[i], "wall",
                                         direction=projectile["vel"].normalize())

    projectiles = [
        p for p in projectiles
        if point_in_polygon((p["pos"].x, p["pos"].y), map_vertices)
    ]

    if game_over:
        new_enemies = []
    else:
        new_enemies = spawn_manager.update(dt, enemies, player_pos)

    speed_mult = difficulty_manager.get_enemy_speed_multiplier()
    health_bonus = difficulty_manager.get_enemy_health_bonus()
    for enemy_unit in new_enemies:
        enemy_unit.speed *= speed_mult
        enemy_unit.health += health_bonus
        enemy_unit.max_health = enemy_unit.health

    enemies.extend(new_enemies)

    if not game_over:
        for enemy_unit in enemies:
            enemy_unit.update(dt, player_pos)

    for enemy_unit in enemies:
        dist = enemy_unit.pos.distance_to(player_pos)
        min_dist = enemy_unit.radius + player_radius
        if dist < min_dist and dist > 0:
            if not game_over and player_invulnerable_timer <= 0:
                player_health -= 1
                player_invulnerable_timer = player_invulnerable_duration
                if player_health <= 0:
                    player_health = 0
                    game_over = True
                    player_velocity.x = 0
                    player_velocity.y = 0

            push_dir = (enemy_unit.pos - player_pos).normalize()
            enemy_unit.pos = player_pos + push_dir * min_dist

    bullets_to_remove = set()
    enemies_to_remove = set()

    for p_idx, projectile in enumerate(projectiles if not game_over else []):
        for e_idx, enemy_unit in enumerate(enemies):
            if e_idx in enemies_to_remove:
                continue
            if enemy_unit.collides_with(projectile["pos"], projectile_radius):
                bullets_to_remove.add(p_idx)
                if enemy_unit.take_damage(1):
                    enemies_to_remove.add(e_idx)
                    score += enemy_unit.score_value
                    spawn_powerup(enemy_unit.pos)
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(enemy_unit.pos), "enemy"
                    )
                break

    if bullets_to_remove:
        projectiles = [p for i, p in enumerate(projectiles) if i not in bullets_to_remove]
    if enemies_to_remove:
        enemies = [e for i, e in enumerate(enemies) if i not in enemies_to_remove]

    collected_powerups = set()
    for powerup_idx, powerup in enumerate(powerups if not game_over else []):
        powerup["age"] += dt
        if powerup["pos"].distance_to(player_pos) < player_radius + powerup_radius:
            apply_powerup(powerup["type"])
            collected_powerups.add(powerup_idx)
        elif powerup["age"] >= powerup_lifetime:
            collected_powerups.add(powerup_idx)

    if collected_powerups:
        powerups = [
            p for i, p in enumerate(powerups)
            if i not in collected_powerups
        ]

    trail_timer += dt
    if trail_timer >= TRAIL_INTERVAL and move_dir.length() > 0:
        trail.append((pygame.Vector2(player_pos), 0))
        trail_timer = 0

    trail = [(pos, age + dt) for pos, age in trail if age < TRAIL_LIFETIME]

    camera_offset.x = player_pos.x - screen.get_width() / 2
    camera_offset.y = player_pos.y - screen.get_height() / 2

    if not game_over:
        game_time += dt
        difficulty_manager.update(dt)

    vfx_manager.update(dt)


# ============================================
# Main game loop - Mangu tsukkel
# ============================================
init_game()

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    current_state = state_manager.current_state

    if current_state == GameState.PLAYING:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state_manager.push_state(GameState.PAUSED)
                break

        update_game_logic()

        if game_over and current_state == GameState.PLAYING:
            game_over_screen.set_game_stats(score, difficulty_manager.get_elapsed_time())
            state_manager.change_state(GameState.GAME_OVER)

        render_game_screen()

    elif current_state == GameState.PAUSED:
        render_game_screen()
        pause_screen.handle_events(events)
        pause_screen.update(dt)
        pause_screen.draw(screen)

    else:
        if current_state == GameState.MENU:
            main_menu_screen.handle_events(events)
            main_menu_screen.update(dt)
            main_menu_screen.draw(screen)
            if main_menu_screen.is_quit_requested():
                running = False
        elif current_state == GameState.SETTINGS:
            settings_screen.handle_events(events)
            settings_screen.update(dt)
            settings_screen.draw(screen)
        elif current_state == GameState.UPGRADES:
            upgrades_screen.handle_events(events)
            upgrades_screen.update(dt)
            upgrades_screen.draw(screen)
        elif current_state == GameState.GAME_OVER:
            game_over_screen.handle_events(events)
            game_over_screen.update(dt)
            game_over_screen.draw(screen)

    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
