import os
import pygame


# Heliefektide kaardistamine - Sound effect name mapping
# Iga klahv on lühike identifikaator, väärtus on tegelik failinimi
# Each key is a short identifier, value is the actual filename
SOUND_MAP = {
    "bullet": "Bullet shoot.wav",        # Kuuli laskmine - Player shooting
    "wall_hit": "Wall hit.wav",           # Seina tabamus - Projectile hitting wall
    "enemy_hit": "enemy hit.wav",         # Vaenlase tabamus - Enemy taking damage
    "enemy_dead": "enemy dead.wav",       # Vaenlase surm - Enemy killed
    "player_hit": "get hit.wav",          # Mängija tabamus - Player taking damage
    "player_die": "player die.wav",       # Mängija surm - Player death
    "press_start": "press start.wav",     # Mängu startimine - Game start / menu action
}


class SoundManager:
    """Heliefektide haldur - Manages loading, playing, and volume control for game sound effects."""

    # Maksimaalne kaugus, millelt heli on veel kuuldav (pikslites)
    # Maximum distance at which sound is still audible (in pixels)
    MAX_DISTANCE = 1000

    def __init__(self, sfx_volume=0.8):
        """Algustab helihalduri.
        
        Args:
            sfx_volume (float): Helitugevus 0.0 (vaikne) kuni 1.0 (vali).
                Volume from 0.0 (silent) to 1.0 (full).
        """
        self._sounds = {}                  # Laaditud helide kollektsioon - Loaded sounds collection
        self._volume = sfx_volume          # Aluseline helitugevus - Base volume level
        self._player_pos = None            # Mängija asukoht maailmas - Player world position
        self._load_sounds()                # Lae kõik heliefektid - Load all sound effects

    def _load_sounds(self):
        """Laeb kõik heliefektid assets/sfx kaustast.
        Loads all sound effects from the assets/sfx directory."""
        # Leia sfx kaust - Find sfx directory
        sfx_dir = os.path.join(os.path.dirname(__file__), "assets", "sfx")
        for key, filename in SOUND_MAP.items():
            path = os.path.join(sfx_dir, filename)
            if os.path.exists(path):
                self._sounds[key] = pygame.mixer.Sound(path)
                # Sea Sound objekt alati täishelile, helitugevust juhitakse kanali kaudu
                # Always set Sound object to full volume, volume is controlled via channel
                self._sounds[key].set_volume(1.0)

    def set_player_position(self, pos):
        """Uuendab mängija asukohta kauguse arvutamiseks.
        Updates player position for distance-based volume calculation.
        
        Args:
            pos (pygame.Vector2): Mängija asukoht maailmas - Player world position.
        """
        self._player_pos = pos

    def _calculate_distance_volume(self, sound_pos):
        """Arvutab helitugevuse põhinevalt kaugusel mängijast.
        Calculates volume based on distance from player.
        Lineaarne sumbumine: täisheli mängija juures, vaikus MAX_DISTANCE kaugusel.
        Linear falloff: full volume at player, silent at MAX_DISTANCE.
        
        Args:
            sound_pos (pygame.Vector2): Heli allika asukoht - Sound source position.
            
        Returns:
            float: Kauguse põhine helitugevus 0.0 kuni 1.0.
                Distance-based volume from 0.0 to 1.0.
        """
        if self._player_pos is None:
            return 1.0
        
        distance = self._player_pos.distance_to(sound_pos)
        # Lineaarne sumbumine kaugusega - Linear falloff with distance
        distance_factor = max(0.0, 1.0 - (distance / self.MAX_DISTANCE))
        return distance_factor

    def play(self, name, position=None):
        """Mängib heliefekti antud nime järgi.
        Plays a sound effect by its registered name.
        
        Args:
            name (str): Heliefekti identifikaator SOUND_MAP-ist.
                Sound effect identifier from SOUND_MAP.
            position (pygame.Vector2, optional): Heli allika asukoht maailmas.
                Kui määratud, rakendub kaugusepõhine helitugevus.
                Sound source world position. If given, distance-based volume is applied.
        """
        if name not in self._sounds:
            return
        
        sound = self._sounds[name]
        # Arvuta efektiivne helitugevus: aluseline + kauguse sumbumine
        # Calculate effective volume: base volume * distance attenuation
        effective_volume = self._volume
        if position is not None:
            distance_factor = self._calculate_distance_volume(position)
            effective_volume *= distance_factor
        
        # Mängi uuel kanalis - Play on a new channel (enables concurrent sounds)
        channel = sound.play()
        if channel:
            channel.set_volume(effective_volume)

    def set_volume(self, volume):
        """Uuendab heliefektide baashelitugevust.
        Updates the base volume for sound effects.
        
        Note: Tegelik helitugevus rakendatakse iga mängimise ajal kanali tasemel.
        Actual volume is applied per-channel at play time.
        
        Args:
            volume (float): Uus baashelitugevus 0.0 kuni 1.0.
                New base volume from 0.0 to 1.0.
        """
        self._volume = max(0.0, min(1.0, volume))

    @property
    def volume(self):
        """Tagastab praeguse helitugevuse - Returns current volume level."""
        return self._volume
