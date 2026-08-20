# game/scenes/daily_rewards.py - Daily Reward Claim Calendar screen

import pygame
import time
from datetime import datetime
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager

class DailyRewardsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Load user profile streak index
        profile = SaveManager.get_profile()
        # Default streak index to 0 if missing
        self.streak_idx = profile.setdefault("claim_streak_index", 0)

        # Rewards list
        self.rewards = [
            {"desc": "50 Coins", "icon": "🪙", "coins": 50, "booster": None},
            {"desc": "1 Bomb", "icon": "💣", "coins": 0, "booster": "bomb"},
            {"desc": "100 Coins", "icon": "🪙", "coins": 100, "booster": None},
            {"desc": "1 Lightning", "icon": "⚡", "coins": 0, "booster": "lightning"},
            {"desc": "Mega Chest!", "icon": "🎁", "coins": 150, "booster": "rainbow"} # Rainbow booster + 150 coins
        ]

        self.claim_btn = Button("🎁 CLAIM REWARD", w=220, h=48, bg_color=GameConfig.COLOR_SUCCESS)
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        
        # Check claim state
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.already_claimed = (SaveManager.get_last_claim_date() == today_str)
        self.status_msg = "Claim your reward for today!" if not self.already_claimed else "Already claimed today! Come back tomorrow."

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Back click
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("MainMenu")
            return

        # Claim click
        if not self.already_claimed:
            if self.claim_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 120):
                self.process_claim()

    def process_claim(self):
        # 1. Fetch active reward
        r = self.rewards[self.streak_idx]
        
        # Credit rewards
        if r["coins"] > 0:
            SaveManager.add_coins(r["coins"])
        if r["booster"]:
            SaveManager.add_booster(r["booster"], count=1)
            # If Chest reward, also give 1 of other boosters!
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
        
        pygame.mixer.Sound(GameConfig.get_asset_path('audio', 'popcork.ogg')).play()

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Header Title
        Label("DAILY REWARDS", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)
        Label(self.status_msg, size=13, color=GameConfig.COLOR_PRIMARY).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 110
        )

        # Draw Calendar cards for 5 days
        for i in range(5):
            r = self.rewards[i]
            cy = 170 + i * 70
            
            # Convert cards
            scx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2)
            scy = GameConfig.to_screen_y(cy)
            sw = int(340 * GameConfig.scale_x)
            sh = int(54 * GameConfig.scale_y)
            card_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)

            # Determine background coloring depending on active/claimed streak
            if i < self.streak_idx:
                # Already claimed in the past
                bg_color = (25, 35, 30)
                border_color = GameConfig.COLOR_SUCCESS
                tag = "CLAIMED"
            elif i == self.streak_idx and not self.already_claimed:
                # Active today!
                bg_color = (35, 25, 55)
                border_color = GameConfig.COLOR_PRIMARY
                tag = "TODAY"
            else:
                # Locked future rewards
                bg_color = GameConfig.COLOR_BG_LIGHT
                border_color = (60, 50, 85)
                tag = f"DAY {i+1}"

            pygame.draw.rect(surface, bg_color, card_rect, border_radius=10)
            pygame.draw.rect(surface, border_color, card_rect, width=1, border_radius=10)

            # Draw card descriptors
            Label(tag, size=12, color=border_color, title=True, align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2 - 140, cy, originX=0
            )
            Label(r["icon"], size=22).draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 40, cy)
            Label(r["desc"], size=14, color=(255, 255, 255), align="left").draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, cy, originX=0
            )

        # Draw claim button
        if not self.already_claimed:
            self.claim_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 120)
        
        self.back_btn.draw(surface, 80, 50)
