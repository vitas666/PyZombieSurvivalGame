"""
Main game logic and coordination.
"""
import pygame
import math
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FPS, BLACK, BROWN, GREEN, WHITE, RED, YELLOW,
    WeaponType, ZOMBIE_MIN_SPAWN_DISTANCE
)
from player import Player
from zombie import Zombie, FastZombie
from weapon import WeaponPickup


class Game:
    """Main game class that coordinates all game systems."""
    
    def __init__(self):
        """Initialize the game."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Zombie Survivor")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = Player(100, 100)
        self.bullets = []
        self.grenades = []
        self.zombies = []
        self.obstacles = []
        self.weapon_pickups = []
        self.exit_rect = None
        
        # Camera system
        self.camera_x = 0
        self.camera_y = 0
        
        # Game state
        self.last_zombie_damage = 0
        self.game_state = "playing"  # "playing", "won", "lost"
        
        # Initialize game world
        self._generate_map()
        self._spawn_zombies(50)
        self._spawn_weapon_pickups()
    
    def _generate_map(self):
        """Generate random obstacles and exit."""
        # Generate random obstacles
        for _ in range(30):
            x = random.randint(50, MAP_SIZE - 50)
            y = random.randint(50, MAP_SIZE - 50)
            width = random.randint(30, 80)
            height = random.randint(30, 80)
            self.obstacles.append(pygame.Rect(x, y, width, height))
        
        # Create exit in bottom-right corner
        self.exit_rect = pygame.Rect(MAP_SIZE - 100, MAP_SIZE - 100, 80, 80)
    
    def _spawn_zombies(self, count):
        """
        Spawn zombies with a mix of normal and fast types.
        
        Args:
            count (int): Total number of zombies to spawn
        """
        fast_zombie_count = count // 5  # 20% fast zombies
        normal_zombie_count = count - fast_zombie_count
        
        # Spawn normal zombies
        for _ in range(normal_zombie_count):
            self._spawn_single_zombie(Zombie)
        
        # Spawn fast zombies
        for _ in range(fast_zombie_count):
            self._spawn_single_zombie(FastZombie)
    
    def _spawn_single_zombie(self, zombie_class):
        """
        Spawn a single zombie of given class.
        
        Args:
            zombie_class: Zombie or FastZombie class
        """
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(50, MAP_SIZE - 50)
            y = random.randint(50, MAP_SIZE - 50)
            
            # Ensure zombie spawns away from player
            distance_to_player = math.sqrt((x - self.player.x)**2 + (y - self.player.y)**2)
            if distance_to_player > ZOMBIE_MIN_SPAWN_DISTANCE:
                zombie = zombie_class(x, y)
                if not zombie._check_collision(x, y, self.obstacles):
                    self.zombies.append(zombie)
                    break
    
    def _spawn_weapon_pickups(self):
        """Spawn weapon pickups around the map."""
        weapons = [WeaponType.MACHINE_GUN, WeaponType.SHOTGUN, WeaponType.GRENADE, WeaponType.MACHINE_GUN, WeaponType.GRENADE]
        
        for weapon in weapons:
            max_attempts = 50
            for _ in range(max_attempts):
                x = random.randint(100, MAP_SIZE - 100)
                y = random.randint(100, MAP_SIZE - 100)
                pickup_rect = pygame.Rect(x-15, y-15, 30, 30)
                
                if not any(pickup_rect.colliderect(obs) for obs in self.obstacles):
                    self.weapon_pickups.append(WeaponPickup(x, y, weapon))
                    break
    
    def _update_camera(self):
        """Update camera position to follow player."""
        self.camera_x = self.player.x - SCREEN_WIDTH // 2
        self.camera_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Keep camera within map bounds
        self.camera_x = max(0, min(MAP_SIZE - SCREEN_WIDTH, self.camera_x))
        self.camera_y = max(0, min(MAP_SIZE - SCREEN_HEIGHT, self.camera_y))
    
    def handle_input(self):
        """Handle player input."""
        if self.game_state != "playing":
            return
            
        keys = pygame.key.get_pressed()
        dx = dy = 0
        
        # Movement input
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        
        self.player.move(dx, dy, self.obstacles)
        
        # Mouse aiming and shooting
        mouse_pos = pygame.mouse.get_pos()
        mouse_x = mouse_pos[0] + self.camera_x
        mouse_y = mouse_pos[1] + self.camera_y
        
        self.player.weapon_angle = math.atan2(mouse_y - self.player.y, mouse_x - self.player.x)
        
        # Weapon switching
        if keys[pygame.K_1]:
            self.player.switch_to_weapon_slot(0)
        if keys[pygame.K_2]:
            self.player.switch_to_weapon_slot(1)
        
        # Reload (only if not in game over state)
        if keys[pygame.K_r] and self.game_state == "playing":
            self.player.start_reload()
        
        if pygame.mouse.get_pressed()[0]:
            new_bullets, new_grenades = self.player.shoot(mouse_x, mouse_y)
            self.bullets.extend(new_bullets)
            self.grenades.extend(new_grenades)
    
    def update_game(self):
        """Update all game systems."""
        if self.game_state != "playing":
            return
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_out_of_bounds():
                self.bullets.remove(bullet)
        
        # Update grenades
        for grenade in self.grenades[:]:
            grenade.update()
            
            # Check grenade collisions and explosions
            if not grenade.exploded:
                grenade.check_collision(self.zombies, self.obstacles)
            
            if grenade.exploded:
                # Handle explosion damage
                damaged_zombies, player_in_range = grenade.get_explosion_damage_targets(self.zombies, self.player)
                
                # Damage zombies in explosion radius
                for zombie in damaged_zombies:
                    if zombie.take_damage(grenade.damage):
                        if zombie in self.zombies:
                            self.zombies.remove(zombie)
                
                # Damage player if in explosion radius
                if player_in_range:
                    if self.player.take_damage():
                        self.game_state = "lost"
                        return
            
            # Remove finished grenades
            if grenade.is_finished() or grenade.is_out_of_bounds():
                self.grenades.remove(grenade)
        
        # Update zombies
        for zombie in self.zombies:
            zombie.update(self.player.x, self.player.y, self.obstacles, self.zombies)
        
        # Update player reload
        self.player.update_reload()
        
        # Handle bullet-zombie collisions
        for bullet in self.bullets[:]:
            for zombie in self.zombies[:]:
                distance = math.sqrt((bullet.x - zombie.x)**2 + (bullet.y - zombie.y)**2)
                if distance < (bullet.size + zombie.size):
                    if zombie.take_damage(bullet.damage):
                        self.zombies.remove(zombie)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
        
        # Handle zombie-player collisions (with cooldown)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_zombie_damage > 1000:  # 1 second cooldown
            for zombie in self.zombies:
                if zombie.can_damage_player(self.player.x, self.player.y):
                    if self.player.take_damage():
                        self.game_state = "lost"
                        return
                    self.last_zombie_damage = current_time
                    break
        
        # Handle weapon pickups
        for pickup in self.weapon_pickups:
            if pickup.check_pickup(self.player.x, self.player.y):
                self.player.upgrade_weapon(pickup.weapon_type)
        
        # Check win condition (player reaches exit)
        player_rect = pygame.Rect(
            self.player.x - self.player.size//2, 
            self.player.y - self.player.size//2, 
            self.player.size, 
            self.player.size
        )
        if player_rect.colliderect(self.exit_rect):
            self.game_state = "won"
    
    def draw(self):
        """Draw all game elements."""
        self.screen.fill(BLACK)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            screen_rect = pygame.Rect(
                obstacle.x - self.camera_x, 
                obstacle.y - self.camera_y, 
                obstacle.width, 
                obstacle.height
            )
            pygame.draw.rect(self.screen, BROWN, screen_rect)
        
        # Draw exit
        exit_screen_rect = pygame.Rect(
            self.exit_rect.x - self.camera_x, 
            self.exit_rect.y - self.camera_y, 
            self.exit_rect.width, 
            self.exit_rect.height
        )
        pygame.draw.rect(self.screen, GREEN, exit_screen_rect)
        
        # Draw weapon pickups
        for pickup in self.weapon_pickups:
            pickup.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw zombies
        for zombie in self.zombies:
            zombie.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw grenades
        for grenade in self.grenades:
            grenade.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw player
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw UI
        self._draw_ui()
        
        pygame.display.flip()
    
    def _draw_ui(self):
        """Draw user interface elements."""
        font = pygame.font.Font(None, 36)
        
        # Game stats
        health_text = font.render(f"Health: {self.player.health}", True, WHITE)
        current_weapon = self.player.get_current_weapon()
        weapon_name = current_weapon.name if current_weapon else "None"
        weapon_text = font.render(f"Weapon: {weapon_name}", True, WHITE)
        zombies_text = font.render(f"Zombies: {len(self.zombies)}", True, WHITE)
        
        # Weapon inventory display
        weapon1_name = self.player.weapons[0].name if self.player.weapons[0] else "Empty"
        weapon2_name = self.player.weapons[1].name if self.player.weapons[1] else "Empty"
        current_indicator1 = ">" if self.player.current_weapon_index == 0 else " "
        current_indicator2 = ">" if self.player.current_weapon_index == 1 else " "
        inventory_text = font.render(f"1{current_indicator1}{weapon1_name}  2{current_indicator2}{weapon2_name}", True, WHITE)
        
        # Ammunition display
        current_weapon = self.player.get_current_weapon()
        if current_weapon == WeaponType.GRENADE:
            ammo_text = font.render(f"Grenades: {self.player.grenade_count}", True, WHITE)
        else:
            current_ammo = self.player.get_current_ammo()
            max_ammo = self.player.get_max_ammo()
            ammo_text = font.render(f"Ammo: {int(current_ammo)}/{int(max_ammo)}", True, WHITE)
        
        # Reload status
        reload_text = None
        if self.player.is_reloading:
            if self.player.reload_weapon == WeaponType.SHOTGUN:
                reload_text = font.render("RELOADING...", True, YELLOW)
            else:
                reload_text = font.render("RELOADING...", True, YELLOW)
        
        self.screen.blit(health_text, (10, 10))
        self.screen.blit(weapon_text, (10, 50))
        self.screen.blit(inventory_text, (10, 90))
        self.screen.blit(ammo_text, (10, 130))
        if reload_text:
            self.screen.blit(reload_text, (10, 170))
            self.screen.blit(zombies_text, (10, 210))
        else:
            self.screen.blit(zombies_text, (10, 170))
        
        # Game over screens
        if self.game_state == "won":
            win_text = font.render("YOU WON! Press R to restart", True, GREEN)
            text_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(win_text, text_rect)
        elif self.game_state == "lost":
            lose_text = font.render("YOU LOST! Press R to restart", True, RED)
            text_rect = lose_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(lose_text, text_rect)
    
    def restart_game(self):
        """Restart the game by reinitializing."""
        self.__init__()
    
    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_state in ["won", "lost"]:
                        self.restart_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == "playing":
                        if event.button == 4:  # Mouse wheel up
                            self.player.switch_weapon(-1)
                        elif event.button == 5:  # Mouse wheel down
                            self.player.switch_weapon(1)
            
            # Update game
            if self.game_state == "playing":
                self.handle_input()
                self.update_game()
                self._update_camera()
            
            # Draw everything
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()