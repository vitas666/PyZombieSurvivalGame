"""
Bullet class for projectiles fired by the player.
"""
import pygame
import math
from constants import YELLOW, RED, BULLET_SIZE, MAP_SIZE


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
    
    def update(self, obstacles=None):
        """
        Update bullet position and check for obstacle collisions.
        
        Args:
            obstacles (list): List of obstacle rectangles to check collision with
        """
        self.x += self.dx
        self.y += self.dy
        
        # Check collision with obstacles
        if obstacles and self.check_obstacle_collision(obstacles):
            return True  # Signal that bullet should be removed
        
        return False
    
    def check_obstacle_collision(self, obstacles):
        """
        Check if bullet collides with any obstacle.
        
        Args:
            obstacles (list): List of obstacle rectangles
            
        Returns:
            bool: True if collision detected
        """
        bullet_rect = pygame.Rect(
            self.x - self.size, 
            self.y - self.size, 
            self.size * 2, 
            self.size * 2
        )
        
        for obstacle in obstacles:
            if bullet_rect.colliderect(obstacle):
                return True
        return False
    
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


class HomingBullet(Bullet):
    """Homing bullet that tracks the nearest zombie."""
    
    def __init__(self, x, y, speed, angle, damage, duration=10000):
        """
        Initialize a homing bullet.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
            speed (float): Bullet speed
            angle (float): Initial direction angle in radians
            damage (int): Damage dealt by bullet
            duration (int): How long the bullet homes for (milliseconds)
        """
        super().__init__(x, y, speed, angle, damage)
        self.homing_duration = duration
        self.creation_time = pygame.time.get_ticks()
        self.speed = speed
        
    def update(self, obstacles=None, zombies=None):
        """
        Update homing bullet position, tracking nearest zombie.
        
        Args:
            obstacles (list): List of obstacle rectangles
            zombies (list): List of zombies to track
        """
        current_time = pygame.time.get_ticks()
        
        # Check if homing period is active
        if current_time - self.creation_time < self.homing_duration and zombies:
            # Find nearest zombie
            nearest_zombie = None
            min_distance = float('inf')
            
            for zombie in zombies:
                distance = math.sqrt((zombie.x - self.x)**2 + (zombie.y - self.y)**2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_zombie = zombie
            
            # Adjust direction toward nearest zombie
            if nearest_zombie:
                angle_to_zombie = math.atan2(nearest_zombie.y - self.y, nearest_zombie.x - self.x)
                self.dx = math.cos(angle_to_zombie) * self.speed
                self.dy = math.sin(angle_to_zombie) * self.speed
        
        # Update position
        self.x += self.dx
        self.y += self.dy
        
        # Check collision with obstacles
        if obstacles and self.check_obstacle_collision(obstacles):
            return True  # Signal that bullet should be removed
        
        return False
    
    def draw(self, screen, camera_x, camera_y):
        """Draw homing bullet with distinctive red color."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        pygame.draw.circle(screen, RED, (int(screen_x), int(screen_y)), self.size)