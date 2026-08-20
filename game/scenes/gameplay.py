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
        y_pos = GameConfig.VIRTUAL_HEIGHT - 35
        if self.bomb_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 120, y_pos):
            self.toggle_powerup("bomb")
            return
        if self.lightning_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 - 40, y_pos):
            self.toggle_powerup("lightning")
            return
        if self.rainbow_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 40, y_pos):
            self.toggle_powerup("rainbow")
            return
        if self.fireball_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2 + 120, y_pos):
            self.toggle_powerup("fireball")
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

        # Draw objective description text centered below HUD bar (board shifted to board_y=80)
        obj_text = ""
        if self.objective["type"] == "clear_board":
            obj_text = "Objective: Clear all bubbles"
        elif self.objective["type"] == "rescue":
            rescue_count = sum(1 for r in range(self.board.rows) for c in range(self.board.cols) if self.board.grid[r][c] != self.board.blank and self.board.grid[r][c].bubble_type == "rescue")
            obj_text = f"Rescue all pets (🐱 remaining: {rescue_count})"
        elif self.objective["type"] == "score":
            target = self.objective.get("target", 1000)
            obj_text = f"Target Score: {target} (Current: {self.score})"
        
        Label(obj_text, size=12, color=GameConfig.COLOR_TEXT_MUTED).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 64)

        # Draw game notices (such as out-of-stock messages)
        if self.notice_text and time.time() - self.notice_time < 2.0:
            Label(self.notice_text, size=13, color=GameConfig.COLOR_FAILURE, title=True, shadow=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 - 100
            )

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

        # Draw power-up selectors symmetrically
        y_pos = GameConfig.VIRTUAL_HEIGHT - 35
        self.bomb_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 120, y_pos)
        self.lightning_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 - 40, y_pos)
        self.rainbow_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 40, y_pos)
        self.fireball_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2 + 120, y_pos)

        # Draw active powerup indicator
        if self.active_powerup:
            Label(f"Active: {self.active_powerup.upper()}", size=12, color=GameConfig.COLOR_PRIMARY, title=True).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT - 85
            )
