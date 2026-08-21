# game/ui/design_system.py - Centralized Stitch Design System renderers for Pygame
#
# Provides reusable drawing primitives matching the "Bubble Blast Saga" Stitch design:
# glassmorphism panels, 3D buttons, progress bars, star displays, currency chips,
# gradient backgrounds, and glow effects.

import pygame
import math
import time
from game.core.config import GameConfig


# ─────────────────────────────────────────────
# GLASS PANEL RENDERER
# ─────────────────────────────────────────────
def draw_glass_panel(surface, rect, opacity=100, border_color=None, radius=None, glow=False):
    """Draws a glassmorphism panel: semi-transparent with highlight border simulation.

    Args:
        surface: Pygame surface to draw on.
        rect: pygame.Rect in screen coordinates.
        opacity: Alpha value (0-255) for panel fill.
        border_color: Custom border color, or None for default white/purple edge.
        radius: Corner radius in pixels. None = auto-calculated.
        glow: If True, adds an outer glow effect.
    """
    if radius is None:
        radius = min(rect.width, rect.height) // 6

    # 1. Outer glow (optional)
    if glow:
        glow_surf = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*GameConfig.COLOR_PRIMARY_LIGHT[:3], 25),
                         (0, 0, rect.width + 16, rect.height + 16),
                         border_radius=radius + 4)
        surface.blit(glow_surf, (rect.x - 8, rect.y - 8))

    # 2. Panel fill with alpha
    panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    fill_color = (44, 40, 52, opacity)  # surface-container-high with alpha
    pygame.draw.rect(panel_surf, fill_color, (0, 0, rect.width, rect.height),
                     border_radius=radius)
    surface.blit(panel_surf, rect.topleft)

    # 3. Top-left highlight border (simulates glass edge light catch)
    highlight_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(highlight_surf, (255, 255, 255, 45),
                     (0, 0, rect.width, rect.height),
                     width=1, border_radius=radius)
    surface.blit(highlight_surf, rect.topleft)

    # 4. Secondary border (subtle purple bottom-right)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, width=1, border_radius=radius)


# ─────────────────────────────────────────────
# 3D BUTTON RENDERER
# ─────────────────────────────────────────────
def draw_3d_button(surface, rect, color, pressed=False, glow=False, radius=None):
    """Draws a premium 3D pill-shaped button with shadow base and highlight.

    Args:
        surface: Pygame surface.
        rect: pygame.Rect in screen coordinates.
        color: Primary button fill color tuple.
        pressed: If True, flatten the button (remove shadow).
        glow: If True, add outer glow matching button color.
        radius: Custom border radius.
    """
    if radius is None:
        radius = rect.height // 2  # Pill shape

    shadow_h = max(2, int(4 * GameConfig.scale_y))

    # 1. Outer glow
    if glow and not pressed:
        glow_surf = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color[:3], 60),
                         (0, 0, rect.width + 20, rect.height + 20),
                         border_radius=radius + 6)
        surface.blit(glow_surf, (rect.x - 10, rect.y - 10))

    if not pressed:
        # 2. Bottom shadow "base"
        shadow_color = tuple(max(0, c - 80) for c in color[:3])
        shadow_rect = pygame.Rect(rect.x, rect.y + shadow_h, rect.width, rect.height)
        pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=radius)

    # 3. Main button body
    draw_rect = rect if pressed else pygame.Rect(rect.x, rect.y, rect.width, rect.height)
    pygame.draw.rect(surface, color, draw_rect, border_radius=radius)

    # 4. Top highlight gradient simulation
    highlight_surf = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    pygame.draw.rect(highlight_surf, (255, 255, 255, 35),
                     (0, 0, rect.width, rect.height // 2),
                     border_radius=radius)
    surface.blit(highlight_surf, draw_rect.topleft)

    # 5. Thin white inner border
    border_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(border_surf, (255, 255, 255, 30),
                     (0, 0, rect.width, rect.height),
                     width=1, border_radius=radius)
    surface.blit(border_surf, draw_rect.topleft)


# ─────────────────────────────────────────────
# PROGRESS BAR RENDERER
# ─────────────────────────────────────────────
def draw_progress_bar(surface, rect, fill_pct, track_color=None, fill_color=None,
                      star_positions=None, radius=None):
    """Draws a Stitch-style progress bar with luminous fill and optional star markers.

    Args:
        surface: Pygame surface.
        rect: pygame.Rect in screen coordinates.
        fill_pct: Fill percentage (0.0 to 1.0).
        track_color: Custom track background.
        fill_color: Custom fill gradient start.
        star_positions: List of floats (0-1) for star marker positions.
        radius: Corner radius.
    """
    if track_color is None:
        track_color = GameConfig.COLOR_SURFACE_HIGHEST
    if fill_color is None:
        fill_color = GameConfig.COLOR_SUCCESS
    if radius is None:
        radius = rect.height // 2

    # 1. Track (recessed dark glass tube)
    pygame.draw.rect(surface, track_color, rect, border_radius=radius)
    # Inner shadow
    inner_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(inner_surf, (0, 0, 0, 40), (0, 0, rect.width, rect.height),
                     border_radius=radius)
    surface.blit(inner_surf, rect.topleft)

    # 2. Fill bar (luminous gradient)
    fill_pct = max(0.0, min(1.0, fill_pct))
    if fill_pct > 0.01:
        fill_width = max(radius * 2, int(rect.width * fill_pct))
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=radius)

        # Sparkle at leading edge
        sparkle_surf = pygame.Surface((8, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sparkle_surf, (255, 255, 255, 180), (0, 0, 8, rect.height),
                         border_radius=4)
        sparkle_x = rect.x + fill_width - 8
        if sparkle_x > rect.x:
            surface.blit(sparkle_surf, (sparkle_x, rect.y))

    # 3. Star markers on track
    if star_positions:
        for pos in star_positions:
            sx = rect.x + int(rect.width * pos)
            sy = rect.y + rect.height // 2
            star_size = max(6, int(rect.height * 0.7))
            filled = fill_pct >= pos
            star_color = GameConfig.COLOR_GOLD if filled else GameConfig.COLOR_OUTLINE_DIM
            _draw_star_shape(surface, sx, sy, star_size, star_color)


def _draw_star_shape(surface, cx, cy, size, color):
    """Draws a 5-pointed star polygon."""
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.45
        px = cx + math.cos(angle) * r
        py = cy - math.sin(angle) * r
        points.append((int(px), int(py)))
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, points)


# ─────────────────────────────────────────────
# STAR DISPLAY RENDERER
# ─────────────────────────────────────────────
def draw_stars(surface, cx, cy, stars_earned, total=3, size=18, animated=False, start_time=None):
    """Draws a row of filled/unfilled stars centered at (cx, cy).

    Args:
        surface: Pygame surface.
        cx, cy: Center position in virtual coordinates.
        stars_earned: Number of filled stars (0-total).
        total: Total stars to display.
        size: Star size in virtual pixels.
        animated: If True, stars appear with staggered scale animation.
        start_time: Animation start time for staggered reveal.
    """
    spacing = int(size * 2.5)
    start_x = cx - (total - 1) * spacing // 2

    for i in range(total):
        sx = GameConfig.to_screen_x(start_x + i * spacing)
        sy = GameConfig.to_screen_y(cy)
        s_size = int(size * min(GameConfig.scale_x, GameConfig.scale_y))

        # Staggered animation
        scale = 1.0
        if animated and start_time:
            t = time.time() - start_time
            target_t = 0.3 + i * 0.25
            if t < target_t:
                scale = 0.0
            elif t < target_t + 0.2:
                progress = (t - target_t) / 0.2
                scale = 0.5 + 0.5 * math.sin(progress * math.pi / 2)

        actual_size = int(s_size * scale)
        if actual_size <= 1:
            continue

        filled = i < stars_earned
        color = GameConfig.COLOR_GOLD if filled else GameConfig.COLOR_OUTLINE_DIM
        _draw_star_shape(surface, sx, sy, actual_size, color)

        # Glow for filled stars
        if filled:
            glow_surf = pygame.Surface((actual_size * 3, actual_size * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*GameConfig.COLOR_GOLD, 30),
                               (actual_size * 3 // 2, actual_size * 3 // 2),
                               actual_size)
            surface.blit(glow_surf, (sx - actual_size * 3 // 2, sy - actual_size * 3 // 2))


# ─────────────────────────────────────────────
# CURRENCY CHIP RENDERER
# ─────────────────────────────────────────────
def draw_currency_chip(surface, cx, cy, icon_text, value, color=None):
    """Draws a Stitch-style currency capsule chip.

    Args:
        surface: Pygame surface.
        cx, cy: Center position in virtual coordinates.
        icon_text: Icon string (e.g. "🪙" or "⭐").
        value: Display value (int or string).
        color: Chip background color.
    """
    if color is None:
        color = GameConfig.COLOR_SURFACE_HIGH

    sw = int(100 * GameConfig.scale_x)
    sh = int(28 * GameConfig.scale_y)
    sx = GameConfig.to_screen_x(cx) - sw // 2
    sy = GameConfig.to_screen_y(cy) - sh // 2

    chip_rect = pygame.Rect(sx, sy, sw, sh)

    # Capsule background
    draw_glass_panel(surface, chip_rect, opacity=140, radius=sh // 2)

    # Border
    pygame.draw.rect(surface, GameConfig.COLOR_OUTLINE_DIM, chip_rect, width=1,
                     border_radius=sh // 2)

    # Icon
    icon_size = GameConfig.scale_font_size(14)
    try:
        font = pygame.font.SysFont('Segoe UI Emoji', icon_size)
    except Exception:
        font = pygame.font.Font(None, icon_size)
    icon_surf = font.render(str(icon_text), True, GameConfig.COLOR_GOLD)
    surface.blit(icon_surf, (sx + int(8 * GameConfig.scale_x),
                             sy + (sh - icon_surf.get_height()) // 2))

    # Value
    val_size = GameConfig.scale_font_size(13)
    try:
        val_font = pygame.font.SysFont(GameConfig.FONT_BODY, val_size, bold=True)
    except Exception:
        val_font = pygame.font.Font(None, val_size)
    val_surf = val_font.render(str(value), True, GameConfig.COLOR_TEXT)
    surface.blit(val_surf, (sx + int(30 * GameConfig.scale_x),
                            sy + (sh - val_surf.get_height()) // 2))


# ─────────────────────────────────────────────
# GRADIENT BACKGROUND RENDERER
# ─────────────────────────────────────────────
def draw_gradient_bg(surface, top_color=None, bot_color=None, radial=False):
    """Fills the surface with a vertical or radial gradient background.

    Args:
        surface: Pygame surface (usually the full screen).
        top_color: Gradient start color (top).
        bot_color: Gradient end color (bottom).
        radial: If True, adds a radial highlight at top-center.
    """
    if top_color is None:
        top_color = (42, 27, 77)   # Slightly brighter purple at top
    if bot_color is None:
        bot_color = GameConfig.COLOR_BG

    w = surface.get_width()
    h = surface.get_height()

    # Vertical gradient
    for y in range(h):
        ratio = y / max(1, h)
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

    # Radial highlight at top center (simulates magical light source)
    if radial:
        radial_surf = pygame.Surface((w, h // 2), pygame.SRCALPHA)
        center = (w // 2, 0)
        max_rad = min(w, h // 2)
        for r in range(max_rad, 0, -4):
            alpha = int(15 * (r / max_rad))
            pygame.draw.circle(radial_surf, (98, 0, 238, alpha), center, r)
        surface.blit(radial_surf, (0, 0))


# ─────────────────────────────────────────────
# TOGGLE SWITCH RENDERER
# ─────────────────────────────────────────────
def draw_toggle_switch(surface, cx, cy, is_on, w=50, h=26):
    """Draws a visual on/off toggle switch.

    Args:
        surface: Pygame surface.
        cx, cy: Center position in virtual coordinates.
        is_on: Boolean toggle state.
        w, h: Virtual dimensions.
    """
    sw = int(w * GameConfig.scale_x)
    sh = int(h * GameConfig.scale_y)
    sx = GameConfig.to_screen_x(cx) - sw // 2
    sy = GameConfig.to_screen_y(cy) - sh // 2

    track_rect = pygame.Rect(sx, sy, sw, sh)
    radius = sh // 2

    # Track
    track_color = GameConfig.COLOR_SUCCESS if is_on else GameConfig.COLOR_SURFACE_HIGHEST
    pygame.draw.rect(surface, track_color, track_rect, border_radius=radius)
    pygame.draw.rect(surface, (255, 255, 255, 30) if is_on else GameConfig.COLOR_OUTLINE_DIM,
                     track_rect, width=1, border_radius=radius)

    # Thumb (circle knob)
    thumb_rad = int((sh - 6) // 2)
    if is_on:
        thumb_x = sx + sw - thumb_rad - 4
    else:
        thumb_x = sx + thumb_rad + 4
    thumb_y = sy + sh // 2

    # Shadow
    pygame.draw.circle(surface, (0, 0, 0, 60), (thumb_x + 1, thumb_y + 1), thumb_rad)
    # Thumb
    pygame.draw.circle(surface, (255, 255, 255), (thumb_x, thumb_y), thumb_rad)

    # Glow when on
    if is_on:
        glow_surf = pygame.Surface((thumb_rad * 4, thumb_rad * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*GameConfig.COLOR_SUCCESS, 40),
                           (thumb_rad * 2, thumb_rad * 2), thumb_rad * 2)
        surface.blit(glow_surf, (thumb_x - thumb_rad * 2, thumb_y - thumb_rad * 2))


# ─────────────────────────────────────────────
# FLOATING BUBBLE PARTICLES
# ─────────────────────────────────────────────
class AmbientBubble:
    """A decorative floating bubble for background ambience."""

    def __init__(self, vw=None, vh=None):
        import random
        self.vx = random.randint(30, (vw or GameConfig.VIRTUAL_WIDTH) - 30)
        self.vy = random.randint(50, (vh or GameConfig.VIRTUAL_HEIGHT) - 50)
        self.r = random.randint(8, 28)
        self.color = random.choice(GameConfig.BUBBLE_COLORS)
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.3, 0.9)
        self.alpha = random.randint(15, 40)

    def update(self, dt):
        self.phase += dt * self.speed
        self.vy -= self.speed * 8 * dt
        if self.vy < -self.r:
            import random
            self.vy = GameConfig.VIRTUAL_HEIGHT + self.r
            self.vx = random.randint(30, GameConfig.VIRTUAL_WIDTH - 30)

    def draw(self, surface):
        sx = GameConfig.to_screen_x(self.vx + math.sin(self.phase) * 18)
        sy = GameConfig.to_screen_y(self.vy)
        srad = int(self.r * min(GameConfig.scale_x, GameConfig.scale_y))
        if srad <= 0:
            return

        bub_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
        pygame.draw.circle(bub_surf, (*self.color, self.alpha), (srad, srad), srad)
        # Gloss highlight
        gloss_r = max(1, srad // 3)
        pygame.draw.circle(bub_surf, (255, 255, 255, self.alpha // 2),
                           (int(srad * 0.65), int(srad * 0.55)), gloss_r)
        surface.blit(bub_surf, (sx - srad, sy - srad))


def create_ambient_bubbles(count=10):
    """Creates a list of ambient decorative floating bubbles."""
    return [AmbientBubble() for _ in range(count)]


def update_ambient_bubbles(bubbles, dt):
    """Updates all ambient bubbles."""
    for b in bubbles:
        b.update(dt)


def draw_ambient_bubbles(surface, bubbles):
    """Draws all ambient bubbles."""
    for b in bubbles:
        b.draw(surface)
