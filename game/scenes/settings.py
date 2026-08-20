# game/scenes/settings.py - Settings options screen with Reset Progress confirmations

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager

class SettingsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.settings = SaveManager.get_settings()
        self.show_confirm = False

        # Controls UI elements
        self._update_buttons()
        self.reset_btn = Button("⚠️ RESET PROGRESS", w=220, h=44, bg_color=GameConfig.COLOR_FAILURE)
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)

        # Confirmation panel buttons
        self.yes_btn = Button("RESET", w=100, h=40, bg_color=GameConfig.COLOR_FAILURE)
        self.no_btn = Button("CANCEL", w=100, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)

    def _update_buttons(self):
        music_lbl = f"MUSIC: {'ON' if self.settings['music'] else 'OFF'}"
        sfx_lbl = f"SFX: {'ON' if self.settings['sfx'] else 'OFF'}"
        vib_lbl = f"VIBRATION: {'ON' if self.settings['vibration'] else 'OFF'}"

        self.music_btn = Button(music_lbl, w=220, h=48, bg_color=GameConfig.COLOR_ACCENT)
        self.sfx_btn = Button(sfx_lbl, w=220, h=48, bg_color=GameConfig.COLOR_ACCENT)
        self.vib_btn = Button(vib_lbl, w=220, h=48, bg_color=GameConfig.COLOR_ACCENT)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                if self.show_confirm:
                    self.show_confirm = False
                else:
                    self.manager.change_scene("MainMenu")
                return

        if self.show_confirm:
            if self.yes_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 60, 420):
                SaveManager.reset_progress()
                self.settings = SaveManager.get_settings()
                self._update_buttons()
                self.show_confirm = False
            elif self.no_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 60, 420):
                self.show_confirm = False
            return

        # Main options interactions
        if self.music_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 180):
            self.settings["music"] = not self.settings["music"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
            AudioManager.update_settings()
            self._update_buttons()
            if self.settings["music"]:
                AudioManager.play_music('Goofy_Theme.ogg')
        elif self.sfx_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 240):
            self.settings["sfx"] = not self.settings["sfx"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
            self._update_buttons()
        elif self.vib_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 300):
            self.settings["vibration"] = not self.settings["vibration"]
            SaveManager.save_settings(self.settings["music"], self.settings["sfx"], self.settings["vibration"])
            self._update_buttons()
        elif self.reset_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 380):
            self.show_confirm = True
        elif self.back_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)
        Label("SETTINGS", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 60)

        # Draw buttons
        self.music_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 180)
        self.sfx_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 240)
        self.vib_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 300)
        self.reset_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 380)

        # Draw details info
        Label("Bubble Shooter Mobile v2.0.0", size=14, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 480
        )
        Label("Built using Pygame-CE & Python", size=12, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 505
        )

        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)

        # Modal dialog layout for confirmation
        if self.show_confirm:
            # Semi-transparent overlay surface
            sc = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
            sc.fill((10, 8, 20, 220))
            surface.blit(sc, (0, 0))

            # Dialog card bounds
            dc_w = int(280 * GameConfig.scale_x)
            dc_h = int(180 * GameConfig.scale_y)
            dc_x = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2) - dc_w // 2
            dc_y = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT / 2) - dc_h // 2
            pygame.draw.rect(surface, GameConfig.COLOR_BG, (dc_x, dc_y, dc_w, dc_h), border_radius=15)
            pygame.draw.rect(surface, GameConfig.COLOR_FAILURE, (dc_x, dc_y, dc_w, dc_h), width=2, border_radius=15)

            Label("RESET ALL PROGRESS?", size=18, color=GameConfig.COLOR_FAILURE, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 - 40
            )
            Label("This cannot be undone!", size=13, color=GameConfig.COLOR_TEXT_MUTED).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 - 10
            )
            self.yes_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35)
            self.no_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 60, GameConfig.VIRTUAL_HEIGHT / 2 + 35)
