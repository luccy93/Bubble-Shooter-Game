# game/core/config.py - Screen Scaling, Colors, and Paths

import pygame
import os

class GameConfig:
    # Target virtual resolution (portrait mobile aspect ratio)
    VIRTUAL_WIDTH = 450
    VIRTUAL_HEIGHT = 800

    # Running display scaling factors (updated dynamically at launch)
    scale_x = 1.0
    scale_y = 1.0
    actual_width = VIRTUAL_WIDTH
    actual_height = VIRTUAL_HEIGHT
    screen = None

    # Gameplay-specific layout boundary coordinates (calculated relative to virtual dimensions)
    # The grid uses a 400x500 board area, centered on the screen.
    BOARD_WIDTH = 400
    BOARD_HEIGHT = 500
    board_x = (VIRTUAL_WIDTH - BOARD_WIDTH) // 2
    board_y = 60

    # Bubble parameters
    BUBBLE_RAD = 24
    BUBBLE_WD = BUBBLE_RAD * 2
    BUBBLE_ROWS = 12
    BUBBLE_COLS = 8
    BUB_ADJUST = 5  # Vertical pixel compression per row

    # Colors (harmonious palette instead of plain raw primaries)
    COLOR_BG = (15, 12, 32)
    COLOR_BG_LIGHT = (25, 21, 48)
    COLOR_TEXT = (255, 255, 255)
    COLOR_TEXT_MUTED = (187, 170, 221)
    COLOR_ACCENT = (110, 76, 255)
    COLOR_PRIMARY = (255, 109, 0)
    COLOR_SUCCESS = (76, 175, 80)
    COLOR_FAILURE = (255, 82, 82)

    # Bubble visual colors mapped to indexes
    BUBBLE_COLORS = [
        (255, 59, 48),    # Red
        (0, 122, 255),    # Blue
        (52, 199, 89),    # Green
        (255, 204, 0),    # Yellow
        (175, 82, 222)    # Purple
    ]
    COLOR_KEYS = ['red', 'blue', 'green', 'yellow', 'purple']

    # Path helpers
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    SAVE_FILE = os.path.join(BASE_DIR, 'save_data.json')

    @classmethod
    def init_screen(cls, width, height, fullscreen=False):
        """Initializes Pygame screen and sets up scaling factors."""
        cls.actual_width = width
        cls.actual_height = height
        cls.scale_x = width / cls.VIRTUAL_WIDTH
        cls.scale_y = height / cls.VIRTUAL_HEIGHT
        
        flags = pygame.FULLSCREEN if fullscreen else 0
        cls.screen = pygame.display.set_mode((width, height), flags)
        return cls.screen

    @classmethod
    def to_screen_x(cls, vx):
        """Converts virtual X coordinate to actual screen coordinate."""
        return int(vx * cls.scale_x)

    @classmethod
    def to_screen_y(cls, vy):
        """Converts virtual Y coordinate to actual screen coordinate."""
        return int(vy * cls.scale_y)

    @classmethod
    def scale_font_size(cls, base_size):
        """Calculates appropriate font size based on screen scaling."""
        return int(base_size * min(cls.scale_x, cls.scale_y))

    @classmethod
    def get_asset_path(cls, *paths):
        """Safe utility to build asset paths."""
        return os.path.join(cls.ASSETS_DIR, *paths)
