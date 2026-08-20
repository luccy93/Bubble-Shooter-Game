# game/entities/bubble.py - Bubble Entity wrapping colors, types, positions, and physics

import pygame
import math
import pygame.gfxdraw
from game.core.config import GameConfig

class Bubble(pygame.sprite.Sprite):
    def __init__(self, color, row=0, col=0, x=None, y=None, bubble_type="normal"):
        pygame.sprite.Sprite.__init__(self)
        self.color = color
        self.row = row
        self.col = col
        self.radius = GameConfig.BUBBLE_RAD
        self.bubble_type = bubble_type  # "normal", "bomb", "rainbow"
        
        # Physics attributes
        self.speed = 10
        self.angle = 90
        
        # Center coordinates in virtual space
        if x is not None and y is not None:
            self.vx = x
            self.vy = y
        else:
            self.vx = GameConfig.VIRTUAL_WIDTH / 2
            self.vy = GameConfig.VIRTUAL_HEIGHT - 100

        # Collision hitbox rect (in virtual coordinates)
        self.rect = pygame.Rect(
            int(self.vx - self.radius),
            int(self.vy - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def update_rect(self):
        """Syncs the virtual rect with the active virtual coordinates."""
        self.rect.x = int(self.vx - self.radius)
        self.rect.y = int(self.vy - self.radius)

    def update(self):
        """Updates the bubble position in virtual coordinates based on its launch angle."""
        if self.angle == 90:
            dx = 0
            dy = -self.speed
        elif self.angle < 90:
            dx = self.xcalc(self.angle)
            dy = self.ycalc(self.angle)
        else:
            # Angle > 90
            dx = self.xcalc(180 - self.angle) * -1
            dy = self.ycalc(180 - self.angle)

        self.vx += dx
        self.vy += dy
        self.update_rect()

    def xcalc(self, angle):
        return math.cos(math.radians(angle)) * self.speed

    def ycalc(self, angle):
        return math.sin(math.radians(angle)) * self.speed * -1

    def draw(self, surface):
        """Draws a premium 3D radial-glossy bubble on the screen."""
        # 0. Sync colors for special types
        symbol = None
        symbol_color = (255, 255, 255)
        
        if self.bubble_type == "bomb":
            symbol = "B"
            self.color = (255, 102, 0)
        elif self.bubble_type == "lightning":
            symbol = "L"
            self.color = (186, 104, 200)
        elif self.bubble_type == "fireball":
            symbol = "F"
            self.color = (255, 75, 40)
        elif self.bubble_type == "rescue":
            symbol = "🐱"
            self.color = (244, 143, 177)
        elif self.bubble_type == "obstacle":
            symbol = "🧱"
            self.color = (120, 120, 120)

        sx = GameConfig.to_screen_x(self.vx)
        sy = GameConfig.to_screen_y(self.vy)
        srad = int(self.radius * min(GameConfig.scale_x, GameConfig.scale_y))
        
        if srad <= 0:
            return

        # 1. Outer drop shadow
        shadow_surf = pygame.Surface((srad * 2 + 4, srad * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 45), (srad + 1, srad + 2), srad - 1)
        surface.blit(shadow_surf, (sx - srad - 1, sy - srad - 2))

        # 2. Main Bubble Circle (anti-aliased)
        if self.bubble_type == "rainbow":
            # Procedural rainbow drawing
            pygame.gfxdraw.filled_circle(surface, sx, sy, srad, (255, 255, 255))
            pygame.gfxdraw.aacircle(surface, sx, sy, srad, (200, 200, 200))
            # Nested colorful arcs
            for r_offset, arc_color in zip([2, 5, 8], [(175, 82, 222), (0, 122, 255), (255, 59, 48)]):
                if srad - r_offset > 0:
                    pygame.gfxdraw.aacircle(surface, sx, sy, srad - r_offset, arc_color)
        else:
            pygame.gfxdraw.filled_circle(surface, sx, sy, srad, self.color)
            pygame.gfxdraw.aacircle(surface, sx, sy, srad, (100, 100, 100))

            # 3. Inner radial gloss highlight (3D sphere effect)
            gloss_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
            gx, gy = int(srad * 0.7), int(srad * 0.6)
            for r in range(1, int(srad * 0.7)):
                alpha = int(140 * (1 - r / (srad * 0.7)))
                pygame.draw.circle(gloss_surf, (255, 255, 255, alpha), (gx, gy), r)
            surface.blit(gloss_surf, (sx - srad, sy - srad))

            # Draw symbol centered inside special bubbles
            if symbol:
                font_name = 'Segoe UI Emoji' if self.bubble_type == "rescue" else 'Arial'
                try:
                    font = pygame.font.SysFont(font_name, int(srad * 1.1), bold=True)
                except Exception:
                    font = pygame.font.Font(None, int(srad * 1.1))
                text = font.render(symbol, True, symbol_color)
                surface.blit(text, text.get_rect(center=(sx, sy)))
