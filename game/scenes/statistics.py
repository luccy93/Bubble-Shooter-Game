# game/scenes/statistics.py - Stats display screen

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager

class StatisticsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        save_data = SaveManager.load_game()
        self.stats = save_data["stats"]
        
        # Calculate total stars
        total_stars = 0
        for val in save_data.get("stars", {}).values():
            total_stars += val
        self.total_stars = total_stars

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
        surface.fill(GameConfig.COLOR_BG)
        Label("STATISTICS", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)

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
            cy = 135 + i * 54
            
            # Draw row background line
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(cy)
            sw = int(340 * GameConfig.scale_x)
            sh = int(40 * GameConfig.scale_y)
            row_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)
            pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, row_rect, border_radius=8)

            Label(label, size=14, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 150, cy, originX=0
            )
            Label(str(val), size=16, color=GameConfig.COLOR_PRIMARY, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 + 130, cy, originX=1
            )

        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)
