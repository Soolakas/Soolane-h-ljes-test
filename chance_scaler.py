import math
from upgrade_registry import BASE_RARITY_CHANCES, Rarity

# ============================================
# Tõenäosuste skaleerimise seaded - Chance scaling configuration
# ============================================
# Kõik neid väärtusi on lihtne muuta tasakaalustamiseks
# All these values are easily tweakable for balancing

CHANCE_SCALE_RATE = 0.002         # Kui kiiresti tõenäosused muutuvad sekundis
                                  # How fast chances change per second

# Iga rariteedi kasvutegur - Growth factor per rarity tier
# Suurem arv = kiirem kasv - Higher number = faster growth
RARITY_GROWTH_FACTORS = {
    Rarity.COMMON:      -1.0,   # Negatiivne: tavaline väheneb aja jooksul
                                # Negative: common decreases over time
    Rarity.UNCOMMON:    0.5,    # Ebatavaline kasvab mõõdukalt
                                # Uncommon grows moderately
    Rarity.RARE:        0.8,    # Haruldane kasvab keskmiselt
                                # Rare grows at medium rate
    Rarity.EPIC:        1.2,    # Eepiline kasvab kiiresti
                                # Epic grows quickly
    Rarity.LEGENDARY:   1.5,    # Legendaarne kasvab kõige kiiremini
                                # Legendary grows fastest
}


def get_scaled_chances(elapsed_time_without_hit):
    """Arvuta hetke rariteetide tõenäosused põhinevalt ajast viimase tabamuseta.
    Calculate current rarity chances based on time spent without getting hit.
    
    Valem:
    - Common: base * exp(-rate * time) - eksponentsiaalne kahanemine
    - Higher rarities: base * (1 + rate * growth_factor * time) - lineaarne kasv
    
    Formula:
    - Common: base * exp(-rate * time) - exponential decay
    - Higher rarities: base * (1 + rate * growth_factor * time) - linear growth
    
    Args:
        elapsed_time_without_hit (float): Seconds since last hit (or grace period end).
        
    Returns:
        dict: Scaled chance weights for each rarity.
    """
    t = elapsed_time_without_hit
    rate = CHANCE_SCALE_RATE
    
    scaled = {}
    for rarity in Rarity.ALL:
        base = BASE_RARITY_CHANCES[rarity]
        growth = RARITY_GROWTH_FACTORS.get(rarity, 0.0)
        
        if growth < 0:
            # Exponential decay for common
            scaled[rarity] = base * math.exp(growth * rate * t)
        else:
            # Linear growth with diminishing effect (using sqrt for soft cap)
            # sqrt gives growth that slows over time but never stops
            scaled[rarity] = base * (1 + growth * rate * math.sqrt(t))
    
    return scaled


def normalize_chances(scaled_chances):
    """Normaliseeri tõenäosused nii et need moodustavad 100%.
    Normalize chance weights so they sum to 1.0 (100%).
    
    Args:
        scaled_chances (dict): Raw scaled chance weights.
        
    Returns:
        dict: Normalized probabilities for each rarity.
    """
    total = sum(scaled_chances.values())
    if total <= 0:
        # Fallback: equal distribution
        count = len(scaled_chances)
        return {r: 1.0 / count for r in scaled_chances}
    
    return {rarity: weight / total for rarity, weight in scaled_chances.items()}


def pick_rarity(scaled_chances=None):
    """Vali juhuslik rariteet kaalutud tõenäosuste alusel.
    Pick a random rarity based on weighted probabilities.
    
    Args:
        scaled_chances (dict, optional): Pre-computed scaled chances.
            If None, calculates from elapsed_time_without_hit=0.
            
    Returns:
        str: Selected Rarity constant.
    """
    import random
    
    if scaled_chances is None:
        scaled_chances = get_scaled_chances(0)
    
    probabilities = normalize_chances(scaled_chances)
    
    # Weighted random selection
    rarities = list(probabilities.keys())
    weights = [probabilities[r] for r in rarities]
    return random.choices(rarities, weights=weights, k=1)[0]
