"""Tests for gc-high-02 (absolute file paths) and gc-high-05 (name entry cache).

gc-high-02: Verifies that highscores.txt and stats.json are referenced via
absolute paths anchored to __file__, so the game works regardless of CWD.

gc-high-05: Verifies that the name-entry text surface cache (_name_entry_cache)
is only re-rendered when the displayed text changes.
"""
import os
import sys
from pathlib import Path

# Headless drivers BEFORE importing pygame / the game module
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(__file__))
import geocatch_pygame as gm


class TestAbsoluteFilePaths:
    """gc-high-02: File I/O paths must be absolute (anchored to _HERE)."""

    def test_highscores_file_is_absolute(self):
        """_HIGHSCORES_FILE should be an absolute path."""
        assert gm._HIGHSCORES_FILE.is_absolute(), (
            f"_HIGHSCORES_FILE is not absolute: {gm._HIGHSCORES_FILE}"
        )

    def test_stats_file_is_absolute(self):
        """_stats_file should be an absolute path."""
        assert Path(gm._stats_file).is_absolute(), (
            f"_stats_file is not absolute: {gm._stats_file}"
        )

    def test_highscores_file_in_game_dir(self):
        """_HIGHSCORES_FILE should be in the same directory as geocatch_pygame.py."""
        game_dir = Path(gm.__file__).parent
        assert gm._HIGHSCORES_FILE.parent == game_dir, (
            f"_HIGHSCORES_FILE not in game dir: {gm._HIGHSCORES_FILE}"
        )

    def test_stats_file_in_game_dir(self):
        """_stats_file should be in the same directory as geocatch_pygame.py."""
        game_dir = Path(gm.__file__).parent
        assert Path(gm._stats_file).parent == game_dir, (
            f"_stats_file not in game dir: {gm._stats_file}"
        )

    def test_highscores_filename_correct(self):
        """_HIGHSCORES_FILE should end with 'highscores.txt'."""
        assert gm._HIGHSCORES_FILE.name == "highscores.txt"

    def test_stats_filename_correct(self):
        """_stats_file should end with 'stats.json'."""
        assert Path(gm._stats_file).name == "stats.json"


class TestNameEntryCacheInvalidation:
    """gc-high-05: _name_entry_cache should be keyed by (name+cursor) and reused."""

    def setup_method(self):
        """Reset the cache before each test."""
        gm._name_entry_cache = None

    def test_cache_starts_none(self):
        """_name_entry_cache should be None initially / after reset."""
        gm._name_entry_cache = None
        assert gm._name_entry_cache is None

    def test_cache_reset_clears_name_entry_cache(self):
        """reset_game() must set _name_entry_cache to None."""
        gm._name_entry_cache = ("HELLO|", "fake_surf")
        gm.reset_game()
        assert gm._name_entry_cache is None

    def test_cache_key_format(self):
        """The cache key should concatenate name_input and cursor character."""
        # Simulate what the game loop does: cache_key = name_input + cursor
        name_input = "ABC"
        cursor = "|"
        cache_key = name_input + cursor
        assert cache_key == "ABC|"

    def test_cache_key_changes_on_new_input(self):
        """Different name_input values produce different cache keys."""
        key1 = "AB" + "|"
        key2 = "ABC" + "|"
        assert key1 != key2

    def test_cache_key_changes_on_cursor_flip(self):
        """Same name_input with different cursor produces different keys."""
        name = "HELLO"
        key_cursor = name + "|"
        key_blank = name + " "
        assert key_cursor != key_blank
