"""
Player class for the controllable character.
"""
import pygame
import math
from constants import (
    BLUE, WHITE, RED, GREEN, PLAYER_SPEED, PLAYER_SIZE, PLAYER_MAX_HEALTH,
    WeaponType, WEAPON_STATS
)
from bullet import Bullet


class Player:
    """Represents the player character."""
    
    def __init__(self, x, y):
        """
        Initialize the player.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
        """
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.weapon = WeaponType.PISTOL
        self.last_shot = 0
        self.weapon_angle = 0
    
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
            list: List of bullets created (empty if on cooldown)
        """
        current_time = pygame.time.get_ticks()
        weapon_stats = WEAPON_STATS[self.weapon]
        
        if current_time - self.last_shot > weapon_stats["cooldown"]:
            self.last_shot = current_time
            
            angle = math.atan2(target_y - self.y, target_x - self.x)
            speed = weapon_stats["bullet_speed"]
            damage = weapon_stats["damage"]
            
            if self.weapon == WeaponType.SHOTGUN:
                # Shotgun fires multiple bullets in spread pattern
                bullets = []
                for i in range(-2, 3):
                    spread_angle = angle + (i * 0.2)
                    bullets.append(Bullet(self.x, self.y, speed, spread_angle, damage))
                return bullets
            else:
                return [Bullet(self.x, self.y, speed, angle, damage)]
        return []
    
    def take_damage(self):
        """
        Player takes damage.
        
        Returns:
            bool: True if player died (health <= 0)
        """
        self.health -= 1
        return self.health <= 0
    
    def upgrade_weapon(self, weapon_type):
        """
        Upgrade player's weapon.
        
        Args:
            weapon_type (WeaponType): New weapon type
        """
        self.weapon = weapon_type
    
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
        pygame.draw.circle(screen, BLUE, (int(screen_x), int(screen_y)), self.size)
        
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