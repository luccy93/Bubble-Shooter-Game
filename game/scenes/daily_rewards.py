# game/scenes/daily_rewards.py - Daily Reward Claim Calendar screen with Stitch design

import pygame
import time
from datetime import datetime
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager

class DailyRewardsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Load user profile streak index
        profile = SaveManager.get_profile()
        self.streak_idx = profile.setdefault("claim_streak_index", 0)

        # Rewards list
        self.rewards = [
            {"desc": "50 Coins", "icon": "🪙", "coins": 50, "booster": None},
            {"desc": "1 Bomb", "icon": "💣", "coins": 0, "booster": "bomb"},
            {"desc": "100 Coins", "icon": "🪙", "coins": 100, "booster": None},
            {"desc": "1 Lightning", "icon": "⚡", "coins": 0, "booster": "lightning"},
            {"desc": "Mega Chest!", "icon": "🎁", "coins": 150, "booster": "rainbow"}
        ]

        self.claim_btn = Button("🎁 CLAIM REWARD", w=240, h=50, bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        
        # Check claim state
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.already_claimed = (SaveManager.get_last_claim_date() == today_str)
        self.status_msg = "Claim your reward for today!" if not self.already_claimed else "Already claimed today! Come back tomorrow."
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
        # Claim click
        if not self.already_claimed:
            if self.claim_btn.handle_event(event, cx, GameConfig.VIRTUAL_HEIGHT - 110):
                self.process_claim()

    def process_claim(self):
        # 1. Fetch active reward
        r = self.rewards[self.streak_idx]
        
        # Credit rewards
        if r["coins"] > 0:
            SaveManager.add_coins(r["coins"])
        if r["booster"]:
            SaveManager.add_booster(r["booster"], count=1)
            if r["desc"] == "Mega Chest!":
                SaveManager.add_booster("bomb", count=1)
                SaveManager.add_booster("lightning", count=1)
                SaveManager.add_booster("fireball", count=1)

        # 2. Update claim timestamp and increment streak index
        today_str = datetime.now().strftime("%Y-%m-%d")
        SaveManager.set_last_claim_date(today_str)
        
        data = SaveManager.load_game()
        profile = data["accounts"][SaveManager.get_active_user()]
        profile["claim_streak_index"] = (self.streak_idx + 1) % 5
        SaveManager.save_game()

        # Update visual states
        self.streak_idx = profile["claim_streak_index"]
        self.already_claimed = True
        self.status_msg = "Claimed successfully! Streak progressed."
        
        AudioManager.play_sfx('victory')

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(35, 22, 65), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Header Title
        Label("DAILY REWARDS", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)
        Label(self.status_msg, size=13, color=GameConfig.COLOR_GOLD).draw(
            surface, cx, 105
        )

        # Draw Calendar cards for 5 days
        for i in range(5):
            r = self.rewards[i]
            cy = 175 + i * 76
            
            card_w = int(360 * GameConfig.scale_x)
            card_h = int(62 * GameConfig.scale_y)
            card_x = GameConfig.to_screen_x(cx) - card_w // 2
            card_y = GameConfig.to_screen_y(cy) - card_h // 2
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            if i < self.streak_idx:
                # Already claimed in the past
                border_color = GameConfig.COLOR_SUCCESS
                tag = "CLAIMED"
                tag_color = GameConfig.COLOR_SUCCESS
                glow = False
            elif i == self.streak_idx and not self.already_claimed:
                # Active today!
                border_color = GameConfig.COLOR_GOLD
                tag = "TODAY"
                tag_color = GameConfig.COLOR_GOLD
                glow = True
            else:
                # Locked future rewards
                border_color = GameConfig.COLOR_OUTLINE_DIM
                tag = f"DAY {i+1}"
                tag_color = GameConfig.COLOR_TEXT_MUTED
                glow = False

            draw_glass_panel(surface, card_rect, opacity=90, border_color=border_color,
                             radius=14, glow=glow)

            # Draw card descriptors
            Label(tag, size=12, color=tag_color, title=True, align="left").draw(
                surface, cx - 150, cy, originX=0
            )
            Label(r["icon"], size=22).draw(surface, cx - 40, cy)
            Label(r["desc"], size=14, color=GameConfig.COLOR_TEXT, align="left").draw(
                surface, cx + 5, cy, originX=0
            )

        # Draw claim button
        if not self.already_claimed:
            self.claim_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 110)
        
        self.back_btn.draw(surface, 80, 50)
