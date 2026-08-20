# main.py - App entry point, display scaling, and central clock loop

import pygame
import sys
import os

# Append project root to sys.path to enable imports on all platforms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.core.config import GameConfig
from game.core.scene_manager import SceneManager
from game.storage.save_manager import SaveManager
from game.audio.audio_manager import AudioManager

def main():
    # 1. Initialize Pygame core and font engine
    pygame.init()
    pygame.font.init()

    # 2. Get screen size (portrait orientation setup)
    # On mobile, we fetch the actual system window resolution to scale proportionally.
    # On desktop, we run a default window of 450x800.
    is_android = "ANDROID_ARGUMENT" in os.environ
    if is_android:
        info = pygame.display.Info()
        actual_width = info.current_w
        actual_height = info.current_h
        fullscreen = True
    else:
        actual_width = 450
        actual_height = 800
        fullscreen = False

    # 3. Create window and configure scaling configurations
    screen = GameConfig.init_screen(actual_width, actual_height, fullscreen=fullscreen)
    pygame.display.set_caption("Bubble Shooter")

    # 4. Initialize storage and audio systems
    SaveManager.load_game()
    AudioManager.init()

    # 5. Initialize Scene Manager and load MainMenu
    scene_manager = SceneManager()
    scene_manager.change_scene("MainMenu")

    # 6. Central Game Loop
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # Cap at 60 FPS, dt in seconds

        # Event Dispatcher
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Check Android app lifecycle backgrounding pauses
            elif event.type == pygame.ACTIVEEVENT:
                # App lost focus / went to background (state & 2)
                if event.gain == 0 and event.state & 2:
                    # Notify active gameplay scene of background pause
                    if scene_manager.current_scene and hasattr(scene_manager.current_scene, 'show_pause'):
                        scene_manager.current_scene.show_pause = True
            
            # Forward to scene manager
            scene_manager.handle_event(event)

        # Logic Update
        scene_manager.update(dt)

        # Rendering
        scene_manager.draw(screen)
        pygame.display.flip()

    # Clean termination
    AudioManager.stop_music()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
