"""
Power-up classes for special abilities.
"""
import pygame
import math
from constants import WHITE, YELLOW, RED


class PowerUp:
    """Base power-up class."""
    
    def __init__(self, x, y, pickup_radius=20):
        """
        Initialize a power-up.
        
        Args:
            x (float): X position
            y (float): Y position
            pickup_radius (int): Pickup detection radius
        """
        self.x = x
        self.y = y
        self.pickup_radius = pickup_radius
        self.collected = False
        self.pulse_time = 0
    
    def check_pickup(self, player_x, player_y):
        """
        Check if player is close enough to collect this power-up.
        
        Args:
            player_x (float): Player x position
            player_y (float): Player y position
            
        Returns:
            bool: True if collected
        """
        if self.collected:
            return False
            
        distance = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        if distance < self.pickup_radius:
            self.collected = True
            return True
        return False
    
    def update(self):
        """Update power-up animations."""
        self.pulse_time += 1
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the power-up on screen.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        if self.collected:
            return
            
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Pulsing effect
        pulse_size = int(self.pickup_radius + math.sin(self.pulse_time * 0.1) * 3)
        
        # Draw base circle
        pygame.draw.circle(screen, self._get_color(), (int(screen_x), int(screen_y)), pulse_size)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), pulse_size, 2)
        
        # Draw icon
        self._draw_icon(screen, screen_x, screen_y)
    
    def _get_color(self):
        """Get the power-up's color."""
        return WHITE
    
    def _draw_icon(self, screen, screen_x, screen_y):
        """Draw the power-up's icon."""
        pass


class InstaKillPowerUp(PowerUp):
    """Insta-kill power-up that makes all weapons deadly."""
    
    def __init__(self, x, y):
        """Initialize insta-kill power-up."""
        super().__init__(x, y)
        self.duration = 10000  # 10 seconds in milliseconds
    
    def _get_color(self):
        """Get the insta-kill power-up color (red)."""
        return RED
    
    def _draw_icon(self, screen, screen_x, screen_y):
        """Draw skull icon for insta-kill."""
        # Draw a simple skull icon (circle with X)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), 8)
        # Draw X eyes
        pygame.draw.line(screen, RED, (screen_x-4, screen_y-3), (screen_x-1, screen_y), 2)
        pygame.draw.line(screen, RED, (screen_x-1, screen_y-3), (screen_x-4, screen_y), 2)
        pygame.draw.line(screen, RED, (screen_x+1, screen_y-3), (screen_x+4, screen_y), 2)
        pygame.draw.line(screen, RED, (screen_x+4, screen_y-3), (screen_x+1, screen_y), 2)