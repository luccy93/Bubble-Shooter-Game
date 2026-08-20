# game/levels/level_manager.py - Loads, validates, and manages worlds and levels

import json
import os
from game.core.config import GameConfig

class LevelManager:
    _data = None

    WORLDS_CONFIG = [
        {"id": 0, "name": "Forest Valley", "icon": "🌿", "bg_top": [11, 61, 11], "bg_bot": [26, 74, 26]},
        {"id": 1, "name": "Sunset Desert", "icon": "🏜️", "bg_top": [74, 37, 18], "bg_bot": [45, 24, 16]},
        {"id": 2, "name": "Crystal Cave", "icon": "💎", "bg_top": [10, 22, 40], "bg_bot": [15, 40, 71]},
        {"id": 3, "name": "Ice Kingdom", "icon": "❄️", "bg_top": [30, 60, 90], "bg_bot": [10, 25, 45]},
        {"id": 4, "name": "Sky Kingdom", "icon": "☁️", "bg_top": [50, 80, 110], "bg_bot": [20, 35, 55]},
        {"id": 5, "name": "Volcanic Land", "icon": "🌋", "bg_top": [80, 20, 10], "bg_bot": [40, 10, 5]},
        {"id": 6, "name": "Ocean World", "icon": "🌊", "bg_top": [10, 50, 80], "bg_bot": [5, 25, 40]},
        {"id": 7, "name": "Mystic Ruins", "icon": "🏛️", "bg_top": [40, 30, 50], "bg_bot": [20, 15, 25]}
    ]

    @classmethod
    def load_levels(cls):
        """Loads and validates level data from JSON file."""
        if cls._data is not None:
            return cls._data

        json_path = os.path.join(GameConfig.BASE_DIR, 'game', 'levels', 'levels.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cls._data = json.load(f)
        except Exception:
            # Fallback level in case of read error (safety first)
            cls._data = {
                "worlds": cls.WORLDS_CONFIG[:3],
                "levels": [
                    {
                        "id": 1,
                        "world": 0,
                        "moves": 20,
                        "stars": [1000, 2000, 3000],
                        "grid": [
                            [0, 0, 1, 1, 2, 2, 3, 3],
                            [0, 1, 1, 2, 2, 3, 3]
                        ],
                        "objective": {"type": "clear_board"}
                    }
                ]
            }
        return cls._data

    @classmethod
    def get_worlds(cls):
        return cls.WORLDS_CONFIG

    @classmethod
    def get_world(cls, world_id):
        for w in cls.WORLDS_CONFIG:
            if w["id"] == world_id:
                return w
        return cls.WORLDS_CONFIG[0]

    @classmethod
    def get_levels_for_world(cls, world_id):
        # Allow levels up to 3000 to be queried per world
        # Forest Valley has 1-15, Desert 16-30, etc.
        # So we show 15 levels per world!
        levels = []
        for i in range(15):
            lvl_id = world_id * 15 + i + 1
            levels.append(cls.get_level(lvl_id))
        return levels

    @classmethod
    def get_level(cls, level_id):
        data = cls.load_levels()
        
        # 1. Search hand-crafted level from JSON first (levels 1 to 15)
        for l in data["levels"]:
            if l["id"] == level_id:
                # Add default objective if missing
                if "objective" not in l:
                    l["objective"] = {"type": "clear_board"}
                return l

        # 2. Procedural Generation for levels > 15
        import random
        # Seed generator based on level_id to make it deterministic!
        rng = random.Random(level_id)

        # 15 levels per world
        world_id = min((level_id - 1) // 15, 7)
        moves = max(16, min(36, 20 + (level_id % 6)))
        stars = [moves * 120, moves * 210, moves * 320]

        # Winding rows count scaling
        rows_cnt = min(7, 4 + (level_id // 40))
        color_pool_size = min(6, 3 + (level_id // 50))
        
        # Decide objective type based on level seed
        obj_type = rng.choice(["clear_board", "rescue", "score"])
        objective = {"type": obj_type}
        if obj_type == "score":
            objective["target"] = stars[1]  # Must reach 2-star threshold
        elif obj_type == "rescue":
            objective["target"] = rng.randint(2, 4)

        grid = []
        for r in range(rows_cnt):
            cols_cnt = 8 if r % 2 == 0 else 7
            row = []
            for c in range(cols_cnt):
                # Put empty spaces or obstacles occasionally
                if r == 0:
                    # Ceiling should have bubbles
                    row.append(rng.randint(0, color_pool_size - 1))
                else:
                    chance = rng.random()
                    if chance < 0.15:
                        row.append(-1)  # Empty space
                    elif chance < 0.20 and level_id > 20:
                        row.append(7)  # Stone bubble obstacle (grey/color 7)
                    else:
                        row.append(rng.randint(0, color_pool_size - 1))
            grid.append(row)

        # If rescue objective, place pet nodes (color index 9 / rescue) in grid
        if obj_type == "rescue":
            placed = 0
            target_placed = objective["target"]
            # Loop from bottom row to top to replace some normal bubbles with rescue pets (9)
            for r in range(rows_cnt - 1, 0, -1):
                if placed >= target_placed:
                    break
                for c in range(len(grid[r])):
                    if grid[r][c] >= 0 and grid[r][c] != 7:
                        grid[r][c] = 9  # 9 indicates Rescue Bubble
                        placed += 1
                        if placed >= target_placed:
                            break

        return {
            "id": level_id,
            "world": world_id,
            "moves": moves,
            "stars": stars,
            "grid": grid,
            "objective": objective
        }

    @classmethod
    def get_total_levels(cls):
        return 120  # Map contains 8 worlds * 15 levels = 120 levels scroll path!

    @classmethod
    def calculate_stars(cls, level_id, score):
        level = cls.get_level(level_id)
        thresholds = level["stars"]
        if score >= thresholds[2]:
            return 3
        elif score >= thresholds[1]:
            return 2
        elif score >= thresholds[0]:
            return 1
        return 0
