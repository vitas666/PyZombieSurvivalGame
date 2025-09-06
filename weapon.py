"""
Weapon pickup system.
"""
import pygame
import math
from constants import BROWN, BLACK, WHITE, GRAY, WeaponType, WEAPON_PICKUP_SIZE


class WeaponPickup:
    """Represents a weapon that can be picked up by the player."""
    
    def __init__(self, x, y, weapon_type):
        """
        Initialize a weapon pickup.
        
        Args:
            x (float): X position
            y (float): Y position
            weapon_type (WeaponType): Type of weapon
        """
        self.x = x
        self.y = y
        self.weapon_type = weapon_type
        self.size = WEAPON_PICKUP_SIZE
        self.collected = False
    
    def check_pickup(self, player_x, player_y):
        """
        Check if player is close enough to pickup weapon.
        
        Args:
            player_x (float): Player x position
            player_y (float): Player y position
            
        Returns:
            bool: True if weapon was picked up
        """
        if self.collected:
            return False
            
        distance = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        if distance < (self.size + 20):
            self.collected = True
            return True
        return False
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the weapon pickup on screen with detailed sprite.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        if self.collected:
            return
            
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if self.weapon_type == WeaponType.SHOTGUN:
            self._draw_shotgun(screen, screen_x, screen_y)
        elif self.weapon_type == WeaponType.MACHINE_GUN:
            self._draw_machine_gun(screen, screen_x, screen_y)
        elif self.weapon_type == WeaponType.GRENADE:
            self._draw_grenade(screen, screen_x, screen_y)
    
    def _draw_shotgun(self, screen, x, y):
        """Draw shotgun sprite - longer barrel, wooden stock."""
        # Shotgun barrel (longer and thicker)
        barrel_rect = pygame.Rect(x - 15, y - 3, 25, 6)
        pygame.draw.rect(screen, BLACK, barrel_rect)
        
        # Wooden stock/handle
        stock_rect = pygame.Rect(x - 18, y - 2, 8, 4)
        pygame.draw.rect(screen, BROWN, stock_rect)
        
        # Trigger guard
        pygame.draw.circle(screen, BLACK, (int(x - 12), int(y)), 3, 2)
        
        # Pump action grip
        pump_rect = pygame.Rect(x - 5, y - 4, 6, 8)
        pygame.draw.rect(screen, BROWN, pump_rect, 2)
        
        # Highlight to show it's pickupable
        pygame.draw.rect(screen, WHITE, (x - 20, y - 8, 35, 16), 2)
    
    def _draw_machine_gun(self, screen, x, y):
        """Draw machine gun sprite - bipod, magazine, automatic features."""
        # Main barrel (medium length)
        barrel_rect = pygame.Rect(x - 12, y - 2, 20, 4)
        pygame.draw.rect(screen, BLACK, barrel_rect)
        
        # Stock
        stock_rect = pygame.Rect(x - 16, y - 2, 6, 4)
        pygame.draw.rect(screen, BLACK, stock_rect)
        
        # Large magazine/drum
        magazine_rect = pygame.Rect(x - 8, y + 2, 8, 6)
        pygame.draw.rect(screen, GRAY, magazine_rect)
        pygame.draw.rect(screen, BLACK, magazine_rect, 1)
        
        # Bipod legs (distinctive feature)
        pygame.draw.line(screen, BLACK, (x - 5, y + 3), (x - 10, y + 10), 2)
        pygame.draw.line(screen, BLACK, (x + 5, y + 3), (x + 10, y + 10), 2)
        
        # Muzzle flash suppressor
        muzzle_rect = pygame.Rect(x + 8, y - 3, 4, 6)
        pygame.draw.rect(screen, GRAY, muzzle_rect)
        
        # Highlight to show it's pickupable
        pygame.draw.rect(screen, WHITE, (x - 18, y - 8, 30, 20), 2)
    
    def _draw_grenade(self, screen, x, y):
        """Draw grenade sprite - dark green with pin."""
        # Main grenade body
        pygame.draw.circle(screen, (50, 100, 50), (int(x), int(y)), 8)
        pygame.draw.circle(screen, (30, 80, 30), (int(x), int(y)), 8, 2)
        
        # Grenade segments/texture
        pygame.draw.line(screen, (30, 80, 30), (x - 6, y), (x + 6, y), 1)
        pygame.draw.line(screen, (30, 80, 30), (x, y - 6), (x, y + 6), 1)
        
        # Safety pin
        pygame.draw.circle(screen, (200, 200, 200), (int(x + 6), int(y - 6)), 2)
        
        # Highlight to show it's pickupable
        pygame.draw.rect(screen, WHITE, (x - 12, y - 12, 24, 24), 2)