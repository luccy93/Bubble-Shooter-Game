# game/scenes/overlays.py - Premium Pause, Victory, and Defeat screen overlays with glassmorphism

import pygame
import math
import time
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_glass_panel, draw_stars
from game.audio.audio_manager import AudioManager
from game.effects.particles import ParticleSystem


class PauseOverlay:
    def __init__(self, scene):
        self.scene = scene
        self.resume_btn = Button("▶  RESUME", w=220, h=48, bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        self.restart_btn = Button("🔄  RESTART", w=220, h=44, bg_color=GameConfig.COLOR_PRIMARY)
        self.select_btn = Button("🗺️  LEVEL SELECT", w=220, h=44, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.menu_btn = Button("🏠  MAIN MENU", w=220, h=44, bg_color=GameConfig.COLOR_SURFACE_HIGH)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.scene.show_pause = False
                return True

        cx = GameConfig.VIRTUAL_WIDTH / 2
        if self.resume_btn.handle_event(event, cx, 300):
            self.scene.show_pause = False
        elif self.restart_btn.handle_event(event, cx, 365):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, cx, 430):
            self.scene.manager.change_scene("LevelSelect")
        elif self.menu_btn.handle_event(event, cx, 495):
            self.scene.manager.change_scene("MainMenu")
        return True

    def draw(self, surface):
        # Dark overlay
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 210))
        surface.blit(sc, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Glass dialog panel
        panel_w = int(300 * GameConfig.scale_x)
        panel_h = int(350 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(150)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=140, radius=int(24 * min(GameConfig.scale_x, GameConfig.scale_y)),
                         glow=True)

        # Title
        Label("⏸️  PAUSED", size=30, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 200)

        # Buttons
        self.resume_btn.draw(surface, cx, 300)
        self.restart_btn.draw(surface, cx, 365)
        self.select_btn.draw(surface, cx, 430)
        self.menu_btn.draw(surface, cx, 495)


class VictoryOverlay:
    def __init__(self, scene, score, stars, level_id):
        self.scene = scene
        self.score = score
        self.stars = stars
        self.level_id = level_id
        self.start_time = time.time()

        AudioManager.play_sfx('victory')
        ParticleSystem.create_confetti(count=35)

        # Calculate coins earned (10 per star + score bonus)
        self.coins_earned = stars * 10 + score // 100

        self.next_btn = Button("▶  NEXT LEVEL", w=220, h=50,
                               bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        self.replay_btn = Button("🔄  REPLAY", w=220, h=44,
                                 bg_color=GameConfig.COLOR_PRIMARY)
        self.select_btn = Button("🗺️  MAP", w=220, h=44,
                                 bg_color=GameConfig.COLOR_SURFACE_HIGH)

    def handle_event(self, event):
        cx = GameConfig.VIRTUAL_WIDTH / 2
        if self.next_btn.handle_event(event, cx, 430):
            next_lvl = min(self.level_id + 1, 3000)
            self.scene.manager.change_scene("Gameplay", level_id=next_lvl)
        elif self.replay_btn.handle_event(event, cx, 495):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, cx, 560):
            next_lvl = min(self.level_id + 1, 3000)
            self.scene.manager.change_scene("LevelSelect", newly_unlocked=next_lvl)
        return True

    def draw(self, surface):
        # Dark overlay
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 230))
        surface.blit(sc, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Glass dialog panel
        panel_w = int(320 * GameConfig.scale_x)
        panel_h = int(420 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(100)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=150, radius=int(24 * min(GameConfig.scale_x, GameConfig.scale_y)),
                         glow=True)

        # "LEVEL COMPLETE!" with gradient glow
        Label("✨ LEVEL COMPLETE! ✨", size=26, title=True,
              color=GameConfig.COLOR_SUCCESS, glow=True).draw(surface, cx, 150)

        # Score display
        Label(f"Score: {self.score}", size=22, title=True,
              color=GameConfig.COLOR_GOLD).draw(surface, cx, 210)

        # Coins earned badge
        Label(f"🪙 +{self.coins_earned} coins", size=15,
              color=GameConfig.COLOR_SECONDARY_CONTAINER).draw(surface, cx, 250)

        # Stars with staggered animation
        draw_stars(surface, cx, 310, self.stars, total=3, size=22,
                   animated=True, start_time=self.start_time)

        # Confetti particles
        ParticleSystem.draw(surface)

        # Buttons
        self.next_btn.draw(surface, cx, 430)
        self.replay_btn.draw(surface, cx, 495)
        self.select_btn.draw(surface, cx, 560)


class DefeatOverlay:
    def __init__(self, scene, score, level_id):
        self.scene = scene
        self.score = score
        self.level_id = level_id

        AudioManager.play_sfx('failure')

        self.retry_btn = Button("🔄  TRY AGAIN", w=220, h=50,
                                bg_color=GameConfig.COLOR_FAILURE, hero=True)
        self.select_btn = Button("🗺️  MAP", w=220, h=44,
                                 bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.menu_btn = Button("🏠  MAIN MENU", w=220, h=44,
                               bg_color=GameConfig.COLOR_SURFACE_HIGH)

    def handle_event(self, event):
        cx = GameConfig.VIRTUAL_WIDTH / 2
        if self.retry_btn.handle_event(event, cx, 380):
            self.scene.restart_level()
        elif self.select_btn.handle_event(event, cx, 445):
            self.scene.manager.change_scene("LevelSelect")
        elif self.menu_btn.handle_event(event, cx, 510):
            self.scene.manager.change_scene("MainMenu")
        return True

    def draw(self, surface):
        # Dark overlay
        sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        sc.fill((10, 8, 20, 230))
        surface.blit(sc, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Glass dialog panel
        panel_w = int(300 * GameConfig.scale_x)
        panel_h = int(350 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(120)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=150, radius=int(24 * min(GameConfig.scale_x, GameConfig.scale_y)),
                         border_color=GameConfig.COLOR_FAILURE)

        # Title with red glow
        Label("LEVEL FAILED", size=30, title=True,
              color=GameConfig.COLOR_FAILURE, glow=True).draw(surface, cx, 180)

        Label(f"Score: {self.score}", size=18,
              color=GameConfig.COLOR_TEXT_MUTED).draw(surface, cx, 240)
        Label("Don't give up! Try again!", size=14,
              color=GameConfig.COLOR_OUTLINE).draw(surface, cx, 280)

        # Buttons
        self.retry_btn.draw(surface, cx, 380)
        self.select_btn.draw(surface, cx, 445)
        self.menu_btn.draw(surface, cx, 510)
