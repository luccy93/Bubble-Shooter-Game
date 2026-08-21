# game/scenes/profile.py - Premium User Profile with glassmorphism cards and real data

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel
from game.storage.save_manager import SaveManager
from game.auth.session_manager import SessionManager


class ProfileScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)

        self.active_user = SaveManager.get_active_user()
        self.profile = SaveManager.get_profile()
        self.stats = self.profile["stats"]
        self.is_guest = (self.active_user == "guest")

        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH)

        if self.is_guest:
            self.action_btn = Button("📝 CREATE ACCOUNT", w=220, h=46,
                                     bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        else:
            self.action_btn = Button("🔒 LOG OUT", w=200, h=44,
                                     bg_color=GameConfig.COLOR_FAILURE)

        # Calculate stars
        stars_count = sum(self.profile.get("stars", {}).values())
        self.stars_count = stars_count
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        if self.back_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")
            return

        if self.action_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 510):
            if self.is_guest:
                self.manager.change_scene("SignUp")
            else:
                SessionManager.logout()
                self.manager.change_scene("Welcome")

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(35, 22, 65), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2
        Label("USER PROFILE", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)

        # Avatar card with glassmorphism
        card_w = int(350 * GameConfig.scale_x)
        card_h = int(100 * GameConfig.scale_y)
        card_x = GameConfig.to_screen_x(cx) - card_w // 2
        card_y = GameConfig.to_screen_y(150) - card_h // 2
        draw_glass_panel(surface, pygame.Rect(card_x, card_y, card_w, card_h),
                         opacity=100, radius=int(16 * min(GameConfig.scale_x, GameConfig.scale_y)),
                         border_color=GameConfig.COLOR_PRIMARY)

        # Avatar symbol
        avatar_symbol = "👤" if not self.is_guest else "🎮"
        Label(avatar_symbol, size=32).draw(surface, cx - 120, 150)

        usr_title = self.profile["name"]
        usr_sub = self.active_user if not self.is_guest else "Playing locally as Guest"
        Label(usr_title, size=18, title=True, align="left").draw(surface, cx - 70, 135, originX=0)
        Label(usr_sub, size=12, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
            surface, cx - 70, 165, originX=0)

        # Stats rows with glass cards
        entries = [
            ("Levels Cleared", f"{self.stats['levels_completed']} / 15"),
            ("Total Stars", f"{self.stars_count} / 45"),
            ("Highest Score", self.stats["highest_score"]),
            ("Highest Combo", f"x{self.stats['highest_combo']}")
        ]

        for i, (label, val) in enumerate(entries):
            ry = 265 + i * 55
            row_w = int(350 * GameConfig.scale_x)
            row_h = int(42 * GameConfig.scale_y)
            row_x = GameConfig.to_screen_x(cx) - row_w // 2
            row_y = GameConfig.to_screen_y(ry) - row_h // 2
            draw_glass_panel(surface, pygame.Rect(row_x, row_y, row_w, row_h),
                             opacity=70, radius=10)

            Label(label, size=14, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, cx - 145, ry, originX=0)
            Label(str(val), size=15, color=GameConfig.COLOR_PRIMARY_LIGHT, title=True).draw(
                surface, cx + 130, ry, originX=1)

        # Sign up prompt for guests
        if self.is_guest:
            Label("Sign up to save progress across sessions!", size=11,
                  color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 468)

        self.action_btn.draw(surface, cx, 510)
        self.back_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 60)
