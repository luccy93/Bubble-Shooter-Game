# game/scenes/splash.py - Fading game splash launch scene

import pygame
import time
from game.scenes.base import BaseScene
from game.core.config import GameConfig
from game.ui.widgets import Label

class SplashScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.start_time = time.time()
        self.logo_label = Label("BUBBLE", size=48, title=True, color=GameConfig.COLOR_PRIMARY)
        self.sub_label = Label("SHOOTER", size=40, title=True, color=(255, 255, 255))
        self.alpha = 0
        self.fade_duration = 0.8
        self.display_duration = 1.2
        self.transitioning = False

    def handle_event(self, event):
        # Quick skip splash on click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.manager.change_scene("Welcome")

    def update(self, dt):
        elapsed = time.time() - self.start_time
        
        # Calculate fade alpha
        if elapsed < self.fade_duration:
            self.alpha = int((elapsed / self.fade_duration) * 255)
        elif elapsed < self.fade_duration + self.display_duration:
            self.alpha = 255
        elif elapsed < self.fade_duration * 2 + self.display_duration:
            fade_out_elapsed = elapsed - (self.fade_duration + self.display_duration)
            self.alpha = int((1.0 - (fade_out_elapsed / self.fade_duration)) * 255)
        else:
            self.alpha = 0
            if not self.transitioning:
                self.transitioning = True
                self.manager.change_scene("Welcome")

    def draw(self, surface):
        surface.fill(GameConfig.COLOR_BG)

        # Draw logo centered with alpha fade
        if self.alpha > 0:
            # Temporary alpha surface
            logo_surf = pygame.Surface((GameConfig.actual_width, GameConfig.actual_height), pygame.SRCALPHA)
            
            # Render labels onto temporary surface
            self.logo_label.draw(logo_surf, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 - 30)
            self.sub_label.draw(logo_surf, GameConfig.VIRTUAL_WIDTH / 2, GameConfig.VIRTUAL_HEIGHT / 2 + 30)
            
            # Apply alpha factor
            logo_surf.set_alpha(self.alpha)
            surface.blit(logo_surf, (0, 0))
