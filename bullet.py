"""
Bullet class for projectiles fired by the player.
"""
import pygame
import math
from constants import YELLOW, BULLET_SIZE, MAP_SIZE


class Bullet:
    """Represents a bullet fired by the player."""
    
    def __init__(self, x, y, speed, angle, damage):
        """
        Initialize a bullet.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
            speed (float): Bullet speed
            angle (float): Direction angle in radians
            damage (int): Damage dealt by bullet
        """
        self.x = x
        self.y = y
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.damage = damage
        self.size = BULLET_SIZE
    
    def update(self):
        """Update bullet position."""
        self.x += self.dx
        self.y += self.dy
    
    def is_out_of_bounds(self):
        """Check if bullet is outside the map boundaries."""
        return self.x < 0 or self.x > MAP_SIZE or self.y < 0 or self.y > MAP_SIZE
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the bullet on screen.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), self.size)