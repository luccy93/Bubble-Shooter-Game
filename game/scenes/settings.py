# game/scenes/settings.py - Settings with glassmorphism cards and toggle switches

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel, draw_toggle_switch
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager


class SettingsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)

        self.settings = SaveManager.get_settings()
        self.show_confirm = False

        self.reset_btn = Button("⚠️ RESET PROGRESS", w=220, h=44,
                                bg_color=GameConfig.COLOR_FAILURE)
        self.back_btn = Button("← BACK", w=140, h=40,
                               bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.yes_btn = Button("RESET", w=100, h=40, bg_color=GameConfig.COLOR_FAILURE)
        self.no_btn = Button("CANCEL", w=100, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH)

        # Toggle button hit areas (invisible buttons covering toggle row)
        self.music_toggle_btn = Button("", w=350, h=48, bg_color=GameConfig.COLOR_BG)
        self.sfx_toggle_btn = Button("", w=350, h=48, bg_color=GameConfig.COLOR_BG)
        self.vib_toggle_btn = Button("", w=350, h=48, bg_color=GameConfig.COLOR_BG)

        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                if self.show_confirm:
                    self.show_confirm = False
                else:
                    self.manager.change_scene("MainMenu")
                return

        cx = GameConfig.VIRTUAL_WIDTH / 2

        if self.show_confirm:
            if self.yes_btn.handle_event(event, cx - 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35):
                SaveManager.reset_progress()
                self.settings = SaveManager.get_settings()
                self.show_confirm = False
            elif self.no_btn.handle_event(event, cx + 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35):
                self.show_confirm = False
            return

        if self.music_toggle_btn.handle_event(event, cx, 190):
            self.settings["music"] = not self.settings["music"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
            AudioManager.update_settings()
            if self.settings["music"]:
                AudioManager.play_music('Goofy_Theme.ogg')
        elif self.sfx_toggle_btn.handle_event(event, cx, 255):
            self.settings["sfx"] = not self.settings["sfx"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
        elif self.vib_toggle_btn.handle_event(event, cx, 320):
            self.settings["vibration"] = not self.settings["vibration"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
        elif self.reset_btn.handle_event(event, cx, 400):
            self.show_confirm = True
        elif self.back_btn.handle_event(event, cx, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(35, 22, 65), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2
        Label("SETTINGS", size=24, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 60)

        # Toggle rows with glass cards
        toggles = [
            ("🎵  Music", self.settings["music"], 190),
            ("🔊  Sound Effects", self.settings["sfx"], 255),
            ("📳  Vibration", self.settings["vibration"], 320),
        ]

        for label_text, is_on, cy in toggles:
            row_w = int(350 * GameConfig.scale_x)
            row_h = int(48 * GameConfig.scale_y)
            row_x = GameConfig.to_screen_x(cx) - row_w // 2
            row_y = GameConfig.to_screen_y(cy) - row_h // 2
            draw_glass_panel(surface, pygame.Rect(row_x, row_y, row_w, row_h),
                             opacity=70, radius=12)

            Label(label_text, size=15, color=GameConfig.COLOR_TEXT, align="left").draw(
                surface, cx - 140, cy, originX=0)
            draw_toggle_switch(surface, cx + 130, cy, is_on)

        # Reset button
        self.reset_btn.draw(surface, cx, 400)

        # App info
        Label("Bubble Quest v2.0.0", size=14,
              color=GameConfig.COLOR_TEXT_MUTED).draw(surface, cx, 490)
        Label("Built with Pygame-CE & Python", size=12,
              color=GameConfig.COLOR_OUTLINE).draw(surface, cx, 515)

        self.back_btn.draw(surface, cx, GameConfig.VIRTUAL_HEIGHT - 60)

        # Confirmation dialog
        if self.show_confirm:
            overlay = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
            overlay.fill((10, 8, 20, 220))
            surface.blit(overlay, (0, 0))

            dc_w = int(280 * GameConfig.scale_x)
            dc_h = int(180 * GameConfig.scale_y)
            dc_x = GameConfig.to_screen_x(cx) - dc_w // 2
            dc_y = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT / 2) - dc_h // 2
            draw_glass_panel(surface, pygame.Rect(dc_x, dc_y, dc_w, dc_h),
                             opacity=200, radius=15, border_color=GameConfig.COLOR_FAILURE)

            Label("RESET ALL PROGRESS?", size=18, color=GameConfig.COLOR_FAILURE, title=True).draw(
                surface, cx, GameConfig.VIRTUAL_HEIGHT / 2 - 40)
            Label("This cannot be undone!", size=13, color=GameConfig.COLOR_TEXT_MUTED).draw(
                surface, cx, GameConfig.VIRTUAL_HEIGHT / 2 - 10)
            self.yes_btn.draw(surface, cx - 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35)
            self.no_btn.draw(surface, cx + 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35)
