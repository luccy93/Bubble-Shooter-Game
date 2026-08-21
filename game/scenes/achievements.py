# game/scenes/achievements.py - Achievements checklist display scene with Stitch design

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel
from game.storage.save_manager import SaveManager

class AchievementsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        profile = SaveManager.get_profile()
        self.unlocked_achievements = profile.get("achievements", [])

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
        self._bg_surface = None

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
        Label("ACHIEVEMENTS", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)

        for i, (ach_id, name, desc) in enumerate(self.ach_defs):
            is_unlocked = ach_id in self.unlocked_achievements
            cy = 135 + i * 72

            card_w = int(360 * GameConfig.scale_x)
            card_h = int(60 * GameConfig.scale_y)
            card_x = GameConfig.to_screen_x(cx) - card_w // 2
            card_y = GameConfig.to_screen_y(cy) - card_h // 2
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            stroke_color = GameConfig.COLOR_SUCCESS if is_unlocked else GameConfig.COLOR_OUTLINE_DIM
            draw_glass_panel(surface, card_rect, opacity=90 if is_unlocked else 60,
                             border_color=stroke_color, radius=12, glow=is_unlocked)

            # Draw labels
            title_color = GameConfig.COLOR_SUCCESS if is_unlocked else GameConfig.COLOR_TEXT_MUTED
            Label(name, size=15, color=title_color, title=True, align="left").draw(
                surface, cx - 155, cy - 10, originX=0
            )
            desc_color = GameConfig.COLOR_TEXT if is_unlocked else GameConfig.COLOR_TEXT_MUTED
            Label(desc, size=11, color=desc_color, align="left").draw(
                surface, cx - 155, cy + 12, originX=0
            )

            # Checkmark indicator
            status_char = "✅" if is_unlocked else "🔒"
            Label(status_char, size=16).draw(surface, cx + 145, cy)

        self.back_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 60)
