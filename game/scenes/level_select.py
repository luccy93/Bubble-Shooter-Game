# game/scenes/level_select.py - Adventure Level Road Map with scrolling, locks, stars, and animated arrows

import pygame
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.levels.level_manager import LevelManager
from game.storage.save_manager import SaveManager
from game.effects.particles import ParticleSystem

class LevelSelectScene(BaseScene):
    def __init__(self, manager, newly_unlocked=None):
        super().__init__(manager)
        
        # Load profile progress
        self.unlocked_level, _, self.stars_data = SaveManager.get_progress()
        self.newly_unlocked = newly_unlocked  # Level ID to run unlock animations for

        # Define path coordinates for levels 1 to 15 (winding adventure road)
        self.path_points = []
        for i in range(15):
            # i runs from 0 (Level 1) to 14 (Level 15)
            # Center X oscillates with sine wave to create a winding road
            vx = GameConfig.VIRTUAL_WIDTH / 2 + math.sin(i * 1.5) * 80
            # Y coordinate places Level 1 at the bottom and climbs upwards
            vy = GameConfig.VIRTUAL_HEIGHT - 160 - (i * 120)
            self.path_points.append((vx, vy))

        # Camera scroll targeting
        # Determine current world and local level index
        if newly_unlocked:
            self.world_id = min((newly_unlocked - 1) // 15, 7)
            target_idx = min((newly_unlocked - 1) % 15, 14)
        else:
            self.world_id = min((self.unlocked_level - 1) // 15, 7)
            target_idx = min((self.unlocked_level - 1) % 15, 14)

        active_y = self.path_points[target_idx][1]
        self.scroll_y = active_y - GameConfig.VIRTUAL_HEIGHT / 2

        self.min_scroll = self.path_points[-1][1] - 150
        self.max_scroll = GameConfig.VIRTUAL_HEIGHT - 250
        self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll))

        # UI elements
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.prev_world_btn = Button("◀", w=36, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.next_world_btn = Button("▶", w=36, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)

        # Unlock animation timer
        self.unlock_scale = 1.0
        self.unlock_time = time.time()
        self.spawned_particles = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        # Back button action
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("MainMenu")
            return

        # World selection actions
        if self.prev_world_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 130, 42):
            if self.world_id > 0:
                self.world_id -= 1
                AudioManager.play_sfx('button')
                self.scroll_y = self.path_points[0][1] - GameConfig.VIRTUAL_HEIGHT / 2
                self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll))
            return

        max_unlocked_world = min((self.unlocked_level - 1) // 15, 7)
        if self.next_world_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 130, 42):
            if self.world_id < max_unlocked_world:
                self.world_id += 1
                AudioManager.play_sfx('button')
                self.scroll_y = self.path_points[0][1] - GameConfig.VIRTUAL_HEIGHT / 2
                self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll))
            return

        # Level node hit targets checks
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos
            vmx = mx / GameConfig.scale_x
            vmy = my / GameConfig.scale_y

            # Adjust vertical mouse click with scroll offset
            adjusted_vmy = vmy + self.scroll_y

            for idx, (px, py) in enumerate(self.path_points):
                lvl_id = self.world_id * 15 + idx + 1
                dist = math.hypot(vmx - px, adjusted_vmy - py)
                # Level node radius target is 30px
                if dist <= 32:
                    if lvl_id <= self.unlocked_level:
                        pygame.mixer.Sound(GameConfig.get_asset_path('audio', 'button.ogg')).play()
                        self.manager.change_scene("Gameplay", level_id=lvl_id)
                        return

        # Simple drag to scroll
        elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            _, dy = event.rel
            # Adjust scroll speed
            self.scroll_y -= dy / GameConfig.scale_y
            
            # Clamp boundaries
            self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll))

    def update(self, dt):
        ParticleSystem.update()

        # Handle unlock animations trigger
        if self.newly_unlocked:
            t = time.time() - self.unlock_time
            if t < 1.0:
                # Oscillate scaling factor
                self.unlock_scale = 1.0 + math.sin(t * math.pi * 3) * 0.25
                if not self.spawned_particles and t > 0.1:
                    self.spawned_particles = True
                    target_pt = self.path_points[self.newly_unlocked - 1]
                    ParticleSystem.create_confetti(count=20)
            else:
                self.unlock_scale = 1.0
                self.newly_unlocked = None

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Create virtual canvas sub-surface for scrolling elements
        # Map goes from level 15 (top coordinate) to level 1 (bottom coordinate)
        virtual_h = int(1900 * GameConfig.scale_y)
        scroll_surf = pygame.Surface((GameConfig.actual_width, virtual_h), pygame.SRCALPHA)

        # Draw connecting road path (dotted line segments)
        for i in range(14):
            p1 = self.path_points[i]
            p2 = self.path_points[i + 1]
            
            sp1 = (GameConfig.to_screen_x(p1[0]), GameConfig.to_screen_y(p1[1] - self.scroll_y))
            sp2 = (GameConfig.to_screen_x(p2[0]), GameConfig.to_screen_y(p2[1] - self.scroll_y))
            
            # Draw primary road pipeline
            pygame.draw.line(scroll_surf, (60, 50, 95), sp1, sp2, width=int(12 * GameConfig.scale_x))
            pygame.draw.line(scroll_surf, (110, 76, 255), sp1, sp2, width=int(4 * GameConfig.scale_x))

        # Draw Level nodes
        for idx, (px, py) in enumerate(self.path_points):
            lvl_id = self.world_id * 15 + idx + 1
            is_locked = lvl_id > self.unlocked_level
            is_new = (lvl_id == self.newly_unlocked)
            
            # Map node coordinates
            sx = GameConfig.to_screen_x(px)
            sy = GameConfig.to_screen_y(py - self.scroll_y)

            # Node size (base radius 28)
            node_scale = self.unlock_scale if is_new else 1.0
            srad = int(28 * node_scale * min(GameConfig.scale_x, GameConfig.scale_y))
            if srad <= 0:
                continue

            # 1. Glow highlight outer ring if unlocked next level node
            if lvl_id == self.unlocked_level:
                glow_val = int(128 + math.sin(time.time() * 6) * 127)
                pygame.draw.circle(scroll_surf, (110, 76, 255, glow_val), (sx, sy), srad + int(6 * GameConfig.scale_x))

            # 2. Main Circle Body
            if is_locked:
                bg_color = (40, 35, 60)
                stroke_color = (65, 55, 90)
            elif lvl_id == self.unlocked_level:
                bg_color = GameConfig.COLOR_PRIMARY
                stroke_color = (255, 255, 255)
            else:
                bg_color = GameConfig.COLOR_SUCCESS
                stroke_color = (255, 255, 255)

            pygame.draw.circle(scroll_surf, bg_color, (sx, sy), srad)
            pygame.draw.circle(scroll_surf, stroke_color, (sx, sy), srad, width=2)

            # 3. Label identifiers
            if is_locked:
                # Lock symbol
                font = pygame.font.SysFont(None, int(srad * 1.1))
                text = font.render("L", True, (100, 100, 130))
                scroll_surf.blit(text, text.get_rect(center=(sx, sy)))
            else:
                # Level number
                font = pygame.font.SysFont(None, int(srad * 1.1), bold=True)
                text = font.render(str(lvl_id), True, (255, 255, 255))
                scroll_surf.blit(text, text.get_rect(center=(sx, sy)))

                # Draw stars characters under completed levels
                stars = self.stars_data.get(str(lvl_id), 0)
                if stars > 0:
                    star_lbl = Label("★" * stars, size=11, color=(255, 235, 59))
                    # Render below node
                    star_lbl.draw(scroll_surf, px, py - self.scroll_y + 38)

            # 4. Animated Hover Pointer Arrow pointing down at the active level node
            if lvl_id == self.unlocked_level and not is_new:
                bounce = math.sin(time.time() * 8) * 8
                arrow_y = py - self.scroll_y - 48 + bounce
                # Draw small triangle indicator pointing down
                ax = GameConfig.to_screen_x(px)
                ay = GameConfig.to_screen_y(arrow_y)
                aw = int(14 * GameConfig.scale_x)
                ah = int(16 * GameConfig.scale_y)
                pygame.draw.polygon(scroll_surf, GameConfig.COLOR_PRIMARY, [
                    (ax, ay + ah),
                    (ax - aw, ay),
                    (ax + aw, ay)
                ])
                pygame.draw.polygon(scroll_surf, (255, 255, 255), [
                    (ax, ay + ah),
                    (ax - aw, ay),
                    (ax + aw, ay)
                ], width=1)

        # Blit scroll surface onto main screen
        surface.blit(scroll_surf, (0, 0))

        # Render particles effects
        ParticleSystem.draw(surface)

        # Header HUD card (Non-scrolling overlays)
        hud_bar = pygame.Rect(0, 0, GameConfig.actual_width, int(68 * GameConfig.scale_y))
        pygame.draw.rect(surface, (10, 8, 20, 180), hud_bar)
        
        # World name label
        world_info = LevelManager.get_world(self.world_id)
        world_title = f"{world_info['icon']} {world_info['name']}"
        Label(world_title, size=17, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 42)

        # Draw world navigation buttons next to it
        if self.world_id > 0:
            self.prev_world_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 130, 42)
        
        max_unlocked_world = min((self.unlocked_level - 1) // 15, 7)
        if self.world_id < max_unlocked_world:
            self.next_world_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 130, 42)

        # Back Button
        self.back_btn.draw(surface, 80, 50)
