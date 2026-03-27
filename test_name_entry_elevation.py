"""Tests for name entry elevation — card layout, shadow, input field, and submit button.

gc-high-01: Tests import layout helpers directly from geocatch_pygame via headless
SDL drivers, ensuring no pygame display is required and CI runs cleanly.
"""
import os
import sys

# Headless drivers BEFORE importing pygame / the game module
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(__file__))
from geocatch_pygame import (
    compute_card_layout,
    compute_shadow_rect,
    compute_input_field,
    compute_submit_button,
    compute_leaderboard_rect,
    get_input_border_color,
    get_submit_button_state,
    WIDTH,
    ACCENT,
)

# ── Tests ──


class TestCardLayout:
    """Test the elevated card-style container."""

    def test_card_is_centered_horizontally(self):
        """Card should be centered on the screen width."""
        cx = WIDTH // 2
        card_x, _, card_w, _ = compute_card_layout(cx)
        card_center = card_x + card_w // 2
        assert card_center == cx

    def test_card_dimensions(self):
        """Card should be 320x150 for a prominent appearance."""
        _, _, card_w, card_h = compute_card_layout()
        assert card_w == 320
        assert card_h == 150

    def test_card_positioned_below_stats(self):
        """Card should start at stats_y + 24."""
        stats_y = 300
        _, card_y, _, _ = compute_card_layout(stats_y=stats_y)
        assert card_y == stats_y + 24


class TestShadowEffect:
    """Test the subtle shadow for depth."""

    def test_shadow_offset_right_and_down(self):
        """Shadow should be offset 4px right and 4px down."""
        card_x, card_y, card_w, card_h = compute_card_layout()
        sx, sy, sw, sh = compute_shadow_rect(card_x, card_y, card_w, card_h)
        assert sx == card_x + 4
        assert sy == card_y + 4

    def test_shadow_same_dimensions_as_card(self):
        """Shadow rect should have same width/height as card."""
        card_x, card_y, card_w, card_h = compute_card_layout()
        _, _, sw, sh = compute_shadow_rect(card_x, card_y, card_w, card_h)
        assert sw == card_w
        assert sh == card_h


class TestInputField:
    """Test the prominent input field."""

    def test_input_field_inside_card(self):
        """Input field should be within card boundaries."""
        card_x, card_y, card_w, card_h = compute_card_layout()
        pill_x, pill_y, pill_w, pill_h = compute_input_field(card_x, card_y)
        assert pill_x >= card_x
        assert pill_x + pill_w <= card_x + card_w
        assert pill_y >= card_y
        assert pill_y + pill_h <= card_y + card_h

    def test_input_field_dimensions_prominent(self):
        """Input field should be 200x42 (larger than old 180x38)."""
        card_x, card_y, _, _ = compute_card_layout()
        _, _, pill_w, pill_h = compute_input_field(card_x, card_y)
        assert pill_w == 200
        assert pill_h == 42

    def test_input_border_inactive_when_empty(self):
        """Border should be muted grey when no text entered."""
        color = get_input_border_color("")
        assert color == (80, 85, 110)

    def test_input_border_accent_when_typing(self):
        """Border should be ACCENT orange when text is present."""
        color = get_input_border_color("ABC")
        assert color == ACCENT


class TestSubmitButton:
    """Test the submit button styling."""

    def test_button_inside_card(self):
        """Submit button should be within card boundaries."""
        card_x, card_y, card_w, card_h = compute_card_layout()
        btn_x, btn_y, btn_w, btn_h = compute_submit_button(card_x, card_y, card_w)
        assert btn_x >= card_x
        assert btn_x + btn_w <= card_x + card_w
        assert btn_y >= card_y
        assert btn_y + btn_h <= card_y + card_h

    def test_button_right_aligned(self):
        """Submit button should sit to the right of the input field."""
        card_x, card_y, card_w, _ = compute_card_layout()
        pill_x, _, pill_w, _ = compute_input_field(card_x, card_y)
        btn_x, _, _, _ = compute_submit_button(card_x, card_y, card_w)
        assert btn_x > pill_x + pill_w  # button is to the right of input

    def test_button_same_height_as_input(self):
        """Submit button should be same height as input for alignment."""
        card_x, card_y, card_w, _ = compute_card_layout()
        _, _, _, pill_h = compute_input_field(card_x, card_y)
        _, _, _, btn_h = compute_submit_button(card_x, card_y, card_w)
        assert btn_h == pill_h

    def test_button_inactive_when_empty(self):
        """Button should be dimmed when no name is entered."""
        bg, active = get_submit_button_state("")
        assert not active
        assert bg == (50, 52, 70)

    def test_button_active_when_has_input(self):
        """Button should be ACCENT orange when name has text."""
        bg, active = get_submit_button_state("A")
        assert active
        assert bg == ACCENT


class TestLeaderboardPosition:
    """Test leaderboard is centered below the name entry card."""

    def test_leaderboard_below_card(self):
        """Leaderboard should start 12px below the card."""
        card_x, card_y, card_w, card_h = compute_card_layout()
        cx = WIDTH // 2
        _, lb_y, _ = compute_leaderboard_rect(cx, card_y, card_h)
        assert lb_y == card_y + card_h + 12

    def test_leaderboard_centered(self):
        """Leaderboard should be centered on screen."""
        cx = WIDTH // 2
        card_x, card_y, card_w, card_h = compute_card_layout()
        lb_x, _, lb_w = compute_leaderboard_rect(cx, card_y, card_h)
        lb_center = lb_x + lb_w // 2
        assert lb_center == cx
