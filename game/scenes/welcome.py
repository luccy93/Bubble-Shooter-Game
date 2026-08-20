# game/scenes/welcome.py - Entry portal selecting Guest mode or Accounts login/signup

import pygame
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label, Button
from game.auth.session_manager import SessionManager

class WelcomeScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.title_label = Label("WELCOME", size=36, title=True, color=GameConfig.COLOR_PRIMARY)
        self.sub_label = Label("Select your play mode", size=15, color=GameConfig.COLOR_TEXT_MUTED)

        # Main options buttons
        self.guest_btn = Button("🎮 PLAY AS GUEST", w=220, h=52, bg_color=GameConfig.COLOR_PRIMARY)
        self.login_btn = Button("🔑 SIGN IN", w=220, h=48)
        self.signup_btn = Button("📝 SIGN UP", w=220, h=48, bg_color=GameConfig.COLOR_BG_LIGHT)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_AC_BACK]:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        # Button clicks routing
        if self.guest_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 340):
            # Ensure guest user is active
            SessionManager.logout()
            self.manager.change_scene("MainMenu")
        elif self.login_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 420):
            self.manager.change_scene("SignIn")
        elif self.signup_btn.handle_event(event, GameConfig.VIRTUAL_WIDTH / 2, 490):
            self.manager.change_scene("SignUp")

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Draw branding headers
        self.title_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 180)
        self.sub_label.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 230)

        # Draw buttons
        self.guest_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 340)
        self.login_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 420)
        self.signup_btn.draw(surface, GameConfig.VIRTUAL_WIDTH / 2, 490)
