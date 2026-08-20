# game/core/scene_manager.py - Scene Manager implementing state routing and transition bindings

import pygame

class SceneManager:
    def __init__(self):
        self.current_scene = None
        self.scenes_registry = {}

    def register_scene(self, name, scene_class):
        self.scenes_registry[name] = scene_class

    def change_scene(self, name, **kwargs):
        """Transitions to target scene, instantiating it with kwargs."""
        if name in self.scenes_registry:
            scene_class = self.scenes_registry[name]
            self.current_scene = scene_class(self, **kwargs)
        else:
            # Lazy import fallback to prevent circular dependencies
            if name == "MainMenu":
                from game.scenes.main_menu import MainMenuScene
                self.current_scene = MainMenuScene(self, **kwargs)
            elif name == "LevelSelect":
                from game.scenes.level_select import LevelSelectScene
                self.current_scene = LevelSelectScene(self, **kwargs)
            elif name == "Gameplay":
                from game.scenes.gameplay import GameplayScene
                self.current_scene = GameplayScene(self, **kwargs)
            elif name == "Settings":
                from game.scenes.settings import SettingsScene
                self.current_scene = SettingsScene(self, **kwargs)
            elif name == "HowToPlay":
                from game.scenes.how_to_play import HowToPlayScene
                self.current_scene = HowToPlayScene(self, **kwargs)
            elif name == "Achievements":
                from game.scenes.achievements import AchievementsScene
                self.current_scene = AchievementsScene(self, **kwargs)
            elif name == "Statistics":
                from game.scenes.statistics import StatisticsScene
                self.current_scene = StatisticsScene(self, **kwargs)

    def handle_event(self, event):
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)
