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
from menu.screens.dev_panel import DevPanel
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
player_max_health = 5                         # Maksimaalne tervis - 5 hits to die
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
    # New upgrade stats
    "speed_multiplier": 1.0,          # Thruster Tuning (+0.08 per stack)
    "crit_chance": 0.0,               # Sharp bullets (+0.10 per stack, caps at 1.0)
    "crit_multiplier": 3.0,           # Sharp bullets (triple damage)
    "accuracy": 0,                    # GPS tracker (0-3, tightens spread)
    "knockback_force": 0.0,           # A bat (exponential decrease formula)
    "poison_chance": 0.0,            # Green Juice (exponential decrease)
    "poison_damage": 0.0,             # Green Juice (flat HP/s, exponential decrease)
    "max_bounces": 0,                 # Waller (bounces off walls)
    "bounce_speed_multiplier": 1.0,   # Waller (velocity increase on bounce)
    "random_bullet_chance": 0.0,       # One bullet per sometimes (exponential decrease)
    "dash_count": 0,                  # The shift key (1 or 2 dashes)
    "proximity_damage_bonus": 0.0,     # Heavy metal (+0.20 per stack, infinite)
    "cactus_armor_stacks": 0,         # Cactus armor (1 or 2, 3+ useless)
}

score = 0  # Punktid

enemies = []  # Vaenlased

# ============================================
# Enemy debuffs - Vaenlaste staatuseefektid
# ============================================
# Jälgib mürgitatud vaenlasi ja teisi efekte - Tracks poisoned enemies and other effects
enemy_debuffs = {}  # {id(enemy): {"poison_timer": float, "poison_damage": float, "poison_source_pos": Vector2, ...}}

# ============================================
# Dash system - Dash süsteem
# ============================================
dash_state = {
    "active": False,                  # Kas dash on aktiivne - Is dash currently active
    "timer": 0.0,                     # Dash'i kestus - Dash duration
    "duration": 0.075,                # Dash'i pikkus sekundites - Dash length in seconds
    "direction": pygame.Vector2(0, 0),# Dash'i suund - Dash direction
    "speed": 3000,                    # Dash'i kiirus - Dash speed
    "cooldowns": [],                  # Iga dash'i cooldown - Cooldown for each dash
    "cooldown_duration": 15.0,        # Dash'i cooldown sekundites - Dash cooldown in seconds
}

# ============================================
# Cactus armor aura tracking - Cactus armor'i aura jälgimine
# ============================================
cactus_armor_aura_timer = {}  # {id(enemy): float} - Aeg, kui kaua vaenlane on aurast sees - Time enemy has been in aura
CACTUS_AURA_RADIUS = 60         # Aura raadius pikslites - Aura radius in pixels
HEAVY_METAL_RADIUS = 250        # Heavy metal'i kahju aura raadius - Heavy metal damage aura radius

# ============================================
# Knockback counter - Tagasilöögi loendur
# ============================================
knockback_shot_counter = 0  # Loeb lasku, et iga 5. lasu tekitaks tagasilöögi - Counts shots for knockback every 5th

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
    global enemy_debuffs, dash_state, cactus_armor_aura_timer, knockback_shot_counter

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
        "speed_multiplier": 1.0,
        "crit_chance": 0.0,
        "crit_multiplier": 3.0,
        "accuracy": 0,
        "knockback_force": 0.0,
        "poison_chance": 0.0,
        "poison_damage": 0.0,
        "max_bounces": 0,
        "bounce_speed_multiplier": 1.0,
        "random_bullet_chance": 0.0,
        "dash_count": 0,
        "proximity_damage_bonus": 0.0,
        "cactus_armor_stacks": 0,
    }

    # Lähtesta vaenlaste debuff'id - Reset enemy debuffs
    enemy_debuffs = {}

    # Lähtesta dash süsteem - Reset dash system
    dash_state["active"] = False
    dash_state["timer"] = 0.0
    dash_state["direction"] = pygame.Vector2(0, 0)
    dash_state["cooldowns"] = []

    # Lähtesta cactus armor'i aura - Reset cactus armor aura tracking
    cactus_armor_aura_timer = {}

    # Lähtesta knockback loendur - Reset knockback counter
    knockback_shot_counter = 0

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
# Developer mode - Arendaja režiim
# ============================================
dev_panel = DevPanel(sound_manager)
dev_invulnerable = False  # Arendaja haavamatus - Dev invincibility flag

def apply_dev_upgrade(upgrade):
    """Rakenda arendaja uuendus - Apply dev upgrade instantly."""
    upgrade_manager.apply_upgrade(upgrade, player_stats)

def skip_time(seconds):
    """Jäta aeg vahele - Skip time forward."""
    global game_time
    game_time += seconds
    difficulty_manager.elapsed_time += seconds
    upgrade_manager.time_without_hit += seconds

def kill_all_enemies():
    """Tapa kõik vaenlased - Kill all enemies instantly."""
    global enemies, score
    for enemy_unit in enemies:
        score += enemy_unit.score_value
        vfx_manager.spawn_hit_effect(pygame.Vector2(enemy_unit.pos), "enemy")
        sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
    enemies.clear()
    enemy_debuffs.clear()

def set_dev_invincible(inv):
    """Seab arendaja haavatamatuse - Set dev invincibility."""
    global dev_invulnerable
    dev_invulnerable = inv

dev_panel.set_callback('toggle_invincible', set_dev_invincible)
dev_panel.set_callback('grant_upgrade', lambda u: apply_dev_upgrade(u))
dev_panel.set_callback('skip_time', lambda s: skip_time(s))
dev_panel.set_callback('kill_all', lambda: kill_all_enemies())
dev_panel.set_callback('reset', lambda: reset_game())


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


def _get_wall_normal(pos, vertices):
    """Leiab seina normaali antud asukohas - Finds wall normal at given position.
    
    Used for Waller bounce physics - calculating reflection angle.
    
    Args:
        pos (pygame.Vector2): Position outside the polygon.
        vertices (list): Map polygon vertices.
        
    Returns:
        pygame.Vector2 or None: Normalized wall normal vector pointing inward.
    """
    min_dist = float('inf')
    best_normal = None

    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        
        # Leiab lähima punkti serval - Find closest point on edge
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            continue
        
        t = max(0, min(1, ((pos.x - x1) * dx + (pos.y - y1) * dy) / (dx * dx + dy * dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        dist = math.hypot(pos.x - closest_x, pos.y - closest_y)
        if dist < min_dist:
            min_dist = dist
            # Normaal on suund servast punkti poole - Normal is direction from edge to point
            if dist > 0:
                best_normal = pygame.Vector2(pos.x - closest_x, pos.y - closest_y).normalize()
            else:
                # Kui täpselt serval, kasuta ristsuunda - If exactly on edge, use perpendicular
                edge_dir = pygame.Vector2(dx, dy).normalize()
                best_normal = pygame.Vector2(-edge_dir.y, edge_dir.x)
    
    return best_normal


def create_projectile(spawn_pos, direction, bullet_props=None):
    """Loob uue kuuli antud asukohast ja suunas koos omadustega.
    Creates a new projectile at given position and direction with properties.
    
    Args:
        spawn_pos (pygame.Vector2): Spawn position.
        direction (pygame.Vector2): Direction vector.
        bullet_props (dict, optional): Bullet properties from parent bullet or defaults.
        
    Returns:
        dict: Projectile dictionary with all properties.
    """
    # Vaikimisi omadused - Default properties
    props = {
        "pos": pygame.Vector2(spawn_pos),
        "vel": direction * projectile_speed,
        "is_crit": False,           # Sharp bullets - kas kriitiline löök
        "has_knockback": False,     # A bat - kas on tagasilöögi kuul
        "knockback_force": 0.0,     # A bat - tagasilöögi jõud
        "has_poison": False,        # Green Juice - kas mürgitab
        "poison_damage": 0.0,       # Green Juice - mürgi kahju
        "poison_duration": 4.0,     # Green Juice - mürgi kestus
        "bounce_count": 0,          # Waller - hüpete arv
        "max_bounces": 0,           # Waller - maksimaalsed hüpped
        "damage_multiplier": 1.0,   # Heavy metal - kahju kordaja
        "bullet_radius": projectile_radius,  # Suurus (muutub knockback'i puhul)
    }
    
    # Kui omadused on antud, kopeeri need (suvalise kuuli jaoks)
    # If properties provided, copy them (for random bullet inheritance)
    if bullet_props:
        for key, value in bullet_props.items():
            if key not in ("pos", "vel"):  # Ära kopeeri asukohta ja kiirust
                props[key] = value
    
    return props


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

    # Kuulid - glow line projectiles with upgrade visuals
    for projectile in projectiles:
        # Sharp bullets - kriitiline kuul on kollane/oranž - Critical bullets are yellow/orange
        if projectile.get("is_crit", False):
            # Ajutine salvesta algne värv ja joonista eri värvi
            # Temporarily save original color and draw different color
            orig_color = textures.PROJECTILE_COLOR
            textures.PROJECTILE_COLOR = (255, 160, 30)  # Orange for crit
            textures.draw_projectile(screen, projectile, camera_offset)
            textures.PROJECTILE_COLOR = orig_color
        # A bat - tagasilöögi kuul on suurem - Knockback bullet is bigger
        elif projectile.get("has_knockback", False):
            # Joonista suurem kuul - Draw bigger bullet
            bullet_radius = projectile.get("bullet_radius", projectile_radius)
            screen_pos = (
                int(projectile["pos"].x - camera_offset.x),
                int(projectile["pos"].y - camera_offset.y),
            )
            pygame.draw.circle(screen, textures.PROJECTILE_COLOR, screen_pos, int(bullet_radius), 2)
        else:
            textures.draw_projectile(screen, projectile, camera_offset)

        # Green Juice - mürgitatud kuulidel rohelised osakesed - Poisoned bullets have green particles
        if projectile.get("has_poison", False):
            screen_pos = (
                int(projectile["pos"].x - camera_offset.x),
                int(projectile["pos"].y - camera_offset.y),
            )
            # Väike roheline täpp - Small green dot
            pygame.draw.circle(screen, (80, 255, 80), screen_pos, 3)

    # Visuaalsed efektid
    vfx_manager.draw(screen, camera_offset)

    # ============================================
    # Upgrade auras - Uuenduste aurad
    # ============================================
    # Cactus armor - faint green circle around player
    if player_stats.get("cactus_armor_stacks", 0) > 0:
        aura_pos = (int(player_pos.x - camera_offset.x), int(player_pos.y - camera_offset.y))
        pygame.draw.circle(screen, (50, 200, 50, 30), aura_pos, CACTUS_AURA_RADIUS, 1)
        # Faint fill
        aura_surf = pygame.Surface((CACTUS_AURA_RADIUS * 2, CACTUS_AURA_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (50, 200, 50, 15), (CACTUS_AURA_RADIUS, CACTUS_AURA_RADIUS), CACTUS_AURA_RADIUS)
        screen.blit(aura_surf, (aura_pos[0] - CACTUS_AURA_RADIUS, aura_pos[1] - CACTUS_AURA_RADIUS))

    # Heavy metal - faint red/dark circle around player
    if player_stats.get("proximity_damage_bonus", 0.0) > 0:
        aura_pos = (int(player_pos.x - camera_offset.x), int(player_pos.y - camera_offset.y))
        pygame.draw.circle(screen, (200, 50, 50, 30), aura_pos, HEAVY_METAL_RADIUS, 1)
        # Faint fill
        aura_surf = pygame.Surface((HEAVY_METAL_RADIUS * 2, HEAVY_METAL_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (200, 50, 50, 10), (HEAVY_METAL_RADIUS, HEAVY_METAL_RADIUS), HEAVY_METAL_RADIUS)
        screen.blit(aura_surf, (aura_pos[0] - HEAVY_METAL_RADIUS, aura_pos[1] - HEAVY_METAL_RADIUS))

    # Green Juice - mürgitatud vaenlaste rohelised osakesed - Poisoned enemy green particles
    for enemy_unit in enemies:
        enemy_id = id(enemy_unit)
        if enemy_id in enemy_debuffs:
            # Mürgi osakesed - Poison particles
            for _ in range(2):
                particle_offset = pygame.Vector2(
                    random.uniform(-enemy_unit.radius, enemy_unit.radius),
                    random.uniform(-enemy_unit.radius, enemy_unit.radius),
                )
                particle_pos = (
                    int(enemy_unit.pos.x - camera_offset.x + particle_offset.x),
                    int(enemy_unit.pos.y - camera_offset.y + particle_offset.y),
                )
                pygame.draw.circle(screen, (80, 255, 80, 150), particle_pos, random.randint(1, 3))

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

    # ============================================
    # Enemy debuffs update - Vaenlaste staatuseefektide uuendus
    # ============================================
    # Initialize removal sets early for cactus armor and poison
    enemies_to_remove = set()  # Indices for collision detection
    enemies_to_remove_cactus = set()  # IDs for cactus armor kills
    enemies_to_remove_poison = set()  # IDs for poison kills
    
    # Green Juice - mürgi uuendamine - Update poison debuffs
    for enemy_unit in enemies:
        enemy_id = id(enemy_unit)
        if enemy_id in enemy_debuffs:
            debuff = enemy_debuffs[enemy_id]
            debuff["poison_timer"] -= dt
            if debuff["poison_timer"] > 0:
                # Mürgi kahju sekundis - Poison damage per second
                # Rakenda kahju järk-järgult - Apply damage gradually over the second
                damage_this_frame = debuff["poison_damage"] * dt
                if enemy_unit.take_damage(damage_this_frame):
                    enemies_to_remove_poison.add(enemy_id)
                    score += enemy_unit.score_value
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(enemy_unit.pos), "enemy"
                    )
                    sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
            else:
                # Mürk on läbi - Poison expired
                del enemy_debuffs[enemy_id]

    # Eemalda mürgiga surnud vaenlased - Remove poison-killed enemies
    for enemy_id in enemies_to_remove_poison:
        if enemy_id in enemy_debuffs:
            del enemy_debuffs[enemy_id]
        enemies = [e for e in enemies if id(e) != enemy_id]

    # ============================================
    # Cactus armor aura - Cactus armor'i aura
    # ============================================
    cactus_stacks = player_stats.get("cactus_armor_stacks", 0)
    if cactus_stacks > 0:
        for enemy_unit in enemies:
            enemy_id = id(enemy_unit)
            dist = enemy_unit.pos.distance_to(player_pos)
            if dist < CACTUS_AURA_RADIUS + enemy_unit.radius:
                # Vaenlane on aurast sees - Enemy is in aura
                if enemy_id not in cactus_armor_aura_timer:
                    cactus_armor_aura_timer[enemy_id] = 0.0
                cactus_armor_aura_timer[enemy_id] += dt

                # Kui vaenlane on olnud aurast 0.5s, tapa see - If enemy in aura for 0.5s, kill it
                if cactus_armor_aura_timer[enemy_id] >= 0.5:
                    # Tavalised vaenlased surevad - Common enemies die (×10 scale)
                    if enemy_unit.health <= 20 or enemy_unit.max_health <= 20:
                        score += enemy_unit.score_value
                        vfx_manager.spawn_hit_effect(
                            pygame.Vector2(enemy_unit.pos), "enemy"
                        )
                        sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
                        enemies_to_remove_cactus.add(enemy_id)

                        # Stack 2: pildu kuulid - Spawn bullets in all directions
                        if cactus_stacks >= 2:
                            for angle_idx in range(6):
                                angle = angle_idx * 60
                                dir_vec = pygame.Vector2(1, 0).rotate(angle)
                                cactus_bullet = create_projectile(
                                    pygame.Vector2(enemy_unit.pos), dir_vec
                                )
                                # Põhilised kuulid ilma efektideta - Basic bullets without effects
                                projectiles.append(cactus_bullet)

                        if enemy_id in cactus_armor_aura_timer:
                            del cactus_armor_aura_timer[enemy_id]
                    else:
                        # Tugevamad vaenlased saavad kahju - Stronger enemies take damage (×10 scale)
                        enemy_unit.take_damage(20)
                        if not enemy_unit.is_alive():
                            score += enemy_unit.score_value
                            vfx_manager.spawn_hit_effect(
                                pygame.Vector2(enemy_unit.pos), "enemy"
                            )
                            sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
                            enemies_to_remove_cactus.add(enemy_id)
                            if enemy_id in cactus_armor_aura_timer:
                                del cactus_armor_aura_timer[enemy_id]
            else:
                # Vaenlane on aurast väljas - Enemy left aura
                if enemy_id in cactus_armor_aura_timer:
                    del cactus_armor_aura_timer[enemy_id]

    # ============================================
    # Dash system - Dash süsteem
    # ============================================
    dash_count = player_stats.get("dash_count", 0)
    if dash_count > 0:
        # Uuenda cooldown'e - Update cooldowns
        while len(dash_state["cooldowns"]) < dash_count:
            dash_state["cooldowns"].append(0.0)

        for i in range(len(dash_state["cooldowns"])):
            if dash_state["cooldowns"][i] > 0:
                dash_state["cooldowns"][i] -= dt

        # Dash on aktiivne - Dash is active
        if dash_state["active"]:
            dash_state["timer"] -= dt
            # Rakenda dash'i kiirus - Apply dash velocity
            player_velocity = dash_state["direction"] * dash_state["speed"]
            player_pos += player_velocity * dt
            player_pos = clamp_to_map(player_pos, map_vertices, player_radius)

            if dash_state["timer"] <= 0:
                dash_state["active"] = False
                player_velocity *= 0.3  # Aeglusta pärast dash'i - Slow down after dash
        else:
            # Kontrolli shift sisendit - Check shift input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                # Leia dash'i suund kursori poole - Find dash direction toward cursor
                world_mouse = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
                dash_dir = world_mouse - player_pos
                if dash_dir.length() > 0:
                    dash_dir = dash_dir.normalize()

                    # Leia esimene cooldown'ita dash - Find first dash off cooldown
                    for i in range(dash_count):
                        if dash_state["cooldowns"][i] <= 0:
                            dash_state["active"] = True
                            dash_state["timer"] = dash_state["duration"]
                            dash_state["direction"] = dash_dir
                            dash_state["cooldowns"][i] = dash_state["cooldown_duration"]
                            player_invulnerable_timer = max(player_invulnerable_timer, dash_state["duration"])
                            break

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
    # Dash'i ajal väldi tavalist liikumist - Avoid normal movement during dash
    if not dash_state["active"]:
        if input_dir.length() > 0:
            input_dir = input_dir.normalize()
            # Kasuta püsivat kiirenduse kordajat - Use permanent acceleration multiplier
            # Thruster Tuning - kiiruse kordaja - Speed multiplier
            current_acceleration = player_acceleration * player_stats["acceleration_multiplier"] * player_stats["speed_multiplier"]
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

            # Lase mängija äärest - Shoot from player edge
            spawn_pos = player_pos + direction * (player_radius + projectile_radius)

            # GPS tracker - vähenda hajumist - Reduce spread based on accuracy
            # Baashajumine kõikidele kuulidele - Base spread for all bullets
            # Algne hajumine on 15 kraadi - Initial spread is 15 degrees
            base_spread = 15.0
            accuracy = player_stats["accuracy"]
            # Valem: spread väheneb 50% iga accuracy punkti kohta, max +2 = 0 spread
            # Formula: spread decreases 50% per accuracy point, max +2 = 0 spread
            single_shot_spread = base_spread * max(0.0, 1.0 - accuracy * 0.5)
            
            # Mitmelasu hajumine - Multi-shot spread
            multi_spread = player_stats["multi_shot_spread"]
            multi_effective_spread = multi_spread * max(0.0, 1.0 - accuracy * 0.5)

            # Kasuta püsivaid uuendusi - Use permanent upgrades for multi-shot
            shot_count = player_stats["multi_shot_count"]

            # Arvuta kuuli omadused - Calculate bullet properties for this shot
            global knockback_shot_counter
            knockback_shot_counter += 1

            # Sharp bullets - crit chance roll
            is_crit = random.random() < player_stats["crit_chance"]

            # A bat - knockback every 5th shot
            has_knockback = (knockback_shot_counter % 5 == 0) and player_stats["knockback_force"] > 0
            knockback_force = player_stats["knockback_force"] if has_knockback else 0.0

            # Green Juice - poison chance roll
            has_poison = random.random() < player_stats["poison_chance"]
            poison_damage = player_stats["poison_damage"] if has_poison else 0.0

            # Waller - bounce properties
            max_bounces = player_stats["max_bounces"]

            # Heavy metal - proximity damage bonus
            damage_multiplier = 1.0

            # Ehitame kuuli omaduste dict-i - Build bullet properties dict
            bullet_props = {
                "is_crit": is_crit,
                "has_knockback": has_knockback,
                "knockback_force": knockback_force,
                "has_poison": has_poison,
                "poison_damage": poison_damage,
                "poison_duration": 4.0,
                "bounce_count": 0,
                "max_bounces": max_bounces,
                "damage_multiplier": 1.0,
                "bullet_radius": projectile_radius * (1.5 if has_knockback else 1.0),  # A bat visual: bigger bullet
            }

            if shot_count > 1:
                middle_index = (shot_count - 1) / 2
                for shot_index in range(shot_count):
                    spread_angle = (shot_index - middle_index) * multi_effective_spread
                    shot_direction = direction.rotate(spread_angle)
                    # Loo kuul ja rakenda konksud - Create bullet and apply spawn hooks
                    bullet = create_projectile(spawn_pos, shot_direction, bullet_props)
                    bullet = upgrade_manager.hooks.dispatch_bullet_spawn(bullet, player_stats)
                    projectiles.append(bullet)
            else:
                # Üks kuul - lisage väike juhuslik hajumine - Single bullet: add small random spread
                random_offset = random.uniform(-single_shot_spread, single_shot_spread)
                shot_direction = direction.rotate(random_offset)
                # Loo kuul ja rakenda konksud - Create bullet and apply spawn hooks
                bullet = create_projectile(spawn_pos, shot_direction, bullet_props)
                bullet = upgrade_manager.hooks.dispatch_bullet_spawn(bullet, player_stats)
                projectiles.append(bullet)

            # One bullet per sometimes - suvaline lisakuul - Random extra bullet
            if player_stats["random_bullet_chance"] > 0:
                if random.random() < player_stats["random_bullet_chance"]:
                    # Suvaline suund - Random direction
                    random_angle = random.uniform(0, 360)
                    random_direction = pygame.Vector2(1, 0).rotate(random_angle)
                    # Kopeeri kõik omadused peale suuna - Copy all properties except direction
                    random_bullet = create_projectile(spawn_pos, random_direction, bullet_props)
                    random_bullet = upgrade_manager.hooks.dispatch_bullet_spawn(random_bullet, player_stats)
                    projectiles.append(random_bullet)

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

    # Seina kokkupõrke efektid ja Waller hüpped
    # Wall hit effects and Waller bounces
    bullets_to_remove_wall = set()
    for i, projectile in enumerate(projectiles):
        if not point_in_polygon((projectile["pos"].x, projectile["pos"].y), map_vertices):
            max_bounces = projectile.get("max_bounces", 0)
            bounce_count = projectile.get("bounce_count", 0)

            if bounce_count < max_bounces:
                # Waller: arvuta peegeldus seina normaali järgi
                # Waller: calculate reflection off wall normal
                wall_normal = _get_wall_normal(projectile["pos"], map_vertices)
                if wall_normal:
                    # Peegelda kiirust - Reflect velocity
                    vel = pygame.Vector2(projectile["vel"])
                    dot_product = vel.dot(wall_normal)
                    reflected_vel = vel - 2 * dot_product * wall_normal

                    # Rakenda kiiruse suurendust - Apply speed increase
                    speed_mult = projectile.get("bounce_speed_multiplier", 1.0) if "bounce_speed_multiplier" in projectile else 1.0
                    # Use player_stats for bounce speed multiplier
                    reflected_vel *= player_stats.get("bounce_speed_multiplier", 1.0)

                    projectile["vel"] = reflected_vel
                    projectile["bounce_count"] = bounce_count + 1

                    # Tagasta kuul kaardi sisse - Push bullet back inside map
                    projectile["pos"] = old_positions[i] + wall_normal * 5
                    continue

            # Eemalda kuul - Remove bullet
            # Mängi seina tabamuse heli kuuli asukohas - Play wall hit sound at projectile position
            sound_manager.play("wall_hit", position=pygame.Vector2(old_positions[i]))
            vfx_manager.spawn_hit_effect(old_positions[i], "wall",
                                         direction=projectile["vel"].normalize())
            bullets_to_remove_wall.add(i)

    # Eemalda seinast eemaldatud kuulid - Remove wall-removed bullets
    if bullets_to_remove_wall:
        projectiles = [p for i, p in enumerate(projectiles) if i not in bullets_to_remove_wall]
        old_positions = [p for i, p in enumerate(old_positions) if i not in bullets_to_remove_wall]

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
            if not game_over and player_invulnerable_timer <= 0 and not dev_invulnerable:
                # Kontrolli kaitseperioodi - Check grace period
                # Kaitseperioodil on mängija haavamatu - During grace period, player is invulnerable
                is_grace_period = upgrade_manager._is_first_hit and upgrade_manager.time_without_hit < upgrade_manager._grace_period

                if is_grace_period:
                    # Kaitseperiood - ei kahju ega uuendusi - Grace period: no damage, no upgrades
                    # Märgi esimene tabamus toimunuks - Mark first hit as occurred
                    upgrade_manager._is_first_hit = False
                    upgrade_manager.time_without_hit = 0
                    # Lüka vaenlane siiski tagasi - Still push enemy away
                    push_dir = (enemy_unit.pos - player_pos).normalize()
                    enemy_unit.pos = player_pos + push_dir * min_dist
                    continue

                # Tavaline tabamus - Normal hit
                player_health -= 1
                player_invulnerable_timer = player_invulnerable_duration
                # Mängi mängija tabamuse heli - Play player hit sound at player position
                sound_manager.play("player_hit", position=pygame.Vector2(player_pos))

                # Cleave on hit - tapa lähedal olevad vaenlased, et vältida topelt tabamust
                # Kill nearby enemies when hit to prevent getting hit twice in a row
                cleave_radius = 250  # pikslites - in pixels (buffed from 120)
                enemies_cleaved = []
                for nearby_enemy in enemies:
                    if nearby_enemy.pos.distance_to(player_pos) < cleave_radius:
                        enemies_cleaved.append(nearby_enemy)
                
                for cleaved_enemy in enemies_cleaved:
                    if not cleaved_enemy.is_alive():
                        continue
                    score += cleaved_enemy.score_value
                    cleaved_enemy.health = 0
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(cleaved_enemy.pos), "enemy"
                    )
                    sound_manager.play("enemy_dead", position=pygame.Vector2(cleaved_enemy.pos))
                
                # Eemalda surnud cleave'i vaenlased - Remove cleave-killed enemies
                if enemies_cleaved:
                    cleaved_ids = {id(e) for e in enemies_cleaved}
                    enemies = [e for e in enemies if id(e) not in cleaved_ids]
                    # Eemalda debuff'id kohapeal - Remove debuffs in place
                    for eid in list(enemy_debuffs.keys()):
                        if eid in cleaved_ids:
                            del enemy_debuffs[eid]

                # Uuenda uuenduste haldurit - Update upgrade manager on hit
                # Oluline: salvesta aeg enne taimeri lähtestamist kuvamiseks
                # Important: save time before resetting timer for display
                time_before_hit = upgrade_manager.time_without_hit
                should_trigger = upgrade_manager.should_trigger_upgrade()
                upgrade_manager.on_player_hit()  # Lähtestab taimeri - Resets the timer

                # Kui grazes periood on möödas, näita uuenduste valikut
                # If grace period passed, show upgrade selection
                if should_trigger:
                    upgrade_manager.generate_choices()
                    upgrade_selection_screen.set_time_without_hit(time_before_hit)
                    upgrade_selection_screen._build_ui()  # Ehitab kaardid uuesti - Rebuild cards
                    upgrade_selection_screen.reset_cooldown()  # 0.5s viivitus enne klikkimist - 0.5s delay before clicking
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
    # enemies_to_remove already initialized above for cactus armor

    for p_idx, projectile in enumerate(projectiles if not game_over else []):
        for e_idx, enemy_unit in enumerate(enemies):
            if e_idx in enemies_to_remove:
                continue
            # Kasuta kuuli raadiust kokkupõrke kontrollimiseks - Use bullet radius for collision
            bullet_radius = projectile.get("bullet_radius", projectile_radius)
            if enemy_unit.collides_with(projectile["pos"], bullet_radius):
                bullets_to_remove.add(p_idx)

                # ============================================
                # Kahju arvutamine - Damage calculation
                # ============================================
                base_damage = 10  # Baaskahju - Base damage (×10 scale)

                # Sharp bullets - kriitiline löök - Critical strike
                if projectile.get("is_crit", False):
                    base_damage = round(projectile.get("crit_multiplier", 3.0) * base_damage)

                # Heavy metal - läheduse kahju boonus - Proximity damage bonus
                enemy_dist = enemy_unit.pos.distance_to(player_pos)
                proximity_bonus = player_stats.get("proximity_damage_bonus", 0.0)
                if enemy_dist < HEAVY_METAL_RADIUS and proximity_bonus > 0:
                    # Rakenda ainult otsesele kahjule - Apply to direct damage only
                    base_damage = round(base_damage * (1 + proximity_bonus))

                # Mängi vaenlase tabamuse heli vaenlase asukohas - Play enemy hit sound
                sound_manager.play("enemy_hit", position=pygame.Vector2(enemy_unit.pos))

                # A bat - tagasilöök - Knockback
                if projectile.get("has_knockback", False):
                    kb_force = projectile.get("knockback_force", 0.0)
                    if kb_force > 0:
                        # Lüka vaenlast tagasi kuuli liikumissuunas - Push enemy in bullet direction
                        bullet_vel = pygame.Vector2(projectile["vel"])
                        if bullet_vel.length() > 0:
                            kb_direction = bullet_vel.normalize()
                            enemy_unit.pos += kb_direction * kb_force * dt * 2

                # Green Juice - mürgi rakendamine - Apply poison
                if projectile.get("has_poison", False):
                    poison_dmg = projectile.get("poison_damage", 0.0)
                    poison_dur = projectile.get("poison_duration", 4.0)
                    if poison_dmg > 0:
                        enemy_id = id(enemy_unit)
                        # Mürgi uuendamine: lähtesta taimer - Refresh poison: reset timer
                        if enemy_id in enemy_debuffs:
                            enemy_debuffs[enemy_id]["poison_timer"] = poison_dur
                            enemy_debuffs[enemy_id]["poison_damage"] = poison_dmg
                        else:
                            enemy_debuffs[enemy_id] = {
                                "poison_timer": poison_dur,
                                "poison_damage": poison_dmg,
                            }

                # Rakenda kahju vaenlasele - Apply damage to enemy
                if enemy_unit.take_damage(base_damage):
                    enemies_to_remove.add(e_idx)
                    score += enemy_unit.score_value
                    # Mängi vaenlase surma heli vaenlase asukohas - Play enemy death sound
                    sound_manager.play("enemy_dead", position=pygame.Vector2(enemy_unit.pos))
                    vfx_manager.spawn_hit_effect(
                        pygame.Vector2(enemy_unit.pos), "enemy"
                    )

                    # Eemalda debuff'id surnud vaenlaselt - Remove debuffs from dead enemy
                    enemy_id = id(enemy_unit)
                    if enemy_id in enemy_debuffs:
                        del enemy_debuffs[enemy_id]

                break

    # Eemalda tabatud kuulid ja surnud vaenlased
    if bullets_to_remove:
        projectiles = [p for i, p in enumerate(projectiles) if i not in bullets_to_remove]
    if enemies_to_remove:
        enemies = [e for i, e in enumerate(enemies) if i not in enemies_to_remove]
    # Eemalda cactus armor'iga surnud vaenlased - Remove cactus armor killed enemies by ID
    if enemies_to_remove_cactus:
        enemies = [e for e in enemies if id(e) not in enemies_to_remove_cactus]

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
            # PLUS klahv avab arendaja režiimi - PLUS key toggles dev mode
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PLUS:
                dev_panel.toggle()

        update_game_logic()

        # Kui mäng on läbi, vaheta game over ekraanile
        if game_over and current_state == GameState.PLAYING:
            game_over_screen.set_game_stats(score, difficulty_manager.get_elapsed_time())
            state_manager.change_state(GameState.GAME_OVER)

        render_game_screen()

        # Arendaja paneeli joonistamine - Draw dev panel
        if dev_panel.active:
            dev_panel.handle_events(events)
            dev_panel.update(dt)
            # Build upgrade counts for display
            upgrade_counts = {}
            for upgrade in upgrade_manager.active_upgrades:
                uid = upgrade.get("id", "unknown")
                upgrade_counts[uid] = upgrade_counts.get(uid, 0) + 1
            dev_panel.set_upgrade_counts(upgrade_counts)
            dev_panel.draw(screen)
            dev_panel.draw_info_overlay(screen, player_stats, difficulty_manager, enemies, game_time, upgrade_counts)

        # Arendaja haavamatus - Dev invincibility (handled via callback)
        # Just ensure dev_invulnerable flag is respected

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
