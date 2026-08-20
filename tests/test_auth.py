# tests/test_auth.py - Unit tests for the authentication, validators, and session manager systems

import unittest
import os
import json
from game.auth.validators import validate_name, validate_email, validate_password
from game.auth.auth_manager import hash_password, generate_salt, verify_password
from game.auth.session_manager import SessionManager
from game.storage.save_manager import SaveManager
from game.core.config import GameConfig

class TestAuthSystem(unittest.TestCase):
    def setUp(self):
        # Configure a temporary separate test save file path to prevent overwriting user saves
        self.original_save_file = GameConfig.SAVE_FILE
        GameConfig.SAVE_FILE = "test_save_data.json"
        
        # Reset singleton state
        SaveManager._data = None
        SaveManager._active_user = "guest"
        if os.path.exists(GameConfig.SAVE_FILE):
            os.remove(GameConfig.SAVE_FILE)

    def tearDown(self):
        if os.path.exists(GameConfig.SAVE_FILE):
            os.remove(GameConfig.SAVE_FILE)
        GameConfig.SAVE_FILE = self.original_save_file
        SaveManager._data = None

    def test_name_validation(self):
        self.assertIsNotNone(validate_name(""))
        self.assertIsNotNone(validate_name("A"))  # too short
        self.assertIsNone(validate_name("Devendra"))  # valid

    def test_email_validation(self):
        self.assertIsNotNone(validate_email(""))
        self.assertIsNotNone(validate_email("invalid-email"))
        self.assertIsNotNone(validate_email("invalid@domain"))
        self.assertIsNone(validate_email("user@gmail.com"))  # valid

    def test_password_validation(self):
        self.assertIsNotNone(validate_password("", ""))
        self.assertIsNotNone(validate_password("123", "123"))  # too short
        self.assertIsNotNone(validate_password("123456", "123457"))  # mismatch
        self.assertIsNone(validate_password("123456", "123456"))  # valid

    def test_password_hashing(self):
        pwd = "SecretPassword123"
        salt = generate_salt()
        
        # Verify salt uniqueness
        salt2 = generate_salt()
        self.assertNotEqual(salt, salt2)

        # Hash and check verification
        hashed = hash_password(pwd, salt)
        self.assertTrue(verify_password(pwd, hashed, salt))
        
        # Check invalid password mismatch
        self.assertFalse(verify_password("WrongPassword123", hashed, salt))

    def test_session_manager_flow(self):
        # 1. Initialize empty game save
        SaveManager.load_game()
        self.assertEqual(SaveManager.get_active_user(), "guest")

        # 2. Modify guest progress (simulate gameplay in guest mode)
        SaveManager.update_progress(level=2, score=5000, stars=3)
        self.assertEqual(SaveManager.get_progress()[0], 3)  # Next unlocked should be 3
        self.assertEqual(SaveManager.get_progress()[1], 5000)

        # 3. Register user and verify guest progress auto-merges
        success, msg = SessionManager.register_user("Player One", "player1@test.com", "Password123")
        self.assertTrue(success)
        self.assertEqual(SaveManager.get_active_user(), "player1@test.com")

        # Verify progress was migrated to the new user account
        unlocked, high_score, stars_map = SaveManager.get_progress()
        self.assertEqual(unlocked, 3)
        self.assertEqual(high_score, 5000)
        self.assertEqual(stars_map.get("2"), 3)

        # Verify guest progress was reset
        SaveManager.set_active_user("guest")
        unlocked_g, high_score_g, _ = SaveManager.get_progress()
        self.assertEqual(unlocked_g, 1)
        self.assertEqual(high_score_g, 0)

        # 4. Test Logout
        SessionManager.logout()
        self.assertEqual(SaveManager.get_active_user(), "guest")

        # 5. Test Login
        success, msg = SessionManager.login_user("player1@test.com", "Password123")
        self.assertTrue(success)
        self.assertEqual(SaveManager.get_active_user(), "player1@test.com")

        # Test invalid password login failure
        success, msg = SessionManager.login_user("player1@test.com", "WrongPassword")
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
