# game/scenes/auth_screens.py - Sign Up and Sign In with glassmorphism, Stitch design
# All auth logic (SessionManager, validators) remains 100% untouched.

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button, InputField
from game.ui.design_system import (draw_gradient_bg, draw_glass_panel,
                                    create_ambient_bubbles, update_ambient_bubbles,
                                    draw_ambient_bubbles)
from game.auth.session_manager import SessionManager
from game.auth.validators import validate_name, validate_email, validate_password


class SignInScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)

        self.email_input = InputField("Email address", w=280, h=46)
        self.pass_input = InputField("Password", w=280, h=46, is_password=True)

        self.submit_btn = Button("SIGN IN", w=260, h=50,
                                 bg_color=GameConfig.COLOR_PRIMARY, hero=True)
        self.back_btn = Button("← BACK", w=120, h=36,
                               bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.signup_link = Button("Don't have an account? SIGN UP", w=280, h=30,
                                  bg_color=GameConfig.COLOR_BG, font_size=12)

        self.error_msg = ""
        self.success_msg = ""
        self.bubbles = create_ambient_bubbles(6)
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("Welcome")
                return

        cx = GameConfig.VIRTUAL_WIDTH / 2
        self.email_input.handle_event(event, cx, 300)
        self.pass_input.handle_event(event, cx, 370)

        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("Welcome")
        elif self.signup_link.handle_event(event, cx, 540):
            self.manager.change_scene("SignUp")
        elif self.submit_btn.handle_event(event, cx, 460):
            self.attempt_login()

    def attempt_login(self):
        email = self.email_input.text
        password = self.pass_input.text

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
            self.manager.change_scene("MainMenu")
        else:
            self.error_msg = msg

    def update(self, dt):
        update_ambient_bubbles(self.bubbles, dt)

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(42, 27, 77),
                             bot_color=(15, 13, 23), radial=True)
        surface.blit(self._bg_surface, (0, 0))
        draw_ambient_bubbles(surface, self.bubbles)

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Header
        Label("SIGN IN", size=32, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 160)
        Label("Enter your credentials", size=14,
              color=GameConfig.COLOR_TEXT_MUTED).draw(surface, cx, 210)

        # Glass panel container for form
        panel_w = int(320 * GameConfig.scale_x)
        panel_h = int(220 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(260) - int(10 * GameConfig.scale_y)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=60, radius=int(20 * min(GameConfig.scale_x, GameConfig.scale_y)))

        # Fields
        self.email_input.draw(surface, cx, 300)
        self.pass_input.draw(surface, cx, 370)

        # Messages
        if self.error_msg:
            Label(self.error_msg, size=12, color=GameConfig.COLOR_FAILURE).draw(surface, cx, 420)
        elif self.success_msg:
            Label(self.success_msg, size=12, color=GameConfig.COLOR_SUCCESS).draw(surface, cx, 420)

        # Buttons
        self.submit_btn.draw(surface, cx, 460)
        self.signup_link.draw(surface, cx, 540)
        self.back_btn.draw(surface, 80, 50)


class SignUpScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)

        self.name_input = InputField("Name", w=280, h=42)
        self.email_input = InputField("Email address", w=280, h=42)
        self.pass_input = InputField("Password (min 6 char)", w=280, h=42, is_password=True)
        self.confirm_input = InputField("Confirm Password", w=280, h=42, is_password=True)

        self.submit_btn = Button("CREATE ACCOUNT", w=260, h=50,
                                 bg_color=GameConfig.COLOR_SUCCESS, hero=True)
        self.back_btn = Button("← BACK", w=120, h=36,
                               bg_color=GameConfig.COLOR_SURFACE_HIGH)
        self.signin_link = Button("Already have an account? SIGN IN", w=280, h=30,
                                  bg_color=GameConfig.COLOR_BG, font_size=12)

        self.error_msg = ""
        self.success_msg = ""
        self.bubbles = create_ambient_bubbles(6)
        self._bg_surface = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                self.manager.change_scene("Welcome")
                return

        cx = GameConfig.VIRTUAL_WIDTH / 2
        self.name_input.handle_event(event, cx, 240)
        self.email_input.handle_event(event, cx, 300)
        self.pass_input.handle_event(event, cx, 360)
        self.confirm_input.handle_event(event, cx, 420)

        if self.back_btn.handle_event(event, 80, 50):
            self.manager.change_scene("Welcome")
        elif self.signin_link.handle_event(event, cx, 580):
            self.manager.change_scene("SignIn")
        elif self.submit_btn.handle_event(event, cx, 510):
            self.attempt_signup()

    def attempt_signup(self):
        name = self.name_input.text
        email = self.email_input.text
        password = self.pass_input.text
        confirm = self.confirm_input.text

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

        success, msg = SessionManager.register_user(name, email, password)
        if success:
            self.error_msg = ""
            self.success_msg = msg
            self.manager.change_scene("MainMenu")
        else:
            self.error_msg = msg

    def update(self, dt):
        update_ambient_bubbles(self.bubbles, dt)

    def draw(self, surface):
        if self._bg_surface is None or self._bg_surface.get_size() != surface.get_size():
            self._bg_surface = surface.copy()
            draw_gradient_bg(self._bg_surface, top_color=(42, 27, 77),
                             bot_color=(15, 13, 23), radial=True)
        surface.blit(self._bg_surface, (0, 0))
        draw_ambient_bubbles(surface, self.bubbles)

        cx = GameConfig.VIRTUAL_WIDTH / 2

        # Header
        Label("SIGN UP", size=32, title=True, glow=True,
              color=GameConfig.COLOR_PRIMARY_LIGHT).draw(surface, cx, 130)
        Label("Create your profile", size=14,
              color=GameConfig.COLOR_TEXT_MUTED).draw(surface, cx, 175)

        # Glass form container
        panel_w = int(320 * GameConfig.scale_x)
        panel_h = int(310 * GameConfig.scale_y)
        panel_x = GameConfig.to_screen_x(cx) - panel_w // 2
        panel_y = GameConfig.to_screen_y(210) - int(10 * GameConfig.scale_y)
        draw_glass_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                         opacity=60, radius=int(20 * min(GameConfig.scale_x, GameConfig.scale_y)))

        # Fields
        self.name_input.draw(surface, cx, 240)
        self.email_input.draw(surface, cx, 300)
        self.pass_input.draw(surface, cx, 360)
        self.confirm_input.draw(surface, cx, 420)

        # Error display
        if self.error_msg:
            Label(self.error_msg, size=12, color=GameConfig.COLOR_FAILURE).draw(surface, cx, 465)
        elif self.success_msg:
            Label(self.success_msg, size=12, color=GameConfig.COLOR_SUCCESS).draw(surface, cx, 465)

        # Buttons
        self.submit_btn.draw(surface, cx, 510)
        self.signin_link.draw(surface, cx, 580)
        self.back_btn.draw(surface, 80, 50)
