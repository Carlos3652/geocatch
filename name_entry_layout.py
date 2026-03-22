"""Name entry card layout helpers — shared between geocatch_pygame.py and tests.

Pure geometry/logic functions with no pygame dependency, so they can be
imported safely in test environments without initialising a display.
"""

# Screen constants (must match geocatch_pygame.py)
WIDTH, HEIGHT = 1000, 700
ACCENT = (255, 107, 53)


def compute_card_layout(cx=None, stats_y=None):
    """Compute card-style container geometry. Returns (x, y, w, h)."""
    if cx is None:
        cx = WIDTH // 2
    if stats_y is None:
        stats_y = 0
    card_w, card_h = 320, 150
    card_x = cx - card_w // 2
    card_y = stats_y + 24
    return card_x, card_y, card_w, card_h


def compute_shadow_rect(card_x, card_y, card_w, card_h):
    """Shadow offset 4px right and down, same size as card."""
    return card_x + 4, card_y + 4, card_w, card_h


def compute_input_field(card_x, card_y):
    """Prominent input field geometry inside the card. Returns (x, y, w, h)."""
    pill_w, pill_h = 200, 42
    pill_x = card_x + 20
    pill_y = card_y + 70
    return pill_x, pill_y, pill_w, pill_h


def compute_submit_button(card_x, card_y, card_w):
    """Submit button geometry, right-aligned inside card. Returns (x, y, w, h)."""
    _, pill_y, _, pill_h = compute_input_field(card_x, card_y)
    btn_w = 70
    btn_h = pill_h
    btn_x = card_x + card_w - btn_w - 20
    btn_y = pill_y
    return btn_x, btn_y, btn_w, btn_h


def compute_leaderboard_rect(cx, card_y, card_h):
    """Leaderboard geometry below the card, clamped to screen. Returns (x, y, w)."""
    lb_w = 280
    lb_x = cx - lb_w // 2
    lb_y = card_y + card_h + 12
    max_lb_h = 170
    # Clamp so leaderboard + its height stays above the nav bar (HEIGHT - 36)
    if lb_y + max_lb_h > HEIGHT - 36:
        lb_y = HEIGHT - 36 - max_lb_h
    if lb_y < 0:
        lb_y = 0
    return lb_x, lb_y, lb_w


def get_input_border_color(text):
    """Return accent color when text is present, muted grey otherwise."""
    if text:
        return ACCENT
    return (80, 85, 110)


def get_submit_button_state(text):
    """Return (bg_color, is_active) for the submit button."""
    if text:
        return ACCENT, True
    return (50, 52, 70), False
