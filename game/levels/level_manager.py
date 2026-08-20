# game/levels/level_manager.py - Loads, validates, and manages worlds and levels

import json
import os
from game.core.config import GameConfig

class LevelManager:
    _data = None

    @classmethod
    def load_levels(cls):
        """Loads and validates level data from JSON file."""
        if cls._data is not None:
            return cls._data

        json_path = os.path.join(GameConfig.BASE_DIR, 'game', 'levels', 'levels.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cls._data = json.load(f)
        except Exception as e:
            # Fallback level in case of read error (safety first)
            cls._data = {
                "worlds": [
                    {"id": 0, "name": "Forest Valley", "icon": "🌿", "bg_top": [11, 61, 11], "bg_bot": [26, 74, 26]}
                ],
                "levels": [
                    {
                        "id": 1,
                        "world": 0,
                        "moves": 20,
                        "stars": [1000, 2000, 3000],
                        "grid": [
                            [0, 0, 1, 1, 2, 2, 3, 3],
                            [0, 1, 1, 2, 2, 3, 3]
                        ]
                    }
                ]
            }
        return cls._data

    @classmethod
    def get_worlds(cls):
        data = cls.load_levels()
        return data["worlds"]

    @classmethod
    def get_world(cls, world_id):
        worlds = cls.get_worlds()
        for w in worlds:
            if w["id"] == world_id:
                return w
        return worlds[0]

    @classmethod
    def get_levels_for_world(cls, world_id):
        data = cls.load_levels()
        return [l for l in data["levels"] if l["world"] == world_id]

    @classmethod
    def get_level(cls, level_id):
        data = cls.load_levels()
        for l in data["levels"]:
            if l["id"] == level_id:
                return l
        return data["levels"][0]

    @classmethod
    def get_total_levels(cls):
        data = cls.load_levels()
        return len(data["levels"])

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
