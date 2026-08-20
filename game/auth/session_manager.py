# game/auth/session_manager.py - User session logins, registrations, and guest migrations

import re
from game.storage.save_manager import SaveManager
from game.auth.auth_manager import hash_password, generate_salt, verify_password

class SessionManager:
    @classmethod
    def register_user(cls, name, email, password):
        """Creates a new local user account and optionally merges guest progress."""
        data = SaveManager.load_game()
        normalized_email = email.strip().lower()

        if normalized_email in data["accounts"]:
            return False, "An account with this email already exists."

        # Generate secure credentials
        salt = generate_salt()
        pwd_hash = hash_password(password, salt)

        # 1. Base profile structure
        new_profile = {
            "name": name.strip(),
            "password_hash": pwd_hash,
            "salt": salt,
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},
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

        # 2. Merge offline Guest progress if present
        guest = data["accounts"].get("guest")
        if guest:
            # Merge stars (taking maximum score/stars)
            for lvl, stars in guest.get("stars", {}).items():
                new_profile["stars"][lvl] = max(new_profile["stars"].get(lvl, 0), stars)
            
            new_profile["unlocked_level"] = max(new_profile["unlocked_level"], guest.get("unlocked_level", 1))
            new_profile["high_score"] = max(new_profile["high_score"], guest.get("high_score", 0))

            # Merge stats metrics
            for key, val in guest.get("stats", {}).items():
                if key in ["highest_score", "highest_combo"]:
                    new_profile["stats"][key] = max(new_profile["stats"][key], val)
                else:
                    new_profile["stats"][key] += val

            # Merge achievements list
            new_profile["achievements"] = list(set(new_profile["achievements"] + guest.get("achievements", [])))

            # Clear guest progress after merge to prevent duplicate transfers
            cls.clear_guest_progress()

        # Save account
        data["accounts"][normalized_email] = new_profile
        SaveManager.save_game()
        
        # Log in automatically
        SaveManager.set_active_user(normalized_email)
        return True, "Account created successfully."

    @classmethod
    def login_user(cls, email, password):
        """Verifies email/password and sets active user session."""
        data = SaveManager.load_game()
        normalized_email = email.strip().lower()

        if normalized_email not in data["accounts"] or normalized_email == "guest":
            return False, "Invalid email or password."

        profile = data["accounts"][normalized_email]
        stored_hash = profile["password_hash"]
        salt = profile["salt"]

        if verify_password(password, stored_hash, salt):
            SaveManager.set_active_user(normalized_email)
            return True, "Login successful."
        return False, "Invalid email or password."

    @classmethod
    def logout(cls):
        """Logs active user out, reverting session back to local guest mode."""
        SaveManager.set_active_user("guest")

    @classmethod
    def clear_guest_progress(cls):
        """Helper to reset guest account properties after account merge."""
        data = SaveManager.load_game()
        guest = data["accounts"]["guest"]
        guest.update({
            "unlocked_level": 1,
            "high_score": 0,
            "stars": {},
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
        })
        SaveManager.save_game()
