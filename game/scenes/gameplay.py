# game/scenes/gameplay.py - Core gameplay loop, physics, collisions, matchings, combos, and overlays

import pygame
import random
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.ui.design_system import (draw_gradient_bg, draw_glass_panel,
                                    draw_progress_bar, draw_stars)
from game.entities.bubble import Bubble
from game.entities.launcher import Launcher
from game.gameplay.board import Board
from game.effects.particles import ParticleSystem
from game.audio.audio_manager import AudioManager
from game.storage.save_manager import SaveManager
from game.levels.level_manager import LevelManager
from game.scenes.overlays import PauseOverlay, VictoryOverlay, DefeatOverlay

class GameplayScene(BaseScene):
    def __init__(self, manager, level_id=1):
        super().__init__(manager)
        self.level_id = level_id
        
        # Load Level details
        self.level_data = LevelManager.get_level(self.level_id)
        self.world_data = LevelManager.get_world(self.level_data["world"])
        self.target_scores = self.level_data.get("target_scores", [1000, 2500, 5000])
        self._bg_surface = None
        
        # Gameplay states
        self.score = 0
        self.moves = self.level_data["moves"]
        self.combo_count = 0
        self.total_shots = 0
        self.start_time = time.time()

        # Engine instances
        self.board = Board()
        self.board.load_layout(self.level_data["grid"])
        self.launcher = Launcher()

        # Bubble projectile queues
        self.current_bubble = None
        self.next_bubble = None
        self.is_firing = False
        
        # Power-ups
        self.active_powerup = None
        
        # Init projectile queues
        self.prepare_next_bubble()

        # Navigation overlays
        self.show_pause = False
        self.show_victory = False
        self.show_defeat = False
        
        self.pause_overlay = PauseOverlay(self)
        self.victory_overlay = None
        self.defeat_overlay = None

        # Level Objective
        self.objective = self.level_data.get("objective", {"type": "clear_board"})

        # Custom UI buttons inside gameplay
        self.pause_btn = Button("⏸", w=40, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        self._init_powerup_buttons()

        # Notification message
        self.notice_text = ""
        self.notice_time = 0

        # Start soundtrack
        AudioManager.play_music('Whatever_It _Takes_OGG.ogg')

    def _init_powerup_buttons(self):
        # Powerup selectors at bottom bar
        boosters = SaveManager.get_boosters()
        self.bomb_btn = Button(f"💣 x{boosters.get('bomb',0)}", w=72, h=36, bg_color=(255, 102, 0), font_size=11)
        self.lightning_btn = Button(f"⚡ x{boosters.get('lightning',0)}", w=72, h=36, bg_color=(156, 39, 176), font_size=11)
        self.rainbow_btn = Button(f"🌈 x{boosters.get('rainbow',0)}", w=72, h=36, bg_color=(0, 188, 212), font_size=11)
        self.fireball_btn = Button(f"🔥 x{boosters.get('fireball',0)}", w=72, h=36, bg_color=(220, 50, 50), font_size=11)

    def toggle_powerup(self, b_type):
        boosters = SaveManager.get_boosters()
        if boosters.get(b_type, 0) > 0:
            if self.active_powerup == b_type:
                self.active_powerup = None
            else:
                self.active_powerup = b_type
            AudioManager.play_sfx('button')
        else:
            self.notice_text = f"Out of {b_type.capitalize()} boosters! Buy in Shop."
            self.notice_time = time.time()
            AudioManager.play_sfx('failure')

    def prepare_next_bubble(self):
        """Prepares active and preview bubbles."""
        # 1. Update remaining colors pool
        color_pool = self.board.get_remaining_colors()
        if not color_pool:
            color_pool = GameConfig.BUBBLE_COLORS

        # 2. Setup current projectile if empty
        if self.current_bubble is None:
            if self.next_bubble is not None:
                self.current_bubble = self.next_bubble
            else:
                color = random.choice(color_pool)
                self.current_bubble = Bubble(color)
            
            # Reposition to launcher center
            self.current_bubble.vx = self.launcher.vx
            self.current_bubble.vy = self.launcher.vy - 20
            self.current_bubble.update_rect()

        # 3. Setup next preview
        color = random.choice(color_pool)
        self.next_bubble = Bubble(color)
        self.next_bubble.vx = 55
        self.next_bubble.vy = GameConfig.VIRTUAL_HEIGHT - 55
        self.next_bubble.update_rect()

    def restart_level(self):
        """Resets gameplay loop variables."""
        self.score = 0
        self.moves = self.level_data["moves"]
        self.combo_count = 0
        self.total_shots = 0
        self.start_time = time.time()
        
        self.objective = self.level_data.get("objective", {"type": "clear_board"})
        self.notice_text = ""
        self.notice_time = 0

        self.board.load_layout(self.level_data["grid"])
        self.current_bubble = None
        self.next_bubble = None
        self.is_firing = False
        self.active_powerup = None
        self.prepare_next_bubble()
        self._refresh_booster_buttons()

        self.show_pause = False
        self.show_victory = False
        self.show_defeat = False
        ParticleSystem.clear()

    def _refresh_booster_buttons(self):
        boosters = SaveManager.get_boosters()
        self.bomb_btn.label.set_text(f"💣 x{boosters.get('bomb',0)}")
        self.lightning_btn.label.set_text(f"⚡ x{boosters.get('lightning',0)}")
        self.rainbow_btn.label.set_text(f"🌈 x{boosters.get('rainbow',0)}")
        self.fireball_btn.label.set_text(f"🔥 x{boosters.get('fireball',0)}")

    def handle_event(self, event):
        # Forward inputs to pause/victory/defeat overlays if active
        if self.show_pause:
            self.pause_overlay.handle_event(event)
            return
        if self.show_victory and self.victory_overlay:
            self.victory_overlay.handle_event(event)
            return
        if self.show_defeat and self.defeat_overlay:
            self.defeat_overlay.handle_event(event)
            return

        # Android back button pauses game
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.show_pause = True
                return

        # Powerup interactions check
        y_pos = GameConfig.VIRTUAL_HEIGHT - 38
        if self.bomb_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 110, y_pos):
            self.toggle_powerup("bomb")
            return
        if self.lightning_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 35, y_pos):
            self.toggle_powerup("lightning")
            return
        if self.rainbow_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 40, y_pos):
            self.toggle_powerup("rainbow")
            return
        if self.fireball_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 115, y_pos):
            self.toggle_powerup("fireball")
            return

        # Handle pause button on top-left of app bar
        if self.pause_btn.handle_event(event, 28, 25):
            self.show_pause = True
            return

        # Touch aim / release logic
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            vmy = my / GameConfig.scale_y
            # Don't register click if in top HUD or bottom powerups boundaries
            if 60 <= vmy < GameConfig.VIRTUAL_HEIGHT - 80:
                self.launcher.set_target(mx, my)

        elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            mx, my = event.pos
            vmy = my / GameConfig.scale_y
            if 60 <= vmy < GameConfig.VIRTUAL_HEIGHT - 80:
                self.launcher.set_target(mx, my)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos
            vmy = my / GameConfig.scale_y
            if 60 <= vmy < GameConfig.VIRTUAL_HEIGHT - 80:
                self.fire_projectile()

    def fire_projectile(self):
        """Fires current bubble."""
        if self.is_firing or self.current_bubble is None:
            return

        self.is_firing = True
        self.moves -= 1
        self.total_shots += 1
        
        # Apply selected power-ups
        if self.active_powerup:
            if SaveManager.use_booster(self.active_powerup):
                self.current_bubble.bubble_type = self.active_powerup
                if self.active_powerup == "bomb":
                    self.current_bubble.color = (255, 102, 0)
                elif self.active_powerup == "lightning":
                    self.current_bubble.color = (186, 104, 200)
                elif self.active_powerup == "rainbow":
                    self.current_bubble.color = (255, 255, 255)
                elif self.active_powerup == "fireball":
                    self.current_bubble.color = (255, 75, 40)
                self._refresh_booster_buttons()
            else:
                self.active_powerup = None
            
        self.active_powerup = None

        # Launcher recoil animation bounce
        self.current_bubble.angle = self.launcher.angle
        AudioManager.play_sfx('shoot')
        
        # Save statistics update
        SaveManager.update_stats(games_played=0)

    def update(self, dt):
        if self.show_pause or self.show_victory or self.show_defeat:
            return

        ParticleSystem.update()

        if self.is_firing and self.current_bubble:
            # Add particle flight trail
            ParticleSystem.create_trail(self.current_bubble.vx, self.current_bubble.vy, self.current_bubble.color)

            # Standard update steps
            self.current_bubble.update()

            # Side walls bounce collision (board left/right bounds)
            # Board area starts at board_x, ends at board_x + BOARD_WIDTH
            left_limit = GameConfig.board_x + GameConfig.BUBBLE_RAD
            right_limit = GameConfig.board_x + GameConfig.BOARD_WIDTH - GameConfig.BUBBLE_RAD

            if self.current_bubble.vx <= left_limit:
                self.current_bubble.vx = left_limit
                self.current_bubble.angle = 180 - self.current_bubble.angle
                self.current_bubble.update_rect()
                AudioManager.play_sfx('button')  # Bounce sound
            elif self.current_bubble.vx >= right_limit:
                self.current_bubble.vx = right_limit
                self.current_bubble.angle = 180 - self.current_bubble.angle
                self.current_bubble.update_rect()
                AudioManager.play_sfx('button')  # Bounce sound

            # Check Fireball piercing logic
            if self.current_bubble.bubble_type == "fireball":
                to_pop = []
                for r in range(self.board.rows):
                    for c in range(self.board.cols):
                        other = self.board.grid[r][c]
                        if other != self.board.blank:
                            dist = math.hypot(self.current_bubble.vx - other.vx, self.current_bubble.vy - other.vy)
                            if dist < GameConfig.BUBBLE_WD - 4:
                                to_pop.append((r, c))
                if to_pop:
                    self.board.pop_bubbles(to_pop)
                    points = len(to_pop) * 100
                    self.score += points
                    SaveManager.update_stats(bubbles_popped=len(to_pop))
                    
                    floaters = self.board.check_floaters()
                    if floaters:
                        self.board.pop_bubbles(floaters)
                        self.score += len(floaters) * 200
                        SaveManager.update_stats(bubbles_dropped=len(floaters))
                
                # Fireball terminates when it reaches ceiling
                if self.current_bubble.vy - GameConfig.BUBBLE_RAD <= GameConfig.board_y:
                    self.is_firing = False
                    self.current_bubble = None
                    self.check_game_state()
                    self.prepare_next_bubble()
            else:
                # Grid bubble collision checking (normal, bomb, lightning, rainbow)
                collided = False
                hit_r, hit_c = -1, -1

                # Check top ceiling boundary
                if self.current_bubble.vy - GameConfig.BUBBLE_RAD <= GameConfig.board_y:
                    hit_r, hit_c = self.board.add_bubble_to_top(self.current_bubble)
                    collided = True
                else:
                    # Check collision with other locked bubbles
                    for r in range(self.board.rows):
                        for c in range(self.board.cols):
                            other = self.board.grid[r][c]
                            if other != self.board.blank:
                                # Distance collision check
                                dist = math.hypot(self.current_bubble.vx - other.vx, self.current_bubble.vy - other.vy)
                                if dist < GameConfig.BUBBLE_WD - 4:
                                    hit_r, hit_c = self.board.snap_and_add(self.current_bubble, r, c)
                                    collided = True
                                    break
                        if collided:
                            break

                if collided:
                    self.is_firing = False
                    
                    # Check target matches or special booster action
                    new_bubble = self.board.grid[hit_r][hit_c]
                    if new_bubble != self.board.blank:
                        if new_bubble.bubble_type == "bomb":
                            # Blow up surrounding neighbors
                            neighbors = self.board.get_neighbors(hit_r, hit_c)
                            targets = [(hit_r, hit_c)] + [n for n in neighbors if self.board.grid[n[0]][n[1]] != self.board.blank]
                            self.board.pop_bubbles(targets)
                            
                            points = len(targets) * 100
                            self.score += points
                            SaveManager.update_stats(bubbles_popped=len(targets))
                        elif new_bubble.bubble_type == "lightning":
                            # Clears the entire snapped row
                            targets = []
                            for c in range(self.board.cols):
                                if self.board.grid[hit_r][c] != self.board.blank:
                                    targets.append((hit_r, c))
                            self.board.pop_bubbles(targets)
                            
                            points = len(targets) * 100
                            self.score += points
                            SaveManager.update_stats(bubbles_popped=len(targets))
                        else:
                            matches = self.board.check_matches(hit_r, hit_c, new_bubble.color)
                            if len(matches) >= 3:
                                self.combo_count += 1
                                self.board.pop_bubbles(matches)
                                
                                # Add matching score
                                points = len(matches) * 100 * self.combo_count
                                self.score += points
                                SaveManager.update_stats(bubbles_popped=len(matches))

                                # Drop floating clusters
                                floaters = self.board.check_floaters()
                                if floaters:
                                    self.board.pop_bubbles(floaters)
                                    self.score += len(floaters) * 200
                                    SaveManager.update_stats(bubbles_dropped=len(floaters))
                                
                                if self.combo_count >= 2:
                                    AudioManager.play_sfx('combo')
                            else:
                                self.combo_count = 0

                        # Drop any floaters after bomb or lightning pop
                        if new_bubble.bubble_type in ["bomb", "lightning"]:
                            floaters = self.board.check_floaters()
                            if floaters:
                                self.board.pop_bubbles(floaters)
                                self.score += len(floaters) * 200
                                SaveManager.update_stats(bubbles_dropped=len(floaters))

                    # Clear projectile
                    self.current_bubble = None
                    self.check_game_state()
                    self.prepare_next_bubble()

    def check_game_state(self):
        """Evaluates win/lose constraints."""
        play_time = int(time.time() - self.start_time)
        
        # Check winning criteria
        win = False
        if self.objective["type"] == "clear_board":
            win = self.board.is_empty()
        elif self.objective["type"] == "rescue":
            rescue_count = sum(1 for r in range(self.board.rows) for c in range(self.board.cols) if self.board.grid[r][c] != self.board.blank and self.board.grid[r][c].bubble_type == "rescue")
            win = (rescue_count == 0)
        elif self.objective["type"] == "score":
            win = (self.score >= self.objective.get("target", 1000))

        if win:
            stars = LevelManager.calculate_stars(self.level_id, self.score)
            
            # Save achievements check
            if self.level_id == 1:
                SaveManager.unlock_achievement("first_win")
            if stars == 3:
                SaveManager.unlock_achievement("perfect_clear")
            
            SaveManager.update_progress(self.level_id, self.score, stars)
            SaveManager.update_stats(
                levels_completed=1,
                games_played=1,
                highest_score=self.score,
                highest_combo=self.combo_count,
                play_time_sec=play_time
            )
            
            self.show_victory = True
            self.victory_overlay = VictoryOverlay(self, self.score, stars, self.level_id)
            return

        # LOSE: out of moves or bubble crosses launcher boundary
        bottom_limit = self.launcher.vy - GameConfig.BUBBLE_RAD
        if self.moves <= 0 or self.board.check_lose(bottom_limit):
            SaveManager.update_stats(
                games_played=1,
                play_time_sec=play_time
            )
            self.show_defeat = True
            self.defeat_overlay = DefeatOverlay(self, self.score, self.level_id)

    def draw(self, surface):
        # Draw gradient background base
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(28, 20, 52), bot_color=(15, 13, 23))
        surface.blit(self._bg_surface, (0, 0))

        # Draw Staggered Grid Playboard boundary with glassmorphism style
        border_rect = pygame.Rect(
            GameConfig.to_screen_x(GameConfig.board_x),
            GameConfig.to_screen_y(GameConfig.board_y),
            int(GameConfig.BOARD_WIDTH * GameConfig.scale_x),
            int(GameConfig.BOARD_HEIGHT * GameConfig.scale_y)
        )
        draw_glass_panel(surface, border_rect, opacity=35, radius=12)
        pygame.draw.rect(surface, GameConfig.COLOR_PRIMARY_DIM, border_rect, width=1, border_radius=12)

        # Draw ceiling line (luminous)
        ceiling_y = GameConfig.to_screen_y(GameConfig.board_y)
        pygame.draw.line(surface, (*GameConfig.COLOR_PRIMARY_LIGHT[:3],), (border_rect.left + 4, ceiling_y), (border_rect.right - 4, ceiling_y), width=2)

        # Draw grid board bubbles
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                bubble = self.board.grid[r][c]
                if bubble != self.board.blank:
                    bubble.draw(surface)

        # Draw projectile
        if self.current_bubble:
            self.current_bubble.draw(surface)

        # Draw launcher base & arrow pointer
        self.launcher.draw(surface)

        # Draw laser pointer trajectory helper
        if not self.is_firing and self.current_bubble:
            self._draw_trajectory(surface)

        # Draw particles system
        ParticleSystem.draw(surface)

        # Draw combo popup if combo >= 2
        if self.combo_count >= 2:
            combo_pulse = 1.0 + math.sin(time.time() * 8) * 0.15
            combo_surf = pygame.Surface((140, 36), pygame.SRCALPHA)
            combo_rect = pygame.Rect(0, 0, 140, 36)
            draw_glass_panel(combo_surf, combo_rect, opacity=160, border_color=GameConfig.COLOR_GOLD, radius=18, glow=True)
            Label(f"x{self.combo_count} COMBO!", size=15, color=GameConfig.COLOR_GOLD, title=True).draw(
                combo_surf, 70, 18
            )
            csx = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2) - int(70 * combo_pulse)
            csy = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT / 2 - 40)
            scaled_combo = pygame.transform.smoothscale(combo_surf, (int(140 * combo_pulse), int(36 * combo_pulse)))
            surface.blit(scaled_combo, (csx, csy))

        # Render HUD Overlay elements
        self._draw_hud(surface)

        # Render overlays
        if self.show_pause:
            self.pause_overlay.draw(surface)
        elif self.show_victory and self.victory_overlay:
            self.victory_overlay.draw(surface)
        elif self.show_defeat and self.defeat_overlay:
            self.defeat_overlay.draw(surface)

    def _draw_trajectory(self, surface):
        """Draws dotted reflection trajectory path."""
        max_bounces = 2
        dot_color = (255, 255, 255)
        if self.active_powerup == "bomb":
            dot_color = (255, 102, 0)
        elif self.active_powerup == "lightning":
            dot_color = (186, 104, 200)
        elif self.active_powerup == "rainbow":
            dot_color = (0, 255, 255)
        elif self.active_powerup == "fireball":
            dot_color = (255, 75, 40)

        cx = self.launcher.vx
        cy = self.launcher.vy - 20
        rad_angle = math.radians(self.launcher.angle)
        dx = math.cos(rad_angle)
        dy = -math.sin(rad_angle)

        bounces = 0
        left_limit = GameConfig.board_x + GameConfig.BUBBLE_RAD
        right_limit = GameConfig.board_x + GameConfig.BOARD_WIDTH - GameConfig.BUBBLE_RAD

        while bounces <= max_bounces:
            t_wall = float('inf')
            if dx > 0:
                t_wall = (right_limit - cx) / dx
            elif dx < 0:
                t_wall = (left_limit - cx) / dx

            t_ceil = (GameConfig.board_y + GameConfig.BUBBLE_RAD - cy) / dy if dy != 0 else float('inf')
            t = min(t_wall, t_ceil)
            if t <= 0:
                break

            step = 12
            steps_count = int(t / step)
            for i in range(steps_count):
                st = i * step
                sx = GameConfig.to_screen_x(cx + dx * st)
                sy = GameConfig.to_screen_y(cy + dy * st)
                pygame.draw.circle(surface, dot_color, (sx, sy), 2)

            if t_ceil <= t_wall:
                break

            cx = cx + dx * t
            cy = cy + dy * t
            dx = -dx
            bounces += 1

    def _draw_hud(self, surface):
        """Draws screen overlay HUD indicators with Stitch design system."""
        # Top Glass App Bar
        hud_h = int(50 * GameConfig.scale_y)
        hud_bar = pygame.Rect(0, 0, GameConfig.actual_width, hud_h)
        draw_glass_panel(surface, hud_bar, opacity=180, radius=0)

        # Pause Button on left
        self.pause_btn.draw(surface, 28, 25)

        # Level Title & Progress Bar centered
        Label(f"Level {self.level_id}", size=14, color=GameConfig.COLOR_PRIMARY_LIGHT, title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2 - 40, 16
        )
        Label(f"⭐ {self.score}", size=14, color=GameConfig.COLOR_GOLD, title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2 + 50, 16
        )

        # Progress bar showing score relative to star targets
        pbar_w = int(180 * GameConfig.scale_x)
        pbar_h = int(10 * GameConfig.scale_y)
        pbar_x = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2) - pbar_w // 2
        pbar_y = int(32 * GameConfig.scale_y)
        
        max_score = max(1, self.target_scores[2] if len(self.target_scores) >= 3 else 3000)
        fill_pct = min(1.0, self.score / max_score)
        
        star_positions = [
            (self.target_scores[0] / max_score) if len(self.target_scores) > 0 else 0.33,
            (self.target_scores[1] / max_score) if len(self.target_scores) > 1 else 0.66,
            1.0
        ]
        draw_progress_bar(surface, pygame.Rect(pbar_x, pbar_y, pbar_w, pbar_h), fill_pct,
                          star_positions=star_positions)

        # Sub-header: Objective Chip & Shots Remaining Chip
        # Objective chip
        obj_text = "Clear Board"
        obj_icon = "🫧"
        if self.objective["type"] == "rescue":
            rescue_count = sum(1 for r in range(self.board.rows) for c in range(self.board.cols) if self.board.grid[r][c] != self.board.blank and self.board.grid[r][c].bubble_type == "rescue")
            obj_text = f"Rescue: {rescue_count}"
            obj_icon = "🐱"
        elif self.objective["type"] == "score":
            target = self.objective.get("target", 1000)
            obj_text = f"Target: {target}"
            obj_icon = "⭐"

        # Objective capsule
        obj_w = int(140 * GameConfig.scale_x)
        obj_h = int(24 * GameConfig.scale_y)
        obj_x = GameConfig.to_screen_x(25)
        obj_y = GameConfig.to_screen_y(54)
        draw_glass_panel(surface, pygame.Rect(obj_x, obj_y, obj_w, obj_h), opacity=120, radius=12)
        Label(f"{obj_icon} {obj_text}", size=11, color=GameConfig.COLOR_TEXT, align="left").draw(
            surface, 32, 66, originX=0
        )

        # Shots capsule
        shots_color = GameConfig.COLOR_FAILURE if self.moves <= 5 else GameConfig.COLOR_SUCCESS
        shots_w = int(100 * GameConfig.scale_x)
        shots_h = int(24 * GameConfig.scale_y)
        shots_x = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH - 125)
        shots_y = GameConfig.to_screen_y(54)
        draw_glass_panel(surface, pygame.Rect(shots_x, shots_y, shots_w, shots_h), opacity=120, radius=12)
        Label(f"Shots: {self.moves}", size=12, color=shots_color, title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH - 75, 66
        )

        # Draw game notices (e.g. out-of-stock messages)
        if self.notice_text and time.time() - self.notice_time < 2.0:
            notice_w = int(280 * GameConfig.scale_x)
            notice_h = int(36 * GameConfig.scale_y)
            notice_x = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2) - notice_w // 2
            notice_y = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT / 2 - 100)
            draw_glass_panel(surface, pygame.Rect(notice_x, notice_y, notice_w, notice_h),
                             opacity=180, border_color=GameConfig.COLOR_FAILURE, radius=18)
            Label(self.notice_text, size=12, color=GameConfig.COLOR_FAILURE, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 - 82
            )

        # Bottom Powerups Bar panel
        pbar_rect = pygame.Rect(0, int((GameConfig.VIRTUAL_HEIGHT - 72) * GameConfig.scale_y),
                                GameConfig.actual_width, int(72 * GameConfig.scale_y))
        draw_glass_panel(surface, pbar_rect, opacity=180, radius=0)

        # Next preview bubble frame
        if self.next_bubble:
            sx = GameConfig.to_screen_x(50)
            sy = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT - 48)
            srad = int(22 * min(GameConfig.scale_x, GameConfig.scale_y))
            frame_rect = pygame.Rect(sx - srad, sy - srad, srad * 2, srad * 2)
            draw_glass_panel(surface, frame_rect, opacity=100, radius=srad, border_color=GameConfig.COLOR_PRIMARY)
            
            self.next_bubble.draw(surface)
            Label("NEXT", size=9, color=GameConfig.COLOR_TEXT_MUTED).draw(
                surface, 50, GameConfig.VIRTUAL_HEIGHT - 18
            )

        # Draw power-up selectors symmetrically
        y_pos = GameConfig.VIRTUAL_HEIGHT - 38
        self.bomb_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 110, y_pos)
        self.lightning_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 35, y_pos)
        self.rainbow_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 40, y_pos)
        self.fireball_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 115, y_pos)

        # Draw active powerup indicator
        if self.active_powerup:
            act_w = int(160 * GameConfig.scale_x)
            act_h = int(24 * GameConfig.scale_y)
            act_x = GameConfig.to_screen_x(GameConfig.VIRTUAL_WIDTH / 2) - act_w // 2
            act_y = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT - 88)
            draw_glass_panel(surface, pygame.Rect(act_x, act_y, act_w, act_h),
                             opacity=180, border_color=GameConfig.COLOR_GOLD, radius=12, glow=True)
            Label(f"Active: {self.active_powerup.upper()}", size=11, color=GameConfig.COLOR_GOLD, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 76
            )
