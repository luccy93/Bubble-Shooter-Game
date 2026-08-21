# game/scenes/splash.py - Animated splash with radial gradient, particles, and pulsing glow

import pygame
import time
import math
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label
from game.ui.design_system import draw_gradient_bg, create_ambient_bubbles, update_ambient_bubbles, draw_ambient_bubbles


class SplashScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.start_time = time.time()
        self.logo_label = Label("BUBBLE", size=52, title=True, color=GameConfig.COLOR_PRIMARY_LIGHT, glow=True)
        self.sub_label = Label("QUEST", size=44, title=True, color=GameConfig.COLOR_GOLD, glow=True)
        self.alpha = 0
        self.fade_duration = 0.8
        self.display_duration = 1.2
        self.transitioning = False

        # Ambient floating bubble particles
        self.bubbles = create_ambient_bubbles(12)

        # Pre-render gradient background
        self._bg_surface = None

    def handle_event(self, event):
        # Quick skip splash on click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.manager.change_scene("Welcome")

    def update(self, dt):
        elapsed = time.time() - self.start_time

        # Update ambient bubbles
        update_ambient_bubbles(self.bubbles, dt)

        # Calculate fade alpha
        if elapsed < self.fade_duration:
            self.alpha = int((elapsed / self.fade_duration) * 255)
        elif elapsed < self.fade_duration + self.display_duration:
            self.alpha = 255
        elif elapsed < self.fade_duration * 2 + self.display_duration:
            fade_out_elapsed = elapsed - (self.fade_duration + self.display_duration)
            self.alpha = int((1.0 - (fade_out_elapsed / self.fade_duration)) * 255)
        else:
            self.alpha = 0
            if not self.transitioning:
                self.transitioning = True
                self.manager.change_scene("Welcome")

    def draw(self, surface):
        # Render gradient background (cached)
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(42, 27, 77), bot_color=(15, 13, 23), radial=True)
        surface.blit(self._bg_surface, (0, 0))

        # Draw ambient floating bubbles
        draw_ambient_bubbles(surface, self.bubbles)

        # Draw logo centered with alpha fade
        if self.alpha > 0:
            logo_surf = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)

            cx = GameConfig.VIRTUAL_WIDTH / 2
            cy = GameConfig.VIRTUAL_HEIGHT / 2

            # Pulsing glow ring behind text
            elapsed = time.time() - self.start_time
            pulse = 0.5 + 0.5 * math.sin(elapsed * 4)
            ring_alpha = int(30 + 40 * pulse)
            ring_rad = int(90 * min(GameConfig.scale_x, GameConfig.scale_y))
            ring_surf = pygame.Surface((ring_rad * 2, ring_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*GameConfig.COLOR_PRIMARY[:3], ring_alpha),
                               (ring_rad, ring_rad), ring_rad)
            ring_sx = GameConfig.to_screen_x(cx) - ring_rad
            ring_sy = GameConfig.to_screen_y(cy) - ring_rad
            logo_surf.blit(ring_surf, (ring_sx, ring_sy))

            # Render labels onto temporary surface
            self.logo_label.draw(logo_surf, cx, cy - 30)
            self.sub_label.draw(logo_surf, cx, cy + 30)

            # Sparkle dots
            for i in range(6):
                angle = elapsed * 1.5 + i * math.pi / 3
                dist = 70 + math.sin(elapsed * 2 + i) * 15
                sx = GameConfig.to_screen_x(cx + math.cos(angle) * dist)
                sy = GameConfig.to_screen_y(cy + math.sin(angle) * dist)
                spark_alpha = int(100 + 80 * math.sin(elapsed * 5 + i * 2))
                spark_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(spark_surf, (255, 255, 255, spark_alpha), (3, 3), 3)
                logo_surf.blit(spark_surf, (sx - 3, sy - 3))

            # Apply alpha factor
            logo_surf.set_alpha(self.alpha)
            surface.blit(logo_surf, (0, 0))
