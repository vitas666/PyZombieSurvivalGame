"""
Player class for the controllable character.
"""
import pygame
import math
from constants import (
    BLUE, WHITE, RED, GREEN, PLAYER_SPEED, PLAYER_SIZE, PLAYER_MAX_HEALTH,
    WeaponType, WEAPON_STATS, HeroType, HERO_STATS
)
from bullet import Bullet, HomingBullet
from grenade import Grenade


class Player:
    """Represents the player character."""
    
    def __init__(self, x, y, hero_type=HeroType.NATHAN):
        """
        Initialize the player.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
            hero_type (HeroType): Selected hero type
        """
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.weapons = [WeaponType.PISTOL, WeaponType.GRENADE]  # Two weapon slots
        self.current_weapon_index = 0
        self.last_shot = 0
        self.weapon_angle = 0
        self.grenade_count = 2  # Start with 2 grenades
        
        # Ammunition system
        self.ammo = {
            WeaponType.PISTOL: 12,  # 12 rounds
            WeaponType.SHOTGUN: 5,
            WeaponType.MACHINE_GUN: 30,
            WeaponType.GRENADE: float('inf'),  # Uses grenade_count instead
            WeaponType.MINIGUN: 200
        }
        
        # Reloading system
        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_weapon = None
        self.shotgun_shells_reloaded = 0  # Track partial shotgun reload
        
        # Power-up system
        self.insta_kill_active = False
        self.insta_kill_end_time = 0
        
        # Scoring system
        self.score = 0
        self.kills_normal = 0
        self.kills_fast = 0
        self.kills_boss = 0
        self.total_kills = 0
        
        # Skill streak system
        self.kills_without_hit = 0
        self.last_skill_bonus_at = 0  # Track last skill bonus milestone
        
        # Hero system
        self.hero_type = hero_type
        self.hero_color = HERO_STATS[hero_type]["color"]
        self.ability_charge = 0  # 0-100%
        self.ability_active = False
        self.ability_end_time = 0
    
    def move(self, dx, dy, obstacles):
        """
        Move the player, checking for collisions.
        
        Args:
            dx (float): Horizontal movement direction (-1, 0, 1)
            dy (float): Vertical movement direction (-1, 0, 1)
            obstacles (list): List of obstacle rectangles
        """
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        if not self._check_collision(new_x, new_y, obstacles):
            self.x = new_x
            self.y = new_y
            
        # Keep player within map boundaries
        self.x = max(self.size, min(1500 - self.size, self.x))  # MAP_SIZE imported in constants
        self.y = max(self.size, min(1500 - self.size, self.y))
    
    def _check_collision(self, x, y, obstacles):
        """
        Check if player would collide with obstacles at given position.
        
        Args:
            x (float): X position to check
            y (float): Y position to check
            obstacles (list): List of obstacle rectangles
            
        Returns:
            bool: True if collision detected
        """
        player_rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        for obstacle in obstacles:
            if player_rect.colliderect(obstacle):
                return True
        return False
    
    def shoot(self, target_x, target_y):
        """
        Attempt to shoot towards target position.
        
        Args:
            target_x (float): Target x coordinate
            target_y (float): Target y coordinate
            
        Returns:
            tuple: (bullets, grenades) - Lists of projectiles created
        """
        current_weapon = self.get_current_weapon()
        if current_weapon is None:
            return [], []
        
        # Cannot shoot while reloading (except shotgun interrupt)
        if self.is_reloading and current_weapon != WeaponType.SHOTGUN:
            return [], []
        
        # For shotgun, check if we can interrupt reload
        if self.is_reloading and current_weapon == WeaponType.SHOTGUN:
            if self.ammo[current_weapon] < 1:  # Need at least 1 shell to interrupt
                return [], []
            # Interrupt reload
            self.is_reloading = False
            
        current_time = pygame.time.get_ticks()
        weapon_stats = WEAPON_STATS[current_weapon]
        
        # Check ammunition
        if current_weapon == WeaponType.GRENADE:
            if self.grenade_count <= 0:
                return [], []
        else:
            if self.ammo[current_weapon] <= 0:
                return [], []  # No ammo
        
        if current_time - self.last_shot > weapon_stats["cooldown"]:
            self.last_shot = current_time
            
            angle = math.atan2(target_y - self.y, target_x - self.x)
            speed = weapon_stats["bullet_speed"]
            damage = weapon_stats["damage"]
            
            # Apply insta-kill power-up (massive damage)
            if self.insta_kill_active:
                damage = 1000
            
            if current_weapon == WeaponType.GRENADE:
                # Consume one grenade
                self.grenade_count -= 1
                
                # Throw grenade
                explosion_radius = weapon_stats["explosion_radius"]
                grenade = Grenade(self.x, self.y, speed, angle, damage, explosion_radius)
                return [], [grenade]
            elif current_weapon == WeaponType.SHOTGUN:
                # Consume ammo (except Nathan during ability)
                if not (self.hero_type == HeroType.NATHAN and self.ability_active):
                    self.ammo[current_weapon] -= 1
                    
                    # Auto-reload if ammo runs out
                    if self.ammo[current_weapon] <= 0:
                        self.start_reload()
                
                # Shotgun fires multiple bullets in spread pattern
                bullets = []
                for i in range(-2, 3):
                    spread_angle = angle + (i * 0.2)
                    bullets.append(Bullet(self.x, self.y, speed, spread_angle, damage))
                return bullets, []
            else:
                # Consume ammo for other weapons (except Nathan during ability)
                if self.ammo[current_weapon] != float('inf'):
                    # Nathan's ability = infinite ammo (no consumption)
                    if not (self.hero_type == HeroType.NATHAN and self.ability_active):
                        self.ammo[current_weapon] -= 1
                        
                        # Auto-reload if ammo runs out
                        if self.ammo[current_weapon] <= 0:
                            self.start_reload()
                
                # Create bullet (homing if Nathan's ability is active)
                if self.hero_type == HeroType.NATHAN and self.ability_active:
                    bullet = HomingBullet(self.x, self.y, speed, angle, damage)
                else:
                    bullet = Bullet(self.x, self.y, speed, angle, damage)
                
                return [bullet], []
        return [], []
    
    def take_damage(self):
        """
        Player takes damage.
        
        Returns:
            bool: True if player died (health <= 0)
        """
        self.health -= 1
        # Reset skill streak when hit
        self.kills_without_hit = 0
        self.last_skill_bonus_at = 0
        return self.health <= 0
    
    def get_current_weapon(self):
        """
        Get currently selected weapon.
        
        Returns:
            WeaponType or None: Current weapon
        """
        return self.weapons[self.current_weapon_index]
    
    def switch_weapon(self, direction=1):
        """
        Switch to next/previous weapon.
        
        Args:
            direction (int): 1 for next, -1 for previous
        """
        # Clear reload state when switching weapons
        self._clear_reload_state()
        
        # Find next available weapon slot
        for _ in range(len(self.weapons)):
            self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)
            if self.weapons[self.current_weapon_index] is not None:
                break
    
    def switch_to_weapon_slot(self, slot_index):
        """
        Switch to specific weapon slot if it has a weapon.
        
        Args:
            slot_index (int): Weapon slot index (0 or 1)
        """
        if 0 <= slot_index < len(self.weapons) and self.weapons[slot_index] is not None:
            # Clear reload state when switching weapons
            self._clear_reload_state()
            self.current_weapon_index = slot_index
    
    def add_weapon(self, weapon_type):
        """
        Add weapon to inventory, replacing if slots are full.
        
        Args:
            weapon_type (WeaponType): New weapon type
        """
        if weapon_type == WeaponType.GRENADE:
            # Grenades are consumable - add to ammo count
            self.add_grenades(1)
            # Also add grenade weapon to inventory if not present
            if WeaponType.GRENADE not in self.weapons:
                # Find empty slot first
                for i in range(len(self.weapons)):
                    if self.weapons[i] is None:
                        self.weapons[i] = weapon_type
                        return
                # If no empty slots, replace current weapon
                self.weapons[self.current_weapon_index] = weapon_type
            return
        
        # Check if we already have this weapon
        if weapon_type in self.weapons:
            # If we already have it, refill ammo
            if weapon_type in self.ammo:
                max_ammo = WEAPON_STATS[weapon_type]["max_ammo"]
                self.ammo[weapon_type] = max_ammo
            return
        
        # Find empty slot first
        for i in range(len(self.weapons)):
            if self.weapons[i] is None:
                self.weapons[i] = weapon_type
                # Initialize ammo for new weapon
                if weapon_type in self.ammo:
                    max_ammo = WEAPON_STATS[weapon_type]["max_ammo"]
                    self.ammo[weapon_type] = max_ammo
                return
        
        # If no empty slots, replace current weapon
        old_weapon = self.weapons[self.current_weapon_index]
        # Clear reload state since we're replacing current weapon
        self._clear_reload_state()
        self.weapons[self.current_weapon_index] = weapon_type
        # Initialize ammo for new weapon
        if weapon_type in self.ammo:
            max_ammo = WEAPON_STATS[weapon_type]["max_ammo"]
            self.ammo[weapon_type] = max_ammo
    
    def add_grenades(self, count):
        """
        Add grenades to player's ammunition.
        
        Args:
            count (int): Number of grenades to add
        """
        self.grenade_count += count
    
    def start_reload(self):
        """Start reloading current weapon if it needs ammo."""
        current_weapon = self.get_current_weapon()
        if current_weapon is None or current_weapon == WeaponType.GRENADE:
            return False
        
        # Prevent manual reload if already reloading
        if self.is_reloading:
            return False
        
        weapon_stats = WEAPON_STATS[current_weapon]
        max_ammo = weapon_stats["max_ammo"]
        
        # Check if weapon needs reloading
        if self.ammo[current_weapon] >= max_ammo or max_ammo == float('inf'):
            return False
        
        # Start reload
        self.is_reloading = True
        self.reload_start_time = pygame.time.get_ticks()
        self.reload_weapon = current_weapon
        self.shotgun_shells_reloaded = 0
        return True
    
    def update_reload(self):
        """Update reload progress."""
        if not self.is_reloading:
            return
        
        current_time = pygame.time.get_ticks()
        weapon_stats = WEAPON_STATS[self.reload_weapon]
        reload_time = weapon_stats["reload_time"]
        max_ammo = weapon_stats["max_ammo"]
        
        if self.reload_weapon == WeaponType.SHOTGUN:
            # Shotgun reloads one shell at a time
            time_per_shell = reload_time  # 1 second per shell
            
            # Calculate how many shells should be loaded by now based on time elapsed
            elapsed_time = current_time - self.reload_start_time
            shells_that_should_be_loaded = elapsed_time // time_per_shell
            
            # Load shells until we reach the target or max ammo
            while (self.shotgun_shells_reloaded < shells_that_should_be_loaded and 
                   self.ammo[self.reload_weapon] < max_ammo):
                self.ammo[self.reload_weapon] += 1
                self.shotgun_shells_reloaded += 1
            
            # Check if fully reloaded
            if self.ammo[self.reload_weapon] >= max_ammo:
                self.is_reloading = False
        else:
            # Other weapons reload all at once
            if current_time - self.reload_start_time >= reload_time:
                self.ammo[self.reload_weapon] = max_ammo
                self.is_reloading = False
    
    def update_powerups(self):
        """Update active power-ups."""
        current_time = pygame.time.get_ticks()
        
        # Check if insta-kill power-up has expired
        if self.insta_kill_active and current_time > self.insta_kill_end_time:
            self.insta_kill_active = False
        
        # Check if hero ability has expired
        if self.ability_active and current_time > self.ability_end_time:
            self.ability_active = False
            
            # Nathan's ability ending: reload current weapon to full ammo
            if self.hero_type == HeroType.NATHAN:
                current_weapon = self.get_current_weapon()
                if current_weapon and current_weapon in self.ammo:
                    max_ammo = WEAPON_STATS[current_weapon]["max_ammo"]
                    if max_ammo != float('inf'):
                        self.ammo[current_weapon] = max_ammo
                        # Clear any ongoing reload
                        self._clear_reload_state()
    
    def activate_insta_kill(self, duration):
        """
        Activate insta-kill power-up.
        
        Args:
            duration (int): Duration in milliseconds
        """
        current_time = pygame.time.get_ticks()
        self.insta_kill_active = True
        self.insta_kill_end_time = current_time + duration
    
    def activate_hero_ability(self):
        """Activate hero-specific ability if charged."""
        if self.ability_charge >= 100:
            current_time = pygame.time.get_ticks()
            
            if self.hero_type == HeroType.NATHAN:
                # Nathan: Homing bullets for 10 seconds
                self.ability_active = True
                self.ability_end_time = current_time + 10000
            elif self.hero_type == HeroType.KELLY:
                # Kelly: Restore health to full immediately
                self.health = self.max_health
            
            # Reset charge after use
            self.ability_charge = 0
            return True
        return False
    
    def add_kill(self, zombie_type):
        """
        Add a kill to the player's score and track kill streaks.
        
        Args:
            zombie_type (str): Type of zombie killed ("normal", "fast", or "boss")
        """
        # Add to kill counts
        if zombie_type == "normal":
            self.kills_normal += 1
            score_points = 100
        elif zombie_type == "fast":
            self.kills_fast += 1
            score_points = 150
        elif zombie_type == "boss":
            self.kills_boss += 1
            score_points = 1500
        else:
            score_points = 100  # Default
        
        self.total_kills += 1
        self.kills_without_hit += 1
        self.score += score_points
        
        # Charge hero ability (20% per kill if streak increases)
        if self.ability_charge < 100:
            self.ability_charge = min(100, self.ability_charge + 20)
        
        # Check for skill bonuses (every 10 kills without being hit)
        skill_bonus_milestone = (self.kills_without_hit // 10) * 10
        if (skill_bonus_milestone > self.last_skill_bonus_at and 
            skill_bonus_milestone >= 10):
            
            skill_bonus = skill_bonus_milestone * 50  # 10 kills = 500, 20 kills = 1000, etc.
            self.score += skill_bonus
            self.last_skill_bonus_at = skill_bonus_milestone
            
            return skill_bonus  # Return bonus for UI notification
        
        return 0  # No bonus
    
    def get_current_ammo(self):
        """Get current ammunition for active weapon."""
        current_weapon = self.get_current_weapon()
        if current_weapon == WeaponType.GRENADE:
            return self.grenade_count
        elif current_weapon in self.ammo:
            return self.ammo[current_weapon]
        return 0
    
    def get_max_ammo(self):
        """Get maximum ammunition for active weapon."""
        current_weapon = self.get_current_weapon()
        if current_weapon in WEAPON_STATS:
            return WEAPON_STATS[current_weapon]["max_ammo"]
        return 0
    
    def _clear_reload_state(self):
        """Clear the current reload state."""
        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_weapon = None
        self.shotgun_shells_reloaded = 0
    
    def upgrade_weapon(self, weapon_type):
        """
        Upgrade player's weapon (backwards compatibility).
        
        Args:
            weapon_type (WeaponType): New weapon type
        """
        self.add_weapon(weapon_type)
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the player on screen.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Draw player body
        pygame.draw.circle(screen, self.hero_color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw weapon pointing towards mouse
        weapon_length = 25
        weapon_end_x = screen_x + math.cos(self.weapon_angle) * weapon_length
        weapon_end_y = screen_y + math.sin(self.weapon_angle) * weapon_length
        pygame.draw.line(screen, WHITE, (screen_x, screen_y), (weapon_end_x, weapon_end_y), 3)
        
        # Draw front facing indicator
        body_front_x = screen_x + math.cos(self.weapon_angle) * (self.size - 5)
        body_front_y = screen_y + math.sin(self.weapon_angle) * (self.size - 5)
        pygame.draw.circle(screen, WHITE, (int(body_front_x), int(body_front_y)), 3)
        
        # Draw health bar
        health_bar_width = 40
        health_bar_height = 6
        health_ratio = self.health / self.max_health
        health_bar_x = screen_x - health_bar_width//2
        health_bar_y = screen_y - self.size - 15
        
        pygame.draw.rect(screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (health_bar_x, health_bar_y, health_bar_width * health_ratio, health_bar_height))