# game/scenes/level_start_popup.py - Level Start Modal Popup Scene

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import draw_gradient_bg, draw_glass_panel, draw_stars
from game.levels.level_manager import LevelManager
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager

class LevelStartPopupScene(BaseScene):
    def __init__(self, manager, level_id=1):
        super().__init__(manager)
        self.level_id = level_id
        
        # Get level data
        self.level_data = LevelManager.get_level(level_id)
        self.moves = self.level_data.get("moves", 25)
        self.objective = self.level_data.get("objective", {"type": "clear_board"})
        self.target_scores = self.level_data.get("target_scores", [1000, 2500, 5000])

        # Get saved progress on this level
        save_data = SaveManager.load_game()
        stars_dict = save_data.get("stars", {})
        self.earned_stars = stars_dict.get(str(level_id), 0)

        # Objective description
        obj_type = self.objective.get("type", "clear_board")
        if obj_type == "clear_board":
            self.obj_desc = "Pop all bubbles to clear the board"
            self.obj_icon = "🫧"
        elif obj_type == "collect_color":
            color_name = self.objective.get("color", "red").capitalize()
            count = self.objective.get("count", 15)
            self.obj_desc = f"Collect {count} {color_name} bubbles"
            self.obj_icon = "🎯"
        elif obj_type == "rescue_pets":
            count = self.objective.get("count", 3)
            self.obj_desc = f"Rescue {count} trapped pets"
            self.obj_icon = "🐱"
        else:
            self.obj_desc = "Complete the level target"
            self.obj_icon = "⭐"

        # Buttons
        self.play_btn = Button("▶ START LEVEL", w=220, h=52, bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        self.close_btn = Button("✕", w=40, h=40, bg_color=GameConfig.COLOR_SURFACE_HIGH, font_size=16)
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("LevelSelect")
                return

        cx = GameConfig.VIRTUAL_WIDTH / 2
        if self.play_btn.handle_event(event, cx, 520):
            AudioManager.play_sfx('button')
            self.manager.change_scene("Gameplay", level_id=self.level_id)
        elif self.close_btn.handle_event(event, cx + 140, 190):
            self.manager.change_scene("LevelSelect")

    def update(self, dt):
        pass

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(25, 18, 50), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        # Semi-transparent dark backdrop
        dark_overlay = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
        dark_overlay.fill((10, 8, 20, 160))
        surface.blit(dark_overlay, (0, 0))

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Main Popup Card
        card_w = int(340 * GameConfig.scale_x)
        card_h = int(420 * GameConfig.scale_y)
        card_x = GameConfig.to_screen_x(cx) - card_w // 2
        card_y = GameConfig.to_screen_y(170)
        draw_glass_panel(surface, pygame.Rect(card_x, card_y, card_w, card_h),
                         opacity=160, radius=20, border_color=GameConfig.COLOR_PRIMARY, glow=True)

        # Close button
        self.close_btn.draw(surface, cx + 130, 200)

        # Title
        Label(f"LEVEL {self.level_id}", size=28, title=True, glow=True,
              color=GameConfig.COLOR_GOLD).draw(surface, cx, 220)

        # Earned Stars display
        draw_stars(surface, cx, 265, self.earned_stars, total=3, size=18)

        # Objective box
        obj_box_w = int(290 * GameConfig.scale_x)
        obj_box_h = int(72 * GameConfig.scale_y)
        obj_box_x = GameConfig.to_screen_x(cx) - obj_box_w // 2
        obj_box_y = GameConfig.to_screen_y(305)
        draw_glass_panel(surface, pygame.Rect(obj_box_x, obj_box_y, obj_box_w, obj_box_h),
                         opacity=80, radius=12)

        Label(f"{self.obj_icon} OBJECTIVE", size=13, color=GameConfig.COLOR_PRIMARY_LIGHT, title=True).draw(
            surface, cx, 325
        )
        Label(self.obj_desc, size=12, color=GameConfig.COLOR_TEXT).draw(
            surface, cx, 355
        )

        # Stats summary (Moves available)
        moves_chip_w = int(180 * GameConfig.scale_x)
        moves_chip_h = int(38 * GameConfig.scale_y)
        moves_chip_x = GameConfig.to_screen_x(cx) - moves_chip_w // 2
        moves_chip_y = GameConfig.to_screen_y(400)
        draw_glass_panel(surface, pygame.Rect(moves_chip_x, moves_chip_y, moves_chip_w, moves_chip_h),
                         opacity=90, radius=19)

        Label(f"🎯 {self.moves} Moves Available", size=13, color=GameConfig.COLOR_GOLD, title=True).draw(
            surface, cx, 420
        )

        # Play Button
        self.play_btn.draw(surface, cx, 510)
