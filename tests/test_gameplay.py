# tests/test_gameplay.py - Unit tests for board mechanics, level loading, and save validations

import unittest
import sys
import os

# Append project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.core.config import GameConfig
from game.gameplay.board import Board
from game.entities.bubble import Bubble
from game.levels.level_manager import LevelManager
from game.storage.save_manager import SaveManager

class TestGameplayMechanics(unittest.TestCase):
    def setUp(self):
        # Setup config boundaries for tests
        GameConfig.board_x = 25
        GameConfig.board_y = 60
        
        self.board = Board(rows=6, cols=6)

    def test_neighbors_even_row(self):
        # Neighbor coordinate checks for row 0 (even)
        neighbors = self.board.get_neighbors(0, 1)
        # Expected: (0,0), (0,2), (1,1), (1,0) (and -1 rows are out of bounds)
        self.assertIn((0, 0), neighbors)
        self.assertIn((0, 2), neighbors)
        self.assertIn((1, 1), neighbors)
        self.assertIn((1, 0), neighbors)
        self.assertNotIn((-1, 1), neighbors)

    def test_neighbors_odd_row(self):
        # Neighbor coordinate checks for row 1 (odd)
        neighbors = self.board.get_neighbors(1, 1)
        # Expected: (1,0), (1,2), (0,1), (0,2), (2,1), (2,2)
        self.assertIn((1, 0), neighbors)
        self.assertIn((1, 2), neighbors)
        self.assertIn((0, 1), neighbors)
        self.assertIn((0, 2), neighbors)
        self.assertIn((2, 1), neighbors)
        self.assertIn((2, 2), neighbors)

    def test_color_matching_cluster(self):
        # Manually inject adjacent same-color bubbles
        red_color = (255, 59, 48)
        self.board.grid[0][0] = Bubble(red_color, row=0, col=0)
        self.board.grid[0][1] = Bubble(red_color, row=0, col=1)
        self.board.grid[1][0] = Bubble(red_color, row=1, col=0) # Neighbor of (0,0) and (0,1)
        
        matches = self.board.check_matches(0, 0, red_color)
        self.assertEqual(len(matches), 3)
        self.assertIn((0, 0), matches)
        self.assertIn((0, 1), matches)
        self.assertIn((1, 0), matches)

    def test_floating_clusters_drop(self):
        red_color = (255, 59, 48)
        blue_color = (0, 122, 255)
        
        # Row 0 (attached to ceiling)
        self.board.grid[0][0] = Bubble(red_color, row=0, col=0)
        
        # Connected branch
        self.board.grid[1][0] = Bubble(red_color, row=1, col=0)
        
        # Disconnected float branch (Row 3, no path to Row 0)
        self.board.grid[3][0] = Bubble(blue_color, row=3, col=0)
        self.board.grid[3][1] = Bubble(blue_color, row=3, col=1)

        floaters = self.board.check_floaters()
        self.assertEqual(len(floaters), 2)
        self.assertIn((3, 0), floaters)
        self.assertIn((3, 1), floaters)
        self.assertNotIn((0, 0), floaters)
        self.assertNotIn((1, 0), floaters)

    def test_level_manager_loading(self):
        LevelManager.load_levels()
        self.assertGreaterEqual(LevelManager.get_total_levels(), 1)
        
        lvl = LevelManager.get_level(1)
        self.assertEqual(lvl["id"], 1)
        self.assertIn("moves", lvl)
        self.assertIn("grid", lvl)

    def test_save_manager_validation(self):
        invalid_data = {
            "version": "wrong_type",
            "unlocked_level": -10,  # Below bound
            "high_score": "15000",  # String instead of int
            "stars": {"1": "5", "invalid": 2}, # Stars cap at 3
            "settings": {"music": "yes"},
            "stats": {"bubbles_popped": -50}
        }
        
        defaults = {
            "version": 1,
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},
            "settings": {"music": True, "sfx": True, "vibration": True},
            "stats": {"games_played": 0, "levels_completed": 0, "bubbles_popped": 0, "bubbles_dropped": 0, "highest_score": 0, "highest_combo": 0, "play_time_sec": 0},
            "achievements": []
        }
        
        sanitized = SaveManager._validate_and_sanitize(invalid_data, defaults)
        self.assertEqual(sanitized["unlocked_level"], 1)
        self.assertEqual(sanitized["high_score"], 15000)
        self.assertEqual(sanitized["stars"]["1"], 3) # Clamped from 5 to 3
        self.assertNotIn("invalid", sanitized["stars"])
        self.assertEqual(sanitized["settings"]["music"], True) # Fallback to default bool
        self.assertEqual(sanitized["stats"]["bubbles_popped"], 0) # Non-negative bounds clamped

if __name__ == '__main__':
    unittest.main()
