# game/scenes/overlays.py - Pause, Victory, and Defeat screen overlays

import pygame
import math
import time
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.audio.audio_manager import AudioManager

class PauseOverlay:
    def __init__(self, scene):
        self.scene = scene
        self.resume_btn = Button("▶ RESUME", w=180, h=44, bg_color=GameConfig.COLOR_SUCCESS)
        self.restart_btn = Button("🔄 RESTART", w=180, h=44, bg_color=GameConfig.COLOR_PRIMARY)
        self.select_btn = Button("📋 LEVEL SELECT", w=180, h=44)
        self.menu_btn = Button("🏠 MAIN MENU", w=180, h=44, bg_color=GameConfig.COLOR_BG_LIGHT)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.scene.show_pause = False
                return True

        if self.resume_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 280):
            self.scene.show_pause = False
        elif self.restart_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 340):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 400):
            self.scene.manager.change_scene("LevelSelect")
        elif self.menu_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 460):
            self.scene.manager.change_scene("MainMenu")
        return True

    def draw(self, surface):
        # Draw dark tint overlay
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 200))
        surface.blit(sc, (0, 0))

        # Pause Title
        Label("PAUSED", size=32, title=True, shadow=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 180)

        # Draw buttons
        self.resume_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 280)
        self.restart_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 340)
        self.select_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 400)
        self.menu_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 460)


class VictoryOverlay:
    def __init__(self, scene, score, stars, level_id):
        self.scene = scene
        self.score = score
        self.stars = stars
        self.level_id = level_id
        
        # Audio & haptics check
        AudioManager.play_sfx('victory')

        self.next_btn = Button("▶ NEXT LEVEL", w=180, h=46, bg_color=GameConfig.COLOR_SUCCESS)
        self.replay_btn = Button("🔄 REPLAY", w=180, h=44, bg_color=GameConfig.COLOR_PRIMARY)
        self.select_btn = Button("📋 LEVEL SELECT", w=180, h=44)
        self.start_time = time.time()

    def handle_event(self, event):
        if self.next_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 380):
            next_lvl = min(self.level_id + 1, 15)
            self.scene.manager.change_scene("Gameplay", level_id=next_lvl)
        elif self.replay_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 440):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 500):
            self.scene.manager.change_scene("LevelSelect")
        return True

    def draw(self, surface):
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 225))
        surface.blit(sc, (0, 0))

        # Title completes
        Label("LEVEL COMPLETE!", size=30, title=True, color=GameConfig.COLOR_SUCCESS, shadow=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 140
        )
        Label(f"Score: {self.score}", size=20, title=True, color=(255, 235, 59)).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 200
        )

        # Star counts individually animated (fade/scale depending on time elapsed)
        t_elapsed = time.time() - self.start_time
        for i in range(3):
            # Staggered animation entrance: 0.2s delay between stars
            target_time = 0.3 + i * 0.25
            if t_elapsed >= target_time:
                star_char = "⭐" if i < self.stars else "☆"
                star_color = (255, 235, 59) if i < self.stars else (80, 80, 100)
                Label(star_char, size=38, color=star_color).draw(
                    surface, GameConfig.VIRTUAL_WIDTH / 2 - 50 + i * 50, 260
                )

        self.next_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 380)
        self.replay_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 440)
        self.select_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 500)


class DefeatOverlay:
    def __init__(self, scene, score, level_id):
        self.scene = scene
        self.score = score
        self.level_id = level_id

        # Audio check
        AudioManager.play_sfx('failure')

        self.retry_btn = Button("🔄 TRY AGAIN", w=180, h=46, bg_color=GameConfig.COLOR_FAILURE)
        self.select_btn = Button("📋 LEVEL SELECT", w=180, h=44)
        self.menu_btn = Button("🏠 MAIN MENU", w=180, h=44, bg_color=GameConfig.COLOR_BG_LIGHT)

    def handle_event(self, event):
        if self.retry_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 360):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 420):
            self.scene.manager.change_scene("LevelSelect")
        elif self.menu_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 480):
            self.scene.manager.change_scene("MainMenu")
        return True

    def draw(self, surface):
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 225))
        surface.blit(sc, (0, 0))

        Label("LEVEL FAILED", size=32, title=True, color=GameConfig.COLOR_FAILURE, shadow=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 160
        )
        Label(f"Score: {self.score}", size=18, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 220
        )
        Label("Don't give up! Try again!", size=14, color=(140, 140, 160)).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 255
        )

        self.retry_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 360)
        self.select_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 420)
        self.menu_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 480)
import time
