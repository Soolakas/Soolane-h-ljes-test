import pygame
import math
import random

from enemy import Enemy
from spawn_manager import SpawnManager
from difficulty_manager import DifficultyManager
from vfx_manager import VFXManager
from sound_manager import SoundManager
from upgrade_manager import UpgradeManager, GRACE_PERIOD
from upgrade_registry import UPGRADES, register_upgrade, Rarity
import textures
from menu.state_manager import StateManager, GameState
from menu.screens.main_menu import MainMenuScreen
from menu.screens.settings import SettingsScreen
from menu.screens.upgrades import UpgradesScreen
from menu.screens.pause import PauseScreen
from menu.screens.game_over import GameOverScreen
from menu.screens.upgrade_selection import UpgradeSelectionScreen
from config.settings_store import GameSettings

# ============================================
# pygame setup - Pygame seadistus
# ============================================
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0  # Eelneva kaadri kestus sekundites

# ============================================
# Seaded ja olekuhaldur - Settings and state manager
# ============================================
settings = GameSettings()        # Mängu seadete objekt (salvestab JSON faili)
state_manager = StateManager()   # Olekuhaldur (menüü, mäng, paus jne)

# ============================================
# Helihaldur - Sound manager
# ============================================
pygame.mixer.init()
pygame.mixer.set_num_channels(32)        # Luba kuni 32 samaaegset heli - Allow up to 32 simultaneous sounds
sound_manager = SoundManager(sfx_volume=settings.sfx_volume)

# ============================================
# Uuenduste haldur - Upgrade manager
# ============================================
upgrade_manager = UpgradeManager(grace_period=GRACE_PERIOD)  # Uuenduste valikute haldur

# ============================================
# Map configuration - Kaardi seaded
# ============================================
WORLD_SIZE = 3000    # Maailma suurus pikslites
MAP_INSET = 300      # Kaardi serva taandumine

center = WORLD_SIZE / 2
apothem = (WORLD_SIZE - 2 * MAP_INSET) / 2

# Genereerime kaheksanurkse kaardi tipud
map_vertices = []
for i in range(8):
    angle = math.radians(45 * i + 22.5)
    x = center + apothem * math.cos(angle)
    y = center + apothem * math.sin(angle)
    map_vertices.append((x, y))

# ============================================
# Ekraanid - Screens
# ============================================
# Iga menüüekraan on eraldi klass, mis haldab oma nuppe ja joonistamist
main_menu_screen = MainMenuScreen(state_manager, settings, sound_manager)
settings_screen = SettingsScreen(state_manager, settings, screen, sound_manager)
upgrades_screen = UpgradesScreen(state_manager, settings)
pause_screen = PauseScreen(state_manager, settings)
game_over_screen = GameOverScreen(state_manager, settings)
upgrade_selection_screen = UpgradeSelectionScreen(state_manager, settings, upgrade_manager)

# Ekraanide register - kasutatakse peamenüü alam-ekraanide jaoks
screens = {
    GameState.MENU: main_menu_screen,
    GameState.SETTINGS: settings_screen,
    GameState.UPGRADES: upgrades_screen,
    GameState.PAUSED: pause_screen,
    GameState.GAME_OVER: game_over_screen,
    GameState.UPGRADE_SELECTION: upgrade_selection_screen,
}

# ============================================
# Camera - Kaamera seaded
# ============================================
camera_offset = pygame.Vector2(0, 0)  # Kaamera nihe maailma suhtes

# ============================================
# Game state variables - Mängu oleku muutujad
# ============================================
player_pos = pygame.Vector2(center, center)   # Mängija asukoht maailmas
player_radius = 15                            # Mängija suurus
player_angle = 0                              # Mängija pöördenurk
target_angle = 0                              # Sihtpöördenurk
rotation_speed = 8                            # Pöörlemise kiirus
player_max_health = 7                         # Maksimaalne tervis
player_health = player_max_health             # Praegune tervis
player_invulnerable_timer = 0.0               # Haavamatususe taimer
player_invulnerable_duration = 1.0            # Haavamatususe kestus
game_over = False                             # Kas mäng on läbi

player_velocity = pygame.Vector2(0, 0)        # Mängija kiirus (triivfüüsika)
player_acceleration = 1200                    # Kiirendus (pikslit/s²)
player_drag = 4.0                             # Hõõrdetegur (suurem = vähem triivi)

projectiles = []                               # Kuulid
projectile_speed = 700                        # Kuuli kiirus
projectile_radius = 8                         # Kuuli suurus

shoot_cooldown = 0.25                         # Laskmise jahe
shoot_timer = 0                               # Laskmise taimer

# ============================================
# Player stats - permanent upgrades - Mängija statistika püsivõimendused
# ============================================
# Need väärtused muutuvad ainult uuenduste kaudu - Only modified by upgrades
player_stats = {
    "acceleration_multiplier": 1.0,   # Kiirenduse kordaja - Acceleration multiplier
    "multi_shot_count": 1,            # Kuulide arv ühe lasuga - Projectiles per shot
    "multi_shot_spread": 18,          # Kuulide nurkhajumine - Projectile spread angle
    "fire_rate_multiplier": 1.0,      # Tulekiiruse kordaja - Fire rate multiplier
}

score = 0  # Punktid

enemies = []  # Vaenlased

# Raskusaste ja tekitamine - Difficulty and spawning
difficulty_manager = DifficultyManager()
spawn_manager = SpawnManager(map_vertices, (center, center), difficulty_manager)

# Visuaalsed efektid - Visual effects
vfx_manager = VFXManager()

# Mängija jälg - Player trail
TRAIL_LIFETIME = 0.5    # Kui kaua jälje punktid kestavad
TRAIL_INTERVAL = 0.02   # Kui tihti jälgipunkti lisatakse
trail_timer = 0
trail = []

game_time = 0  # Mängu aeg


def init_game():
    """Lähtestab kõik mängu muutujad algväärtustele.
    Initialize all game variables to their starting values."""
    global player_pos, player_angle, target_angle, player_health, player_invulnerable_timer
    global game_over, player_velocity, shoot_timer, projectiles, score
    global enemies, trail_timer, trail, game_time, player_stats

    player_pos = pygame.Vector2(center, center)
    player_angle = 0
    target_angle = 0
    player_health = player_max_health
    player_invulnerable_timer = 0.0
    game_over = False

    player_velocity = pygame.Vector2(0, 0)
    shoot_timer = 0

    # Lähtesta mängija statistika - Reset player stats to base values
    player_stats = {
        "acceleration_multiplier": 1.0,
        "multi_shot_count": 1,
        "multi_shot_spread": 18,
        "fire_rate_multiplier": 1.0,
    }

    projectiles = []
    score = 0
    enemies = []

    trail_timer = 0
    trail = []
    game_time = 0

    # Lähtestame ka raskuse, tekitamise ja uuendused
    difficulty_manager.elapsed_time = 0.0
    spawn_manager.spawn_timer = 0.0
    vfx_manager.particles = []
    upgrade_manager.reset()


def reset_game():
    """Lähtestab mängu oleku, kui menüüdest tagasi mängu tullakse.
    Reset game state when returning to playing from menus."""
    init_game()


# Seame tagasihelistamised menüüekraanidele
pause_screen.set_game_reset_callback(reset_game)
game_over_screen.set_restart_callback(reset_game)

# Seame uuenduse valiku tagasihelistamise - Set upgrade selection callback
def on_upgrade_selected(index):
    """Rakenda valitud uuendus ja naase mängu - Apply selected upgrade and resume game."""
    choices = upgrade_manager.pending_choices
    if 0 <= index < len(choices):
        upgrade_manager.apply_upgrade(choices[index], player_stats)
    upgrade_manager.clear_pending()
    state_manager.pop_state()  # Naase mängu olekusse - Return to PLAYING state

upgrade_selection_screen.set_callback(on_upgrade_selected)


# ============================================
# Utility functions - Abifunktsioonid
# ============================================

def point_in_polygon(point, vertices):
    """Kontrollib, kas punkt asub hulknurga sees (kiirete algoritm)."""
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
    """Piirab mängija asukoha kaardi sisse. Kui väljas, leiab lähima serva punkti."""
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


def create_projectile(spawn_pos, direction):
    """Loob uue kuuli antud asukohast ja suunas."""
    return {
        "pos": pygame.Vector2(spawn_pos),
        "vel": direction * projectile_speed
    }


def render_game_screen():
    """Joonistab kogu mängu ekraani: tausta, kaardi, vaenlased, mängija, kuulid, efektid, HUD."""

    # Neon grid background
    textures.draw_background(screen, camera_offset)

    # Kaardi piirjoon
    pygame.draw.polygon(screen, "white", [(v[0] - camera_offset.x, v[1] - camera_offset.y) for v in map_vertices], 3)

    # Vaenlased
    for enemy_unit in enemies:
        enemy_unit.draw(screen, camera_offset)

    # Mängija jälg - animated pixel fire trail
    textures.draw_player_trail(screen, trail, player_pos, TRAIL_LIFETIME, camera_offset, 9)

    # Mängija laev - sprite sheet based player model
    textures.draw_player_sprite(
        screen,
        player_pos,
        player_angle,
        player_radius,
        camera_offset,
        player_invulnerable_timer > 0,
    )

    # Kuulid - glow line projectiles
    for projectile in projectiles:
        textures.draw_projectile(screen, projectile, camera_offset)

    # Visuaalsed efektid
    vfx_manager.draw(screen, camera_offset)

    # Tervise ruudud
    health_size = 24
    health_gap = 8
    health_width = player_max_health * health_size + (player_max_health - 1) * health_gap
    health_x = screen.get_width() / 2 - health_width / 2
    for health_idx in range(player_max_health):
        square_x = int(health_x + health_idx * (health_size + health_gap))
        textures.draw_health_square(screen, square_x, 10, health_size, health_idx < player_health)

    # Aeg ja punktid
    font = pygame.font.SysFont(None, 28)
    time_text = font.render(f"Time: {difficulty_manager.get_elapsed_time()}", True, (255, 255, 255))
    screen.blit(time_text, (10, 10))
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 38))


def update_game_logic():
    """Uuendab kogu mängu loogikat: sisend, liikumine, laskmine, kokkupõrked, vaenlased.
    Updates all game logic: input, movement, shooting, collisions, enemies."""
    global player_pos, player_angle, target_angle, player_health, player_invulnerable_timer
    global game_over, player_velocity, shoot_timer, projectiles, score
    global enemies, trail_timer, trail, game_time

    # Uuenda mängija asukohta helihaldurile kauguse arvutamiseks
    # Update player position for sound distance calculation
    sound_manager.set_player_position(player_pos)

    # Uuenda uuenduste haldurit - Track time without hit for upgrade chances
    upgrade_manager.update(dt)

    # Saada frame_update konks uuendustele - Dispatch frame update hook for upgrades
    upgrade_manager.hooks.dispatch_frame_update(dt, player_stats, enemies, player_pos)

    # Vähendame haavamatuse taimerit
    player_invulnerable_timer = max(0.0, player_invulnerable_timer - dt)

    # ============================================
    # Player input - Mängija sisend
    # ============================================
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

    # ============================================
    # Drift movement - Triivliikumine
    # ============================================
    if input_dir.length() > 0:
        input_dir = input_dir.normalize()
        # Kasuta püsivat kiirenduse kordajat - Use permanent acceleration multiplier
        current_acceleration = player_acceleration * player_stats["acceleration_multiplier"]
        player_velocity += input_dir * current_acceleration * dt

    # Hõõrdumine aeglustab kiirust
    player_velocity *= (1 - player_drag * dt)

    # Kiirus rakendatakse asukohale
    player_pos += player_velocity * dt

    # Hoia mängija kaardi sees
    player_pos = clamp_to_map(player_pos, map_vertices, player_radius)

    # Sujuv pööramine liikumissuunas
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

    # ============================================
    # Shooting - Laskmine
    # ============================================
    shoot_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()

    if not game_over and mouse_buttons[0] and shoot_timer <= 0:
        world_mouse = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
        direction = world_mouse - player_pos

        if direction.length() != 0:
            direction = direction.normalize()

            # Lase mängija äärest
            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            # Kasuta püsivaid uuendusi - Use permanent upgrades for multi-shot
            shot_count = player_stats["multi_shot_count"]
            spread = player_stats["multi_shot_spread"]

            if shot_count > 1:
                middle_index = (shot_count - 1) / 2
                for shot_index in range(shot_count):
                    spread_angle = (shot_index - middle_index) * spread
                    shot_direction = direction.rotate(spread_angle)
                    # Loo kuul ja rakenda konksud - Create bullet and apply spawn hooks
                    bullet = create_projectile(spawn_pos, shot_direction)
                    bullet = upgrade_manager.hooks.dispatch_bullet_spawn(bullet, player_stats)
                    projectiles.append(bullet)
            else:
                # Loo kuul ja rakenda konksud - Create bullet and apply spawn hooks
                bullet = create_projectile(spawn_pos, direction)
                bullet = upgrade_manager.hooks.dispatch_bullet_spawn(bullet, player_stats)
                projectiles.append(bullet)
            # Mängi laskmise heli mängija asukohast - Play bullet shoot sound at player position
            sound_manager.play("bullet", position=pygame.Vector2(player_pos))
            current_shoot_cooldown = shoot_cooldown
            # Kasuta püsivat tulekiiruse kordajat - Use permanent fire rate multiplier
            current_shoot_cooldown /= player_stats["fire_rate_multiplier"]
            shoot_timer = current_shoot_cooldown

    # ============================================
    # Update projectiles - Kuulide uuendus
    # ============================================
    old_positions = []
    for projectile in projectiles:
        old_positions.append(pygame.Vector2(projectile["pos"]))
        projectile["pos"] += projectile["vel"] * dt

    # Seina kokkupõrke efektid
    for i, projectile in enumerate(projectiles):
        if not point_in_polygon((projectile["pos"].x, projectile["pos"].y), map_vertices):
            # Mängi seina tabamuse heli kuuli asukohas - Play wall hit sound at projectile position
            sound_manager.play("wall_hit", position=pygame.Vector2(old_positions[i]))
            vfx_manager.spawn_hit_effect(old_positions[i], "wall",
                                         direction=projectile["vel"].normalize())

    # Eemalda kuulid, mis kaardilt välja lähevad
    projectiles = [
        p for p in projectiles
        if point_in_polygon((p["pos"].x, p["pos"].y), map_vertices)
    ]

    # ============================================
    # Enemy system - Vaenlaste süsteem
    # ============================================
    if game_over:
        new_enemies = []
    else:
        new_enemies = spawn_manager.update(dt, enemies, player_pos)

    # Rakenda raskuse kiiruse skaleerimine uutele vaenlastele
    speed_mult = difficulty_manager.get_enemy_speed_multiplier()
    health_bonus = difficulty_manager.get_enemy_health_bonus()
    for enemy_unit in new_enemies:
        enemy_unit.speed *= speed_mult
        enemy_unit.health += health_bonus
        enemy_unit.max_health = enemy_unit.health

    enemies.extend(new_enemies)

    # Uuenda vaenlasi - liigu mängija poole
    if not game_over:
        for enemy_unit in enemies:
            enemy_unit.update(dt, player_pos)

    # Vaenlase-mängija kokkupõrge ja tõukumine
    for enemy_unit in enemies:
        dist = enemy_unit.pos.distance_to(player_pos)
        min_dist = enemy_unit.radius + player_radius
        if dist < min_dist and dist > 0:
            if not game_over and player_invulnerable_timer <= 0:
                player_health -= 1
                player_invulnerable_timer = player_invulnerable_duration
                # Mängi mängija tabamuse heli - Play player hit sound at player position
                sound_manager.play("player_hit", position=pygame.Vector2(player_pos))

                # Uuenda uuenduste haldurit - Update upgrade manager on hit
                upgrade_manager.on_player_hit()

                # Kui grazes periood on möödas, näita uuenduste valikut
                # If grace period passed, show upgrade selection
                if upgrade_manager.should_trigger_upgrade():
                    upgrade_manager.generate_choices()
                    state_manager.push_state(GameState.UPGRADE_SELECTION)

                if player_health <= 0:
                    player_health = 0
                    game_over = True
                    player_velocity.x = 0
                    player_velocity.y = 0
                    # Mängi mängija surma heli - Play player death sound at player position
                    sound_manager.play("player_die", position=pygame.Vector2(player_pos))

            push_dir = (enemy_unit.pos - player_pos).normalize()
            enemy_unit.pos = player_pos + push_dir * min_dist

    # ============================================
    # Collision detection - Kokkupõrked
    # ============================================
    bullets_to_remove = set()
    enemies_to_remove = set()

    for p_idx, projectile in enumerate(projectiles if not game_over else []):
        for e_idx, enemy_unit in enumerate(enemies):
            if e_idx in enemies_to_remove:
                continue
            if enemy_unit.collides_with(projectile["pos"], projectile_radius):
                bullets_to_remove.add(p_idx)
                # Mängi vaenlase tabamuse heli vaenlase asukohas - Play enemy hit sound at enemy position
                sound_manager.play("enemy_hit", position=pygame.Vector2(enemy_unit.pos))
                if enemy_unit.take_damage(1):
                    enemies_to_remove.add(e_idx)
                    score += enemy_unit.score_value
                    # Mängi vaenlase surma heli vaenlase asukohas - Play enemy death sound at enemy position
                    sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(enemy_unit.pos), "enemy"
                    )
                break

    # Eemalda tabatud kuulid ja surnud vaenlased
    if bullets_to_remove:
        projectiles = [p for i, p in enumerate(projectiles) if i not in bullets_to_remove]
    if enemies_to_remove:
        enemies = [e for i, e in enumerate(enemies) if i not in enemies_to_remove]

    # ============================================
    # Player trail - Mängija jälg
    # ============================================
    trail_timer += dt
    if trail_timer >= TRAIL_INTERVAL and move_dir.length() > 0:
        trail.append((pygame.Vector2(player_pos), 0))
        trail_timer = 0

    trail = [(pos, age + dt) for pos, age in trail if age < TRAIL_LIFETIME]

    # ============================================
    # Camera follows the player - Kaamera jälgimine
    # ============================================
    camera_offset.x = player_pos.x - screen.get_width() / 2
    camera_offset.y = player_pos.y - screen.get_height() / 2

    # ============================================
    # Update time - Aja uuendus
    # ============================================
    if not game_over:
        game_time += dt
        difficulty_manager.update(dt)

    # ============================================
    # Update VFX - Efektide uuendus
    # ============================================
    vfx_manager.update(dt)


# ============================================
# Main game loop - Mängu tsükkel
# ============================================
init_game()

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    current_state = state_manager.current_state

    # ============================================
    # PLAYING state - Aktiivne mäng
    # ============================================
    if current_state == GameState.PLAYING:
        # ESC klahv avab pausiekraani
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state_manager.push_state(GameState.PAUSED)
                break

        update_game_logic()

        # Kui mäng on läbi, vaheta game over ekraanile
        if game_over and current_state == GameState.PLAYING:
            game_over_screen.set_game_stats(score, difficulty_manager.get_elapsed_time())
            state_manager.change_state(GameState.GAME_OVER)

        render_game_screen()

    # ============================================
    # PAUSED state - Mäng on peatatud
    # ============================================
    elif current_state == GameState.PAUSED:
        # Joonista mäng taha ja pausi peale
        render_game_screen()
        pause_screen.handle_events(events)
        pause_screen.update(dt)
        pause_screen.draw(screen)

    # ============================================
    # UPGRADE_SELECTION state - Uuenduse valik
    # ============================================
    elif current_state == GameState.UPGRADE_SELECTION:
        # Joonista mäng taha ja valik ekraan peale
        render_game_screen()
        upgrade_selection_screen.handle_events(events)
        upgrade_selection_screen.update(dt)
        upgrade_selection_screen.draw(screen)

    # ============================================
    # MENU / SETTINGS / UPGRADES / GAME_OVER states - Menüü ekraanid
    # ============================================
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

    # flip() the display to put your work on screen
    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
