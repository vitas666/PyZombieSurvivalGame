"""
Game constants and configuration values.
"""
from enum import Enum

# Screen and map dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
MAP_SIZE = 1500
FPS = 60

# Color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Weapon configuration
class WeaponType(Enum):
    PISTOL = 1
    SHOTGUN = 2
    MACHINE_GUN = 3
    GRENADE = 4
    MINIGUN = 5

WEAPON_STATS = {
    WeaponType.PISTOL: {"damage": 1, "cooldown": 300, "bullet_speed": 10, "max_ammo": 12, "reload_time": 2000, "name": "Pistol"},
    WeaponType.SHOTGUN: {"damage": 3, "cooldown": 500, "bullet_speed": 8, "max_ammo": 5, "reload_time": 1000, "name": "Shotgun"},
    WeaponType.MACHINE_GUN: {"damage": 2, "cooldown": 100, "bullet_speed": 12, "max_ammo": 30, "reload_time": 3000, "name": "Machine Gun"},
    WeaponType.GRENADE: {"damage": 5, "cooldown": 1500, "bullet_speed": 6, "explosion_radius": 80, "max_ammo": float('inf'), "reload_time": 0, "name": "Grenade"},
    WeaponType.MINIGUN: {"damage": 4, "cooldown": 50, "bullet_speed": 15, "max_ammo": 200, "reload_time": 5000, "name": "Minigun"}
}

# Hero configuration
class HeroType(Enum):
    NATHAN = 1
    KELLY = 2

HERO_STATS = {
    HeroType.NATHAN: {"name": "Nathan", "color": BLUE, "ability": "Infinite Ammo + Homing"},
    HeroType.KELLY: {"name": "Kelly", "color": PURPLE, "ability": "Health Restore"}
}

# Game balance
PLAYER_SPEED = 5
PLAYER_SIZE = 20
PLAYER_MAX_HEALTH = 5

ZOMBIE_SPEED = 3
ZOMBIE_SIZE = 18
ZOMBIE_HEALTH = 3

FAST_ZOMBIE_SPEED = 4
FAST_ZOMBIE_SIZE = 16
FAST_ZOMBIE_HEALTH = 2

BULLET_SIZE = 5
WEAPON_PICKUP_SIZE = 15

# AI parameters
ZOMBIE_STUCK_THRESHOLD = 30
ZOMBIE_AVOIDANCE_DURATION = 60
ZOMBIE_MIN_SPAWN_DISTANCE = 200