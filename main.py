"""
Zombie Survivor Game - Main Entry Point

A 2D top-down zombie survival game where the player must navigate through
a map filled with zombies, collect weapon upgrades, and reach the exit.

Controls:
- WASD or Arrow Keys: Move player
- Mouse: Aim weapon
- Mouse Click: Shoot
- 1, 2: Switch between weapons
- Mouse Wheel: Switch weapons
- R: Reload weapon / Restart game (when game over)

Game Features:
- Player with directional weapon display and 2-weapon inventory
- Normal zombies (red) and fast zombies (orange)
- Weapon upgrades: Pistol (12 rounds), Shotgun (5 shells), Machine Gun (30 rounds), Grenades
- Ammunition system with auto-reload: Pistol (2s reload), Machine Gun (3s reload), Shotgun (1s per shell, interruptible)
- Grenade explosions with area damage (affects both zombies and player)
- Weapon switching with keys 1/2 and mouse wheel
- Procedurally generated obstacles
- Smart zombie AI with pathfinding
- Health system and collision detections
"""
import pygame
from game import Game


def main():
    """Initialize pygame and start the game."""
    pygame.init()
    
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        raise


if __name__ == "__main__":
    main()