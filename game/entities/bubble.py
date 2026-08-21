# game/entities/bubble.py - Bubble Entity with Stitch 3D sphere gradient rendering and physics

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
        self.bubble_type = bubble_type  # "normal", "bomb", "rainbow", "lightning", "fireball", "rescue", "obstacle"
        
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
        """Draws a premium 3D radial-gradient glossy bubble matching the Stitch design."""
        symbol = None
        symbol_color = (255, 255, 255)
        
        # Determine gradient colors
        grad_start = None
        grad_end = None

        if self.bubble_type == "bomb":
            symbol = "💣"
            grad_start, grad_end = (255, 140, 0), (180, 50, 0)
            self.color = (255, 102, 0)
        elif self.bubble_type == "lightning":
            symbol = "⚡"
            grad_start, grad_end = (220, 130, 240), (130, 40, 160)
            self.color = (186, 104, 200)
        elif self.bubble_type == "fireball":
            symbol = "🔥"
            grad_start, grad_end = (255, 120, 50), (200, 30, 20)
            self.color = (255, 75, 40)
        elif self.bubble_type == "rescue":
            symbol = "🐱"
            grad_start, grad_end = (255, 180, 210), (200, 100, 140)
            self.color = (244, 143, 177)
        elif self.bubble_type == "obstacle":
            symbol = "🧱"
            grad_start, grad_end = (160, 160, 160), (70, 70, 70)
            self.color = (120, 120, 120)
        elif self.bubble_type == "rainbow":
            pass
        else:
            # Match standard bubble colors to Stitch gradient pairs
            for idx, col in enumerate(GameConfig.BUBBLE_COLORS):
                if self.color == col and idx < len(GameConfig.BUBBLE_GRADIENTS):
                    grad_start, grad_end = GameConfig.BUBBLE_GRADIENTS[idx]
                    break
            if grad_start is None:
                grad_start = tuple(min(255, c + 40) for c in self.color)
                grad_end = tuple(max(0, c - 40) for c in self.color)

        sx = GameConfig.to_screen_x(self.vx)
        sy = GameConfig.to_screen_y(self.vy)
        srad = int(self.radius * min(GameConfig.scale_x, GameConfig.scale_y))
        
        if srad <= 0:
            return

        # 1. Outer soft drop shadow
        shadow_surf = pygame.Surface((srad * 2 + 6, srad * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 55), (srad + 3, srad + 4), srad - 1)
        surface.blit(shadow_surf, (sx - srad - 3, sy - srad - 4))

        # 2. Main Bubble Body
        if self.bubble_type == "rainbow":
            # Procedural multi-arc rainbow sphere
            pygame.gfxdraw.filled_circle(surface, sx, sy, srad, (255, 255, 255))
            pygame.gfxdraw.aacircle(surface, sx, sy, srad, (220, 220, 240))
            arcs = [
                (srad, (175, 82, 222)),
                (int(srad * 0.8), (0, 122, 255)),
                (int(srad * 0.6), (52, 199, 89)),
                (int(srad * 0.4), (255, 204, 0)),
                (int(srad * 0.2), (255, 59, 48))
            ]
            for r_val, arc_col in arcs:
                if r_val > 0:
                    pygame.gfxdraw.filled_circle(surface, sx, sy, r_val, arc_col)
                    pygame.gfxdraw.aacircle(surface, sx, sy, r_val, (255, 255, 255))
        else:
            # 3D Sphere with radial gradient
            sphere_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
            
            # Base dark tone
            pygame.draw.circle(sphere_surf, grad_end, (srad, srad), srad)
            
            # Light source offset towards top-left (30% 30%)
            lx = int(srad * 0.7)
            ly = int(srad * 0.65)
            
            # Layered radial gradient circles
            steps = max(4, srad // 2)
            for i in range(steps, 0, -1):
                ratio = i / steps
                r_col = (
                    int(grad_end[0] + (grad_start[0] - grad_end[0]) * ratio),
                    int(grad_end[1] + (grad_start[1] - grad_end[1]) * ratio),
                    int(grad_end[2] + (grad_start[2] - grad_end[2]) * ratio)
                )
                cur_r = int(srad * ratio)
                cur_cx = int(srad + (lx - srad) * (1 - ratio))
                cur_cy = int(srad + (ly - srad) * (1 - ratio))
                if cur_r > 0:
                    pygame.draw.circle(sphere_surf, r_col, (cur_cx, cur_cy), cur_r)
            
            # 3. Specular Highlight (gloss gleam at top-left)
            gleam_rad = max(2, int(srad * 0.35))
            gleam_x = int(srad * 0.65)
            gleam_y = int(srad * 0.55)
            gleam_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
            pygame.draw.circle(gleam_surf, (255, 255, 255, 140), (gleam_x, gleam_y), gleam_rad)
            # Secondary micro gleam
            pygame.draw.circle(gleam_surf, (255, 255, 255, 80), (gleam_x + 3, gleam_y + 3), max(1, gleam_rad // 2))
            sphere_surf.blit(gleam_surf, (0, 0))

            # 4. Subtle bottom-right rim light
            rim_x = int(srad * 1.3)
            rim_y = int(srad * 1.3)
            pygame.draw.circle(sphere_surf, (255, 255, 255, 25), (rim_x, rim_y), max(1, srad // 3))

            surface.blit(sphere_surf, (sx - srad, sy - srad))
            pygame.gfxdraw.aacircle(surface, sx, sy, srad, (255, 255, 255, 40))

            # Draw symbol for special bubbles
            if symbol:
                font_name = 'Segoe UI Emoji' if self.bubble_type in ["rescue", "bomb", "lightning", "fireball", "obstacle"] else 'Arial'
                try:
                    font = pygame.font.SysFont(font_name, int(srad * 1.1), bold=True)
                except Exception:
                    font = pygame.font.Font(None, int(srad * 1.1))
                text = font.render(symbol, True, symbol_color)
                surface.blit(text, text.get_rect(center=(sx, sy)))
