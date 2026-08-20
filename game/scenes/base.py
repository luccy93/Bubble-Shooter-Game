# game/scenes/base.py - Base Scene Interface class

class BaseScene:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        """Processes events. Returns True if event consumed."""
        pass

    def update(self, dt):
        """Processes logic updates."""
        pass

    def draw(self, surface):
        """Draws components onto display surface."""
        pass
