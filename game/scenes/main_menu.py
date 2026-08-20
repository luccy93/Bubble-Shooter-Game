# game/scenes/main_menu.py - Premium Main Menu Screen with drifting bubble particles

import pygame
import math
import random
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.audio.audio_manager import AudioManager

class MainMenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Centralized Title setup
        self.title_label = Label("BUBBLE", size=48, title=True, color=GameConfig.COLOR_PRIMARY)
        self.subtitle_label = Label("SHOOTER", size=42, title=True, color=(255, 255, 255))
        
        # Interactive Navigation Buttons
        self.play_btn = Button("▶ PLAY", w=220, h=54, bg_color=GameConfig.COLOR_PRIMARY)
        self.levels_btn = Button("📋 LEVEL SELECT", w=200, h=44, font_size=15)
        self.settings_btn = Button("⚙️ SETTINGS", w=200, h=44, font_size=15)
        self.how_to_btn = Button("❓ HOW TO PLAY", w=200, h=44, font_size=15)
        self.achieve_btn = Button("🏆 ACHIEVEMENTS", w=200, h=44, font_size=15)
        self.stats_btn = Button("📊 STATISTICS", w=200, h=44, font_size=15)

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

    def handle_event(self, event):
        # 1. Back button exit handling
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        # 2. Touch/click checks on active buttons
        if self.play_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 300):
            self.manager.change_scene("LevelSelect")
        elif self.levels_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 380):
            self.manager.change_scene("LevelSelect")
        elif self.settings_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 440):
            self.manager.change_scene("Settings")
        elif self.how_to_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 500):
            self.manager.change_scene("HowToPlay")
        elif self.achieve_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 560):
            self.manager.change_scene("Achievements")
        elif self.stats_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 620):
            self.manager.change_scene("Statistics")

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
        self.title_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 130 + pulse)
        self.subtitle_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 185 + pulse)

        # Render active buttons
        self.play_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 300)
        self.levels_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 380)
        self.settings_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 440)
        self.how_to_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 500)
        self.achieve_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 560)
        self.stats_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 620)
        
        # High Score watermark at bottom
        _, high_score, _ = SaveManager.get_progress()
        Label(f"HIGH SCORE: {high_score}", size=14, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 35
        )
import time
