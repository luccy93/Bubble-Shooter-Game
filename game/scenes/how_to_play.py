# game/scenes/how_to_play.py - How to Play instructions screen with Stitch design

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel

class HowToPlayScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH)
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
        Label("HOW TO PLAY", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)

        steps = [
            ("🎯 AIM", "Touch & drag anywhere to aim launcher"),
            ("🚀 SHOOT", "Release touch to fire bubble"),
            ("💥 MATCH 3+", "Match 3+ same-color bubbles to pop"),
            ("⬇️ DROP", "Disconnected bubbles fall down"),
            ("🏆 WIN", "Clear the entire board to win!")
        ]

        for i, (title, desc) in enumerate(steps):
            cy = 150 + i * 100
            
            card_w = int(360 * GameConfig.scale_x)
            card_h = int(82 * GameConfig.scale_y)
            card_x = GameConfig.to_screen_x(cx) - card_w // 2
            card_y = GameConfig.to_screen_y(cy) - card_h // 2
            draw_glass_panel(surface, pygame.Rect(card_x, card_y, card_w, card_h),
                             opacity=80, radius=14, border_color=GameConfig.COLOR_PRIMARY)

            # Draw text lines
            Label(title, size=18, color=GameConfig.COLOR_GOLD, title=True, align="left").draw(
                surface, cx - 150, cy - 15, originX=0
            )
            Label(desc, size=13, color=GameConfig.COLOR_TEXT, align="left").draw(
                surface, cx - 150, cy + 15, originX=0
            )

        self.back_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 60)
