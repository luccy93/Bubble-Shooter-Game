# game/scenes/level_select.py - Level select screen with worlds tabs and locks

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.levels.level_manager import LevelManager
from game.storage.save_manager import SaveManager

class LevelSelectScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Load progress details
        self.unlocked_level, _, self.stars_data = SaveManager.get_progress()
        self.current_world_id = 0

        # Load levels definitions
        LevelManager.load_levels()

        # UI elements
        self.back_btn = Button("← BACK", w=140, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.prev_world_btn = Button("◀", w=50, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.next_world_btn = Button("▶", w=50, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Handle back button
        if self.back_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60):
            self.manager.change_scene("MainMenu")
            return

        # Handle world navigation
        if self.prev_world_btn.handle_event(event, 60, 120):
            self.current_world_id = max(0, self.current_world_id - 1)
            return
        if self.next_world_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH - 60, 120):
            self.current_world_id = min(len(LevelManager.get_worlds()) - 1, self.current_world_id + 1)
            return

        # Handle level selection cards
        levels = LevelManager.get_levels_for_world(self.current_world_id)
        for i, lvl in enumerate(levels):
            # Define card bounding box
            cx = GameConfig.VIRTUAL_WIDTH / 2
            cy = 230 + i * 85
            card_rect = pygame.Rect(cx - 160, cy - 35, 320, 70)
            
            # Enforce touch bounds
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mx, my = event.pos
                vmx = mx / GameConfig.scale_x
                vmy = my / GameConfig.scale_y
                if card_rect.collidepoint(vmx, vmy):
                    # Check lock state
                    if lvl["id"] <= self.unlocked_level:
                        pygame.mixer.Sound(GameConfig.get_asset_path('audio', 'button.ogg')).play()
                        self.manager.change_scene("Gameplay", level_id=lvl["id"])
                    else:
                        # Vibrate or play fail sound if locked
                        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Active world metadata
        world = LevelManager.get_world(self.current_world_id)
        Label("SELECT LEVEL", size=24, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 50)
        
        # World Switcher Bar
        Label(f"{world['icon']} {world['name']}", size=20, title=True, color=GameConfig.COLOR_PRIMARY).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 120
        )
        self.prev_world_btn.draw(surface, 60, 120)
        self.next_world_btn.draw(surface, GameConfig.VIRTUAL_WIDTH - 60, 120)

        # Draw Level Card lists
        levels = LevelManager.get_levels_for_world(self.current_world_id)
        for i, lvl in enumerate(levels):
            lvl_id = lvl["id"]
            is_locked = lvl_id > self.unlocked_level
            
            cx = GameConfig.VIRTUAL_WIDTH / 2
            cy = 230 + i * 85

            # Card background Rect
            scx = GameConfig.to_screen_x(cx)
            scy = GameConfig.to_screen_y(cy)
            sw = int(320 * GameConfig.scale_x)
            sh = int(70 * GameConfig.scale_y)
            card_rect = pygame.Rect(scx - sw // 2, scy - sh // 2, sw, sh)

            # Draw card rounded rect
            bg_color = GameConfig.COLOR_BG_LIGHT if not is_locked else (24, 20, 36)
            pygame.draw.rect(surface, bg_color, card_rect, border_radius=sw // 24)
            
            # Stroke highlight
            stroke_color = GameConfig.COLOR_ACCENT if not is_locked else (50, 45, 70)
            pygame.draw.rect(surface, stroke_color, card_rect, width=1, border_radius=sw // 24)

            # Render info
            if is_locked:
                Label(f"Level {lvl_id}", size=18, color=(100, 100, 130)).draw(surface, cx - 80, cy)
                Label("🔒", size=22).draw(surface, cx + 100, cy)
            else:
                Label(f"Level {lvl_id}", size=20, title=True).draw(surface, cx - 80, cy)
                # Stars rating characters (e.g. ⭐⭐⭐ or ⭐☆☆)
                stars = self.stars_data.get(str(lvl_id), 0)
                stars_str = "⭐" * stars + "☆" * (3 - stars)
                Label(stars_str, size=16, color=(255, 235, 59)).draw(surface, cx + 80, cy)

        # Back Action button
        self.back_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60)
