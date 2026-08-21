# game/scenes/shop.py - Virtual store scene to buy boosters using coins with Stitch design

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel, draw_currency_chip
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager

class ShopScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.coins = SaveManager.get_coins()
        self.boosters = SaveManager.get_boosters()

        # Buy buttons
        self.buy_bomb_btn = Button("🪙 50 COINS", w=130, h=36, bg_color=(255, 102, 0))
        self.buy_light_btn = Button("🪙 50 COINS", w=130, h=36, bg_color=(156, 39, 176))
        self.buy_rain_btn = Button("🪙 50 COINS", w=130, h=36, bg_color=(0, 188, 212))
        self.buy_fire_btn = Button("🪙 50 COINS", w=130, h=36, bg_color=(220, 50, 50))

        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        
        self.status_msg = "Upgrade your boosters inventory!"
        self.status_color = GameConfig.COLOR_TEXT_MUTED
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Back click
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("MainMenu")
            return

        cx = GameConfig.VIRTUAL_WIDTH / 2
        # Buy items checks
        if self.buy_bomb_btn.handle_event(event, cx + 90, 215):
            self.attempt_purchase("bomb")
        elif self.buy_light_btn.handle_event(event, cx + 90, 295):
            self.attempt_purchase("lightning")
        elif self.buy_rain_btn.handle_event(event, cx + 90, 375):
            self.attempt_purchase("rainbow")
        elif self.buy_fire_btn.handle_event(event, cx + 90, 455):
            self.attempt_purchase("fireball")

    def attempt_purchase(self, b_type):
        coins = SaveManager.get_coins()
        if coins >= 50:
            SaveManager.add_coins(-50)
            SaveManager.add_booster(b_type, count=1)
            
            # Update cache values
            self.coins = SaveManager.get_coins()
            self.boosters = SaveManager.get_boosters()
            
            self.status_msg = f"Purchased 1 {b_type.upper()} booster successfully!"
            self.status_color = GameConfig.COLOR_SUCCESS
            AudioManager.play_sfx('pop')
        else:
            self.status_msg = "Not enough coins! Win more levels to earn coins."
            self.status_color = GameConfig.COLOR_FAILURE

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(35, 22, 65), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Header Title
        Label("VIRTUAL SHOP", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)
        
        # Display coins balance chip
        draw_currency_chip(surface, cx, 110, "🪙", self.coins)
        
        Label(self.status_msg, size=12, color=self.status_color).draw(
            surface, cx, 150
        )

        # Draw Booster inventory items
        items = [
            ("💣 BOMB", "Explodes radius of 2 bubbles", self.boosters.get("bomb", 0), 215, self.buy_bomb_btn, (255, 102, 0)),
            ("⚡ LIGHTNING", "Clears the entire snapped row", self.boosters.get("lightning", 0), 295, self.buy_light_btn, (186, 104, 200)),
            ("🌈 RAINBOW", "Pops all matching colored bubbles", self.boosters.get("rainbow", 0), 375, self.buy_rain_btn, (0, 188, 212)),
            ("🔥 FIREBALL", "Pierces and pops flight trajectory line", self.boosters.get("fireball", 0), 455, self.buy_fire_btn, (255, 75, 40))
        ]

        for label, desc, owned, cy, btn, icon_color in items:
            # Glass Card shape
            card_w = int(360 * GameConfig.scale_x)
            card_h = int(68 * GameConfig.scale_y)
            card_x = GameConfig.to_screen_x(cx) - card_w // 2
            card_y = GameConfig.to_screen_y(cy) - card_h // 2
            draw_glass_panel(surface, pygame.Rect(card_x, card_y, card_w, card_h),
                             opacity=80, radius=14)

            # Details
            Label(label, size=14, title=True, align="left", color=GameConfig.COLOR_TEXT).draw(
                surface, cx - 160, cy - 12, originX=0
            )
            Label(desc, size=10, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, cx - 160, cy + 12, originX=0
            )
            Label(f"Owned: {owned}", size=11, color=GameConfig.COLOR_PRIMARY_LIGHT, title=True).draw(
                surface, cx - 5, cy
            )

            # Draw Buy Button
            btn.draw(surface, cx + 90, cy)

        # Back
        self.back_btn.draw(surface, 80, 50)
