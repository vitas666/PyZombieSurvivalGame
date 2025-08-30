"""
Zombie Survivor Game - Main Entry Point

A 2D top-down zombie survival game where the player must navigate through
a map filled with zombies, collect weapon upgrades, and reach the exit.

Controls:
- WASD or Arrow Keys: Move player
- Mouse: Aim weapon
- Mouse Click: Shoot
- R: Restart game (when game over)

Game Features:
- Player with directional weapon display
- Normal zombies (red) and fast zombies (orange)
- Weapon upgrades: Pistol, Rifle, Shotgun
- Procedurally generated obstacles
- Smart zombie AI with pathfinding
- Health system and collision detection
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