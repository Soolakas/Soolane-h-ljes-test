# Uuenduste register - Upgrade registry
# Iga uuendus on dictionary järgmiste võtmetega:
# Each upgrade is a dictionary with the following keys:
#   id (str): Unique identifier
#   name (str): Display name
#   description (str): What this upgrade does
#   rarity (str): One of the Rarity constants
#   effect (dict): Effect definition - either stat modification or hooks
#   apply (function, optional): Legacy custom apply function (for backwards compatibility)
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
# Need not be percentages - they are used as weighted probabilities
BASE_RARITY_CHANCES = {
    Rarity.COMMON:      80.0,
    Rarity.UNCOMMON:    10.0,
    Rarity.RARE:        6.0,
    Rarity.EPIC:        3.0,
    Rarity.LEGENDARY:   1.0,
}

# Uuenduste register - Upgrade registry
# Uue uuenduse lisamiseks lisa see nimekirja:
# To add a new upgrade, append to this list:
#
# Simple stat-based upgrade example:
# {
#     "id": "extra_projectile",
#     "name": "Multi Shot",
#     "description": "Fire +1 additional projectile",
#     "rarity": Rarity.RARE,
#     "effect": {"type": "stat", "stat": "multi_shot_count", "amount": 1},
# },
#
# Hook-based upgrade example (for complex behavior like poison, aura, piercing):
# {
#     "id": "poison_bullet",
#     "name": "Poison Bullet",
#     "description": "Bullets apply poison that damages enemies over time",
#     "rarity": Rarity.EPIC,
#     "effect": {
#         "type": "hook",
#         "hooks": {
#             "on_bullet_hit": lambda bullet, enemy, stats: {
#                 "damage": 1,
#                 "keep_bullet": False,
#                 "apply_poison": True,  # custom key for game logic
#             },
#         },
#     },
# },
UPGRADES = []


def register_upgrade(upgrade):
    """Registreeri uus uuendus - Register a new upgrade.
    
    Args:
        upgrade (dict): Upgrade dictionary with id, name, description, rarity, effect.
    """
    UPGRADES.append(upgrade)


def get_upgrades_by_rarity(rarity):
    """Tagastab kõik antud rariteediga uuendused - Get all upgrades of a given rarity.
    
    Args:
        rarity (str): Rarity constant from the Rarity class.
        
    Returns:
        list: List of upgrade dictionaries matching the rarity.
    """
    return [u for u in UPGRADES if u.get("rarity") == rarity]


def apply_upgrade_effect(upgrade, stats, hooks_manager):
    """Rakenda uuenduse efekt - Apply upgrade effect.
    
    Handles both stat-based effects and hook-based effects.
    
    Args:
        upgrade (dict): The upgrade to apply.
        stats (dict): Player stats dictionary.
        hooks_manager (UpgradeHooks): Hook manager for registering hooks.
    """
    effect = upgrade.get("effect")
    
    if effect is None:
        # Legacy: use apply function if no effect defined
        if "apply" in upgrade:
            upgrade["apply"](stats)
        return
    
    effect_type = effect.get("type")
    
    if effect_type == "stat":
        # Lihtne statistika muutmine - Simple stat modification
        stat = effect.get("stat")
        if stat:
            current = stats.get(stat, 0)
            if "amount" in effect:
                # Lisa väärtus - Add value
                stats[stat] = current + effect["amount"]
            elif "multiplier" in effect:
                # Korruta väärtusega - Multiply value
                stats[stat] = current * effect["multiplier"]
            elif "value" in effect:
                # Seadistamine - Set value
                stats[stat] = effect["value"]
    
    elif effect_type == "hook":
        # Konksupõhine uuendus - Hook-based upgrade
        hook_defs = effect.get("hooks", {})
        for hook_name, callback in hook_defs.items():
            hooks_manager.register(hook_name, callback)
