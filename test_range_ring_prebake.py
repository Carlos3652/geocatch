"""Tests for CRIT-02: Static range ring surface pre-baked at startup.

Validates that the range ring surface is created once with correct
dimensions and content, rather than being redrawn every frame.
"""
import os
import sys

# Set headless drivers BEFORE importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Only pop pygame if it's a stub/mock; real pygame is safe to reuse
if "pygame" not in sys.modules or not hasattr(sys.modules["pygame"], "init"):
    sys.modules.pop("pygame", None)
import pygame

# Initialize pygame (headless) so Surface operations work
pygame.init()
pygame.display.set_mode((1, 1))

# Import the pre-baked surface and constant from the game module
sys.path.insert(0, os.path.dirname(__file__))
from geocatch_pygame import _range_ring_surf, _RANGE_RING_RADIUS


class TestRangeRingSurfaceProperties:
    """Verify the pre-baked range ring surface has correct properties."""

    def test_surface_exists(self):
        """Pre-baked range ring surface should be created at module load."""
        assert _range_ring_surf is not None

    def test_surface_is_pygame_surface(self):
        assert isinstance(_range_ring_surf, pygame.Surface)

    def test_surface_dimensions(self):
        """Surface should be (2*radius+2) x (2*radius+2) to fit the ring."""
        expected = _RANGE_RING_RADIUS * 2 + 2
        assert _range_ring_surf.get_width() == expected
        assert _range_ring_surf.get_height() == expected

    def test_surface_has_alpha_channel(self):
        """Surface must use SRCALPHA for transparent background."""
        assert _range_ring_surf.get_flags() & pygame.SRCALPHA

    def test_radius_is_55(self):
        """Range ring radius should be 55 pixels."""
        assert _RANGE_RING_RADIUS == 55

    def test_center_pixel_is_transparent(self):
        """Center of the ring surface should be transparent (it's a ring, not filled)."""
        cx = _RANGE_RING_RADIUS + 1
        cy = _RANGE_RING_RADIUS + 1
        color = _range_ring_surf.get_at((cx, cy))
        assert color.a == 0, f"Center should be transparent, got alpha={color.a}"

    def test_ring_edge_has_content(self):
        """A pixel on the ring circumference should have the ring color."""
        cx = _RANGE_RING_RADIUS + 1
        cy = _RANGE_RING_RADIUS + 1
        # Check the top of the ring (center_x, center_y - radius)
        ring_pixel = _range_ring_surf.get_at((cx, cy - _RANGE_RING_RADIUS))
        assert ring_pixel.r == 200
        assert ring_pixel.g == 200
        assert ring_pixel.b == 200
        assert ring_pixel.a == 255

    def test_surface_is_not_all_transparent(self):
        """Surface should contain visible pixels (the ring)."""
        w, h = _range_ring_surf.get_size()
        has_visible = False
        for x in range(w):
            for y in range(h):
                if _range_ring_surf.get_at((x, y)).a > 0:
                    has_visible = True
                    break
            if has_visible:
                break
        assert has_visible, "Surface should contain at least one visible pixel"


class TestRangeRingSurfaceIdentity:
    """Verify the surface is a single pre-baked instance (not recreated)."""

    def test_surface_identity_stable(self):
        """Importing twice should return the same object (pre-baked once)."""
        from geocatch_pygame import _range_ring_surf as surf2
        assert _range_ring_surf is surf2

    def test_no_per_frame_draw_circle_for_range_ring(self):
        """Verify the source code uses blit, not draw.circle, for the range ring.

        This is a code-level check to ensure the optimization is in place.
        """
        src_path = os.path.join(os.path.dirname(__file__), "geocatch_pygame.py")
        with open(src_path, "r") as f:
            src = f.read()

        # The old pattern should NOT exist: draw.circle with radius 55 to screen
        assert "pygame.draw.circle(screen, (200, 200, 200)" not in src, \
            "Found per-frame draw.circle for range ring — should use pre-baked blit"

        # The new pattern SHOULD exist: blit of _range_ring_surf
        assert "_range_ring_surf" in src
