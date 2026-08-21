# game/scenes/main_menu.py - Stitch-accurate Main Menu with TopAppBar, Circular Hero Play Button, Bento Cards, and BottomNav Dock

import pygame
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import (draw_gradient_bg, draw_glass_panel, draw_currency_chip,
                                    draw_3d_button, create_ambient_bubbles, update_ambient_bubbles,
                                    draw_ambient_bubbles)
from game.audio.audio_manager import AudioManager
from game.storage.save_manager import SaveManager


class MainMenuScene(BaseScene):
    _has_checked_daily = False

    def __init__(self, manager):
        super().__init__(manager)

        # Profile / progress data
        self.profile = SaveManager.get_profile()
        self.unlocked_level = self.profile.get("unlocked_level", 1)
        self.coins = SaveManager.get_coins()
        _, self.high_score, stars_data = SaveManager.get_progress()
        self.total_stars = sum(stars_data.values()) if stars_data else 0

        # Ambient floating bubbles background
        self.bubbles = create_ambient_bubbles(10)
        self._bg_surface = None
        self.start_time = time.time()

        # Hero Circular Play button
        self.play_btn = Button("▶\nPLAY", w=160, h=160,
                               bg_color=GameConfig.COLOR_PRIMARY, hero=True, font_size=24)

        # Bento Quick Access Buttons
        self.daily_btn = Button("🎁\nDaily Rewards", w=150, h=74, font_size=12,
                                bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.achieve_btn = Button("🏆\nTrophy Road", w=150, h=74, font_size=12,
                                  bg_color=GameConfig.COLOR_SURFACE_HIGH)

        # Bottom Dock Icons
        self.map_nav_btn = Button("🗺️", w=54, h=48, font_size=18, bg_color=GameConfig.COLOR_PRIMARY)
        self.shop_nav_btn = Button("🛒", w=54, h=48, font_size=18, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.profile_nav_btn = Button("👤", w=54, h=48, font_size=18, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.stats_nav_btn = Button("📊", w=54, h=48, font_size=18, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.settings_nav_btn = Button("⚙️", w=54, h=48, font_size=18, bg_color=GameConfig.COLOR_SURFACE_HIGH)

        # Top profile header hit area
        self.profile_header_btn = Button("", w=160, h=44, bg_color=GameConfig.COLOR_BG)

        # Start soundtrack
        AudioManager.play_music('Goofy_Theme.ogg')

        # Check daily rewards once per game launch
        if not MainMenuScene._has_checked_daily:
            MainMenuScene._has_checked_daily = True
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            if SaveManager.get_last_claim_date() != today_str:
                self.manager.change_scene("DailyRewards")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

        cx = GameConfig.VIRTUAL_WIDTH / 2
        elapsed = time.time() - self.start_time
        float_y = 330 + math.sin(elapsed * 2.0) * 8

        # Top profile header click
        if self.profile_header_btn.handle_event(event, 90, 32):
            self.manager.change_scene("Profile")
            return

        # Hero Play button
        if self.play_btn.handle_event(event, cx, float_y):
            self.manager.change_scene("LevelSelect")
            return

        # Bento cards
        if self.daily_btn.handle_event(event, cx - 85, 485):
            self.manager.change_scene("DailyRewards")
            return
        elif self.achieve_btn.handle_event(event, cx + 85, 485):
            self.manager.change_scene("Achievements")
            return

        # Bottom Dock Icons
        dock_y = GameConfig.VIRTUAL_HEIGHT - 42
        if self.map_nav_btn.handle_event(event, cx - 140, dock_y):
            self.manager.change_scene("LevelSelect")
        elif self.shop_nav_btn.handle_event(event, cx - 70, dock_y):
            self.manager.change_scene("Shop")
        elif self.profile_nav_btn.handle_event(event, cx, dock_y):
            self.manager.change_scene("Profile")
        elif self.stats_nav_btn.handle_event(event, cx + 70, dock_y):
            self.manager.change_scene("Statistics")
        elif self.settings_nav_btn.handle_event(event, cx + 140, dock_y):
            self.manager.change_scene("Settings")

    def update(self, dt):
        update_ambient_bubbles(self.bubbles, dt)

    def draw(self, surface):
        # Gradient background (cached)
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(42, 27, 77),
                             bot_color=(15, 13, 23), radial=True)
        surface.blit(self._bg_surface, (0, 0))

        # Ambient floating bubbles
        draw_ambient_bubbles(surface, self.bubbles)

        cx = GameConfig.VIRTUAL_WIDTH / 2
        elapsed = time.time() - self.start_time

        # ─── 1. TOP APP BAR (Stitch header) ───
        topbar_h = int(64 * GameConfig.scale_y)
        topbar_rect = pygame.Rect(0, 0, GameConfig.actual_width, topbar_h)
        draw_glass_panel(surface, topbar_rect, opacity=180, radius=0)

        # Left: Avatar + Title + Level
        Label("👤", size=24).draw(surface, 28, 30)
        Label("Bubble Quest", size=15, title=True, align="left",
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, 52, 22, originX=0)
        Label(f"Lvl {self.unlocked_level}", size=11, color=GameConfig.COLOR_GOLD, align="left").draw(
            surface, 52, 42, originX=0
        )

        # Right: Currency Chips
        draw_currency_chip(surface, GameConfig.VIRTUAL_WIDTH - 145, 32, "🪙", self.coins)
        draw_currency_chip(surface, GameConfig.VIRTUAL_WIDTH - 48, 32, "⭐", self.total_stars)

        # ─── 2. CENTER HERO PLAY BUTTON (Floating Circular 3D Button) ───
        float_offset = math.sin(elapsed * 2.0) * 8
        hero_cy = 310 + float_offset

        # Pulsing outer glow aura
        pulse = 0.5 + 0.5 * math.sin(elapsed * 3.0)
        aura_rad = int((85 + 15 * pulse) * min(GameConfig.scale_x, GameConfig.scale_y))
        aura_sx = GameConfig.to_screen_x(cx)
        aura_sy = GameConfig.to_screen_y(hero_cy)
        aura_surf = pygame.Surface((aura_rad * 2, aura_rad * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (*GameConfig.COLOR_PRIMARY_LIGHT[:3], int(25 + 30 * pulse)),
                           (aura_rad, aura_rad), aura_rad)
        surface.blit(aura_surf, (aura_sx - aura_rad, aura_sy - aura_rad))

        # Circular Hero Play Button
        btn_rad = int(72 * min(GameConfig.scale_x, GameConfig.scale_y))
        hero_btn_rect = pygame.Rect(aura_sx - btn_rad, aura_sy - btn_rad, btn_rad * 2, btn_rad * 2)
        draw_3d_button(surface, hero_btn_rect, GameConfig.COLOR_PRIMARY, glow=True, radius=btn_rad)

        # Big Play Arrow Icon & Text inside hero button
        Label("▶", size=36, color=(255, 255, 255), title=True).draw(surface, cx, hero_cy - 12)
        Label("PLAY", size=18, color=(255, 255, 255), title=True, glow=True).draw(surface, cx, hero_cy + 24)

        # ─── 3. BENTO QUICK ACCESS CARDS ───
        bento_y = 485
        self.daily_btn.draw(surface, cx - 85, bento_y)
        self.achieve_btn.draw(surface, cx + 85, bento_y)

        # High score watermark
        Label(f"BEST SCORE: {self.high_score}", size=11,
              color=GameConfig.COLOR_TEXT_MUTED).draw(surface, cx, 555)

        # ─── 4. BOTTOM NAVIGATION DOCK (Frosted Glass) ───
        dock_h = int(76 * GameConfig.scale_y)
        dock_rect = pygame.Rect(0, GameConfig.actual_height - dock_h, GameConfig.actual_width, dock_h)
        draw_glass_panel(surface, dock_rect, opacity=200, radius=int(24 * min(GameConfig.scale_x, GameConfig.scale_y)))

        dock_y = GameConfig.VIRTUAL_HEIGHT - 42
        self.map_nav_btn.draw(surface, cx - 140, dock_y)
        self.shop_nav_btn.draw(surface, cx - 70, dock_y)
        self.profile_nav_btn.draw(surface, cx, dock_y)
        self.stats_nav_btn.draw(surface, cx + 70, dock_y)
        self.settings_nav_btn.draw(surface, cx + 140, dock_y)
