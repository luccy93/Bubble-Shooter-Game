# game/scenes/how_to_play.py - How to Play instructions screen

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button

class HowToPlayScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)

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
        Label("HOW TO PLAY", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)

        steps = [
            ("🎯 AIM", "Touch & drag anywhere to aim launcher"),
            ("🚀 SHOOT", "Release touch to fire bubble"),
            ("💥 MATCH 3+", "Match 3+ same-color bubbles to pop"),
            ("⬇️ DROP", "Disconnected bubbles fall down"),
            ("🏆 WIN", "Clear the entire board to win!")
        ]

        for i, (title, desc) in enumerate(steps):
            cy = 150 + i * 100
            
            # Card background Box
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(cy)
            sw = int(340 * GameConfig.scale_x)
            sh = int(80 * GameConfig.scale_y)
            card_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)
            pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, card_rect, border_radius=10)
            pygame.draw.rect(surface, GameConfig.COLOR_ACCENT, card_rect, width=1, border_radius=10)

            # Draw text lines
            Label(title, size=18, color=GameConfig.COLOR_PRIMARY, title=True, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 140, cy - 15, originX=0
            )
            Label(desc, size=13, color=GameConfig.COLOR_TEXT, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 140, cy + 15, originX=0
            )

        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)
