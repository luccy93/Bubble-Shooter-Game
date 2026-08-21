# game/scenes/level_select.py - Adventure World Map with glowing nodes, Stitch glass HUD, and road pipeline

import pygame
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import (draw_gradient_bg, draw_glass_panel, draw_stars,
                                    create_ambient_bubbles, update_ambient_bubbles,
                                    draw_ambient_bubbles)
from game.levels.level_manager import LevelManager
from game.storage.save_manager import SaveManager
from game.effects.particles import ParticleSystem
from game.audio.audio_manager import AudioManager


class LevelSelectScene(BaseScene):
    def __init__(self, manager, newly_unlocked=None):
        super().__init__(manager)

        # Load profile progress
        self.unlocked_level, _, self.stars_data = SaveManager.get_progress()
        self.newly_unlocked = newly_unlocked

        # Define path coordinates for levels 1 to 15 (winding adventure road)
        self.path_points = []
        for i in range(15):
            vx = GameConfig.VIRTUAL_WIDTH / 2 + math.sin(i * 1.5) * 80
            vy = GameConfig.VIRTUAL_HEIGHT - 160 - (i * 120)
            self.path_points.append((vx, vy))

        # Camera scroll targeting
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
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.prev_world_btn = Button("◀", w=36, h=36, bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.next_world_btn = Button("▶", w=36, h=36, bg_color=GameConfig.COLOR_SURFACE_HIGH)

        # Unlock animation timer
        self.unlock_scale = 1.0
        self.unlock_time = time.time()
        self.spawned_particles = False

        # Ambient bubbles for background
        self.bubbles = create_ambient_bubbles(6)
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("MainMenu")
                return

        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("MainMenu")
            return

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

        # Level node hit targets
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos
            vmx = mx / GameConfig.scale_x
            vmy = my / GameConfig.scale_y
            adjusted_vmy = vmy + self.scroll_y

            for idx, (px, py) in enumerate(self.path_points):
                lvl_id = self.world_id * 15 + idx + 1
                dist = math.hypot(vmx - px, adjusted_vmy - py)
                if dist <= 32:
                    if lvl_id <= self.unlocked_level:
                        AudioManager.play_sfx('button')
                        self.manager.change_scene("LevelStartPopup", level_id=lvl_id)
                        return

        elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            _, dy = event.rel
            self.scroll_y -= dy / GameConfig.scale_y
            self.scroll_y = max(self.min_scroll, min(self.scroll_y, self.max_scroll))

    def update(self, dt):
        ParticleSystem.update()
        update_ambient_bubbles(self.bubbles, dt)

        if self.newly_unlocked:
            t = time.time() - self.unlock_time
            if t < 1.0:
                self.unlock_scale = 1.0 + math.sin(t * math.pi * 3) * 0.25
                if not self.spawned_particles and t > 0.1:
                    self.spawned_particles = True
                    ParticleSystem.create_confetti(count=20)
            else:
                self.unlock_scale = 1.0
                self.newly_unlocked = None

    def draw(self, surface):
        # Gradient background (cached)
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(25, 18, 50), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        # Ambient bubbles
        draw_ambient_bubbles(surface, self.bubbles)

        # Create virtual canvas for scrolling elements
        virtual_h = int(1900 * GameConfig.scale_y)
        scroll_surf = pygame.Surface((GameConfig.actual_width, virtual_h), pygame.SRCALPHA)

        # Draw connecting road path (luminous pipeline)
        for i in range(14):
            p1 = self.path_points[i]
            p2 = self.path_points[i + 1]
            sp1 = (GameConfig.to_screen_x(p1[0]), GameConfig.to_screen_y(p1[1] - self.scroll_y))
            sp2 = (GameConfig.to_screen_x(p2[0]), GameConfig.to_screen_y(p2[1] - self.scroll_y))

            # Outer glow pipeline
            glow_width = int(16 * GameConfig.scale_x)
            inner_width = int(4 * GameConfig.scale_x)
            pygame.draw.line(scroll_surf, GameConfig.COLOR_SURFACE_HIGH, sp1, sp2, width=glow_width)
            pygame.draw.line(scroll_surf, GameConfig.COLOR_PRIMARY, sp1, sp2, width=inner_width)
            # Center bright line
            pygame.draw.line(scroll_surf, (*GameConfig.COLOR_PRIMARY_LIGHT[:3],), sp1, sp2,
                             width=max(1, int(2 * GameConfig.scale_x)))

        # Draw Level nodes
        for idx, (px, py) in enumerate(self.path_points):
            lvl_id = self.world_id * 15 + idx + 1
            is_locked = lvl_id > self.unlocked_level
            is_new = (lvl_id == self.newly_unlocked)

            sx = GameConfig.to_screen_x(px)
            sy = GameConfig.to_screen_y(py - self.scroll_y)

            node_scale = self.unlock_scale if is_new else 1.0
            srad = int(28 * node_scale * min(GameConfig.scale_x, GameConfig.scale_y))
            if srad <= 0:
                continue

            # Outer glow ring for current/unlocked level
            if lvl_id == self.unlocked_level:
                glow_pulse = 0.5 + 0.5 * math.sin(time.time() * 5)
                glow_alpha = int(40 + 60 * glow_pulse)
                glow_surf = pygame.Surface((srad * 3, srad * 3), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*GameConfig.COLOR_GOLD[:3], glow_alpha),
                                   (srad * 3 // 2, srad * 3 // 2), srad + int(8 * GameConfig.scale_x))
                scroll_surf.blit(glow_surf, (sx - srad * 3 // 2, sy - srad * 3 // 2))

            # Main circle body (gemstone orb)
            if is_locked:
                bg_color = GameConfig.COLOR_SURFACE_HIGH
                stroke_color = GameConfig.COLOR_OUTLINE_DIM
            elif lvl_id == self.unlocked_level:
                bg_color = GameConfig.COLOR_PRIMARY
                stroke_color = GameConfig.COLOR_GOLD
            else:
                bg_color = GameConfig.COLOR_SUCCESS_DIM
                stroke_color = GameConfig.COLOR_SUCCESS

            # Draw orb with radial gradient simulation
            orb_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
            pygame.draw.circle(orb_surf, bg_color, (srad, srad), srad)
            # Gloss highlight
            gloss_r = max(1, srad // 3)
            pygame.draw.circle(orb_surf, (*[min(255, c + 60) for c in bg_color[:3]], 80),
                               (int(srad * 0.65), int(srad * 0.5)), gloss_r)
            scroll_surf.blit(orb_surf, (sx - srad, sy - srad))

            # Border
            pygame.draw.circle(scroll_surf, stroke_color, (sx, sy), srad, width=2)

            # Label identifiers
            if is_locked:
                font = pygame.font.SysFont(None, int(srad * 0.9))
                text = font.render("🔒", True, GameConfig.COLOR_OUTLINE)
                scroll_surf.blit(text, text.get_rect(center=(sx, sy)))
            else:
                font = pygame.font.SysFont(GameConfig.FONT_HEADLINE, int(srad * 1.0), bold=True)
                text = font.render(str(lvl_id), True, (255, 255, 255))
                scroll_surf.blit(text, text.get_rect(center=(sx, sy)))

                # Stars below completed levels
                stars = self.stars_data.get(str(lvl_id), 0)
                if stars > 0:
                    draw_stars(scroll_surf, px, py - self.scroll_y + 40, stars, total=3, size=8)

            # Animated bouncing pointer for active level
            if lvl_id == self.unlocked_level and not is_new:
                bounce = math.sin(time.time() * 7) * 8
                arrow_y = py - self.scroll_y - 52 + bounce
                ax = GameConfig.to_screen_x(px)
                ay = GameConfig.to_screen_y(arrow_y)
                aw = int(12 * GameConfig.scale_x)
                ah = int(14 * GameConfig.scale_y)
                # Glowing triangle pointer
                pygame.draw.polygon(scroll_surf, GameConfig.COLOR_GOLD, [
                    (ax, ay + ah), (ax - aw, ay), (ax + aw, ay)])
                pygame.draw.polygon(scroll_surf, (255, 255, 255), [
                    (ax, ay + ah), (ax - aw, ay), (ax + aw, ay)], width=1)

        surface.blit(scroll_surf, (0, 0))
        ParticleSystem.draw(surface)

        # Header HUD (glassmorphism)
        hud_h = int(68 * GameConfig.scale_y)
        hud_rect = pygame.Rect(0, 0, GameConfig.actual_width, hud_h)
        draw_glass_panel(surface, hud_rect, opacity=200, radius=0)

        world_info = LevelManager.get_world(self.world_id)
        world_title = f"{world_info['icon']} {world_info['name']}"
        Label(world_title, size=17, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 42)

        if self.world_id > 0:
            self.prev_world_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 130, 42)

        max_unlocked_world = min((self.unlocked_level - 1) // 15, 7)
        if self.world_id < max_unlocked_world:
            self.next_world_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 130, 42)

        self.back_btn.draw(surface, 80, 50)
