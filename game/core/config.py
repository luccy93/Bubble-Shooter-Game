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
    board_y = 80

    # Bubble parameters
    BUBBLE_RAD = 24
    BUBBLE_WD = BUBBLE_RAD * 2
    BUBBLE_ROWS = 12
    BUBBLE_COLS = 8
    BUB_ADJUST = 5  # Vertical pixel compression per row

    # ─── Stitch "Bubble Blast Saga" Design System Colors ───
    # Background & Surface (Deep Magical Purple)
    COLOR_BG = (21, 18, 28)                 # #15121c  surface
    COLOR_BG_LIGHT = (33, 30, 41)           # #211e29  surface-container
    COLOR_SURFACE_DIM = (21, 18, 28)        # #15121c  surface-dim
    COLOR_SURFACE_BRIGHT = (59, 55, 67)     # #3b3743  surface-bright
    COLOR_SURFACE_HIGH = (44, 40, 52)       # #2c2834  surface-container-high
    COLOR_SURFACE_HIGHEST = (55, 51, 63)    # #37333f  surface-container-highest
    COLOR_SURFACE_LOW = (29, 26, 37)        # #1d1a25  surface-container-low
    COLOR_SURFACE_LOWEST = (15, 13, 23)     # #0f0d17  surface-container-lowest

    # Primary (Electric Violet / Magical Purple)
    COLOR_PRIMARY = (98, 0, 238)            # #6200ee  primary-container
    COLOR_PRIMARY_LIGHT = (207, 189, 255)   # #cfbdff  primary
    COLOR_PRIMARY_DIM = (109, 35, 249)      # #6d23f9  inverse-primary

    # Secondary (Gold / Premium)
    COLOR_SECONDARY = (255, 215, 0)         # #ffd700  gold
    COLOR_SECONDARY_CONTAINER = (255, 219, 60)  # #ffdb3c
    COLOR_GOLD = (255, 235, 59)             # Gold for stars/coins

    # Tertiary (Emerald / Success)
    COLOR_SUCCESS = (0, 228, 117)           # #00e475  tertiary
    COLOR_SUCCESS_DIM = (0, 97, 46)         # #00612e  tertiary-container

    # Error / Danger (Ruby Red)
    COLOR_FAILURE = (255, 82, 82)           # Bright red for danger
    COLOR_ERROR = (255, 180, 171)           # #ffb4ab  error

    # Text & Content
    COLOR_TEXT = (231, 224, 240)            # #e7e0f0  on-surface
    COLOR_TEXT_MUTED = (203, 195, 217)      # #cbc3d9  on-surface-variant
    COLOR_ACCENT = (207, 189, 255)          # #cfbdff  primary accent

    # Outline / Borders
    COLOR_OUTLINE = (148, 141, 162)         # #948da2  outline
    COLOR_OUTLINE_DIM = (73, 68, 86)        # #494456  outline-variant

    # ─── Typography (System font fallback mapping) ───
    FONT_HEADLINE = 'Plus Jakarta Sans'
    FONT_BODY = 'Be Vietnam Pro'
    FONT_FALLBACKS = ['Segoe UI', 'Arial', None]

    # ─── Spacing (8px grid) ───
    SPACING_XS = 4
    SPACING_SM = 12
    SPACING_BASE = 8
    SPACING_MD = 24
    SPACING_LG = 40
    SPACING_MARGIN = 20
    SPACING_GUTTER = 12

    # ─── Border Radius ───
    RADIUS_SM = 8
    RADIUS_MD = 16
    RADIUS_LG = 24
    RADIUS_XL = 32
    RADIUS_FULL = 9999

    # Bubble visual colors mapped to indexes (Stitch gradient primaries)
    BUBBLE_COLORS = [
        (255, 59, 48),    # Red    — radial(#ff6b6b → #c0392b)
        (0, 122, 255),    # Blue   — radial(#4facfe → #00f2fe)
        (52, 199, 89),    # Green  — radial(#43e97b → #38f9d7)
        (255, 204, 0),    # Yellow — radial(#f6d365 → #fda085)
        (175, 82, 222)    # Purple — radial(#b8c6db → #f5f7fa)
    ]
    # Secondary bubble gradient endpoints (for enhanced rendering)
    BUBBLE_GRADIENTS = [
        ((255, 107, 107), (192, 57, 43)),   # Red
        ((79, 172, 254),  (0, 242, 254)),    # Blue
        ((67, 233, 123),  (56, 249, 215)),   # Green
        ((246, 211, 101), (253, 160, 133)),   # Yellow
        ((184, 198, 219), (245, 247, 250)),   # Purple
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
