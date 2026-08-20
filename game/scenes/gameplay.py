# game/scenes/gameplay.py - Core gameplay loop, physics, collisions, matchings, combos, and overlays

import pygame
import random
import math
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
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

        # Custom UI buttons inside gameplay
        self.pause_btn = Button("⏸", w=40, h=40, bg_color=GameConfig.COLOR_BG_LIGHT)
        self._init_powerup_buttons()

        # Start soundtrack
        AudioManager.play_music('Whatever_It _Takes_OGG.ogg')

    def _init_powerup_buttons(self):
        # Powerup selectors at bottom bar
        self.bomb_btn = Button("💣", w=60, h=36, bg_color=(255, 102, 0))
        self.rainbow_btn = Button("🌈", w=60, h=36, bg_color=(156, 39, 176))
        self.laser_btn = Button("⚡", w=60, h=36, bg_color=(0, 188, 212))

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
        
        self.board.load_layout(self.level_data["grid"])
        self.current_bubble = None
        self.next_bubble = None
        self.is_firing = False
        self.active_powerup = None
        self.prepare_next_bubble()

        self.show_pause = False
        self.show_victory = False
        self.show_defeat = False
        ParticleSystem.clear()

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
        if self.bomb_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 80, GameConfig.VIRTUAL_HEIGHT - 35):
            self.active_powerup = "bomb"
            AudioManager.play_sfx('button')
            return
        if self.rainbow_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 35):
            self.active_powerup = "rainbow"
            AudioManager.play_sfx('button')
            return
        if self.laser_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 80, GameConfig.VIRTUAL_HEIGHT - 35):
            self.active_powerup = "laser"
            AudioManager.play_sfx('button')
            return

        # Handle pause button
        if self.pause_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH - 30, 24):
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
        if self.active_powerup == "bomb":
            self.current_bubble.bubble_type = "bomb"
            self.current_bubble.color = (255, 102, 0)
        elif self.active_powerup == "rainbow":
            self.current_bubble.bubble_type = "rainbow"
            self.current_bubble.color = (255, 255, 255)
            
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

            # Grid bubble collision checking
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
                
                # Check target matches or bomb blast radius
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

                # Clear projectile
                self.current_bubble = None
                self.check_game_state()
                self.prepare_next_bubble()

    def check_game_state(self):
        """Evaluates win/lose constraints."""
        play_time = int(time.time() - self.start_time)
        
        # WIN: all bubbles cleared
        if self.board.is_empty():
            stars = LevelManager.calculate_stars(self.level_id, self.score)
            
            # Save achievements check
            unlocked_ach = SaveManager.load_game()["achievements"]
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
        # Launcher boundary is at y = launcher.vy - BUBBLE_RAD
        bottom_limit = self.launcher.vy - GameConfig.BUBBLE_RAD
        if self.moves <= 0 or self.board.check_lose(bottom_limit):
            SaveManager.update_stats(
                games_played=1,
                play_time_sec=play_time
            )
            self.show_defeat = True
            self.defeat_overlay = DefeatOverlay(self, self.score, self.level_id)

    def draw(self, surface):
        # Draw background base
        surface.fill(GameConfig.COLOR_BG)

        # Draw Staggered Grid Playboard boundary guides
        border_rect = pygame.Rect(
            GameConfig.to_screen_x(GameConfig.board_x),
            GameConfig.to_screen_y(GameConfig.board_y),
            int(GameConfig.BOARD_WIDTH * GameConfig.scale_x),
            int(GameConfig.BOARD_HEIGHT * GameConfig.scale_y)
        )
        pygame.draw.rect(surface, GameConfig.COLOR_BG_LIGHT, border_rect)
        pygame.draw.rect(surface, GameConfig.COLOR_ACCENT, border_rect, width=2)

        # Draw ceiling line
        ceiling_y = GameConfig.to_screen_y(GameConfig.board_y)
        pygame.draw.line(surface, (255, 255, 255, 128), (border_rect.left, ceiling_y), (border_rect.right, ceiling_y), width=2)

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
        is_laser = self.active_powerup == "laser"
        max_bounces = 5 if is_laser else 2
        dot_color = (0, 255, 255) if is_laser else (255, 255, 255)

        # Start from launcher center
        cx = self.launcher.vx
        cy = self.launcher.vy - 20
        rad_angle = math.radians(self.launcher.angle)
        dx = math.cos(rad_angle)
        dy = -math.sin(rad_angle)  # Pointing up

        bounces = 0
        left_limit = GameConfig.board_x + GameConfig.BUBBLE_RAD
        right_limit = GameConfig.board_x + GameConfig.BOARD_WIDTH - GameConfig.BUBBLE_RAD

        while bounces <= max_bounces:
            # Find next bounce wall or ceiling collision
            # vx(t) = cx + dx * t, vy(t) = cy + dy * t
            t_wall = float('inf')
            if dx > 0:
                t_wall = (right_limit - cx) / dx
            elif dx < 0:
                t_wall = (left_limit - cx) / dx

            t_ceil = (GameConfig.board_y + GameConfig.BUBBLE_RAD - cy) / dy if dy != 0 else float('inf')

            t = min(t_wall, t_ceil)
            if t <= 0:
                break

            # Draw dotted segments
            step = 12
            steps_count = int(t / step)
            for i in range(steps_count):
                st = i * step
                sx = GameConfig.to_screen_x(cx + dx * st)
                sy = GameConfig.to_screen_y(cy + dy * st)
                pygame.draw.circle(surface, dot_color, (sx, sy), 2)

            # If ceiling, terminate path
            if t_ceil <= t_wall:
                break

            # Bounce off wall, reflect X velocity
            cx = cx + dx * t
            cy = cy + dy * t
            dx = -dx
            bounces += 1

    def _draw_hud(self, surface):
        """Draws screen overlay HUD indicators."""
        # Top HUD Bar panel
        hud_bar = pygame.Rect(0, 0, GameConfig.actual_width, int(48 * GameConfig.scale_y))
        pygame.draw.rect(surface, (10, 8, 20, 160), hud_bar)

        Label(f"LV {self.level_id}", size=16, color=(255, 235, 59), title=True, align="left").draw(
            surface, 15, 24, originX=0
        )
        Label(f"⭐ {self.score}", size=16, title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2 - 30, 24
        )
        
        # Moves remaining alerts red if <=5
        moves_color = GameConfig.COLOR_FAILURE if self.moves <= 5 else GameConfig.COLOR_TEXT
        Label(f"💣 {self.moves}", size=16, color=moves_color, title=True).draw(
            surface, GameConfig.VIRTUAL_WIDTH - 90, 24
        )

        self.pause_btn.draw(surface, GameConfig.VIRTUAL_WIDTH - 30, 24)

        # Bottom Powerups Bar panel
        p_bar = pygame.Rect(0, int((GameConfig.VIRTUAL_HEIGHT - 70) * GameConfig.scale_y), GameConfig.actual_width, int(70 * GameConfig.scale_y))
        pygame.draw.rect(surface, (10, 8, 20, 160), p_bar)

        # Powerups selectors label
        Label("POWER-UPS", size=10, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 60
        )

        # Next preview bubble
        if self.next_bubble:
            # Preview slot circular frame
            sx = GameConfig.to_screen_x(55)
            sy = GameConfig.to_screen_y(GameConfig.VIRTUAL_HEIGHT - 55)
            srad = int(22 * min(GameConfig.scale_x, GameConfig.scale_y))
            pygame.draw.circle(surface, GameConfig.COLOR_BG_LIGHT, (sx, sy), srad)
            pygame.draw.circle(surface, GameConfig.COLOR_ACCENT, (sx, sy), srad, width=1)
            
            self.next_bubble.draw(surface)
            Label("NEXT", size=9, color=GameConfig.COLOR_TEXT_MUTED).draw(
                surface, 55, GameConfig.VIRTUAL_HEIGHT - 22
            )

        # Draw power-up selectors
        self.bomb_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 80, GameConfig.VIRTUAL_HEIGHT - 35)
        self.rainbow_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 35)
        self.laser_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 80, GameConfig.VIRTUAL_HEIGHT - 35)

        # Draw active powerup indicator
        if self.active_powerup:
            Label(f"Active: {self.active_powerup.upper()}", size=12, color=GameConfig.COLOR_PRIMARY, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 85
            )
