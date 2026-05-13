import math

# Uuenduste register - Upgrade registry
# Iga uuendus on dictionary järgmiste võtmetega:
# Each upgrade is a dictionary with the following keys:
#   id (str): Unique identifier
#   name (str): Display name
#   description (str): What this upgrade does
#   rarity (str): One of the Rarity constants
#   effect (dict): Effect definition - either stat modification or hooks
#   apply (function, optional): Custom apply function for complex stacking logic
#   max_stacks (int, optional): Maximum times this upgrade can be picked (-1 for unlimited)


class Rarity:
    """Rariteedi tasemed - Rarity tiers for upgrades."""
    COMMON = "common"       # Tavaline - Common
    UNCOMMON = "uncommon"   # Ebatavaline - Uncommon
    RARE = "rare"           # Haruldane - Rare
    EPIC = "epic"           # Eepiline - Epic
    LEGENDARY = "legendary" # Legendaarne - Legendary

    # All rarities in order from lowest to highest
    ALL = [COMMON, UNCOMMON, RARE, EPIC, LEGENDARY]


# Rariteedi kuvamise seaded - Rarity display properties
RARITY_CONFIG = {
    Rarity.COMMON:      {"color": (180, 180, 180), "label": "Common",      "border": (140, 140, 140)},
    Rarity.UNCOMMON:    {"color": (80, 200, 80),   "label": "Uncommon",    "border": (50, 160, 50)},
    Rarity.RARE:        {"color": (80, 140, 255),  "label": "Rare",        "border": (50, 100, 220)},
    Rarity.EPIC:        {"color": (180, 80, 255),  "label": "Epic",        "border": (140, 50, 220)},
    Rarity.LEGENDARY:   {"color": (255, 200, 50),  "label": "Legendary",   "border": (220, 160, 20)},
}

# Alustavad tõenäosused iga rariteedi jaoks (kergesti muudetav)
# Base chance weights for each rarity (easily tweakable)
BASE_RARITY_CHANCES = {
    Rarity.COMMON:      80.0,
    Rarity.UNCOMMON:    10.0,
    Rarity.RARE:        6.0,
    Rarity.EPIC:        3.0,
    Rarity.LEGENDARY:   1.0,
}


def apply_upgrade_effect(upgrade, stats, hooks_manager):
    """Rakenda uuenduse efekt - Apply upgrade effect.
    
    Handles both stat-based effects and custom apply functions.
    """
    effect = upgrade.get("effect")
    
    if effect is not None and effect.get("type") == "hook":
        # Konksupõhine uuendus - Hook-based upgrade
        hook_defs = effect.get("hooks", {})
        for hook_name, callback in hook_defs.items():
            hooks_manager.register(hook_name, callback)
    
    # Kasuta apply funktsiooni kui see on olemas - Use apply function if available
    if "apply" in upgrade:
        upgrade["apply"](stats)
    elif effect is not None and effect.get("type") == "stat":
        # Lihtne statistika muutmine - Simple stat modification
        stat = effect.get("stat")
        if stat:
            current = stats.get(stat, 0)
            if "amount" in effect:
                stats[stat] = current + effect["amount"]
            elif "multiplier" in effect:
                stats[stat] = current * effect["multiplier"]


# Uuenduste register - Upgrade registry
UPGRADES = []


def register_upgrade(upgrade):
    """Registreeri uus uuendus - Register a new upgrade."""
    UPGRADES.append(upgrade)


def get_upgrades_by_rarity(rarity):
    """Tagastab kõik antud rariteediga uuendused - Get all upgrades of a given rarity."""
    return [u for u in UPGRADES if u.get("rarity") == rarity]


# ============================================
# Uuenduste definitsioonid - Upgrade definitions
# ============================================

# 1. Thruster Tuning - Common, +10% speed, additive
register_upgrade({
    "id": "thruster_tuning",
    "name": "Thruster Tuning",
    "description": "Increases the player's speed incrementally (+10%)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("speed_multiplier", stats.get("speed_multiplier", 1.0) + 0.10),
})

# 2. Weapon Cooling - Common, +10% fire rate, additive
register_upgrade({
    "id": "weapon_cooling",
    "name": "Weapon Cooling",
    "description": "Increases the player's fire rate incrementally (+10%)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("fire_rate_multiplier", stats.get("fire_rate_multiplier", 1.0) + 0.10),
})

# 3. (a few) sharp bullets - Common, +10% crit chance, caps at 10 stacks (100%)
register_upgrade({
    "id": "sharp_bullets",
    "name": "(a few) sharp bullets",
    "description": "Adds a chance for a critical strike that deals triple damage (+10%)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("crit_chance", min(1.0, stats.get("crit_chance", 0.0) + 0.10)),
})

# 4. GPS tracker - Common, +1 accuracy, caps at 3
register_upgrade({
    "id": "gps_tracker",
    "name": "GPS tracker",
    "description": "Adds bullet accuracy, tightening spread (+1, caps at +3)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("accuracy", min(3, stats.get("accuracy", 0) + 1)),
})

# 5. A bat (the wooden type) - Common, knockback every 3rd shot, 2x knockback
# 5. A bat (the wooden type) - Common, knockback every 3rd shot, 2x knockback
register_upgrade({
    "id": "a_bat",
    "name": "A bat (the wooden type)",
    "description": "Every third shot pushes the enemy back a lot",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__(
        "knockback_force",
        max(10, 200 * (0.75 ** max(0, stats.get("_bat_stacks", 0))))
    ),
})

# Track bat stacks separately
_original_bat_apply = UPGRADES[-1]["apply"]
def _bat_apply_with_counter(stats):
    stacks = stats.get("_bat_stacks", 0) + 1
    stats["_bat_stacks"] = stacks
    # Each stack ADDS more knockback force (not less), 2x then 1.5x = 3x total
    # Stack 1: 1500, Stack 2: 2250, Stack 3: 3000, Stack 4: 3750...
    stats["knockback_force"] = 1500 + 750 * (stacks - 1)
UPGRADES[-1]["apply"] = _bat_apply_with_counter

# 6. Green Juice - Common, poison chance + damage, heavy exponential dropoff
register_upgrade({
    "id": "green_juice",
    "name": "Green Juice",
    "description": "Chance to inflict poison that deals flat damage per second for 4s (40% chance on first upgrade)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: None,  # Placeholder, replaced below
})

def _green_juice_apply(stats):
    stacks = stats.get("_juice_stacks", 0) + 1
    stats["_juice_stacks"] = stacks
    # Buffed + scaled ×10: 1st: 40% chance, 5.0 HP/s
    # 2nd: +10% (50%), +1.5 (6.5 HP/s)
    # 3rd: +7% (57%), +1.0 (7.5 HP/s)
    chance_increase = 0.40 if stacks == 1 else 0.10 * (0.7 ** (stacks - 2))
    damage_increase = 5.0 if stacks == 1 else 1.5 * (0.67 ** (stacks - 2))
    stats["poison_chance"] = min(1.0, stats.get("poison_chance", 0.0) + chance_increase)
    stats["poison_damage"] = stats.get("poison_damage", 0.0) + damage_increase
UPGRADES[-1]["apply"] = _green_juice_apply

# 8. Waller - Common, bullets bounce off walls once, exponential velocity decrease
register_upgrade({
    "id": "waller",
    "name": "Waller",
    "description": "Bullets bounce off walls once (+1 bounce, velocity increase decreases exponentially)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: None,  # Placeholder, replaced below
})

def _waller_apply(stats):
    stacks = stats.get("_waller_stacks", 0) + 1
    stats["_waller_stacks"] = stacks
    stats["max_bounces"] = stacks
    # Stack 1: 1.0x, Stack 2: 1.4x, Stack 3: 1.8x, Stack 4: 2.2x, Stack 5+: 2.5x cap
    stats["bounce_speed_multiplier"] = min(2.5, 1.0 + 0.4 * max(0, stacks - 1))
UPGRADES[-1]["apply"] = _waller_apply

# 9. One bullet per sometimes - Common, 30% extra random bullet, exponential dropoff
register_upgrade({
    "id": "one_bullet_per_sometimes",
    "name": "One bullet per sometimes",
    "description": "Shoots an additional bullet in a random direction 30% of the time",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: None,  # Placeholder, replaced below
})

def _random_bullet_apply(stats):
    stacks = stats.get("_random_stacks", 0) + 1
    stats["_random_stacks"] = stacks
UPGRADES[-1]["apply"] = _random_bullet_apply

# 7. Cactus armor - Common, kills close enemies, 2nd stack = bullet explosion, max 2
register_upgrade({
    "id": "cactus_armor",
    "name": "Cactus armor",
    "description": "Kills common enemies that get too close. Second stack adds bullet explosion.",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("cactus_armor_stacks", min(2, stats.get("cactus_armor_stacks", 0) + 1)),
})

# 10. The shift key - Common, dash ability, max 2 dashes
register_upgrade({
    "id": "the_shift_key",
    "name": "The shift key",
    "description": 'Unlock a "dash" (Shift key) toward cursor with invulnerability. Max 2 dashes.',
    "rarity": Rarity.COMMON,
    "apply": lambda stats: stats.__setitem__("dash_count", min(2, stats.get("dash_count", 0) + 1)),
})

# 11. Heavy metal - Common, +50% damage to enemies near player, +20% per stack
register_upgrade({
    "id": "heavy_metal",
    "name": "Heavy metal",
    "description": "Deal 50% more damage to enemies near the player (+20% per additional stack)",
    "rarity": Rarity.COMMON,
    "apply": lambda stats: None,  # Placeholder, replaced below
})

def _heavy_metal_apply(stats):
    stacks = stats.get("_hm_stacks", 0) + 1
    stats["_hm_stacks"] = stacks
    # First stack: +50%, subsequent stacks: +20% each
    if stacks == 1:
        stats["proximity_damage_bonus"] = 0.50
    else:
        stats["proximity_damage_bonus"] = 0.50 + 0.20 * (stacks - 1)
UPGRADES[-1]["apply"] = _heavy_metal_apply

