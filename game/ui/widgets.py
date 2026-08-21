# game/ui/widgets.py - Premium Mobile-Friendly UI Widgets (Stitch Design System)

import pygame
import time
import math
from game.core.config import GameConfig
from game.ui.design_system import draw_3d_button, draw_glass_panel


class Label:
    """Text label with optional shadow, glow, and gradient text rendering."""

    def __init__(self, text, size=20, color=GameConfig.COLOR_TEXT, title=False,
                 align="center", shadow=False, glow=False):
        self.text = text
        self.size = size
        self.color = color
        self.title = title
        self.align = align
        self.shadow = shadow or title  # Titles always get shadow
        self.glow = glow
        self._font = None
        self._render_font()

    def _render_font(self):
        """Loads headline or body font with system fallback chain."""
        if self.title:
            font_candidates = [GameConfig.FONT_HEADLINE] + GameConfig.FONT_FALLBACKS
        else:
            font_candidates = [GameConfig.FONT_BODY] + GameConfig.FONT_FALLBACKS

        scaled_size = GameConfig.scale_font_size(self.size)

        for font_name in font_candidates:
            try:
                self._font = pygame.font.SysFont(font_name, scaled_size, bold=self.title)
                return
            except Exception:
                continue
        self._font = pygame.font.Font(None, scaled_size)

    def set_text(self, text):
        self.text = text

    def draw(self, surface, vx, vy, originX=0.5, originY=0.5):
        """Draws text scaled to actual screen space with optional shadow/glow."""
        sx = GameConfig.to_screen_x(vx)
        sy = GameConfig.to_screen_y(vy)

        # Shadow layer (offset dark text below main text)
        if self.shadow:
            shadow_surf = self._font.render(str(self.text), True, (0, 0, 0))
            shadow_rect = shadow_surf.get_rect()
            offset = max(1, int(2 * min(GameConfig.scale_x, GameConfig.scale_y)))
            shadow_rect.x = sx - int(shadow_rect.width * originX) + offset
            shadow_rect.y = sy - int(shadow_rect.height * originY) + offset
            shadow_alpha = pygame.Surface(shadow_surf.get_size(), pygame.SRCALPHA)
            shadow_alpha.blit(shadow_surf, (0, 0))
            shadow_alpha.set_alpha(80)
            surface.blit(shadow_alpha, shadow_rect)

        # Glow layer (soft colored halo behind text)
        if self.glow:
            glow_color = self.color if self.color != GameConfig.COLOR_TEXT else GameConfig.COLOR_PRIMARY_LIGHT
            glow_surf = self._font.render(str(self.text), True, glow_color)
            glow_surf = pygame.transform.smoothscale(
                glow_surf,
                (int(glow_surf.get_width() * 1.15), int(glow_surf.get_height() * 1.15))
            )
            glow_alpha = pygame.Surface(glow_surf.get_size(), pygame.SRCALPHA)
            glow_alpha.blit(glow_surf, (0, 0))
            glow_alpha.set_alpha(35)
            gr = glow_alpha.get_rect()
            gr.x = sx - int(gr.width * originX)
            gr.y = sy - int(gr.height * originY)
            surface.blit(glow_alpha, gr)

        # Main text
        text_surf = self._font.render(str(self.text), True, self.color)
        rect = text_surf.get_rect()
        rect.x = sx - int(rect.width * originX)
        rect.y = sy - int(rect.height * originY)
        surface.blit(text_surf, rect)
        return rect


class Button:
    """Premium 3D pill-shaped button with squish animation, glow, and press feedback."""

    def __init__(self, label_text, w=200, h=50, bg_color=GameConfig.COLOR_PRIMARY,
                 text_color=GameConfig.COLOR_TEXT, font_size=18, hero=False):
        self.label_text = label_text
        self.vw = w
        self.vh = h
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.hero = hero  # Hero buttons get pulsing glow

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
                self.target_scale = 0.92
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
        """Draws a premium 3D pill button with shadow, highlight, and optional pulse glow."""
        # Interpolate press scale for smooth spring animation
        self.press_scale += (self.target_scale - self.press_scale) * 0.25

        # Calculate scaled dimensions
        sw = int(self.vw * self.press_scale * GameConfig.scale_x)
        sh = int(self.vh * self.press_scale * GameConfig.scale_y)
        sx = GameConfig.to_screen_x(vx) - sw // 2
        sy = GameConfig.to_screen_y(vy) - sh // 2

        btn_rect = pygame.Rect(sx, sy, sw, sh)

        # Use design system 3D button renderer
        is_pressed = self.press_scale < 0.98
        draw_3d_button(surface, btn_rect, self.bg_color,
                       pressed=is_pressed,
                       glow=self.hero and not is_pressed)

        # Pulsing outer glow for hero buttons
        if self.hero and not is_pressed:
            pulse = 0.5 + 0.5 * math.sin(time.time() * 3)
            pulse_alpha = int(20 + 30 * pulse)
            pulse_surf = pygame.Surface((sw + 24, sh + 24), pygame.SRCALPHA)
            pygame.draw.rect(pulse_surf, (*self.bg_color[:3], pulse_alpha),
                             (0, 0, sw + 24, sh + 24),
                             border_radius=sh // 2 + 8)
            surface.blit(pulse_surf, (sx - 12, sy - 12))

        # Draw text centered on button
        self.label.draw(surface, vx, vy, originX=0.5, originY=0.5)


class InputField:
    """Text input field with bottom-border focus glow, placeholder text, and cursor blink."""

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

        # Focus glow transition
        self.focus_glow = 0.0

        self.label = Label("", size=14, color=GameConfig.COLOR_TEXT, align="left")
        self.placeholder_label = Label(placeholder, size=14,
                                       color=GameConfig.COLOR_TEXT_MUTED, align="left")

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
        """Draws the text input field with glassmorphism container and focus glow."""
        # Convert to screen coords
        sw = int(self.vw * GameConfig.scale_x)
        sh = int(self.vh * GameConfig.scale_y)
        sx = GameConfig.to_screen_x(vx) - sw // 2
        sy = GameConfig.to_screen_y(vy) - sh // 2

        field_rect = pygame.Rect(sx, sy, sw, sh)

        # Smooth focus glow transition
        target_glow = 1.0 if self.is_focused else 0.0
        self.focus_glow += (target_glow - self.focus_glow) * 0.15

        # Glass panel background
        draw_glass_panel(surface, field_rect, opacity=80, radius=10)

        # Bottom border with focus glow
        border_y = sy + sh - 2
        if self.focus_glow > 0.05:
            # Glowing bottom border when focused
            glow_alpha = int(180 * self.focus_glow)
            glow_surf = pygame.Surface((sw, 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GameConfig.COLOR_PRIMARY_LIGHT[:3], glow_alpha),
                             (0, 0, sw, 6), border_radius=2)
            surface.blit(glow_surf, (sx, border_y - 2))

        # Subtle bottom border line
        border_color = GameConfig.COLOR_PRIMARY_LIGHT if self.is_focused else GameConfig.COLOR_OUTLINE_DIM
        pygame.draw.line(surface, border_color, (sx + 4, border_y), (sx + sw - 4, border_y), width=2)

        # Draw content
        if self.text:
            display_text = "•" * len(self.text) if self.is_password else self.text
            self.label.set_text(display_text)
            self.label.draw(surface, vx - self.vw // 2 + 15, vy, originX=0, originY=0.5)
        else:
            self.placeholder_label.draw(surface, vx - self.vw // 2 + 15, vy,
                                        originX=0, originY=0.5)

        # Draw typing cursor indicator if focused
        if self.is_focused:
            if time.time() - self.last_blink > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.last_blink = time.time()

            if self.cursor_visible:
                font_name = GameConfig.FONT_BODY
                scaled_size = GameConfig.scale_font_size(14)
                try:
                    font = pygame.font.SysFont(font_name, scaled_size)
                except Exception:
                    font = pygame.font.Font(None, scaled_size)

                display_text = "•" * len(self.text) if self.is_password else self.text
                tw, _ = font.size(display_text)

                # Draw cursor line with primary glow
                cx = sx + int(15 * GameConfig.scale_x) + tw
                cy_start = sy + int(8 * GameConfig.scale_y)
                cy_end = sy + sh - int(8 * GameConfig.scale_y)
                pygame.draw.line(surface, GameConfig.COLOR_PRIMARY_LIGHT,
                                 (cx, cy_start), (cx, cy_end), width=2)
