# game/scenes/statistics.py - Stats display screen with Stitch design

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel
from game.storage.save_manager import SaveManager

class StatisticsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        profile = SaveManager.get_profile()
        self.stats = profile["stats"]
        
        # Calculate total stars
        total_stars = 0
        for val in profile.get("stars", {}).values():
            total_stars += val
        self.total_stars = total_stars
        self._bg_surface = None

    def _format_time(self, seconds):
        if seconds <= 0:
            return "0m"
        mins = seconds // 60
        hours = mins // 60
        if hours > 0:
            return f"{hours}h {mins % 60}m"
        return f"{mins}m"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        if self.back_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(35, 22, 65), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2
        Label("STATISTICS", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)

        entries = [
            ("🎮 Games Played", self.stats["games_played"]),
            ("🏆 Levels Completed", self.stats["levels_completed"]),
            ("🫧 Bubbles Popped", self.stats["bubbles_popped"]),
            ("⬇️ Bubbles Dropped", self.stats["bubbles_dropped"]),
            ("⭐ Highest Score", self.stats["highest_score"]),
            ("🔥 Highest Combo", f"x{self.stats['highest_combo']}"),
            ("💫 Total Stars Unlocked", f"{self.total_stars} / 45"),
            ("⏱️ Total Play Time", self._format_time(self.stats["play_time_sec"]))
        ]

        for i, (label, val) in enumerate(entries):
            cy = 135 + i * 56
            
            row_w = int(360 * GameConfig.scale_x)
            row_h = int(44 * GameConfig.scale_y)
            row_x = GameConfig.to_screen_x(cx) - row_w // 2
            row_y = GameConfig.to_screen_y(cy) - row_h // 2
            draw_glass_panel(surface, pygame.Rect(row_x, row_y, row_w, row_h),
                             opacity=70, radius=10)

            Label(label, size=14, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, cx - 150, cy, originX=0
            )
            Label(str(val), size=16, color=GameConfig.COLOR_PRIMARY_LIGHT, title=True).draw(
                surface, cx + 130, cy, originX=1
            )

        self.back_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 60)
