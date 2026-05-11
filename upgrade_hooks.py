# ============================================
# Uuenduste konksusüsteem - Upgrade hook system
# ============================================
# Konksud võimaldavad uuendustel sekkuda mängu loogikasse erinevatel hetkedel.
# Hooks allow upgrades to intervene in game logic at specific points.
#
# Saadaval olevad konksud - Available hooks:
#   on_bullet_spawn(bullet, stats) -> modified_bullet
#       Called when a bullet is created. Can modify bullet dict.
#   on_bullet_hit(bullet, enemy, stats) -> dict with optional keys:
#       "damage": new damage value (default 1)
#       "keep_bullet": True to not remove bullet on hit (for piercing)
#       Called when a bullet hits an enemy.
#   on_frame_update(dt, stats, enemies, player_pos)
#       Called every frame. Use for auras, poison ticks, etc.
#   on_enemy_spawn(enemy, stats) -> modified_enemy
#       Called when an enemy spawns. Can modify enemy properties.
#   on_player_hit(stats, enemies)
#       Called when player takes damage from an enemy.


class UpgradeHooks:
    """Haldab uuenduste konkse - Manages upgrade hooks."""

    def __init__(self):
        # Iga konks on nimekira funktsioonidest
        # Each hook is a list of callback functions
        self._hooks = {
            "on_bullet_spawn": [],
            "on_bullet_hit": [],
            "on_frame_update": [],
            "on_enemy_spawn": [],
            "on_player_hit": [],
        }

    def register(self, hook_name, callback):
        """Registreeri uus konks - Register a new hook.
        
        Args:
            hook_name (str): Konksu nimi - Hook name.
            callback (function): Funktsioon, mida kutsutakse välja - Callback function.
        """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(callback)

    def clear(self):
        """Tühjenda kõik konksud - Clear all hooks."""
        for key in self._hooks:
            self._hooks[key] = []

    def dispatch_bullet_spawn(self, bullet, stats):
        """Saada bullet_spawn konks - Dispatch bullet spawn hook.
        
        Args:
            bullet (dict): Bullet dictionary.
            stats (dict): Player stats.
            
        Returns:
            dict: Possibly modified bullet dictionary.
        """
        for callback in self._hooks["on_bullet_spawn"]:
            result = callback(bullet, stats)
            if result is not None:
                bullet = result
        return bullet

    def dispatch_bullet_hit(self, bullet, enemy, stats):
        """Saada bullet_hit konks - Dispatch bullet hit hook.
        
        Args:
            bullet (dict): Bullet dictionary.
            enemy (Enemy): Enemy instance.
            stats (dict): Player stats.
            
        Returns:
            tuple: (damage, keep_bullet) where:
                damage (int): Damage to deal (default 1).
                keep_bullet (bool): Whether to keep the bullet after hit.
        """
        damage = 1
        keep_bullet = False
        for callback in self._hooks["on_bullet_hit"]:
            result = callback(bullet, enemy, stats)
            if result:
                if isinstance(result, dict):
                    if "damage" in result:
                        damage = result["damage"]
                    if "keep_bullet" in result:
                        keep_bullet = result["keep_bullet"]
                elif isinstance(result, (int, float)):
                    damage = int(result)
        return damage, keep_bullet

    def dispatch_frame_update(self, dt, stats, enemies, player_pos):
        """Saada frame_update konks - Dispatch frame update hook.
        
        Args:
            dt (float): Delta time.
            stats (dict): Player stats.
            enemies (list): List of enemy instances.
            player_pos (pygame.Vector2): Player position.
        """
        for callback in self._hooks["on_frame_update"]:
            callback(dt, stats, enemies, player_pos)

    def dispatch_enemy_spawn(self, enemy, stats):
        """Saada enemy_spawn konks - Dispatch enemy spawn hook.
        
        Args:
            enemy (Enemy): Enemy instance.
            stats (dict): Player stats.
            
        Returns:
            Enemy: Possibly modified enemy.
        """
        for callback in self._hooks["on_enemy_spawn"]:
            result = callback(enemy, stats)
            if result is not None:
                enemy = result
        return enemy

    def dispatch_player_hit(self, stats, enemies):
        """Saada player_hit konks - Dispatch player hit hook.
        
        Args:
            stats (dict): Player stats.
            enemies (list): List of enemy instances.
        """
        for callback in self._hooks["on_player_hit"]:
            callback(stats, enemies)
