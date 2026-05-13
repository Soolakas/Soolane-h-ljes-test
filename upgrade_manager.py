import random
from upgrade_registry import UPGRADES, Rarity, get_upgrades_by_rarity, apply_upgrade_effect
from chance_scaler import get_scaled_chances, pick_rarity
from upgrade_hooks import UpgradeHooks

# ============================================
# Uuenduse halduri seaded - Upgrade manager configuration
# ============================================
UPGRADE_CHOICE_COUNT = 3        # Mitu uuendust mängijale näidatakse - How many upgrade choices to show
GRACE_PERIOD = 5.0              # Algse kaitseperioodi pikkus (sekundites) - Grace period at start of run (seconds)


class UpgradeManager:
    """Haldab mängusiseseid püsivaid uuendusi - Manages in-run permanent upgrades.
    
    Uuendused valitakse välja mängija tabamisel. Tõenäosused rariteetide
    jaoks kasvavad aja jooksul ilma tabamusteta.
    
    Upgrades are selected when the player gets hit. Rarity chances
    increase over time spent without getting hit.
    """

    def __init__(self, chance_scale_rate=0.02, grace_period=GRACE_PERIOD):
        """Algustab uuenduste halduri.
        
        Args:
            chance_scale_rate (float): Tõenäosuste muutumise kiirus.
                Chance scaling rate per second.
            grace_period (float): Kaitseperioodi pikkus sekundites.
                Grace period in seconds at start of run.
        """
        self.active_upgrades = []           # Käesoleva run-i uuendused - Active upgrades this run
        self.time_without_hit = 0.0         # Aeg viimasest tabamusest - Time since last hit
        self._chance_scale_rate = chance_scale_rate
        self._grace_period = grace_period
        self._hit_count = 0               # Tabamuste arv - Hit counter
        self._pending_choices = []          # Praegused valikud - Current upgrade choices
        self.hooks = UpgradeHooks()         # Konksude haldur - Hook manager

    def reset(self):
        """Lähtesta uue run-i jaoks - Reset for new run."""
        self.active_upgrades = []
        self.time_without_hit = 0.0
        self._hit_count = 0
        self._pending_choices = []
        self.hooks.clear()

    def update(self, dt):
        """Uuenda aega ilma tabamuseta - Track time without hit.
        
        Args:
            dt (float): Seconds since last frame.
        """
        self.time_without_hit += dt

    def on_player_hit(self):
        """Kutsutakse välja mängija tabamisel - Called when player gets hit.
        
        Suurendab tabamuste loendurit ja seadistab taimeri.
        Esimene tabamus: 30s, teine: 60s, kolmas: 90s jne.
        Increments hit counter and sets timer.
        First hit: 30s, second: 60s, third: 90s, etc.
        """
        self._hit_count += 1
        self.time_without_hit = self._hit_count * 30

    def should_trigger_upgrade(self):
        """Kas uuenduse valik peaks käivituma - Should upgrade selection trigger.
        
        Esimese tabamuse korral kontrollib kaitseperioodi.
        For first hit, checks grace period. After that, always triggers.
        
        Returns:
            bool: True kui uuenduse valik peaks toimuma.
        """
        if self._hit_count <= 1:
            return self.time_without_hit >= self._grace_period
        return True

    def generate_choices(self, count=UPGRADE_CHOICE_COUNT):
        """Genereeri uuenduste valikud põhinevalt hetke tõenäosustel.
        Generate upgrade choices based on current scaled chances.
        
        Kui uuendusi on vähem kui 'count', lubab duplikaate.
        If fewer than 'count' upgrades registered, allows duplicates.
        
        Returns:
            list: List of upgrade dictionaries (up to 'count' items).
        """
        if not UPGRADES:
            return []
        
        # Arvuta skaleeritud tõenäosused - Calculate scaled chances
        scaled_chances = get_scaled_chances(self.time_without_hit)
        
        choices = []
        for _ in range(count):
            # Vali rariteet - Pick a rarity
            rarity = pick_rarity(scaled_chances)
            
            # Leia selle rariteedi uuendused - Find upgrades of this rarity
            available = get_upgrades_by_rarity(rarity)
            
            if available:
                upgrade = random.choice(available)
                choices.append(upgrade)
            else:
                # Kui sellel rariteedil pole uuendusi, vali juhuslikult
                # If no upgrades of this rarity, pick from any available
                upgrade = random.choice(UPGRADES)
                choices.append(upgrade)
        
        self._pending_choices = choices
        return choices

    def apply_upgrade(self, upgrade, player_stats):
        """Rakenda uuendus mängija statistikale - Apply upgrade to player stats.
        
        Uuendused on kuhjatavad (stackable). Toetab nii statistika
        muutmisi kui konksupõhiseid uuendusi.
        Upgrades are stackable. Supports both stat modifications and hook-based upgrades.
        
        Args:
            upgrade (dict): The upgrade to apply.
            player_stats (dict): Player stats dictionary to modify.
        """
        apply_upgrade_effect(upgrade, player_stats, self.hooks)
        self.active_upgrades.append(upgrade)

    @property
    def pending_choices(self):
        """Tagastab praegused ootel valikud - Returns current pending choices."""
        return self._pending_choices

    def clear_pending(self):
        """Tühjenda ootel valikud - Clear pending choices."""
        self._pending_choices = []
