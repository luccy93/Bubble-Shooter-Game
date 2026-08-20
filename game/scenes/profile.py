# game/scenes/profile.py - User Profile and Stats viewer screen

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager
from game.auth.session_manager import SessionManager

class ProfileScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.active_user = SaveManager.get_active_user()
        self.profile = SaveManager.get_profile()
        self.stats = self.profile["stats"]
        
        # Determine guest status
        self.is_guest = (self.active_user == "guest")

        # Action Buttons
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        
        if self.is_guest:
            self.action_btn = Button("📝 CREATE ACCOUNT", w=220, h=46, bg_color=GameConfig.COLOR_SUCCESS)
        else:
            self.action_btn = Button("🔒 LOG OUT", w=200, h=44, bg_color=GameConfig.COLOR_FAILURE)

        # Calculate stars
        stars_count = 0
        for val in self.profile.get("stars", {}).values():
            stars_count += val
        self.stars_count = stars_count

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Back navigation click
        if self.back_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")
            return

        # Action click
        if self.action_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 490):
            if self.is_guest:
                self.manager.change_scene("SignUp")
            else:
                SessionManager.logout()
                self.manager.change_scene("Welcome")

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)
        Label("USER PROFILE", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)

        # Avatar card box layout
        cy = 150
        scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
        scy = GameConfig.to_screen_y(cy)
        sw = int(350 * GameConfig.scale_x)
        sh = int(100 * GameConfig.scale_y)
        avatar_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)
        pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, avatar_rect, border_radius=12)
        pygame.draw.rect(surface, GameConfig.COLOR_ACCENT, avatar_rect, width=1, border_radius=12)

        # Avatar profile symbol (e.g. Emoji)
        avatar_symbol = "👤" if not self.is_guest else "🎮"
        Label(avatar_symbol, size=32).draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 120, cy)

        # Profile headers
        usr_title = self.profile["name"]
        usr_sub = self.active_user if not self.is_guest else "Playing locally as Guest"
        Label(usr_title, size=18, title=True, align="left").draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2 - 70, cy - 15, originX=0
        )
        Label(usr_sub, size=12, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2 - 70, cy + 15, originX=0
        )

        # Display performance stats indicators
        entries = [
            ("Levels Cleared", f"{self.stats['levels_completed']} / 15"),
            ("Total Stars", f"{self.stars_count} / 45"),
            ("Highest Score", self.stats["highest_score"]),
            ("Highest Combo", f"x{self.stats['highest_combo']}")
        ]

        for i, (label, val) in enumerate(entries):
            ry = 265 + i * 50
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(ry)
            sw = int(350 * GameConfig.scale_x)
            sh = int(38 * GameConfig.scale_y)
            row_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)
            pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, row_rect, border_radius=8)

            Label(label, size=14, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 145, ry, originX=0
            )
            Label(str(val), size=15, color=GameConfig.COLOR_PRIMARY, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 + 130, ry, originX=1
            )

        # Sign Up prompts if Guest
        if self.is_guest:
            Label("Sign up to save progress across sessions!", size=11, color=GameConfig.COLOR_PRIMARY).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, 448
            )

        # Action Buttons
        self.action_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 490)
        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)
