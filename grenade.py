"""
Grenade projectile system.
"""
import pygame
import math
from constants import RED, YELLOW, ORANGE


class Grenade:
    """Represents a grenade projectile that explodes on impact."""
    
    def __init__(self, x, y, speed, angle, damage, explosion_radius):
        """
        Initialize grenade.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
            speed (float): Grenade speed
            angle (float): Launch angle in radians
            damage (int): Explosion damage
            explosion_radius (float): Explosion radius
        """
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.size = 8
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.exploded = False
        self.explosion_timer = 0
        self.max_explosion_time = 20  # Frames to show explosion
        
        # Grenade flight timer - explodes after certain time
        self.flight_time = 0
        self.max_flight_time = 90  # Frames until auto-explosion
    
    def update(self):
        """Update grenade position and check for explosion."""
        if not self.exploded:
            self.x += self.dx
            self.y += self.dy
            self.flight_time += 1
            
            # Auto-explode after max flight time
            if self.flight_time >= self.max_flight_time:
                self.exploded = True
        else:
            self.explosion_timer += 1
    
    def check_collision(self, zombies, obstacles):
        """
        Check collision with zombies or obstacles and explode.
        
        Args:
            zombies (list): List of zombies
            obstacles (list): List of obstacle rectangles
            
        Returns:
            bool: True if grenade hit something and exploded
        """
        if self.exploded:
            return False
        
        # Check zombie collisions
        for zombie in zombies:
            distance = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
            if distance < (self.size + zombie.size):
                self.exploded = True
                return True
        
        # Check obstacle collisions
        grenade_rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
        for obstacle in obstacles:
            if grenade_rect.colliderect(obstacle):
                self.exploded = True
                return True
                
        return False
    
    def get_explosion_damage_targets(self, zombies, player):
        """
        Get all entities within explosion radius.
        
        Args:
            zombies (list): List of zombies
            player: Player object
            
        Returns:
            tuple: (damaged_zombies, player_in_range)
        """
        if not self.exploded:
            return [], False
        
        damaged_zombies = []
        player_in_range = False
        
        # Check zombies in explosion radius
        for zombie in zombies:
            distance = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
            if distance <= self.explosion_radius:
                damaged_zombies.append(zombie)
        
        # Check if player is in explosion radius
        player_distance = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
        if player_distance <= self.explosion_radius:
            player_in_range = True
        
        return damaged_zombies, player_in_range
    
    def is_finished(self):
        """
        Check if grenade animation is finished.
        
        Returns:
            bool: True if explosion animation is complete
        """
        return self.exploded and self.explosion_timer >= self.max_explosion_time
    
    def is_out_of_bounds(self):
        """
        Check if grenade is outside map boundaries.
        
        Returns:
            bool: True if out of bounds
        """
        return self.x < 0 or self.x > 1500 or self.y < 0 or self.y > 1500
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the grenade or explosion.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if not self.exploded:
            # Draw grenade as small dark circle
            pygame.draw.circle(screen, (50, 50, 50), (int(screen_x), int(screen_y)), self.size)
            pygame.draw.circle(screen, (100, 100, 100), (int(screen_x), int(screen_y)), self.size, 2)
        else:
            # Draw explosion effect
            explosion_progress = self.explosion_timer / self.max_explosion_time
            explosion_size = self.explosion_radius * (1 - explosion_progress * 0.5)
            
            # Multi-layered explosion effect
            if explosion_progress < 0.7:
                # Outer red ring
                pygame.draw.circle(screen, RED, (int(screen_x), int(screen_y)), 
                                 int(explosion_size), 3)
                # Middle orange ring
                pygame.draw.circle(screen, ORANGE, (int(screen_x), int(screen_y)), 
                                 int(explosion_size * 0.7), 3)
                # Inner yellow ring
                pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), 
                                 int(explosion_size * 0.4), 2)