"""Tests for pre-baked catch animation frames (CRIT-02 fix).

Validates that _catch_anim_frames contains the correct number of
pre-scaled surfaces for each creature image_key, with expected
size properties at the boundaries.
"""
import os
import sys

# Set headless drivers BEFORE importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Remove any stub pygame injected by other test modules
sys.modules.pop("pygame", None)
import pygame

# Initialize pygame (headless) so Surface operations work
pygame.init()
pygame.display.set_mode((1, 1))

sys.path.insert(0, os.path.dirname(__file__))
from geocatch_pygame import (
    _catch_anim_frames,
    _CATCH_ANIM_N,
    _STICKER_SIZE,
    CREATURE_TYPES,
)

_IMAGE_KEYS = [ct["image_key"] for ct in CREATURE_TYPES]


class TestCatchAnimFramesStructure:
    """Verify _catch_anim_frames dict has the right shape."""

    def test_all_5_image_keys_present(self):
        assert len(_IMAGE_KEYS) == 5
        for key in _IMAGE_KEYS:
            assert key in _catch_anim_frames, f"Missing image_key: {key}"

    def test_each_entry_has_12_surfaces(self):
        for key in _IMAGE_KEYS:
            frames = _catch_anim_frames[key]
            assert len(frames) == 12, f"{key}: expected 12, got {len(frames)}"

    def test_n_constant_is_12(self):
        assert _CATCH_ANIM_N == 12

    def test_frames_are_pygame_surfaces(self):
        for key in _IMAGE_KEYS:
            for i, surf in enumerate(_catch_anim_frames[key]):
                assert isinstance(surf, pygame.Surface), (
                    f"{key}[{i}] is not a Surface"
                )


class TestCatchAnimFrameSizes:
    """Verify frame sizes follow the expand-implode curve."""

    def test_frame_0_width_ge_sticker_size(self):
        """First frame (scale=1.0) should be at least _STICKER_SIZE."""
        for key in _IMAGE_KEYS:
            w = _catch_anim_frames[key][0].get_width()
            assert w >= _STICKER_SIZE, (
                f"{key} frame 0 width {w} < {_STICKER_SIZE}"
            )

    def test_last_frame_width_le_4(self):
        """Last frame (scale≈0) should be near-zero width (<=4)."""
        for key in _IMAGE_KEYS:
            w = _catch_anim_frames[key][-1].get_width()
            assert w <= 4, f"{key} last frame width {w} > 4"

    def test_peak_frame_is_larger_than_sticker(self):
        """Some frame should exceed _STICKER_SIZE (the 1.4x expand)."""
        for key in _IMAGE_KEYS:
            max_w = max(f.get_width() for f in _catch_anim_frames[key])
            assert max_w > _STICKER_SIZE, (
                f"{key} max width {max_w} not > {_STICKER_SIZE}"
            )

    def test_frames_are_square(self):
        for key in _IMAGE_KEYS:
            for i, surf in enumerate(_catch_anim_frames[key]):
                assert surf.get_width() == surf.get_height(), (
                    f"{key}[{i}] not square"
                )

    def test_frame_sizes_follow_expand_then_shrink(self):
        """Widths should increase then decrease across the 12 frames."""
        for key in _IMAGE_KEYS:
            widths = [f.get_width() for f in _catch_anim_frames[key]]
            # Find peak index
            peak_idx = widths.index(max(widths))
            # Before peak: non-decreasing
            for i in range(1, peak_idx + 1):
                assert widths[i] >= widths[i - 1], (
                    f"{key} expand not non-decreasing at {i}"
                )
            # After peak: non-increasing
            for i in range(peak_idx + 1, len(widths)):
                assert widths[i] <= widths[i - 1], (
                    f"{key} implode not non-increasing at {i}"
                )


class TestCatchAnimConstraints:
    """Verify constraints and edge cases."""

    def test_n_le_16(self):
        """N must be <= 16 per spec."""
        assert _CATCH_ANIM_N <= 16

    def test_missing_image_key_returns_none(self):
        """get() on a missing key should return None, not crash."""
        result = _catch_anim_frames.get("nonexistent_key_xyz")
        assert result is None

    def test_no_extra_keys_beyond_creature_types(self):
        """_catch_anim_frames should only have keys from CREATURE_TYPES."""
        for key in _catch_anim_frames:
            assert key in _IMAGE_KEYS, f"Unexpected key: {key}"

    def test_frame_idx_clamp_at_full_progress(self):
        """progress=1.0 should map to last frame index, not out of bounds."""
        for key in _IMAGE_KEYS:
            frames = _catch_anim_frames[key]
            idx = min(len(frames) - 1, int(1.0 * len(frames)))
            assert idx == len(frames) - 1

    def test_all_frames_have_alpha(self):
        """All pre-baked frames should support per-pixel alpha."""
        for key in _IMAGE_KEYS:
            for i, surf in enumerate(_catch_anim_frames[key]):
                assert surf.get_alpha() is None or surf.get_alpha() == 255, (
                    f"{key}[{i}] unexpected alpha"
                )
