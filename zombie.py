"""
Zombie classes for enemy AI.
"""
import pygame
import math
import random
from constants import (
    RED, WHITE, BLACK, ORANGE, YELLOW,
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
        Update zombie AI and movement with improved pathfinding.
        
        Args:
            player_x (float): Player x position
            player_y (float): Player y position
            obstacles (list): List of obstacle rectangles
            other_zombies (list): List of other zombies for collision avoidance
        """
        # Store previous position for stuck detection
        prev_x, prev_y = self.x, self.y
        
        # Calculate angle and distance to player
        self.angle_to_player = math.atan2(player_y - self.y, player_x - self.x)
        distance_to_player = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
        
        # Determine movement strategy
        movement_angle = self._determine_movement_angle(distance_to_player)
        
        # Try direct movement first
        if self._try_direct_movement(movement_angle, obstacles, other_zombies):
            self._update_stuck_detection(prev_x, prev_y, success=True)
            return
        
        # If direct movement failed, try alternative movement strategies
        if self._try_axis_aligned_movement(movement_angle, obstacles, other_zombies):
            self._update_stuck_detection(prev_x, prev_y, success=True)
            return
        
        # Try wall sliding movement
        if self._try_wall_sliding(movement_angle, obstacles, other_zombies):
            self._update_stuck_detection(prev_x, prev_y, success=True)
            return
        
        # If all movement fails, try random movement to unstuck
        self._try_unstuck_movement(obstacles, other_zombies)
        self._update_stuck_detection(prev_x, prev_y, success=False)
    
    def _determine_movement_angle(self, distance_to_player):
        """
        Determine the angle to move based on current state and distance to player.
        
        Args:
            distance_to_player (float): Distance to the player
            
        Returns:
            float: Movement angle in radians
        """
        # Reduce avoidance timer
        if self.avoidance_timer > 0:
            self.avoidance_timer -= 1
        
        # If in avoidance mode, continue with avoidance angle
        if self.avoidance_timer > 0:
            return self.avoidance_angle
        
        # If stuck for too long, enter avoidance mode
        if self.stuck_counter > ZOMBIE_STUCK_THRESHOLD:
            self.avoidance_angle = self.angle_to_player + random.uniform(-math.pi/2, math.pi/2)
            self.avoidance_timer = ZOMBIE_AVOIDANCE_DURATION
            self.stuck_counter = max(0, self.stuck_counter - 10)  # Reduce stuck counter
            return self.avoidance_angle
        
        # Normal movement towards player
        return self.angle_to_player
    
    def _try_direct_movement(self, angle, obstacles, other_zombies):
        """Try moving directly in the desired direction."""
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        new_x, new_y = self.x + dx, self.y + dy
        
        if not self._check_collision(new_x, new_y, obstacles, other_zombies):
            self.x, self.y = new_x, new_y
            return True
        return False
    
    def _try_axis_aligned_movement(self, angle, obstacles, other_zombies):
        """Try moving along X or Y axis separately."""
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        
        # Try X-axis movement first
        if not self._check_collision(self.x + dx, self.y, obstacles, other_zombies):
            self.x += dx
            return True
        
        # Try Y-axis movement
        if not self._check_collision(self.x, self.y + dy, obstacles, other_zombies):
            self.y += dy
            return True
        
        return False
    
    def _try_wall_sliding(self, angle, obstacles, other_zombies):
        """Try sliding along walls by testing multiple angles."""
        slide_angles = [
            angle + 0.3, angle - 0.3,
            angle + 0.6, angle - 0.6,
            angle + 0.9, angle - 0.9,
            angle + math.pi/2, angle - math.pi/2
        ]
        
        for slide_angle in slide_angles:
            dx = math.cos(slide_angle) * self.speed * 0.8
            dy = math.sin(slide_angle) * self.speed * 0.8
            new_x, new_y = self.x + dx, self.y + dy
            
            if not self._check_collision(new_x, new_y, obstacles, other_zombies):
                self.x, self.y = new_x, new_y
                return True
        
        return False
    
    def _try_unstuck_movement(self, obstacles, other_zombies):
        """Try random movement to get unstuck."""
        for _ in range(8):  # Try 8 random directions
            random_angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(random_angle) * self.speed * 0.5
            dy = math.sin(random_angle) * self.speed * 0.5
            new_x, new_y = self.x + dx, self.y + dy
            
            if not self._check_collision(new_x, new_y, obstacles, other_zombies):
                self.x, self.y = new_x, new_y
                return True
        
        return False
    
    def _update_stuck_detection(self, prev_x, prev_y, success):
        """Update stuck detection counters."""
        movement_distance = math.sqrt((self.x - prev_x)**2 + (self.y - prev_y)**2)
        
        if success and movement_distance > 0.1:  # Lowered threshold for better detection
            self.stuck_counter = max(0, self.stuck_counter - 2)  # Reduce stuck counter on successful movement
        else:
            self.stuck_counter += 1
        
        # Cap the stuck counter to prevent it from growing too large
        self.stuck_counter = min(self.stuck_counter, ZOMBIE_STUCK_THRESHOLD * 2)
    
    
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
        
        # Check zombie-to-zombie collisions (reduced clustering)
        if other_zombies:
            for other in other_zombies:
                if other != self:
                    distance = math.sqrt((x - other.x)**2 + (y - other.y)**2)
                    # Reduced collision radius and only apply when very close
                    if distance < (self.size + other.size) * 0.6 and distance < 20:
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


class ZombieBoss(Zombie):
    """Zombie boss with high health, slow movement, and large size."""
    
    def __init__(self, x, y):
        """
        Initialize a zombie boss.
        
        Args:
            x (float): Starting x position
            y (float): Starting y position
        """
        super().__init__(x, y)
        self.size = 35  # Larger than normal zombies
        self.speed = 1.5  # Slower than normal zombies
        self.health = 30  # Much higher health
        self.max_health = 30
        self.boss_pulse_time = 0
    
    def update(self, player_x, player_y, obstacles, other_zombies=None):
        """Update zombie boss with special movement patterns."""
        super().update(player_x, player_y, obstacles, other_zombies)
        self.boss_pulse_time += 1
    
    def take_damage(self, damage):
        """
        Zombie boss takes damage with special resistance to insta-kill.
        
        Args:
            damage (int): Amount of damage to take
            
        Returns:
            bool: True if zombie boss died
        """
        # Boss takes double damage from insta-kill but doesn't die instantly
        if damage >= 1000:  # Insta-kill damage
            damage = damage // 500  # Reduced damage but still significant
        
        self.health -= damage
        self.last_damage_time = pygame.time.get_ticks()
        return self.health <= 0
    
    def draw(self, screen, camera_x, camera_y):
        """
        Draw the zombie boss with distinctive appearance.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x offset
            camera_y (float): Camera y offset
        """
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Pulsing effect for boss
        pulse_intensity = int(abs(math.sin(self.boss_pulse_time * 0.05)) * 50)
        
        # Flash white when taking damage, otherwise dark red with pulsing
        flash_time = pygame.time.get_ticks() - self.last_damage_time
        if flash_time < 200:
            color = WHITE
        else:
            color = (150 + pulse_intensity, 0, 0)  # Pulsing dark red
            
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw boss crown/spikes
        for i in range(8):
            angle = (i * math.pi * 2 / 8) + (self.boss_pulse_time * 0.01)
            spike_x = screen_x + math.cos(angle) * (self.size + 8)
            spike_y = screen_y + math.sin(angle) * (self.size + 8)
            spike_end_x = screen_x + math.cos(angle) * (self.size + 15)
            spike_end_y = screen_y + math.sin(angle) * (self.size + 15)
            spike_color = WHITE if flash_time < 200 else YELLOW
            pygame.draw.line(screen, spike_color, (spike_x, spike_y), (spike_end_x, spike_end_y), 3)
        
        # Draw hands pointing at player (larger for boss)
        hand_length = 25
        hand_offset = 0.2
        
        left_hand_angle = self.angle_to_player - hand_offset
        right_hand_angle = self.angle_to_player + hand_offset
        
        left_hand_x = screen_x + math.cos(left_hand_angle) * hand_length
        left_hand_y = screen_y + math.sin(left_hand_angle) * hand_length
        right_hand_x = screen_x + math.cos(right_hand_angle) * hand_length
        right_hand_y = screen_y + math.sin(right_hand_angle) * hand_length
        
        hand_color = WHITE if flash_time < 200 else BLACK
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (left_hand_x, left_hand_y), 4)
        pygame.draw.line(screen, hand_color, (screen_x, screen_y), (right_hand_x, right_hand_y), 4)
        
        # Draw health bar for boss
        health_bar_width = 60
        health_bar_height = 8
        health_ratio = self.health / self.max_health
        health_bar_x = screen_x - health_bar_width//2
        health_bar_y = screen_y - self.size - 20
        
        # Background
        pygame.draw.rect(screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        # Current health
        pygame.draw.rect(screen, YELLOW, (health_bar_x, health_bar_y, health_bar_width * health_ratio, health_bar_height))
        # Border
        pygame.draw.rect(screen, WHITE, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)