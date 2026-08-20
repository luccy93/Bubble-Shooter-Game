# game/storage/save_manager.py - Local storage and save validation

import json
import os
from game.core.config import GameConfig

class SaveManager:
    _data = None

    @classmethod
    def load_game(cls):
        """Loads save game data from local JSON storage with robust validation."""
        if cls._data is not None:
            return cls._data

        default_data = {
            "version": 1,
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},  # "level_id": stars (0-3)
            "settings": {
                "music": True,
                "sfx": True,
                "vibration": True
            },
            "stats": {
                "games_played": 0,
                "levels_completed": 0,
                "bubbles_popped": 0,
                "bubbles_dropped": 0,
                "highest_score": 0,
                "highest_combo": 0,
                "play_time_sec": 0
            },
            "achievements": []  # List of unlocked achievement IDs
        }

        if not os.path.exists(GameConfig.SAVE_FILE):
            cls._data = default_data
            cls.save_game()
            return cls._data

        try:
            with open(GameConfig.SAVE_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
            # Perform schema validation and bounds checks
            cls._data = cls._validate_and_sanitize(loaded, default_data)
        except Exception as e:
            # Fallback to default data if file is corrupted
            cls._data = default_data
            cls.save_game()

        return cls._data

    @classmethod
    def _validate_and_sanitize(cls, data, defaults):
        """Ensures all expected keys exist and holds valid bounded values."""
        sanitized = {}
        
        # Versioning check
        try:
            sanitized["version"] = int(data.get("version", defaults["version"]))
        except (ValueError, TypeError):
            sanitized["version"] = defaults["version"]
        
        # Progression bounds validation
        try:
            unlocked = int(data.get("unlocked_level", 1))
        except (ValueError, TypeError):
            unlocked = 1
        sanitized["unlocked_level"] = max(1, min(unlocked, 100))
        
        try:
            high_score = int(data.get("high_score", 0))
        except (ValueError, TypeError):
            high_score = 0
        sanitized["high_score"] = max(0, high_score)

        # Star bounds validation (0-3)
        stars = data.get("stars", {})
        sanitized["stars"] = {}
        for lvl_str, val in stars.items():
            try:
                lvl = int(lvl_str)
                s = max(0, min(int(val), 3))
                sanitized["stars"][str(lvl)] = s
            except (ValueError, TypeError):
                continue

        # Settings validation
        settings = data.get("settings", {})
        sanitized["settings"] = {
            "music": bool(settings.get("music", defaults["settings"]["music"])),
            "sfx": bool(settings.get("sfx", defaults["settings"]["sfx"])),
            "vibration": bool(settings.get("vibration", defaults["settings"]["vibration"]))
        }

        # Stats validation
        stats = data.get("stats", {})
        defaults_stats = defaults["stats"]
        sanitized["stats"] = {}
        for key, def_val in defaults_stats.items():
            val = stats.get(key, def_val)
            try:
                sanitized["stats"][key] = max(0, int(val))
            except (ValueError, TypeError):
                sanitized["stats"][key] = def_val

        # Achievements validation
        achievements = data.get("achievements", [])
        sanitized["achievements"] = [str(a) for a in achievements]

        return sanitized

    @classmethod
    def save_game(cls):
        """Saves current state atomically using a temporary file to prevent corruption."""
        if cls._data is None:
            return

        temp_file = GameConfig.SAVE_FILE + ".tmp"
        try:
            # Safe write to temp file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cls._data, f, indent=4)
            # Atomically replace old file
            if os.path.exists(GameConfig.SAVE_FILE):
                os.remove(GameConfig.SAVE_FILE)
            os.rename(temp_file, GameConfig.SAVE_FILE)
        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    @classmethod
    def get_progress(cls):
        data = cls.load_game()
        return data["unlocked_level"], data["high_score"], data["stars"]

    @classmethod
    def update_progress(cls, level, score, stars):
        data = cls.load_game()
        data["stars"][str(level)] = max(data["stars"].get(str(level), 0), stars)
        data["high_score"] = max(data["high_score"], score)
        if level >= data["unlocked_level"]:
            data["unlocked_level"] = min(level + 1, 15)  # Cap at max level 15
        cls.save_game()

    @classmethod
    def get_settings(cls):
        data = cls.load_game()
        return data["settings"]

    @classmethod
    def save_settings(cls, music, sfx, vibration):
        data = cls.load_game()
        data["settings"]["music"] = music
        data["settings"]["sfx"] = sfx
        data["settings"]["vibration"] = vibration
        cls.save_game()

    @classmethod
    def update_stats(cls, **kwargs):
        data = cls.load_game()
        for key, val in kwargs.items():
            if key in data["stats"]:
                if key in ["highest_score", "highest_combo"]:
                    data["stats"][key] = max(data["stats"][key], val)
                else:
                    data["stats"][key] += val
        cls.save_game()

    @classmethod
    def unlock_achievement(cls, ach_id):
        data = cls.load_game()
        if ach_id not in data["achievements"]:
            data["achievements"].append(ach_id)
            cls.save_game()
            return True
        return False

    @classmethod
    def reset_progress(cls):
        """Resets progress settings to default values."""
        cls._data = None
        if os.path.exists(GameConfig.SAVE_FILE):
            try:
                os.remove(GameConfig.SAVE_FILE)
            except OSError:
                pass
        cls.load_game()
