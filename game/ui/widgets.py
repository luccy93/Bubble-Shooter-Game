# game/ui/widgets.py - Mobile-Friendly UI Widgets and Buttons

import pygame
import time
from game.core.config import GameConfig

class Label:
    def __init__(self, text, size=20, color=GameConfig.COLOR_TEXT, title=False, align="center"):
        self.text = text
        self.size = size
        self.color = color
        self.title = title
        self.align = align
        self._font = None
        self._render_font()

    def _render_font(self):
        font_name = 'Fredoka One' if self.title else 'Outfit'
        scaled_size = GameConfig.scale_font_size(self.size)
        
        # Try loading standard system font or fallback
        try:
            self._font = pygame.font.SysFont(font_name, scaled_size)
        except Exception:
            self._font = pygame.font.Font(None, scaled_size)

    def set_text(self, text):
        self.text = text

    def draw(self, surface, vx, vy, originX=0.5, originY=0.5):
        """Draws text scaled to actual screen space."""
        sx = GameConfig.to_screen_x(vx)
        sy = GameConfig.to_screen_y(vy)

        text_surf = self._font.render(str(self.text), True, self.color)
        rect = text_surf.get_rect()
        
        rect.x = sx - int(rect.width * originX)
        rect.y = sy - int(rect.height * originY)
        surface.blit(text_surf, rect)
        return rect


class Button:
    def __init__(self, label_text, w=200, h=50, bg_color=GameConfig.COLOR_ACCENT, text_color=GameConfig.COLOR_TEXT, font_size=18):
        self.label_text = label_text
        self.vw = w
        self.vh = h
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        
        # Micro-interactions states
        self.is_pressed = False
        self.press_scale = 1.0
        self.press_time = 0.0

        # Label object
        self.label = Label(label_text, size=font_size, color=text_color, title=True)

    def handle_event(self, event, vx, vy):
        """Processes mouse/touch inputs, handling press scales and returns trigger flags."""
        if event.type not in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
            return False

        # Convert actual event mouse coordinates back to virtual space for hit detection
        mx, my = event.pos
        vmx = mx / GameConfig.scale_x
        vmy = my / GameConfig.scale_y

        # Define bounding box in virtual coordinates
        rect = pygame.Rect(vx - self.vw // 2, vy - self.vh // 2, self.vw, self.vh)

        # Enforce minimum touch target padding (at least 48px in virtual coordinates)
        touch_rect = rect.inflate(max(0, 48 - self.vw), max(0, 48 - self.vh))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if touch_rect.collidepoint(vmx, vmy):
                self.is_pressed = True
                self.press_scale = 0.93
                return False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed:
                self.is_pressed = False
                self.press_scale = 1.0
                if touch_rect.collidepoint(vmx, vmy):
                    return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_pressed and not touch_rect.collidepoint(vmx, vmy):
                self.is_pressed = False
                self.press_scale = 1.0

        return False

    def draw(self, surface, vx, vy):
        """Draws a premium rounded card button with active press tweens and soft shadows."""
        # Calculate scaled dimensions
        sw = int(self.vw * self.press_scale * GameConfig.scale_x)
        sh = int(self.vh * self.press_scale * GameConfig.scale_y)
        sx = GameConfig.to_screen_x(vx) - sw // 2
        sy = GameConfig.to_screen_y(vy) - sh // 2

        # 1. Shadow Rect
        shadow_offset = int(4 * GameConfig.scale_y)
        shadow_rect = pygame.Rect(sx + shadow_offset // 2, sy + shadow_offset, sw, sh)
        pygame.draw.rect(surface, (5, 4, 15), shadow_rect, border_radius=sw // 6)

        # 2. Main Button Body
        btn_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.bg_color, btn_rect, border_radius=sw // 6)

        # 3. Inner border highlight
        pygame.draw.rect(surface, (255, 255, 255), btn_rect, width=1, border_radius=sw // 6)

        # 4. Text
        self.label.draw(surface, vx, vy, originX=0.5, originY=0.5)
