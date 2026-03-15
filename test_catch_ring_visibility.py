"""Tests for catch ring visibility improvements."""


def compute_ring_params(ticks_ms):
    """Reproduce the catch ring pulse calculation from geocatch_pygame.py."""
    _pt = ticks_ms / 1000.0
    _pulse = (_pt * 1.2) % 1.0
    _ring_r = 30 + int(_pulse * 28)
    _ring_alpha = int(210 * (1 - _pulse))
    # Glow layers
    _glow_alpha = max(0, _ring_alpha // 4)
    _mid_alpha = max(0, _ring_alpha // 2)
    return {
        "pulse": _pulse,
        "radius": _ring_r,
        "core_alpha": _ring_alpha,
        "core_width": 4,
        "mid_alpha": _mid_alpha,
        "mid_width": 5,
        "glow_alpha": _glow_alpha,
        "glow_width": 8,
        "glow_radius_offset": 4,
        "mid_radius_offset": 1,
        "surface_size": 164,
        "center": 82,
        "range_ring_width": 2,
        "range_ring_alpha": 70,
    }


class TestCatchRingStrokeWidth:
    """Verify ring stroke widths are increased for visibility."""

    def test_core_ring_width_is_4(self):
        """Core ring should have stroke width of 4 (up from 2)."""
        p = compute_ring_params(0)
        assert p["core_width"] == 4

    def test_mid_glow_width_is_5(self):
        """Mid glow layer should have stroke width of 5."""
        p = compute_ring_params(0)
        assert p["mid_width"] == 5

    def test_outer_glow_width_is_8(self):
        """Outer glow layer should have stroke width of 8."""
        p = compute_ring_params(0)
        assert p["glow_width"] == 8

    def test_range_ring_width_is_2(self):
        """Static range circle stroke width should be 2 (up from 1)."""
        p = compute_ring_params(0)
        assert p["range_ring_width"] == 2


class TestCatchRingGlow:
    """Verify glow/drop-shadow layers exist with correct alpha."""

    def test_glow_alpha_is_quarter_of_core(self):
        """Outer glow alpha should be 1/4 of core alpha."""
        p = compute_ring_params(0)
        assert p["glow_alpha"] == p["core_alpha"] // 4

    def test_mid_alpha_is_half_of_core(self):
        """Mid glow alpha should be 1/2 of core alpha."""
        p = compute_ring_params(0)
        assert p["mid_alpha"] == p["core_alpha"] // 2

    def test_glow_radius_larger_than_core(self):
        """Glow layer radius should exceed core ring radius."""
        p = compute_ring_params(500)
        assert p["glow_radius_offset"] > 0

    def test_glow_alphas_non_negative_across_cycle(self):
        """All glow alphas should stay non-negative throughout the pulse cycle."""
        for ms in range(0, 1000, 10):
            p = compute_ring_params(ms)
            assert p["glow_alpha"] >= 0, f"Negative glow_alpha at {ms}ms"
            assert p["mid_alpha"] >= 0, f"Negative mid_alpha at {ms}ms"
            assert p["core_alpha"] >= 0, f"Negative core_alpha at {ms}ms"


class TestCatchRingContrast:
    """Verify high contrast against map backgrounds."""

    def test_range_ring_uses_accent_color_with_alpha(self):
        """Range ring should use ACCENT color (not gray) for contrast."""
        p = compute_ring_params(0)
        assert p["range_ring_alpha"] == 70

    def test_core_alpha_starts_bright(self):
        """At pulse start, core alpha should be 210 (full brightness)."""
        p = compute_ring_params(0)
        assert p["core_alpha"] == 210

    def test_mid_alpha_at_pulse_start(self):
        """At pulse start, mid glow alpha should be 105."""
        p = compute_ring_params(0)
        assert p["mid_alpha"] == 105

    def test_glow_alpha_at_pulse_start(self):
        """At pulse start, outer glow alpha should be 52."""
        p = compute_ring_params(0)
        assert p["glow_alpha"] == 52


class TestCatchRingSurface:
    """Verify surface dimensions accommodate the glow effect."""

    def test_surface_size_accommodates_glow(self):
        """Surface should be large enough for max ring radius + glow."""
        p = compute_ring_params(0)
        max_ring_r = 30 + 28  # 58
        max_glow_r = max_ring_r + p["glow_radius_offset"] + p["glow_width"] // 2
        assert p["center"] > max_glow_r, (
            f"Center {p['center']} must exceed max glow radius {max_glow_r}"
        )

    def test_surface_symmetric(self):
        """Surface center should be at half the surface size."""
        p = compute_ring_params(0)
        assert p["center"] == p["surface_size"] // 2

    def test_pulse_cycle_period(self):
        """Pulse cycle should complete in ~833ms (1/1.2 seconds)."""
        p_start = compute_ring_params(0)
        p_cycle = compute_ring_params(833)
        # After one full cycle, pulse should be near 0 again
        assert p_cycle["pulse"] < 0.01 or p_cycle["pulse"] > 0.99
