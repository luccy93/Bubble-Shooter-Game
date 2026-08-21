# game/core/scene_manager.py - Scene Manager with transition system and back-navigation stack

import pygame
import time

class SceneManager:
    # Transition types
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"

    # Default transition durations (seconds)
    TRANSITION_DURATION = 0.3

    # Scenes that should NOT be pushed to back stack
    _NO_BACK_STACK = {"Splash", "Gameplay"}

    # Transition type overrides per source→target pair
    _TRANSITION_MAP = {
        ("Splash", "Welcome"): FADE,
        ("Welcome", "SignIn"): SLIDE_LEFT,
        ("Welcome", "SignUp"): SLIDE_LEFT,
        ("SignIn", "Welcome"): SLIDE_RIGHT,
        ("SignUp", "Welcome"): SLIDE_RIGHT,
        ("Welcome", "MainMenu"): FADE,
        ("SignIn", "MainMenu"): FADE,
        ("SignUp", "MainMenu"): FADE,
        ("MainMenu", "LevelSelect"): SLIDE_LEFT,
        ("LevelSelect", "MainMenu"): SLIDE_RIGHT,
        ("LevelSelect", "Gameplay"): FADE,
    }

    def __init__(self):
        self.current_scene = None
        self.current_scene_name = None
        self.scenes_registry = {}

        # Transition state
        self._transition_active = False
        self._transition_type = self.FADE
        self._transition_start = 0
        self._transition_duration = self.TRANSITION_DURATION
        self._old_surface = None
        self._new_scene_pending = None

        # Back navigation stack
        self._back_stack = []

        # Default back targets for each scene
        self._back_targets = {
            "MainMenu": "Welcome",
            "LevelSelect": "MainMenu",
            "Settings": "MainMenu",
            "Profile": "MainMenu",
            "Shop": "MainMenu",
            "Achievements": "MainMenu",
            "Statistics": "MainMenu",
            "DailyRewards": "MainMenu",
            "HowToPlay": "MainMenu",
            "SignIn": "Welcome",
            "SignUp": "Welcome",
            "LevelStartPopup": "LevelSelect",
        }

    def register_scene(self, name, scene_class):
        self.scenes_registry[name] = scene_class

    def change_scene(self, name, transition=None, **kwargs):
        """Transitions to target scene with optional visual transition.

        Args:
            name: Scene name to navigate to.
            transition: Transition type override. None = auto from map.
            **kwargs: Passed to the scene constructor.
        """
        old_name = self.current_scene_name

        # Push current scene to back stack (if navigable)
        if old_name and old_name not in self._NO_BACK_STACK:
            # Avoid duplicates at the top
            if not self._back_stack or self._back_stack[-1] != old_name:
                self._back_stack.append(old_name)
            # Limit stack depth
            if len(self._back_stack) > 15:
                self._back_stack = self._back_stack[-10:]

        # Determine transition type
        if transition is None:
            pair = (old_name, name)
            transition = self._TRANSITION_MAP.get(pair, self.FADE)

        # Capture old frame for transition blending
        if self.current_scene and pygame.display.get_surface():
            display = pygame.display.get_surface()
            self._old_surface = display.copy()
        else:
            self._old_surface = None

        # Instantiate new scene
        self._instantiate_scene(name, **kwargs)
        self.current_scene_name = name

        # Start transition
        if self._old_surface:
            self._transition_active = True
            self._transition_type = transition
            self._transition_start = time.time()
            self._transition_duration = self.TRANSITION_DURATION
        else:
            self._transition_active = False

    def go_back(self):
        """Navigates back using history stack or default back targets."""
        if self._back_stack:
            target = self._back_stack.pop()
            self.change_scene(target, transition=self.SLIDE_RIGHT)
            return True

        # Fallback to default back target map
        if self.current_scene_name in self._back_targets:
            target = self._back_targets[self.current_scene_name]
            self.change_scene(target, transition=self.SLIDE_RIGHT)
            return True

        return False

    def _instantiate_scene(self, name, **kwargs):
        """Creates a new scene instance via registry or lazy import fallback."""
        if name in self.scenes_registry:
            scene_class = self.scenes_registry[name]
            self.current_scene = scene_class(self, **kwargs)
            return

        # Lazy import fallback to prevent circular dependencies
        scene_map = {
            "MainMenu": ("game.scenes.main_menu", "MainMenuScene"),
            "LevelSelect": ("game.scenes.level_select", "LevelSelectScene"),
            "Gameplay": ("game.scenes.gameplay", "GameplayScene"),
            "Settings": ("game.scenes.settings", "SettingsScene"),
            "HowToPlay": ("game.scenes.how_to_play", "HowToPlayScene"),
            "Achievements": ("game.scenes.achievements", "AchievementsScene"),
            "Statistics": ("game.scenes.statistics", "StatisticsScene"),
            "Splash": ("game.scenes.splash", "SplashScene"),
            "Welcome": ("game.scenes.welcome", "WelcomeScene"),
            "SignIn": ("game.scenes.auth_screens", "SignInScene"),
            "SignUp": ("game.scenes.auth_screens", "SignUpScene"),
            "Profile": ("game.scenes.profile", "ProfileScene"),
            "Shop": ("game.scenes.shop", "ShopScene"),
            "DailyRewards": ("game.scenes.daily_rewards", "DailyRewardsScene"),
            "LevelStartPopup": ("game.scenes.level_start_popup", "LevelStartPopupScene"),
        }

        if name in scene_map:
            module_path, class_name = scene_map[name]
            import importlib
            module = importlib.import_module(module_path)
            scene_class = getattr(module, class_name)
            self.current_scene = scene_class(self, **kwargs)

    def handle_event(self, event):
        # Block events during transition
        if self._transition_active:
            return
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)

        # Draw transition overlay
        if self._transition_active:
            self._draw_transition(surface)

    def _draw_transition(self, surface):
        """Renders the active transition blending between old and new frames."""
        elapsed = time.time() - self._transition_start
        progress = min(1.0, elapsed / self._transition_duration)

        if progress >= 1.0:
            self._transition_active = False
            self._old_surface = None
            return

        w = surface.get_width()
        h = surface.get_height()

        if self._transition_type == self.FADE:
            # Alpha crossfade: old → new
            if self._old_surface:
                self._old_surface.set_alpha(int(255 * (1.0 - progress)))
                surface.blit(self._old_surface, (0, 0))

        elif self._transition_type == self.SLIDE_LEFT:
            # New slides in from right, old slides out left
            offset = int(w * (1.0 - progress))
            new_frame = surface.copy()
            if self._old_surface:
                surface.blit(self._old_surface, (-int(w * progress), 0))
            surface.blit(new_frame, (offset, 0))

        elif self._transition_type == self.SLIDE_RIGHT:
            # New slides in from left, old slides out right
            offset = int(-w * (1.0 - progress))
            new_frame = surface.copy()
            if self._old_surface:
                surface.blit(self._old_surface, (int(w * progress), 0))
            surface.blit(new_frame, (offset, 0))
