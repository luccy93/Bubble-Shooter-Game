# game/scenes/auth_screens.py - Forms and validation logic for Sign Up and Sign In

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button, InputField
from game.auth.session_manager import SessionManager
from game.auth.validators import validate_name, validate_email, validate_password

class SignInScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.email_input = InputField("Email address", w=260, h=44)
        self.pass_input = InputField("Password", w=260, h=44, is_password=True)

        self.submit_btn = Button("SIGN IN", w=220, h=48, bg_color=GameConfig.COLOR_PRIMARY)
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.signup_link = Button("Don't have an account? SIGN UP", w=260, h=30, bg_color=GameConfig.COLOR_BG, font_size=12)

        self.error_msg = ""
        self.success_msg = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("Welcome")
                return

        # Forward inputs to focus text fields
        self.email_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 280)
        self.pass_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 350)

        # Handle buttons
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("Welcome")
        elif self.signup_link.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 520):
            self.manager.change_scene("SignUp")
        elif self.submit_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 440):
            self.attempt_login()

    def attempt_login(self):
        email = self.email_input.text
        password = self.pass_input.text

        # Validate inputs
        email_err = validate_email(email)
        if email_err:
            self.error_msg = email_err
            return

        if not password:
            self.error_msg = "Password is required."
            return

        success, msg = SessionManager.login_user(email, password)
        if success:
            self.error_msg = ""
            self.success_msg = msg
            # Transition to MainMenu on success
            self.manager.change_scene("MainMenu")
        else:
            self.error_msg = msg

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Header Title
        Label("SIGN IN", size=32, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 160)
        Label("Enter your credentials", size=14, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 210
        )

        # Fields
        self.email_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 280)
        self.pass_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 350)

        # Messages (Error/Success feedback)
        if self.error_msg:
            Label(self.error_msg, size=12, color=GameConfig.COLOR_FAILURE).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, 400
            )
        elif self.success_msg:
            Label(self.success_msg, size=12, color=GameConfig.COLOR_SUCCESS).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, 400
            )

        # Buttons
        self.submit_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 440)
        self.signup_link.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 520)
        self.back_btn.draw(surface, 80, 50)


class SignUpScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.name_input = InputField("Name", w=260, h=40)
        self.email_input = InputField("Email address", w=260, h=40)
        self.pass_input = InputField("Password (min 6 char)", w=260, h=40, is_password=True)
        self.confirm_input = InputField("Confirm Password", w=260, h=40, is_password=True)

        self.submit_btn = Button("CREATE ACCOUNT", w=220, h=48, bg_color=GameConfig.COLOR_SUCCESS)
        self.back_btn = Button("← BACK", w=120, h=36, bg_color=GameConfig.COLOR_BG_LIGHT)
        self.signin_link = Button("Already have an account? SIGN IN", w=260, h=30, bg_color=GameConfig.COLOR_BG, font_size=12)

        self.error_msg = ""
        self.success_msg = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("Welcome")
                return

        # Forward input highlights
        self.name_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 230)
        self.email_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 290)
        self.pass_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 350)
        self.confirm_input.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 410)

        # Handle actions
        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("Welcome")
        elif self.signin_link.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 555):
            self.manager.change_scene("SignIn")
        elif self.submit_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 490):
            self.attempt_signup()

    def attempt_signup(self):
        name = self.name_input.text
        email = self.email_input.text
        password = self.pass_input.text
        confirm = self.confirm_input.text

        # Validate entries
        name_err = validate_name(name)
        if name_err:
            self.error_msg = name_err
            return

        email_err = validate_email(email)
        if email_err:
            self.error_msg = email_err
            return

        pass_err = validate_password(password, confirm)
        if pass_err:
            self.error_msg = pass_err
            return

        # Perform sign-up and merge local progress automatically
        success, msg = SessionManager.register_user(name, email, password)
        if success:
            self.error_msg = ""
            self.success_msg = msg
            self.manager.change_scene("MainMenu")
        else:
            self.error_msg = msg

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Header Title
        Label("SIGN UP", size=32, title=True).draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 130)
        Label("Create your profile", size=14, color=GameConfig.COLOR_TEXT_MUTED).draw(
            surface, GameConfig.VIRTUAL_WIDTH / 2, 175
        )

        # Fields
        self.name_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 230)
        self.email_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 290)
        self.pass_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 350)
        self.confirm_input.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 410)

        # Error display
        if self.error_msg:
            Label(self.error_msg, size=12, color=GameConfig.COLOR_FAILURE).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, 452
            )
        elif self.success_msg:
            Label(self.success_msg, size=12, color=GameConfig.COLOR_SUCCESS).draw(
                surface, GameConfig.VIRTUAL_WIDTH / 2, 452
            )

        # Buttons
        self.submit_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 490)
        self.signin_link.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 555)
        self.back_btn.draw(surface, 80, 50)
