"""
Zombie classes for enemy AI.
"""
import pygame
import math
import random
from constants import (
    RED, WHITE, BLACK, ORANGE,
    ZOMBIE_SPEED, ZOMBIE_SIZE, ZOMBIE_HEALTH,
    FAST_ZOMBIE_SPEED, FAST_ZOMBIE_SIZE, FAST_ZOMBIE_HEALTH,
    ZOMBIE_STUCK_THRESHOLD, ZOMBIE_AVOIDANCE_DURATION
)


class Zombie:
    """Base zombie class with improved pathfinding AI."""
    
    def __init__(self, x, y):
        """
        Initialize a zombie.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
        """
        self.x = x
        self.y = y
        self.size = ZOMBIE_SIZE
        self.speed = ZOMBIE_SPEED
        self.health = ZOMBIE_HEALTH
        self.max_health = ZOMBIE_HEALTH
        self.last_damage_time = 0
        self.angle_to_player = 0
        
        # AI pathfinding variables
        self.stuck_counter = 0
        self.last_x = x
        self.last_y = y
        self.avoidance_angle = 0
        self.avoidance_timer = 0
    
    def update(self, player_x, player_y, obstacles, other_zombies=None):
        """
        Update zombie AI and movement.
        
        Args:
            player_x (float): Player x position
            player_y (float): Player y position
            obstacles (list): List of obstacle rectangles
            other_zombies (list): List of other zombies for collision avoidance
        """
        # Detect if zombie is stuck
        movement_distance = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        
        if movement_distance < 0.5:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        
        self.last_x = self.x
        self.last_y = self.y
        
        # Calculate angle to player
        self.angle_to_player = math.atan2(player_y - self.y, player_x - self.x)
        
        # Determine movement angle
        if self.avoidance_timer > 0:
            # Continue avoidance movement
            self.avoidance_timer -= 1
            movement_angle = self.avoidance_angle
        elif self.stuck_counter > ZOMBIE_STUCK_THRESHOLD:
            # Enter avoidance mode when stuck
            self.avoidance_angle = self.angle_to_player + random.uniform(-1.5, 1.5)
            self.avoidance_timer = ZOMBIE_AVOIDANCE_DURATION
            self.stuck_counter = 0
            movement_angle = self.avoidance_angle
        else:
            # Normal movement towards player
            movement_angle = self.angle_to_player
        
        # Calculate movement
        dx = math.cos(movement_angle) * self.speed
        dy = math.sin(movement_angle) * self.speed
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Try movement with collision detection
        if not self._check_collision(new_x, new_y, obstacles, other_zombies):
            self.x = new_x
            self.y = new_y
        else:
            self._handle_collision(movement_angle, obstacles, other_zombies)
    
    def _handle_collision(self, movement_angle, obstacles, other_zombies):
        """
        Handle collision by trying alternative movement patterns.
        
        Args:
            movement_angle (float): Original movement angle
            obstacles (list): List of obstacle rectangles
            other_zombies (list): List of other zombies
        """
        moved = False
        
        # Try axis-aligned movement
        dx = math.cos(movement_angle) * self.speed
        dy = math.sin(movement_angle) * self.speed
        
        if not self._check_collision(self.x + dx, self.y, obstacles, other_zombies):
            self.x += dx
            moved = True
        elif not self._check_collision(self.x, self.y + dy, obstacles, other_zombies):
            self.y += dy
            moved = True
        
        # If still blocked, try wall sliding
        if not moved:
            wall_slide_angles = [
                movement_angle + 0.5, movement_angle - 0.5, 
                movement_angle + 1.0, movement_angle - 1.0,
                movement_angle + 1.5, movement_angle - 1.5
            ]
            
            for slide_angle in wall_slide_angles:
                slide_dx = math.cos(slide_angle) * self.speed * 0.7
                slide_dy = math.sin(slide_angle) * self.speed * 0.7
                slide_x = self.x + slide_dx
                slide_y = self.y + slide_dy
                
                if not self._check_collision(slide_x, slide_y, obstacles, other_zombies):
                    self.x = slide_x
                    self.y = slide_y
                    break
    
    def _check_collision(self, x, y, obstacles, other_zombies=None):
        """
        Check collision with obstacles and other zombies.
        
        Args:
            x (float): X position to check
            y (float): Y position to check
            obstacles (list): List of obstacle rectangles
            other_zombies (list): List of other zombies
            
        Returns:
            bool: True if collision detected
        """
        zombie_rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        
        # Check obstacle collisions
        for obstacle in obstacles:
            if zombie_rect.colliderect(obstacle):
                return True
        
        # Check zombie-to-zombie collisions (optional anti-clustering)
        if other_zombies:
            for other in other_zombies:
                if other != self:
                    distance = math.sqrt((x - other.x)**2 + (y - other.y)**2)
                    if distance < (self.size + other.size) * 0.8:
                        return True
        
        return False
    
    def take_damage(self, damage):
        """
        Take damage and track damage time for visual effects.
        
        Args:
            damage (int): Amount of damage to take
            
        Returns:
            bool: True if zombie died
        """
        self.health -= damage
        self.last_damage_time = pygame.time.get_ticks()
        return self.health <= 0
    
    def can_damage_player(self, player_x, player_y):
        """
        Check if zombie is close enough to damage player.
        
        Args:
            player_x (float): Player x position
            player_y (float): Player y position
            
        Returns:
            bool: True if can damage player
        """
        distance = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        return distance < (self.size + 20)
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the zombie on screen.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Flash white when taking damage
        flash_time = pygame.time.get_ticks() - self.last_damage_time
        color = WHITE if flash_time < 200 else RED
            
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw hands pointing at player
        self._draw_hands(screen, screen_x, screen_y, flash_time)
    
    def _draw_hands(self, screen, screen_x, screen_y, flash_time):
        """
        Draw zombie hands pointing towards player.
        
        Args:
            screen: Pygame screen surface
            screen_x (float): Screen x coordinate
            screen_y (float): Screen y coordinate
            flash_time (int): Time since last damage
        """
        hand_length = 15
        hand_offset = 0.3
        
        left_hand_angle = self.angle_to_player - hand_offset
        right_hand_angle = self.angle_to_player + hand_offset
        
        left_hand_x = screen_x + math.cos(left_hand_angle) * hand_length
        left_hand_y = screen_y + math.sin(left_hand_angle) * hand_length
        right_hand_x = screen_x + math.cos(right_hand_angle) * hand_length
        right_hand_y = screen_y + math.sin(right_hand_angle) * hand_length
        
        hand_color = WHITE if flash_time < 200 else BLACK
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (left_hand_x, left_hand_y), 2)
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (right_hand_x, right_hand_y), 2)


class FastZombie(Zombie):
    """Fast zombie variant with increased speed and different appearance."""
    
    def __init__(self, x, y):
        """
        Initialize a fast zombie.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
        """
        super().__init__(x, y)
        self.speed = FAST_ZOMBIE_SPEED
        self.size = FAST_ZOMBIE_SIZE
        self.health = FAST_ZOMBIE_HEALTH
        self.max_health = FAST_ZOMBIE_HEALTH
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the fast zombie with distinctive appearance.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Flash white when taking damage, otherwise orange
        flash_time = pygame.time.get_ticks() - self.last_damage_time
        color = WHITE if flash_time < 200 else ORANGE
            
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw hands (slightly different parameters for fast zombie)
        hand_length = 13
        hand_offset = 0.4
        
        left_hand_angle = self.angle_to_player - hand_offset
        right_hand_angle = self.angle_to_player + hand_offset
        
        left_hand_x = screen_x + math.cos(left_hand_angle) * hand_length
        left_hand_y = screen_y + math.sin(left_hand_angle) * hand_length
        right_hand_x = screen_x + math.cos(right_hand_angle) * hand_length
        right_hand_y = screen_y + math.sin(right_hand_angle) * hand_length
        
        hand_color = WHITE if flash_time < 200 else BLACK
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (left_hand_x, left_hand_y), 2)
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (right_hand_x, right_hand_y), 2)
        
        # Distinctive center dot
        pygame.draw.circle(screen, BLACK, (int(screen_x), int(screen_y)), 3)