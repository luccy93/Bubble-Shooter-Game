# game/storage/save_manager.py - Local storage with multi-account support and data validation

import json
import os
from game.core.config import GameConfig

class SaveManager:
    _data = None
    _active_user = "guest"  # Key for current user session ("guest" or email string)

    @classmethod
    def load_game(cls):
        """Loads save game data from local JSON storage with robust validation."""
        if cls._data is not None:
            return cls._data

        default_profile = {
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},  # "level_id": stars (0-3)
            "coins": 200,
            "boosters": {
                "bomb": 3,
                "lightning": 3,
                "rainbow": 3,
                "fireball": 3
            },
            "last_claim_date": "",
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

        default_data = {
            "version": 1,
            "active_user": "guest",
            "global_settings": {
                "music": True,
                "sfx": True,
                "vibration": True
            },
            "accounts": {
                "guest": {
                    "name": "Guest",
                    "password_hash": "",
                    "salt": "",
                    **default_profile
                }
            }
        }

        if not os.path.exists(GameConfig.SAVE_FILE):
            cls._data = default_data
            cls._active_user = "guest"
            cls.save_game()
            return cls._data

        try:
            with open(GameConfig.SAVE_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            cls._data = cls._validate_and_sanitize(loaded, default_data)
            cls._active_user = cls._data.get("active_user", "guest")
        except Exception:
            cls._data = default_data
            cls._active_user = "guest"
            cls.save_game()

        return cls._data

    @classmethod
    def _validate_and_sanitize(cls, data, defaults):
        """Ensures all expected keys exist and holds valid bounded values across all accounts."""
        # 1. Backward-compatible check for legacy structure (used in unit tests)
        if "accounts" not in defaults:
            sanitized = {}
            try:
                sanitized["version"] = int(data.get("version", defaults["version"]))
            except (ValueError, TypeError):
                sanitized["version"] = defaults["version"]

            try:
                unlocked = int(data.get("unlocked_level", defaults.get("unlocked_level", 1)))
            except (ValueError, TypeError):
                unlocked = 1
            sanitized["unlocked_level"] = max(1, min(unlocked, 100))

            try:
                high_score = int(data.get("high_score", defaults.get("high_score", 0)))
            except (ValueError, TypeError):
                high_score = 0
            sanitized["high_score"] = max(0, high_score)

            stars = data.get("stars", {})
            sanitized["stars"] = {}
            for lvl_str, val in stars.items():
                try:
                    lvl = int(lvl_str)
                    s = max(0, min(int(val), 3))
                    sanitized["stars"][str(lvl)] = s
                except (ValueError, TypeError):
                    continue

            settings = data.get("settings", {})
            sanitized["settings"] = {}
            for k, def_v in defaults.get("settings", {}).items():
                sanitized["settings"][k] = bool(settings.get(k, def_v))

            stats = data.get("stats", {})
            sanitized["stats"] = {}
            for k, def_v in defaults.get("stats", {}).items():
                val = stats.get(k, def_v)
                try:
                    sanitized["stats"][k] = max(0, int(val))
                except (ValueError, TypeError):
                    sanitized["stats"][k] = def_v

            achievements = data.get("achievements", [])
            sanitized["achievements"] = [str(a) for a in achievements]
            return sanitized

        # 2. Modern multi-account validation
        sanitized = {}
        
        # Versioning check
        try:
            sanitized["version"] = int(data.get("version", defaults["version"]))
        except (ValueError, TypeError):
            sanitized["version"] = defaults["version"]
        
        # Active user tracker
        active = data.get("active_user", "guest")
        sanitized["active_user"] = str(active)

        # Global settings validation
        g_settings = data.get("global_settings", data.get("settings", {}))
        def_settings = defaults.get("global_settings", defaults.get("settings", {"music": True, "sfx": True, "vibration": True}))
        sanitized["global_settings"] = {
            "music": bool(g_settings.get("music", def_settings["music"])),
            "sfx": bool(g_settings.get("sfx", def_settings["sfx"])),
            "vibration": bool(g_settings.get("vibration", def_settings["vibration"]))
        }

        # Accounts list validation
        accounts = data.get("accounts", {})
        sanitized["accounts"] = {}
        
        default_profile = defaults["accounts"]["guest"]

        for acc_key, acc_val in accounts.items():
            if not isinstance(acc_val, dict):
                continue
            
            p_san = {}
            p_san["name"] = str(acc_val.get("name", acc_key))
            p_san["password_hash"] = str(acc_val.get("password_hash", ""))
            p_san["salt"] = str(acc_val.get("salt", ""))

            # Progression limits
            try:
                unlocked = int(acc_val.get("unlocked_level", 1))
            except (ValueError, TypeError):
                unlocked = 1
            p_san["unlocked_level"] = max(1, min(unlocked, 3000))

            try:
                high_score = int(acc_val.get("high_score", 0))
            except (ValueError, TypeError):
                high_score = 0
            p_san["high_score"] = max(0, high_score)

            # Star mapping
            stars = acc_val.get("stars", {})
            p_san["stars"] = {}
            for lvl_str, val in stars.items():
                try:
                    lvl = int(lvl_str)
                    s = max(0, min(int(val), 3))
                    p_san["stars"][str(lvl)] = s
                except (ValueError, TypeError):
                    continue

            # Coins & Boosters
            try:
                p_san["coins"] = max(0, int(acc_val.get("coins", 200)))
            except (ValueError, TypeError):
                p_san["coins"] = 200

            p_san["boosters"] = {}
            boosters = acc_val.get("boosters", {})
            for b_type in ["bomb", "lightning", "rainbow", "fireball"]:
                try:
                    p_san["boosters"][b_type] = max(0, int(boosters.get(b_type, 3)))
                except (ValueError, TypeError):
                    p_san["boosters"][b_type] = 3

            p_san["last_claim_date"] = str(acc_val.get("last_claim_date", ""))

            # Stats validation
            stats = acc_val.get("stats", {})
            p_san["stats"] = {}
            for k, def_v in default_profile["stats"].items():
                val = stats.get(k, def_v)
                try:
                    p_san["stats"][k] = max(0, int(val))
                except (ValueError, TypeError):
                    p_san["stats"][k] = def_v

            # Achievements list
            achievements = acc_val.get("achievements", [])
            p_san["achievements"] = [str(a) for a in achievements]

            sanitized["accounts"][acc_key] = p_san

        # Fallback to verify guest account exists
        if "guest" not in sanitized["accounts"]:
            sanitized["accounts"]["guest"] = defaults["accounts"]["guest"]

        return sanitized

    @classmethod
    def get_active_user(cls):
        return cls._active_user

    @classmethod
    def set_active_user(cls, user_key):
        cls.load_game()
        if user_key in cls._data["accounts"]:
            cls._active_user = user_key
            cls._data["active_user"] = user_key
            cls.save_game()

    @classmethod
    def get_profile(cls):
        """Returns the dictionary profile of the currently active account."""
        data = cls.load_game()
        return data["accounts"][cls._active_user]

    @classmethod
    def get_progress(cls):
        profile = cls.get_profile()
        return profile["unlocked_level"], profile["high_score"], profile["stars"]

    @classmethod
    def update_progress(cls, level, score, stars):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        profile["stars"][str(level)] = max(profile["stars"].get(str(level), 0), stars)
        profile["high_score"] = max(profile["high_score"], score)
        if level >= profile["unlocked_level"]:
            profile["unlocked_level"] = min(level + 1, 3000)  # Expanded limit up to 3000
        cls.save_game()

    @classmethod
    def get_settings(cls):
        data = cls.load_game()
        return data["global_settings"]

    @classmethod
    def save_settings(cls, music, sfx, vibration):
        data = cls.load_game()
        data["global_settings"]["music"] = music
        data["global_settings"]["sfx"] = sfx
        data["global_settings"]["vibration"] = vibration
        cls.save_game()

    @classmethod
    def update_stats(cls, **kwargs):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        for key, val in kwargs.items():
            if key in profile["stats"]:
                if key in ["highest_score", "highest_combo"]:
                    profile["stats"][key] = max(profile["stats"][key], val)
                else:
                    profile["stats"][key] += val
        cls.save_game()

    @classmethod
    def unlock_achievement(cls, ach_id):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        if ach_id not in profile["achievements"]:
            profile["achievements"].append(ach_id)
            cls.save_game()
            return True
        return False

    @classmethod
    def get_coins(cls):
        profile = cls.get_profile()
        return profile.get("coins", 200)

    @classmethod
    def add_coins(cls, amount):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        profile["coins"] = max(0, profile.get("coins", 200) + amount)
        cls.save_game()

    @classmethod
    def get_boosters(cls):
        profile = cls.get_profile()
        return profile.get("boosters", {"bomb": 3, "lightning": 3, "rainbow": 3, "fireball": 3})

    @classmethod
    def add_booster(cls, b_type, count=1):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        boosters = profile.setdefault("boosters", {"bomb": 3, "lightning": 3, "rainbow": 3, "fireball": 3})
        boosters[b_type] = max(0, boosters.get(b_type, 3) + count)
        cls.save_game()

    @classmethod
    def use_booster(cls, b_type):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        boosters = profile.setdefault("boosters", {"bomb": 3, "lightning": 3, "rainbow": 3, "fireball": 3})
        if boosters.get(b_type, 0) > 0:
            boosters[b_type] -= 1
            cls.save_game()
            return True
        return False

    @classmethod
    def get_last_claim_date(cls):
        profile = cls.get_profile()
        return profile.get("last_claim_date", "")

    @classmethod
    def set_last_claim_date(cls, date_str):
        data = cls.load_game()
        profile = data["accounts"][cls._active_user]
        profile["last_claim_date"] = date_str
        cls.save_game()

    @classmethod
    def reset_progress(cls):
        """Resets the currently active profile to default blank values."""
        data = cls.load_game()
        default_profile = {
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},
            "coins": 200,
            "boosters": {
                "bomb": 3,
                "lightning": 3,
                "rainbow": 3,
                "fireball": 3
            },
            "last_claim_date": "",
            "stats": {
                "games_played": 0,
                "levels_completed": 0,
                "bubbles_popped": 0,
                "bubbles_dropped": 0,
                "highest_score": 0,
                "highest_combo": 0,
                "play_time_sec": 0
            },
            "achievements": []
        }
        data["accounts"][cls._active_user].update(default_profile)
        cls.save_game()

    @classmethod
    def save_game(cls):
        """Saves current state atomically using a temporary file to prevent corruption."""
        if cls._data is None:
            return

        temp_file = GameConfig.SAVE_FILE + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cls._data, f, indent=4)
            if os.path.exists(GameConfig.SAVE_FILE):
                os.remove(GameConfig.SAVE_FILE)
            os.rename(temp_file, GameConfig.SAVE_FILE)
        except Exception:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
