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
        self.target_scale = 1.0

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
                self.target_scale = 0.90
                return False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed:
                self.is_pressed = False
                self.target_scale = 1.0
                if touch_rect.collidepoint(vmx, vmy):
                    return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_pressed and not touch_rect.collidepoint(vmx, vmy):
                self.is_pressed = False
                self.target_scale = 1.0

        return False

    def draw(self, surface, vx, vy):
        """Draws a premium rounded card button with active press tweens and soft shadows."""
        # Interpolate press scale towards target scale for smooth spring animation
        self.press_scale += (self.target_scale - self.press_scale) * 0.25

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

        # 4. Text (Draw text relative to target bounds)
        self.label.draw(surface, vx, vy, originX=0.5, originY=0.5)


class InputField:
    def __init__(self, placeholder, w=240, h=40, is_password=False):
        self.placeholder = placeholder
        self.vw = w
        self.vh = h
        self.is_password = is_password
        self.text = ""
        self.is_focused = False
        
        # Cursor blink timing
        self.cursor_visible = True
        self.last_blink = time.time()

        self.label = Label("", size=14, color=GameConfig.COLOR_TEXT, align="left")
        self.placeholder_label = Label(placeholder, size=14, color=(120, 110, 140), align="left")

    def handle_event(self, event, vx, vy):
        """Manages keyboard typing captures and focus bounds hits."""
        # Convert coords
        rx = vx - self.vw // 2
        ry = vy - self.vh // 2
        rect = pygame.Rect(rx, ry, self.vw, self.vh)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            vmx = mx / GameConfig.scale_x
            vmy = my / GameConfig.scale_y
            if rect.collidepoint(vmx, vmy):
                self.is_focused = True
            else:
                self.is_focused = False

        elif event.type == pygame.KEYDOWN and self.is_focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                self.is_focused = False
            else:
                # Add printable characters (limit length to fit input area)
                if event.unicode and len(self.text) < 24 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface, vx, vy):
        """Draws the text input field card container."""
        # Convert to screen coords
        sw = int(self.vw * GameConfig.scale_x)
        sh = int(self.vh * GameConfig.scale_y)
        sx = GameConfig.to_screen_x(vx) - sw // 2
        sy = GameConfig.to_screen_y(vy) - sh // 2

        field_rect = pygame.Rect(sx, sy, sw, sh)
        
        # Background
        bg_color = (25, 20, 45) if self.is_focused else (20, 16, 36)
        pygame.draw.rect(surface, bg_color, field_rect, border_radius=8)

        # Border outline
        border_color = GameConfig.COLOR_ACCENT if self.is_focused else (60, 50, 85)
        pygame.draw.rect(surface, border_color, field_rect, width=1, border_radius=8)

        # Draw content
        if self.text:
            display_text = "*" * len(self.text) if self.is_password else self.text
            self.label.set_text(display_text)
            self.label.draw(surface, vx - self.vw // 2 + 15, vy, originX=0, originY=0.5)
        else:
            self.placeholder_label.draw(surface, vx - self.vw // 2 + 15, vy, originX=0, originY=0.5)

        # Draw typing cursor indicator if focused
        if self.is_focused:
            # Blink cursor every 0.5s
            if time.time() - self.last_blink > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.last_blink = time.time()

            if self.cursor_visible:
                # Measure text width roughly
                font_name = 'Outfit'
                scaled_size = GameConfig.scale_font_size(14)
                try:
                    font = pygame.font.SysFont(font_name, scaled_size)
                except Exception:
                    font = pygame.font.Font(None, scaled_size)
                
                display_text = "*" * len(self.text) if self.is_password else self.text
                tw, _ = font.size(display_text)
                
                # Draw cursor line
                cx = sx + int(15 * GameConfig.scale_x) + tw
                cy_start = sy + int(8 * GameConfig.scale_y)
                cy_end = sy + sh - int(8 * GameConfig.scale_y)
                pygame.draw.line(surface, GameConfig.COLOR_PRIMARY, (cx, cy_start), (cx, cy_end), width=2)
