# game/scenes/main_menu.py - Premium Main Menu Screen with drifting bubble particles

import pygame
import math
import random
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.audio.audio_manager import AudioManager

class MainMenuScene(BaseScene):
    _has_checked_daily = False

    def __init__(self, manager):
        super().__init__(manager)
        
        # Centralized Title setup
        self.title_label = Label("BUBBLE", size=48, title=True, color=GameConfig.COLOR_PRIMARY)
        self.subtitle_label = Label("SHOOTER", size=42, title=True, color=(255, 255, 255))
        
        # Interactive Navigation Buttons
        self.play_btn = Button("▶ PLAY", w=220, h=54, bg_color=GameConfig.COLOR_PRIMARY)
        self.levels_btn = Button("📋 LEVEL SELECT", w=200, h=40, font_size=14)
        self.settings_btn = Button("⚙️ SETTINGS", w=200, h=40, font_size=14)
        self.shop_btn = Button("🛒 SHOP", w=200, h=40, font_size=14)
        self.achieve_btn = Button("🏆 ACHIEVEMENTS", w=200, h=40, font_size=14)
        self.profile_btn = Button("👤 PROFILE", w=200, h=40, font_size=14)
        self.how_to_btn = Button("❓ HOW TO PLAY", w=200, h=40, font_size=14)

        # Ambient floating bubbles background
        self.ambient_bubbles = []
        for _ in range(8):
            self.ambient_bubbles.append({
                "vx": random.randint(30, GameConfig.VIRTUAL_WIDTH - 30),
                "vy": random.randint(50, GameConfig.VIRTUAL_HEIGHT - 50),
                "r": random.randint(10, 22),
                "color": random.choice(GameConfig.BUBBLE_COLORS),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.5, 1.2)
            })

        # Start soundtrack
        AudioManager.play_music('Goofy_Theme.ogg')

        # Check daily rewards once per game launch
        if not MainMenuScene._has_checked_daily:
            MainMenuScene._has_checked_daily = True
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            if SaveManager.get_last_claim_date() != today_str:
                # Redirect to DailyRewards calendar
                self.manager.change_scene("DailyRewards")

    def handle_event(self, event):
        # 1. Back button exit handling
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        # 2. Touch/click checks on active buttons
        if self.play_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 280):
            self.manager.change_scene("LevelSelect")
        elif self.levels_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 350):
            self.manager.change_scene("LevelSelect")
        elif self.settings_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 410):
            self.manager.change_scene("Settings")
        elif self.shop_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 470):
            self.manager.change_scene("Shop")
        elif self.achieve_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 530):
            self.manager.change_scene("Achievements")
        elif self.profile_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 590):
            self.manager.change_scene("Profile")
        elif self.how_to_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 650):
            self.manager.change_scene("HowToPlay")

    def update(self, dt):
        # Gentle floating background animation
        for b in self.ambient_bubbles:
            b["phase"] += dt * b["speed"]
            b["vy"] -= b["speed"] * 10 * dt
            # Wraparound screen edges
            if b["vy"] < -b["r"]:
                b["vy"] = GameConfig.VIRTUAL_HEIGHT + b["r"]
                b["vx"] = random.randint(30, GameConfig.VIRTUAL_WIDTH - 30)

    def draw(self, surface):
        # Draw background base
        surface.fill(GameConfig.COLOR_BG)

        # Draw ambient drift bubbles
        for b in self.ambient_bubbles:
            sx = GameConfig.to_screen_x(b["vx"] + math.sin(b["phase"]) * 15)
            sy = GameConfig.to_screen_y(b["vy"])
            srad = int(b["r"] * min(GameConfig.scale_x, GameConfig.scale_y))
            if srad > 0:
                # Transparent surface for alpha blending
                surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*b["color"], 30), (srad, srad), srad)
                surface.blit(surf, (sx - srad, sy - srad))

        # Title bounce glow pulse
        pulse = math.sin(time.time() * 3) * 3
        self.title_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 120 + pulse)
        self.subtitle_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 175 + pulse)

        # Render active buttons
        self.play_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 280)
        self.levels_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 350)
        self.settings_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 410)
        self.shop_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 470)
        self.achieve_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 530)
        self.profile_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 590)
        self.how_to_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 650)
        
        # High Score watermark at bottom
        _, high_score, _ = SaveManager.get_progress()
        Label(f"HIGH SCORE: {high_score}", size=13, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 28
        )
import time
