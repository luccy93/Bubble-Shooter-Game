# game/effects/particles.py - Particle effects, pop bursts, and launcher trails

import pygame
import random
import math
from game.core.config import GameConfig

class Particle:
    def __init__(self, vx, vy, color, radius=None):
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius if radius else random.randint(2, 5)
        
        # Velocity vector
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        
        self.alpha = 255
        self.fade_rate = random.randint(10, 18)

    def update(self):
        self.vx += self.dx
        self.vy += self.dy
        self.alpha = max(0, self.alpha - self.fade_rate)
        return self.alpha > 0

    def draw(self, surface):
        """Draws the scaled particle with alpha blending."""
        sx = GameConfig.to_screen_x(self.vx)
        sy = GameConfig.to_screen_y(self.vy)
        srad = int(self.radius * min(GameConfig.scale_x, GameConfig.scale_y))
        if srad <= 0:
            return

        # Render alpha blending via temporary surface
        p_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(p_surf, color_with_alpha, (srad, srad), srad)
        surface.blit(p_surf, (sx - srad, sy - srad))


class ParticleSystem:
    _particles = []

    @classmethod
    def create_pop_burst(cls, vx, vy, color):
        """Spawns radial burst particles centered on popped bubble coordinates."""
        for _ in range(8):
            cls._particles.append(Particle(vx, vy, color))

    @classmethod
    def create_trail(cls, vx, vy, color):
        """Spawns soft drift trail particles during bubble flight."""
        if random.random() < 0.35:
            cls._particles.append(Particle(vx, vy, color, radius=2))

    @classmethod
    def create_confetti(cls, count=30):
        """Spawns celebration drop fall particles."""
        colors = GameConfig.BUBBLE_COLORS
        for _ in range(count):
            vx = random.randint(50, GameConfig.VIRTUAL_WIDTH - 50)
            vy = random.randint(50, 300)
            p = Particle(vx, vy, random.choice(colors), radius=random.randint(3, 6))
            # Override to float downward
            p.dy = random.uniform(1.0, 3.0)
            p.dx = random.uniform(-0.5, 0.5)
            p.fade_rate = random.randint(5, 10)
            cls._particles.append(p)

    @classmethod
    def update(cls):
        cls._particles = [p for p in cls._particles if p.update()]

    @classmethod
    def draw(cls, surface):
        for p in cls._particles:
            p.draw(surface)

    @classmethod
    def clear(cls):
        cls._particles.clear()
