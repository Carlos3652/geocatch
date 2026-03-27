"""Tests for gc-23/gc-high-03: _go_anim_done, anim vars, and caches reset in reset_game().

Validates that:
- _go_anim_done is set to False after reset_game()
- _go_anim_timer and _go_anim_score are reset to 0 after reset_game() (gc-high-04)
- module-level _sc_cache and _tm_cache are set to None after reset_game() (gc-high-03)
- module-level _name_entry_cache is set to None after reset_game() (gc-high-05)

NOTE: We do NOT call pygame.init() or pygame.display in this file.
The game module handles its own initialization at import time;
we only set headless env-vars so no real window is created.
"""
import os
import sys

# Headless drivers BEFORE importing pygame / the game module
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(__file__))
import geocatch_pygame as gm


class TestGoAnimDoneReset:
    """Fix A: _go_anim_done must be False after reset_game()."""

    def test_go_anim_done_false_after_reset(self):
        """_go_anim_done should be False after calling reset_game()."""
        gm._go_anim_done = True
        gm.reset_game()
        assert gm._go_anim_done is False

    def test_go_anim_done_stays_false_if_already_false(self):
        """_go_anim_done remains False when it was already False."""
        gm._go_anim_done = False
        gm.reset_game()
        assert gm._go_anim_done is False


class TestGoAnimVarsReset:
    """gc-high-04: _go_anim_timer and _go_anim_score must be reset to 0."""

    def test_go_anim_timer_reset_to_zero(self):
        """_go_anim_timer should be 0.0 after reset_game()."""
        gm._go_anim_timer = 12.5
        gm.reset_game()
        assert gm._go_anim_timer == 0.0

    def test_go_anim_score_reset_to_zero(self):
        """_go_anim_score should be 0 after reset_game()."""
        gm._go_anim_score = 9999
        gm.reset_game()
        assert gm._go_anim_score == 0

    def test_go_anim_vars_reset_when_already_zero(self):
        """_go_anim_timer/_go_anim_score stay 0 when already 0."""
        gm._go_anim_timer = 0.0
        gm._go_anim_score = 0
        gm.reset_game()
        assert gm._go_anim_timer == 0.0
        assert gm._go_anim_score == 0


class TestCacheVarsCleared:
    """gc-high-03: module-level _sc_cache and _tm_cache must be None after reset_game()."""

    def test_sc_cache_none_after_reset(self):
        """_sc_cache should be None after reset_game()."""
        gm._sc_cache = (0, "fake_surface")
        gm.reset_game()
        assert gm._sc_cache is None

    def test_tm_cache_none_after_reset(self):
        """_tm_cache should be None after reset_game()."""
        gm._tm_cache = ((60, False), "fake_surface")
        gm.reset_game()
        assert gm._tm_cache is None

    def test_both_caches_none_after_reset(self):
        """Both _sc_cache and _tm_cache should be None after reset_game()."""
        gm._sc_cache = (0, "s1")
        gm._tm_cache = ((0, False), "s2")
        gm.reset_game()
        assert gm._sc_cache is None
        assert gm._tm_cache is None

    def test_no_error_when_caches_already_none(self):
        """reset_game() should not raise when caches are already None."""
        gm._sc_cache = None
        gm._tm_cache = None
        gm.reset_game()
        assert gm._sc_cache is None
        assert gm._tm_cache is None


class TestNameEntryCacheCleared:
    """gc-high-05: module-level _name_entry_cache must be None after reset_game()."""

    def test_name_entry_cache_none_after_reset(self):
        """_name_entry_cache should be None after reset_game()."""
        gm._name_entry_cache = ("HELLO|", "fake_surface")
        gm.reset_game()
        assert gm._name_entry_cache is None

    def test_name_entry_cache_already_none_no_error(self):
        """reset_game() should not raise when _name_entry_cache is already None."""
        gm._name_entry_cache = None
        gm.reset_game()
        assert gm._name_entry_cache is None


class TestResetGameEdgeCases:
    """Additional edge-case coverage for reset_game()."""

    def test_go_anim_done_reset_after_multiple_toggles(self):
        """_go_anim_done is False even after toggling multiple times."""
        gm._go_anim_done = True
        gm._go_anim_done = False
        gm._go_anim_done = True
        gm.reset_game()
        assert gm._go_anim_done is False

    def test_score_resets_to_zero(self):
        """score should be 0 after reset_game() (sanity check)."""
        gm.score = 999
        gm.reset_game()
        assert gm.score == 0

    def test_go_cache_resets_to_none(self):
        """_go_cache should be None after reset_game()."""
        gm._go_cache = "stale"
        gm.reset_game()
        assert gm._go_cache is None
