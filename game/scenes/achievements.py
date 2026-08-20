# game/scenes/achievements.py - Achievements checklist display scene

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager

class AchievementsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.unlocked_achievements = SaveManager.load_game()["achievements"]

        # Achievements list mapping
        self.ach_defs = [
            ("first_bubble", "🫧 First Pop", "Pop your first bubble"),
            ("first_win", "🎉 First Victory", "Complete your first level"),
            ("pop_100", "💯 Pop Star", "Pop 100 bubbles total"),
            ("pop_1000", "🌟 Bubble Master", "Pop 1,000 bubbles total"),
            ("combo_master", "🔥 Combo King", "Achieve a x5 combo"),
            ("perfect_clear", "✨ Perfect Clear", "Clear all board bubbles"),
            ("levels_10", "🗺️ Adventurer", "Complete 10 levels total")
        ]

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
        Label("ACHIEVEMENTS", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)

        for i, (ach_id, name, desc) in enumerate(self.ach_defs):
            is_unlocked = ach_id in self.unlocked_achievements
            cy = 135 + i * 72

            # Card background Box
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(cy)
            sw = int(350 * GameConfig.scale_x)
            sh = int(58 * GameConfig.scale_y)
            card_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)

            bg_color = (26, 42, 26) if is_unlocked else GameConfig.COLOR_BG_LIGHT
            stroke_color = (76, 175, 80) if is_unlocked else (50, 45, 75)
            
            pygame.draw.rect(surface, bg_color, card_rect, border_radius=10)
            pygame.draw.rect(surface, stroke_color, card_rect, width=1, border_radius=10)

            # Draw labels
            title_color = GameConfig.COLOR_SUCCESS if is_unlocked else GameConfig.COLOR_TEXT_MUTED
            Label(name, size=15, color=title_color, title=True, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 150, cy - 10, originX=0
            )
            desc_color = (136, 187, 136) if is_unlocked else (100, 100, 120)
            Label(desc, size=11, color=desc_color, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 150, cy + 12, originX=0
            )

            # Checkmark indicator
            status_char = "✅" if is_unlocked else "🔒"
            Label(status_char, size=16).draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 140, cy)

        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)
