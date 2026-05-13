import math

# ============================================
# Difficulty configuration - Raskuse seaded
# ============================================
# All formulas scale infinitely - no max cap on difficulty
# Kõik valemid skaleeruvad lõpmatult - raskusel ei ole ülemist piiri

DIFFICULTY_INITIAL_DELAY = 10.0   # Grace period before ramp begins

# ============================================
# Spawn interval scaling - Tekitamise intervalli skaala
# ============================================
# Formula: max(MIN, BASE * exp(-RATE * time))
# Valem: max(MIN, BASE * exp(-RATE * aeg))
BASE_SPAWN_INTERVAL = 5.0          # Starting seconds between waves
MIN_SPAWN_INTERVAL = 0.3           # Fastest possible spawn interval
SPAWN_INTERVAL_RATE = 0.0045       # How fast interval decreases per second

# ============================================
# Wave size scaling - Lainete suuruse skaala
# ============================================
# Formula: BASE_MIN + floor(RATE_MIN * time), BASE_MAX + floor(RATE_MAX * time)
# Valem: BASE_MIN + floor(RATE_MIN * aeg), BASE_MAX + floor(RATE_MAX * aeg)
BASE_WAVE_SIZE_MIN = 1
BASE_WAVE_SIZE_MAX = 4
WAVE_SIZE_MIN_RATE = 0.02          # Minimum wave size increase per second
WAVE_SIZE_MAX_RATE = 0.02          # Maximum wave size increase per second
MAX_WAVE_SIZE_HARD_CAP = 15        # Absolute max enemies per wave (respecting MAX_ENEMIES)

# ============================================
# Enemy health scaling - Vaenlase tervise skaala
# ============================================
# Formula: BASE + floor(RATE * time)
# Valem: BASE + floor(RATE * aeg)
BASE_HEALTH_BONUS = 0
HEALTH_BONUS_RATE = 0.02           # Bonus health per second (1 HP at 60s)

# ============================================
# Enemy speed scaling - Vaenlase kiiruse skaala
# ============================================
# Formula: BASE * (1 + RATE * sqrt(time)) - sqrt for diminishing returns
# Valem: BASE * (1 + RATE * sqrt(aeg)) - sqrt kahaneva tootluse jaoks
BASE_SPEED_MULTIPLIER = 1.0
SPEED_RATE = 0.010                 # Speed increase rate (0.07 bonus at 60s)
MAX_SPEED_MULTIPLIER = 2.0         # Absolute cap on speed (was 3x, now 2x)

# ============================================
# Enemy type weighting - Tüüpide kaal
# ============================================
# Weights shift infinitely toward harder types
# Kaalud nihkuvad lõpmatult raskemate tüüpide poole
BASE_WEIGHTS = (0.89, 0.055, 0.055)  # (basic, fast, tank) - base weights
WEIGHT_SHIFT_RATE = 0.001           # How fast weights shift per second (gentle ramp)


class DifficultyManager:
    """Time-based difficulty scaling - Ajaline raskus.

    Tracks elapsed game time and provides scaling multipliers
    for spawn rate, enemy speed, health, and type distribution.
    All scaling formulas increase infinitely over time.
    Kõik skaleerimise valemid kasvavad lõpmatult aja jooksul.
    """

    def __init__(self):
        """Initialize difficulty manager with zero elapsed time."""
        self.elapsed_time = 0.0

    def update(self, dt):
        """Advance elapsed time by delta time - Aja uuendus.

        Args:
            dt (float): Seconds since last frame.
        """
        self.elapsed_time += dt

    def _get_effective_time(self):
        """Get time since grace period ended - Aeg pärast kaitseperioodi.
        
        Returns:
            float: Seconds of active difficulty scaling.
        """
        return max(0.0, self.elapsed_time - DIFFICULTY_INITIAL_DELAY)

    def get_spawn_interval(self):
        """Get current spawn interval in seconds - Tekitamise intervall.
        
        Uses exponential decay: interval = BASE * exp(-RATE * time)
        Valem: BASE * exp(-RATE * aeg) - eksponentsiaalne kahanemine.

        Returns:
            float: Seconds between spawn waves, decreasing over time.
        """
        t = self._get_effective_time()
        interval = BASE_SPAWN_INTERVAL * math.exp(-SPAWN_INTERVAL_RATE * t)
        return max(MIN_SPAWN_INTERVAL, interval)

    def get_wave_size(self):
        """Get current wave size - Lainete suurus.
        
        Returns:
            tuple: (min_wave_size, max_wave_size) for random selection.
        """
        t = self._get_effective_time()
        wave_min = BASE_WAVE_SIZE_MIN + int(WAVE_SIZE_MIN_RATE * t)
        wave_max = BASE_WAVE_SIZE_MAX + int(WAVE_SIZE_MAX_RATE * t)
        # Cap at hard limit and ensure min <= max
        wave_max = min(wave_max, MAX_WAVE_SIZE_HARD_CAP)
        wave_min = min(wave_min, wave_max)
        return (wave_min, wave_max)

    def get_enemy_speed_multiplier(self):
        """Get enemy speed multiplier - Kiiruse kordaja.
        
        Uses sqrt scaling: BASE * (1 + RATE * sqrt(time))
        Valem: BASE * (1 + RATE * sqrt(aeg)) - sqrt kahaneva tootluse jaoks.

        Returns:
            float: Multiplier applied to enemy base speed.
        """
        t = self._get_effective_time()
        multiplier = BASE_SPEED_MULTIPLIER * (1 + SPEED_RATE * math.sqrt(t))
        return min(MAX_SPEED_MULTIPLIER, multiplier)

    def get_enemy_health_bonus(self):
        """Get bonus health added to enemies - Tervise boonus.
        
        Uses linear scaling: BASE + RATE * time
        Valem: BASE + RATE * aeg - lineaarne kasv.

        Returns:
            int: Extra health points added to enemy base health.
        """
        t = self._get_effective_time()
        return int(BASE_HEALTH_BONUS + HEALTH_BONUS_RATE * t)

    def get_type_weights(self):
        """Get enemy type selection weights - Tüüpide kaalud.
        
        Smooth exponential curve targeting approximate checkpoints:
        - 1 min (50s eff): basic ~85%, fast/tank ~7.5% each
        - 2 min (110s eff): basic ~60%, fast/tank ~20% each
        - 3 min (170s eff): basic ~40%, fast/tank ~30% each
        
        Returns:
            tuple: (basic_weight, fast_weight, tank_weight) for random selection.
        """
        t = self._get_effective_time()
        
        # Exponential decay from 95% over time (no cap, no floor)
        basic = 0.95 * math.exp(-0.005 * t)
        
        # Fast and tank share remaining weight equally
        other = 1.0 - basic
        fast = other * 0.5
        tank = other * 0.5
        
        # Normalize
        total = basic + fast + tank
        return (basic / total, fast / total, tank / total)

    def get_elapsed_time(self):
        """Get formatted elapsed time string - Aja string.

        Returns:
            str: Time formatted as "M:SS" (e.g. "3:42").
        """
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
