"""Tests for gc-23: _go_anim_done and cache attrs reset in reset_game().

Validates that:
- _go_anim_done is set to False after reset_game()
- reset_game._sc_cache and _tm_cache are deleted after reset_game()

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


class TestCacheAttrsCleared:
    """Fix B: _sc_cache and _tm_cache must not exist after reset_game()."""

    def test_sc_cache_removed_after_reset(self):
        """reset_game._sc_cache should not exist after reset_game()."""
        gm.reset_game._sc_cache = (0, "fake_surface")
        gm.reset_game()
        assert not hasattr(gm.reset_game, '_sc_cache')

    def test_tm_cache_removed_after_reset(self):
        """reset_game._tm_cache should not exist after reset_game()."""
        gm.reset_game._tm_cache = (60, "fake_surface")
        gm.reset_game()
        assert not hasattr(gm.reset_game, '_tm_cache')

    def test_both_caches_removed_after_reset(self):
        """Both _sc_cache and _tm_cache should be gone after reset_game()."""
        gm.reset_game._sc_cache = (0, "s1")
        gm.reset_game._tm_cache = (0, "s2")
        gm.reset_game()
        assert not hasattr(gm.reset_game, '_sc_cache')
        assert not hasattr(gm.reset_game, '_tm_cache')

    def test_no_error_when_caches_absent(self):
        """reset_game() should not raise when caches were never set."""
        # Ensure they don't exist
        if hasattr(gm.reset_game, '_sc_cache'):
            del gm.reset_game._sc_cache
        if hasattr(gm.reset_game, '_tm_cache'):
            del gm.reset_game._tm_cache
        # Should not raise
        gm.reset_game()
        assert not hasattr(gm.reset_game, '_sc_cache')
        assert not hasattr(gm.reset_game, '_tm_cache')


class TestResetGameEdgeCases:
    """Additional edge-case coverage for reset_game()."""

    def test_go_anim_done_reset_after_multiple_toggles(self):
        """_go_anim_done is False even after toggling multiple times."""
        gm._go_anim_done = True
        gm._go_anim_done = False
        gm._go_anim_done = True
        gm.reset_game()
        assert gm._go_anim_done is False

    def test_cache_with_none_value_still_removed(self):
        """Cache attrs set to None are still removed."""
        gm.reset_game._sc_cache = None
        gm.reset_game._tm_cache = None
        gm.reset_game()
        assert not hasattr(gm.reset_game, '_sc_cache')
        assert not hasattr(gm.reset_game, '_tm_cache')

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
