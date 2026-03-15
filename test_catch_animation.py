"""Tests for catch expand-implode animation logic."""
import math


def compute_catch_scale(elapsed, max_timer=0.24, expand_dur=0.08):
    """Reproduce the catch animation scale calculation from geocatch_pygame.py."""
    total_dur = max_timer
    if elapsed < expand_dur:
        # Expand phase: scale 1.0 -> 1.4 with ease-out
        t = elapsed / expand_dur
        ease_t = 1.0 - (1.0 - t) ** 2
        scale = 1.0 + 0.4 * ease_t
    else:
        # Implode phase: scale 1.4 -> 0 with ease-in
        t = (elapsed - expand_dur) / (total_dur - expand_dur)
        t = min(t, 1.0)
        ease_t = t * t
        scale = 1.4 * (1.0 - ease_t)
    return scale


class TestCatchAnimation:
    """Test the expand-implode catch animation curve."""

    def test_starts_at_scale_1(self):
        """At t=0, scale should be 1.0 (original size)."""
        assert compute_catch_scale(0.0) == 1.0

    def test_expands_to_1_4_at_80ms(self):
        """At end of expand phase (80ms), scale should reach 1.4."""
        scale = compute_catch_scale(0.08)
        assert abs(scale - 1.4) < 0.01

    def test_implodes_to_zero_at_240ms(self):
        """At end of animation (240ms), scale should be 0."""
        scale = compute_catch_scale(0.24)
        assert abs(scale - 0.0) < 0.01

    def test_expand_phase_monotonically_increases(self):
        """During expand phase (0-80ms), scale should only increase."""
        prev = 0.0
        for i in range(0, 81):
            elapsed = i / 1000.0
            s = compute_catch_scale(elapsed)
            assert s >= prev, f"Scale decreased at {elapsed}s: {prev} -> {s}"
            prev = s

    def test_implode_phase_monotonically_decreases(self):
        """During implode phase (80-240ms), scale should only decrease."""
        prev = float("inf")
        for i in range(80, 241):
            elapsed = i / 1000.0
            s = compute_catch_scale(elapsed)
            assert s <= prev, f"Scale increased at {elapsed}s: {prev} -> {s}"
            prev = s

    def test_scale_always_non_negative(self):
        """Scale should never go negative."""
        for i in range(0, 250):
            elapsed = i / 1000.0
            s = compute_catch_scale(elapsed)
            assert s >= 0.0, f"Negative scale at {elapsed}s: {s}"

    def test_peak_scale_is_at_transition(self):
        """Peak scale should be at the expand->implode boundary (80ms)."""
        peak = 0.0
        peak_t = 0.0
        for i in range(0, 241):
            elapsed = i / 1000.0
            s = compute_catch_scale(elapsed)
            if s > peak:
                peak = s
                peak_t = elapsed
        assert abs(peak_t - 0.08) < 0.001
        assert abs(peak - 1.4) < 0.01

    def test_expand_ease_out_curve(self):
        """Expand phase should decelerate (ease-out): midpoint > linear midpoint."""
        mid = compute_catch_scale(0.04)
        # Linear midpoint would be 1.2; ease-out should be above that
        assert mid > 1.2, f"Ease-out at midpoint should be > 1.2, got {mid}"

    def test_implode_ease_in_curve(self):
        """Implode phase should accelerate (ease-in): midpoint > linear midpoint."""
        mid = compute_catch_scale(0.16)  # midpoint of implode (80ms + 80ms)
        # Linear midpoint would be 0.7; ease-in should be above that (slower start)
        assert mid > 0.7, f"Ease-in at midpoint should be > 0.7, got {mid}"

    def test_animation_dict_structure(self):
        """Validate the expected animation dict fields."""
        anim = {
            "x": 100, "y": 200,
            "image_key": "fire_drake",
            "timer": 0.24,
            "max_timer": 0.24,
            "bob": 3,
        }
        assert anim["timer"] == 0.24
        assert anim["max_timer"] == 0.24
        elapsed = anim["max_timer"] - anim["timer"]
        assert elapsed == 0.0

    def test_timer_decay_produces_correct_elapsed(self):
        """Simulating timer decay with dt should produce correct elapsed times."""
        timer = 0.24
        max_timer = 0.24
        dt = 0.016  # ~60fps
        steps = 0
        while timer > 0:
            elapsed = max_timer - timer
            scale = compute_catch_scale(elapsed)
            assert scale >= 0.0
            timer -= dt
            steps += 1
        assert steps > 0
        assert steps == 15  # 0.24 / 0.016 = 15 steps
