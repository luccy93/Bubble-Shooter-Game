# game/scenes/shop.py - Virtual store scene to buy boosters using coins

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager

class ShopScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.coins = SaveManager.get_coins()
        self.boosters = SaveManager.get_boosters()

        # Buy buttons
        self.buy_bomb_btn = Button("🪙 50 COINS", w=130, h=38, bg_color=(255, 102, 0))
        self.buy_light_btn = Button("🪙 50 COINS", w=130, h=38, bg_color=(156, 39, 176))
        self.buy_rain_btn = Button("🪙 50 COINS", w=130, h=38, bg_color=(0, 188, 212))
        self.buy_fire_btn = Button("🪙 50 COINS", w=130, h=38, bg_color=(220, 50, 50))

        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        
        self.status_msg = "Upgrade your boosters inventory!"
        self.status_color = GameConfig.COLOR_TEXT_MUTED

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Back click
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("MainMenu")
            return

        # Buy items checks
        if self.buy_bomb_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 80, 200):
            self.attempt_purchase("bomb")
        elif self.buy_light_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 80, 280):
            self.attempt_purchase("lightning")
        elif self.buy_rain_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 80, 360):
            self.attempt_purchase("rainbow")
        elif self.buy_fire_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 80, 440):
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
            pygame.mixer.Sound(GameConfig.get_asset_path('audio', 'popcork.ogg')).play()
        else:
            self.status_msg = "Not enough coins! Win more levels to earn coins."
            self.status_color = GameConfig.COLOR_FAILURE

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Header Title
        Label("VIRTUAL SHOP", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)
        
        # Display coins balance
        Label(f"🪙 {self.coins} COINS", size=18, color=(255, 235, 59), title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 105
        )
        
        Label(self.status_msg, size=12, color=self.status_color).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 138
        )

        # Draw Booster inventory items
        items = [
            ("💣 BOMB", "Explodes radius of 2 bubbles", self.boosters.get("bomb", 0), 200, self.buy_bomb_btn),
            ("⚡ LIGHTNING", "Clears the entire snapped row", self.boosters.get("lightning", 0), 280, self.buy_light_btn),
            ("🌈 RAINBOW", "Pops all matching colored bubbles", self.boosters.get("rainbow", 0), 360, self.buy_rain_btn),
            ("🔥 FIREBALL", "Pierces and pops flight trajectory line", self.boosters.get("fireball", 0), 440, self.buy_fire_btn)
        ]

        for label, desc, owned, cy, btn in items:
            # Card shape
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(cy)
            sw = int(350 * GameConfig.scale_x)
            sh = int(60 * GameConfig.scale_y)
            card_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)
            pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, card_rect, border_radius=10)

            # Details
            Label(label, size=13, title=True, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 160, cy - 10, originX=0
            )
            Label(desc, size=9, color=GameConfig.COLOR_TEXT_MUTED, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 160, cy + 12, originX=0
            )
            Label(f"Owned: {owned}", size=11, color=GameConfig.COLOR_PRIMARY, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 20, cy
            )

            # Draw Buy Button
            btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 100, cy)

        # Back
        self.back_btn.draw(surface, 80, 50)
