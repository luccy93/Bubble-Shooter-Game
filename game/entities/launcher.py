# game/entities/launcher.py - Launcher arrow class supporting rotation, touch aim, and procedural fallbacks

import pygame
import math
import os
from game.core.config import GameConfig

class Launcher(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.angle = 90  # Default pointing straight up
        
        # Center in virtual coordinates
        self.vx = GameConfig.VIRTUAL_WIDTH / 2
        self.vy = GameConfig.VIRTUAL_HEIGHT - 100

        # Load Arrow image or synthesize fallback
        self.image = None
        self._load_arrow_image()

        self.transform_image = self.image
        self.rect = self.transform_image.get_rect()
        self._update_transform()

    def _load_arrow_image(self):
        """Loads launcher arrow asset or draws one procedurally as fallback."""
        img_path = GameConfig.get_asset_path('images', 'Arrow.png')
        if os.path.exists(img_path):
            try:
                self.image = pygame.image.load(img_path).convert_alpha()
                # Scale to fit layout
                scaled_wd = int(32 * GameConfig.scale_x)
                scaled_hg = int(64 * GameConfig.scale_y)
                self.image = pygame.transform.smoothscale(self.image, (scaled_wd, scaled_hg))
                return
            except Exception:
                pass

        # Procedural fallback drawing a clean triangle pointer
        sw = int(32 * GameConfig.scale_x)
        sh = int(64 * GameConfig.scale_y)
        self.image = pygame.Surface((sw, sh), pygame.SRCALPHA)
        # Draw arrow triangle
        pygame.draw.polygon(self.image, GameConfig.COLOR_ACCENT, [
            (sw // 2, 2),
            (sw - 2, sh - 4),
            (2, sh - 4)
        ])
        pygame.draw.polygon(self.image, (255, 255, 255), [
            (sw // 2, 2),
            (sw - 2, sh - 4),
            (2, sh - 4)
        ], width=1)

    def set_target(self, tx, ty):
        """Aims towards target screen coordinates, calculating and clamping rotation angle."""
        # Convert target coordinates to virtual coordinates
        vtx = tx / GameConfig.scale_x
        vty = ty / GameConfig.scale_y

        dx = vtx - self.vx
        dy = vty - self.vy

        if dy == 0:
            return

        # Compute angle in degrees (0 to 180, where 90 is straight up)
        rad = math.atan2(-dy, dx)
        angle = math.degrees(rad)
        
        # Clamp launcher angle to prevent aiming too low/backwards (e.g. 15 to 165 degrees)
        self.angle = max(15, min(angle, 165))
        self._update_transform()

    def rotate(self, dir):
        """Keyboard steering rotate (dir is 'left' or 'right')."""
        if dir == 'left' and self.angle < 165:
            self.angle += 2
        elif dir == 'right' and self.angle > 15:
            self.angle -= 2
        self._update_transform()

    def _update_transform(self):
        """Rotates the base arrow image around the center pivot."""
        # Pygame rotates counter-clockwise. Our straight-up is 90 deg.
        # Base image points up, so offset by -90 for rotation
        self.transform_image = pygame.transform.rotate(self.image, self.angle - 90)
        self.rect = self.transform_image.get_rect()
        self.rect.centerx = GameConfig.to_screen_x(self.vx)
        self.rect.centery = GameConfig.to_screen_y(self.vy)

    def draw(self, surface):
        surface.blit(self.transform_image, self.rect)
