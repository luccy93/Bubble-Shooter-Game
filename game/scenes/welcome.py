# game/scenes/welcome.py - Entry portal with glassmorphism, ambient bubbles, and Stitch design

import pygame
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import (draw_gradient_bg, draw_glass_panel,
                                    create_ambient_bubbles, update_ambient_bubbles,
                                    draw_ambient_bubbles)
from game.auth.session_manager import SessionManager


class WelcomeScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)

        self.title_label = Label("BUBBLE", size=46, title=True,
                                 color=GameConfig.COLOR_PRIMARY_LIGHT, glow=True)
        self.title_label2 = Label("QUEST", size=38, title=True,
                                  color=GameConfig.COLOR_GOLD, glow=True)
        self.sub_label = Label("Choose your adventure", size=15,
                               color=GameConfig.COLOR_TEXT_MUTED)

        # Main options buttons — hero guest, glass auth
        self.guest_btn = Button("🎮  PLAY AS GUEST", w=260, h=54,
                                bg_color=GameConfig.COLOR_PRIMARY, hero=True)
        self.login_btn = Button("🔑  SIGN IN", w=260, h=48,
                                bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.signup_btn = Button("📝  CREATE ACCOUNT", w=260, h=48,
                                 bg_color=GameConfig.COLOR_SUCCESS_DIM)

        # Ambient bubbles
        self.bubbles = create_ambient_bubbles(10)
        self._bg_surface = None
        self.start_time = time.time()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        # Button clicks routing
        cx = GameConfig.VIRTUAL_WIDTH / 2
        if self.guest_btn.handle_event(event, cx, 400):
            SessionManager.logout()
            self.manager.change_scene("MainMenu")
        elif self.login_btn.handle_event(event, cx, 480):
            self.manager.change_scene("SignIn")
        elif self.signup_btn.handle_event(event, cx, 550):
            self.manager.change_scene("SignUp")

    def update(self, dt):
        update_ambient_bubbles(self.bubbles, dt)

    def draw(self, surface):
        # Gradient background (cached)
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(42, 27, 77),
                             bot_color=(15, 13, 23), radial=True)
        surface.blit(self._bg_surface, (0, 0))

        # Ambient floating bubbles
        draw_ambient_bubbles(surface, self.bubbles)

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Decorative bubble cluster at top
        elapsed = time.time() - self.start_time
        for i, (ox, oy, r, color_idx) in enumerate([
            (-50, 120, 20, 0), (60, 105, 16, 1), (-20, 80, 12, 3),
            (40, 135, 10, 2), (-65, 145, 8, 4)
        ]):
            bx = cx + ox + math.sin(elapsed * 0.8 + i) * 5
            by = oy + math.cos(elapsed * 0.6 + i * 0.5) * 4
            sx = GameConfig.to_screen_x(bx)
            sy = GameConfig.to_screen_y(by)
            sr = int(r * min(GameConfig.scale_x, GameConfig.scale_y))
            color = GameConfig.BUBBLE_COLORS[color_idx]
            bub_surf = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(bub_surf, (*color, 120), (sr, sr), sr)
            # Gloss highlight
            gloss_r = max(1, sr // 3)
            pygame.draw.circle(bub_surf, (255, 255, 255, 80),
                               (int(sr * 0.6), int(sr * 0.5)), gloss_r)
            surface.blit(bub_surf, (sx - sr, sy - sr))

        # Branding title with subtle bounce
        pulse = math.sin(elapsed * 2.5) * 3
        self.title_label.draw(surface, cx, 200 + pulse)
        self.title_label2.draw(surface, cx, 250 + pulse)
        self.sub_label.draw(surface, cx, 300)

        # Glass panel behind buttons
        panel_w = int(300 * GameConfig.scale_x)
        panel_h = int(250 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(365) - int(20 * GameConfig.scale_y)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=60, radius=int(24 * min(GameConfig.scale_x, GameConfig.scale_y)))

        # Draw buttons
        self.guest_btn.draw(surface, cx, 400)
        self.login_btn.draw(surface, cx, 480)
        self.signup_btn.draw(surface, cx, 550)

        # Footer text
        Label("v2.0.0 • Bubble Quest", size=11,
              color=GameConfig.COLOR_OUTLINE).draw(
            surface, cx, GameConfig.VIRTUAL_HEIGHT - 30)
