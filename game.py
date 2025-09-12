"""
Main game logic and coordination.
"""
import pygame
import math
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FPS, BLACK, BROWN, GREEN, WHITE, RED, YELLOW,
    WeaponType, WEAPON_STATS, HeroType, HERO_STATS, ZOMBIE_MIN_SPAWN_DISTANCE
)
from player import Player
from zombie import Zombie, FastZombie, ZombieBoss
from weapon import WeaponPickup
from powerup import InstaKillPowerUp
from bullet import HomingBullet


class Game:
    """Main game class that coordinates all game systems."""
    
    def __init__(self, hero_type=HeroType.NATHAN):
        """Initialize the game."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Zombie Survivor")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.selected_hero = hero_type
        self.player = Player(100, 100, hero_type)
        self.bullets = []
        self.grenades = []
        self.zombies = []
        self.obstacles = []
        self.weapon_pickups = []
        self.powerups = []
        self.exit_rect = None
        
        # Spawning system
        self.zombie_spawn_timer = 0
        self.zombies_spawned = 0
        self.max_zombies = 100
        self.spawn_interval = 5000  # 3 seconds between waves
        self.zombies_per_wave = 7  # Spawn 20 zombies per wave
        self.boss_spawned = False
        self.boss_killed = False
        self.current_wave = 0
        
        # Camera system
        self.camera_x = 0
        self.camera_y = 0
        
        # Game state
        self.last_zombie_damage = 0
        self.game_state = "menu"  # "menu", "hero_select", "playing", "won", "lost"
        
        # UI notifications
        self.skill_bonus_notification = None
        self.skill_bonus_notification_time = 0
        
        # Initialize game world
        self._generate_map()
        self._spawn_weapon_pickups()
        self._spawn_powerups()
    
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
    
    def _spawn_powerups(self):
        """Spawn power-ups around the map."""
        # Spawn 1 insta-kill power-up
        for _ in range(1):
            max_attempts = 50
            for _ in range(max_attempts):
                x = random.randint(100, MAP_SIZE - 100)
                y = random.randint(100, MAP_SIZE - 100)
                powerup_rect = pygame.Rect(x-20, y-20, 40, 40)
                
                if not any(powerup_rect.colliderect(obs) for obs in self.obstacles):
                    self.powerups.append(InstaKillPowerUp(x, y))
                    break
    
    def _spawn_zombie_wave(self):
        """Spawn zombies in waves of 20 zombies each."""
        current_time = pygame.time.get_ticks()
        
        # Stop spawning if boss is killed
        if self.boss_killed:
            return
        
        # Check if it's time to spawn next wave
        if (current_time - self.zombie_spawn_timer > self.spawn_interval and 
            self.zombies_spawned < self.max_zombies):
            
            # Determine wave composition
            wave_zombies = []
            
            if self.current_wave < 2:
                # First 2 waves: mostly normal zombies (85% normal, 15% fast)
                for _ in range(self.zombies_per_wave):
                    zombie_class = FastZombie if random.random() < 0.15 else Zombie
                    wave_zombies.append(zombie_class)
            elif self.current_wave < 4:
                # Next 2 waves: balanced mix (70% normal, 30% fast)
                for _ in range(self.zombies_per_wave):
                    zombie_class = FastZombie if random.random() < 0.3 else Zombie
                    wave_zombies.append(zombie_class)
            else:
                # Final wave: mostly fast zombies and boss
                if not self.boss_spawned:
                    # Add boss to final wave
                    wave_zombies.append(ZombieBoss)
                    self.boss_spawned = True
                    # Fill rest with fast zombies
                    for _ in range(self.zombies_per_wave - 1):
                        wave_zombies.append(FastZombie)
                else:
                    # All fast zombies
                    for _ in range(self.zombies_per_wave):
                        wave_zombies.append(FastZombie)
            
            # Spawn all zombies in the wave
            for zombie_class in wave_zombies:
                if self.zombies_spawned < self.max_zombies:
                    self._spawn_single_zombie(zombie_class)
                    self.zombies_spawned += 1
            
            self.current_wave += 1
            self.zombie_spawn_timer = current_time
    
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
        
        # Hero ability activation
        if keys[pygame.K_q] and self.game_state == "playing":
            self.player.activate_hero_ability()
        
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
            # Check if bullet hits obstacle or goes out of bounds
            if isinstance(bullet, HomingBullet):
                hit_obstacle = bullet.update(self.obstacles, self.zombies)
            else:
                hit_obstacle = bullet.update(self.obstacles)
            if hit_obstacle or bullet.is_out_of_bounds():
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
                            # Determine zombie type for scoring
                            from zombie import ZombieBoss, FastZombie
                            if isinstance(zombie, ZombieBoss):
                                zombie_type = "boss"
                            elif isinstance(zombie, FastZombie):
                                zombie_type = "fast"
                            else:
                                zombie_type = "normal"
                            
                            # Add kill and check for skill bonus
                            skill_bonus = self.player.add_kill(zombie_type)
                            if skill_bonus > 0:
                                self.skill_bonus_notification = skill_bonus
                                self.skill_bonus_notification_time = pygame.time.get_ticks()
                            
                            # Remove zombie from list BEFORE calling boss death handler
                            self.zombies.remove(zombie)
                            
                            # Handle boss death after removal to avoid list modification conflicts
                            if isinstance(zombie, ZombieBoss):
                                self._handle_boss_death(zombie.x, zombie.y)
                
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
        
        # Update player reload and power-ups
        self.player.update_reload()
        self.player.update_powerups()
        
        # Spawn zombies in waves
        self._spawn_zombie_wave()
        
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.check_pickup(self.player.x, self.player.y):
                if isinstance(powerup, InstaKillPowerUp):
                    self.player.activate_insta_kill(powerup.duration)
                self.powerups.remove(powerup)
        
        # Handle bullet-zombie collisions
        for bullet in self.bullets[:]:
            for zombie in self.zombies[:]:
                distance = math.sqrt((bullet.x - zombie.x)**2 + (bullet.y - zombie.y)**2)
                if distance < (bullet.size + zombie.size):
                    if zombie.take_damage(bullet.damage):
                        # Determine zombie type for scoring
                        from zombie import ZombieBoss, FastZombie
                        if isinstance(zombie, ZombieBoss):
                            zombie_type = "boss"
                        elif isinstance(zombie, FastZombie):
                            zombie_type = "fast"
                        else:
                            zombie_type = "normal"
                        
                        # Add kill and check for skill bonus
                        skill_bonus = self.player.add_kill(zombie_type)
                        if skill_bonus > 0:
                            self.skill_bonus_notification = skill_bonus
                            self.skill_bonus_notification_time = pygame.time.get_ticks()
                        
                        # Remove zombie from list BEFORE calling boss death handler
                        self.zombies.remove(zombie)
                        
                        # Handle boss death after removal to avoid list modification conflicts
                        if isinstance(zombie, ZombieBoss):
                            self._handle_boss_death(zombie.x, zombie.y)
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
    
    def _handle_boss_death(self, boss_x, boss_y):
        """Handle special events when boss dies."""
        self.boss_killed = True
        
        # Drop minigun weapon at boss location
        minigun_pickup = WeaponPickup(boss_x, boss_y, WeaponType.MINIGUN)
        self.weapon_pickups.append(minigun_pickup)
        
        # Convert all remaining zombies to fast zombies
        from zombie import FastZombie
        for i, zombie in enumerate(self.zombies):
            if not isinstance(zombie, FastZombie):
                # Create new fast zombie at same position
                fast_zombie = FastZombie(zombie.x, zombie.y)
                # Preserve some state
                fast_zombie.health = zombie.health
                fast_zombie.angle_to_player = zombie.angle_to_player
                self.zombies[i] = fast_zombie
    
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
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(self.screen, self.camera_x, self.camera_y)
        
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
    
    def _draw_final_stats(self, font):
        """Draw final game statistics."""
        final_score = font.render(f"Final Score: {self.player.score}", True, YELLOW)
        final_kills = font.render(f"Total Kills: {self.player.total_kills}", True, WHITE)
        kill_breakdown = font.render(f"Normal: {self.player.kills_normal} | Fast: {self.player.kills_fast} | Boss: {self.player.kills_boss}", True, WHITE)
        
        self.screen.blit(final_score, (SCREEN_WIDTH//2 - final_score.get_width()//2, SCREEN_HEIGHT//2 - 40))
        self.screen.blit(final_kills, (SCREEN_WIDTH//2 - final_kills.get_width()//2, SCREEN_HEIGHT//2))
        self.screen.blit(kill_breakdown, (SCREEN_WIDTH//2 - kill_breakdown.get_width()//2, SCREEN_HEIGHT//2 + 40))

    def _draw_ui(self):
        """Draw user interface elements."""
        font = pygame.font.Font(None, 36)
        
        # Game stats
        health_text = font.render(f"Health: {self.player.health}", True, WHITE)
        current_weapon = self.player.get_current_weapon()
        weapon_name = WEAPON_STATS[current_weapon]["name"] if current_weapon else "None"
        weapon_text = font.render(f"Weapon: {weapon_name}", True, WHITE)
        zombies_text = font.render(f"Zombies: {len(self.zombies)}", True, WHITE)
        wave_text = font.render(f"Wave: {self.current_wave + 1}", True, WHITE)
        
        # Score and kill stats
        score_text = font.render(f"Score: {self.player.score}", True, YELLOW)
        kills_text = font.render(f"Kills: {self.player.total_kills}", True, WHITE)
        streak_text = font.render(f"Streak: {self.player.kills_without_hit}", True, GREEN)
        
        # Weapon inventory display
        weapon1_name = WEAPON_STATS[self.player.weapons[0]]["name"] if self.player.weapons[0] else "Empty"
        weapon2_name = WEAPON_STATS[self.player.weapons[1]]["name"] if self.player.weapons[1] else "Empty"
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
        # Hide reload UI when Nathan's ability is active (infinite ammo)
        if self.player.is_reloading and not (self.player.hero_type == HeroType.NATHAN and self.player.ability_active):
            if self.player.reload_weapon == WeaponType.SHOTGUN:
                reload_text = font.render("RELOADING...", True, YELLOW)
            else:
                reload_text = font.render("RELOADING...", True, YELLOW)
        
        # Left side UI
        self.screen.blit(health_text, (10, 10))
        self.screen.blit(weapon_text, (10, 50))
        self.screen.blit(inventory_text, (10, 90))
        self.screen.blit(ammo_text, (10, 130))
        
        # Right side UI - Score information
        right_x = SCREEN_WIDTH - 250
        self.screen.blit(score_text, (right_x, 10))
        self.screen.blit(kills_text, (right_x, 50))
        self.screen.blit(streak_text, (right_x, 90))
        
        # Skill bonus notification
        current_time = pygame.time.get_ticks()
        if (self.skill_bonus_notification and 
            current_time - self.skill_bonus_notification_time < 3000):  # Show for 3 seconds
            bonus_text = font.render(f"SKILL BONUS: +{self.skill_bonus_notification}!", True, YELLOW)
            self.screen.blit(bonus_text, (right_x, 130))
        elif current_time - self.skill_bonus_notification_time >= 3000:
            self.skill_bonus_notification = None
        # Power-up status
        powerup_text = None
        if self.player.insta_kill_active:
            time_left = (self.player.insta_kill_end_time - pygame.time.get_ticks()) / 1000
            powerup_text = font.render(f"INSTA-KILL: {time_left:.1f}s", True, RED)
        
        # Hero ability status
        hero_name = HERO_STATS[self.player.hero_type]["name"]
        ability_name = HERO_STATS[self.player.hero_type]["ability"]
        hero_text = font.render(f"Hero: {hero_name}", True, WHITE)
        
        # Ability charge display
        charge_percent = int(self.player.ability_charge)
        if self.player.ability_active:
            if self.player.hero_type == HeroType.NATHAN:
                time_left = (self.player.ability_end_time - pygame.time.get_ticks()) / 1000
                ability_text = font.render(f"{ability_name}: {time_left:.1f}s", True, self.player.hero_color)
            else:
                ability_text = font.render(f"{ability_name}: ACTIVE", True, self.player.hero_color)
        elif charge_percent >= 100:
            ability_text = font.render(f"{ability_name}: READY (Press Q)", True, GREEN)
        else:
            ability_text = font.render(f"{ability_name}: {charge_percent}%", True, WHITE)
        
        y_offset = 170
        if reload_text:
            self.screen.blit(reload_text, (10, y_offset))
            y_offset += 40
        
        if powerup_text:
            self.screen.blit(powerup_text, (10, y_offset))
            y_offset += 40
        
        self.screen.blit(zombies_text, (10, y_offset))
        self.screen.blit(wave_text, (10, y_offset + 40))
        
        # Draw hero info (left side, bottom)
        self.screen.blit(hero_text, (10, y_offset + 80))
        self.screen.blit(ability_text, (10, y_offset + 120))
        
        # Game over screens
        if self.game_state in ["won", "lost"]:
            # Main message
            message = "YOU WON! Press R to restart" if self.game_state == "won" else "YOU LOST! Press R to restart"
            color = GREEN if self.game_state == "won" else RED
            main_text = font.render(message, True, color)
            
            text_rect = main_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            self.screen.blit(main_text, text_rect)
            
            # Draw final stats using helper method
            self._draw_final_stats(font)
        
        # Menu screens
        elif self.game_state == "menu":
            self._draw_main_menu()
        elif self.game_state == "hero_select":
            self._draw_hero_select()
    
    def _draw_main_menu(self):
        """Draw the main menu screen."""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Title
        title_text = font_large.render("ZOMBIE SURVIVOR", True, RED)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        start_text = font_medium.render("Press ENTER to Select Hero", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(start_text, start_rect)
        
        quit_text = font_medium.render("Press ESC to Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(quit_text, quit_rect)
    
    def _draw_hero_select(self):
        """Draw the hero selection screen."""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Title
        title_text = font_large.render("SELECT HERO", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Nathan
        nathan_color = GREEN if self.selected_hero == HeroType.NATHAN else WHITE
        nathan_text = font_medium.render("1 - Nathan", True, nathan_color)
        nathan_rect = nathan_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        self.screen.blit(nathan_text, nathan_rect)
        
        nathan_desc = font_small.render("Ability: Infinite Ammo + Homing Bullets (10s)", True, nathan_color)
        nathan_desc_rect = nathan_desc.get_rect(center=(SCREEN_WIDTH//2, 290))
        self.screen.blit(nathan_desc, nathan_desc_rect)
        
        # Kelly
        kelly_color = GREEN if self.selected_hero == HeroType.KELLY else WHITE
        kelly_text = font_medium.render("2 - Kelly", True, kelly_color)
        kelly_rect = kelly_text.get_rect(center=(SCREEN_WIDTH//2, 370))
        self.screen.blit(kelly_text, kelly_rect)
        
        kelly_desc = font_small.render("Ability: Full Health Restore", True, kelly_color)
        kelly_desc_rect = kelly_desc.get_rect(center=(SCREEN_WIDTH//2, 410))
        self.screen.blit(kelly_desc, kelly_desc_rect)
        
        # Instructions
        instruction_text = font_small.render("Use 1/2 or UP/DOWN arrows to select", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, 480))
        self.screen.blit(instruction_text, instruction_rect)
        
        start_text = font_small.render("Press ENTER to Start Game", True, YELLOW)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, 520))
        self.screen.blit(start_text, start_rect)
        
        back_text = font_small.render("Press ESC to Go Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, 560))
        self.screen.blit(back_text, back_rect)
    
    def restart_game(self):
        """Restart the game by properly cleaning up and reinitializing."""
        # Clear all game objects explicitly
        self.bullets.clear()
        self.grenades.clear()
        self.zombies.clear()
        self.weapon_pickups.clear()
        self.powerups.clear()
        self.obstacles.clear()
        
        # Reset player to starting state
        self.player = Player(100, 100, self.selected_hero)
        
        # Reset spawning system
        self.zombie_spawn_timer = 0
        self.zombies_spawned = 0
        self.boss_spawned = False
        self.boss_killed = False
        self.current_wave = 0
        
        # Reset camera
        self.camera_x = 0
        self.camera_y = 0
        
        # Reset game state
        self.last_zombie_damage = 0
        self.game_state = "playing"
        
        # Reset UI notifications
        self.skill_bonus_notification = None
        self.skill_bonus_notification_time = 0
        
        # Regenerate map and pickups
        self._generate_map()
        self._spawn_weapon_pickups()
        self._spawn_powerups()
    
    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == "menu":
                        if event.key == pygame.K_RETURN:
                            self.game_state = "hero_select"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                    elif self.game_state == "hero_select":
                        if event.key == pygame.K_1 or event.key == pygame.K_UP:
                            self.selected_hero = HeroType.NATHAN
                        elif event.key == pygame.K_2 or event.key == pygame.K_DOWN:
                            self.selected_hero = HeroType.KELLY
                        elif event.key == pygame.K_RETURN:
                            self.player = Player(100, 100, self.selected_hero)
                            self.game_state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            self.game_state = "menu"
                    elif event.key == pygame.K_r and self.game_state in ["won", "lost"]:
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