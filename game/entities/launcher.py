# game/entities/launcher.py - Launcher arrow class with glowing pointer and smooth rotation

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
        """Loads launcher arrow asset or draws a sleek glowing pointer procedurally."""
        img_path = GameConfig.get_asset_path('images', 'Arrow.png')
        if os.path.exists(img_path):
            try:
                self.image = pygame.image.load(img_path).convert_alpha()
                scaled_wd = int(32 * GameConfig.scale_x)
                scaled_hg = int(64 * GameConfig.scale_y)
                self.image = pygame.transform.smoothscale(self.image, (scaled_wd, scaled_hg))
                return
            except Exception:
                pass

        # Procedural glowing pointer
        sw = int(32 * GameConfig.scale_x)
        sh = int(64 * GameConfig.scale_y)
        self.image = pygame.Surface((sw, sh), pygame.SRCALPHA)
        
        # Outer glow
        glow_points = [
            (sw // 2, 2),
            (sw - 2, sh - 4),
            (sw // 2, sh - 14),
            (2, sh - 4)
        ]
        pygame.draw.polygon(self.image, (*GameConfig.COLOR_PRIMARY_LIGHT[:3], 120), glow_points)
        
        # Inner sleek arrowhead
        inner_points = [
            (sw // 2, 5),
            (sw - 5, sh - 8),
            (sw // 2, sh - 16),
            (5, sh - 8)
        ]
        pygame.draw.polygon(self.image, GameConfig.COLOR_PRIMARY_LIGHT, inner_points)
        pygame.draw.polygon(self.image, (255, 255, 255), inner_points, width=1)

    def set_target(self, tx, ty):
        """Aims towards target screen coordinates, calculating and clamping rotation angle."""
        vtx = tx / GameConfig.scale_x
        vty = ty / GameConfig.scale_y

        dx = vtx - self.vx
        dy = vty - self.vy

        if dy == 0:
            return

        rad = math.atan2(-dy, dx)
        angle = math.degrees(rad)
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
        self.transform_image = pygame.transform.rotate(self.image, self.angle - 90)
        self.rect = self.transform_image.get_rect()
        self.rect.centerx = GameConfig.to_screen_x(self.vx)
        self.rect.centery = GameConfig.to_screen_y(self.vy)

    def draw(self, surface):
        # Draw base launcher pedestal (circular glowing ring)
        sx = GameConfig.to_screen_x(self.vx)
        sy = GameConfig.to_screen_y(self.vy)
        base_rad = int(28 * min(GameConfig.scale_x, GameConfig.scale_y))
        
        pedestal_surf = pygame.Surface((base_rad * 2 + 4, base_rad * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(pedestal_surf, (*GameConfig.COLOR_SURFACE_HIGH[:3], 180), (base_rad + 2, base_rad + 2), base_rad)
        pygame.draw.circle(pedestal_surf, (*GameConfig.COLOR_PRIMARY_LIGHT[:3], 120), (base_rad + 2, base_rad + 2), base_rad, width=2)
        surface.blit(pedestal_surf, (sx - base_rad - 2, sy - base_rad - 2))

        # Blit rotated pointer arrow
        surface.blit(self.transform_image, self.rect)
