# game/gameplay/board.py - Bubble board grid, matching, floating algorithms, and collision handling

import pygame
import copy
import math
import random
from game.core.config import GameConfig
from game.entities.bubble import Bubble
from game.effects.particles import ParticleSystem
from game.audio.audio_manager import AudioManager

class Board:
    def __init__(self, rows=GameConfig.BUBBLE_ROWS, cols=GameConfig.BUBBLE_COLS):
        self.rows = rows
        self.cols = cols
        self.blank = '.'
        self.grid = [[self.blank for _ in range(self.cols)] for _ in range(self.rows)]

    def load_layout(self, layout_grid):
        """Populates grid from level layout array (translating ids to colors)."""
        self.clear()
        for r in range(min(len(layout_grid), self.rows)):
            for c in range(min(len(layout_grid[r]), self.cols)):
                color_idx = layout_grid[r][c]
                if color_idx >= 0:
                    if color_idx < len(GameConfig.BUBBLE_COLORS):
                        color = GameConfig.BUBBLE_COLORS[color_idx]
                        self.grid[r][c] = Bubble(color, row=r, col=c)
                    elif color_idx == 7:
                        self.grid[r][c] = Bubble((120, 120, 120), row=r, col=c, bubble_type="obstacle")
                    elif color_idx == 9:
                        self.grid[r][c] = Bubble((244, 143, 177), row=r, col=c, bubble_type="rescue")
        self.recalculate_positions()

    def clear(self):
        self.grid = [[self.blank for _ in range(self.cols)] for _ in range(self.rows)]

    def recalculate_positions(self):
        """Sets the precise virtual coordinates for each grid-locked bubble."""
        for r in range(self.rows):
            for c in range(self.cols):
                bubble = self.grid[r][c]
                if bubble != self.blank:
                    # Calculate center in virtual space
                    x_offset = GameConfig.BUBBLE_RAD if r % 2 != 0 else 0
                    bubble.vx = GameConfig.board_x + (GameConfig.BUBBLE_WD * c) + GameConfig.BUBBLE_RAD + x_offset
                    bubble.vy = GameConfig.board_y + (GameConfig.BUBBLE_WD * r) + GameConfig.BUBBLE_RAD - (GameConfig.BUB_ADJUST * r)
                    bubble.update_rect()

    def get_bubble_at_coords(self, vx, vy):
        """Finds closest grid row and col for placement."""
        row_height = GameConfig.BUBBLE_WD - GameConfig.BUB_ADJUST
        r = int((vy - GameConfig.board_y) / row_height)
        r = max(0, min(r, self.rows - 1))
        
        x_offset = GameConfig.BUBBLE_RAD if r % 2 != 0 else 0
        c = int((vx - GameConfig.board_x - x_offset) / GameConfig.BUBBLE_WD)
        c = max(0, min(c, self.cols - 1))
        return r, c

    def get_neighbors(self, r, c):
        """Returns valid neighbor coordinates in the staggered hex grid."""
        neighbors = []
        offsets = []
        if r % 2 == 0:
            offsets = [
                (0, -1), (0, 1),
                (1, 0), (1, -1),
                (-1, 0), (-1, -1)
            ]
        else:
            offsets = [
                (0, -1), (0, 1),
                (1, 0), (1, 1),
                (-1, 0), (-1, 1)
            ]

        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def add_bubble_to_top(self, bubble):
        """Snaps flying bubble to the top row."""
        r, c = self.get_bubble_at_coords(bubble.vx, bubble.vy)
        # Force row to 0
        self.grid[0][c] = Bubble(bubble.color, row=0, col=c, bubble_type=bubble.bubble_type)
        self.recalculate_positions()
        return 0, c

    def snap_and_add(self, bubble, hit_r, hit_c):
        """Places bubble in nearest empty neighbor cell to impact point."""
        neighbors = self.get_neighbors(hit_r, hit_c)
        
        # Find closest empty neighbor in virtual space
        best_r, best_c = hit_r, hit_c
        min_dist = float('inf')
        
        # Temporary instance to measure coordinates
        temp = Bubble(bubble.color, bubble_type=bubble.bubble_type)

        for nr, nc in neighbors:
            if self.grid[nr][nc] == self.blank:
                # Calculate coordinates
                x_offset = GameConfig.BUBBLE_RAD if nr % 2 != 0 else 0
                tx = GameConfig.board_x + (GameConfig.BUBBLE_WD * nc) + GameConfig.BUBBLE_RAD + x_offset
                ty = GameConfig.board_y + (GameConfig.BUBBLE_WD * nr) + GameConfig.BUBBLE_RAD - (GameConfig.BUB_ADJUST * nr)
                
                dist = math.hypot(bubble.vx - tx, bubble.vy - ty)
                if dist < min_dist:
                    min_dist = dist
                    best_r, best_c = nr, nc

        # Place bubble
        self.grid[best_r][best_c] = Bubble(bubble.color, row=best_r, col=best_c, bubble_type=bubble.bubble_type)
        self.recalculate_positions()
        return best_r, best_c

    def check_matches(self, r, c, target_color):
        """Flood-fill traversal to find all connected matching color bubbles."""
        matched = []
        queue = [(r, c)]
        visited = set()

        while queue:
            curr_r, curr_c = queue.pop(0)
            if (curr_r, curr_c) in visited:
                continue
            visited.add((curr_r, curr_c))
            
            b = self.grid[curr_r][curr_c]
            if b != self.blank:
                # Match normal color or special wildcard
                if b.color == target_color or b.bubble_type == "rainbow":
                    matched.append((curr_r, curr_c))
                    for nr, nc in self.get_neighbors(curr_r, curr_c):
                        if (nr, nc) not in visited:
                            queue.append((nr, nc))
        return matched

    def check_floaters(self):
        """Finds all disconnected clusters not connected to the ceiling."""
        connected = set()
        queue = []

        # Start from top row
        for c in range(self.cols):
            if self.grid[0][c] != self.blank:
                queue.append((0, c))
                connected.add((0, c))

        # BFS from ceiling
        while queue:
            curr_r, curr_c = queue.pop(0)
            for nr, nc in self.get_neighbors(curr_r, curr_c):
                if self.grid[nr][nc] != self.blank and (nr, nc) not in connected:
                    connected.add((nr, nc))
                    queue.append((nr, nc))

        # Any grid cell with bubble not in connected is a floater
        floaters = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != self.blank and (r, c) not in connected:
                    floaters.append((r, c))
        return floaters

    def pop_bubbles(self, coords):
        """Removes bubbles, trigger pop particles, returns points."""
        for r, c in coords:
            b = self.grid[r][c]
            if b != self.blank:
                # Trigger particle burst at bubble coordinates
                ParticleSystem.create_pop_burst(b.vx, b.vy, b.color)
                self.grid[r][c] = self.blank
        AudioManager.play_sfx('pop')

    def get_remaining_colors(self):
        """Gets all distinct colors currently active on the board."""
        colors = set()
        for r in range(self.rows):
            for c in range(self.cols):
                b = self.grid[r][c]
                if b != self.blank:
                    colors.add(b.color)
        return list(colors)

    def is_empty(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != self.blank:
                    return False
        return True

    def check_lose(self, bottom_limit):
        """Returns True if any active bubble crosses bottom limits."""
        for r in range(self.rows):
            for c in range(self.cols):
                b = self.grid[r][c]
                if b != self.blank:
                    # Staggered offset compression adjustments
                    if b.vy + GameConfig.BUBBLE_RAD >= bottom_limit:
                        return True
        return False
