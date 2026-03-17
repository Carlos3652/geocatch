"""Tests that all trainer-fallback branches use the pre-rendered _trainer_fallback
surface instead of calling font.render("T", …) inline (gc-crit-03)."""

import ast
import re
import textwrap
import pytest

SRC = "geocatch_pygame.py"


def _read_source():
    with open(SRC, encoding="utf-8") as f:
        return f.read()


class TestTrainerFallbackUsage:
    """Ensure no inline font.render("T", ...) calls exist outside the definition."""

    def test_no_inline_font_render_T(self):
        """Only the _trainer_fallback definition line should call font.render("T", ...)."""
        source = _read_source()
        pattern = re.compile(r'font\.render\(\s*"T"')
        matches = []
        for i, line in enumerate(source.splitlines(), 1):
            if pattern.search(line):
                matches.append((i, line.strip()))

        # Filter out the definition itself (should contain '_trainer_fallback =')
        inline_calls = [
            (num, txt) for num, txt in matches
            if "_trainer_fallback" not in txt
        ]
        assert inline_calls == [], (
            f"Found inline font.render(\"T\", ...) instead of _trainer_fallback "
            f"at line(s): {inline_calls}"
        )

    def test_trainer_fallback_defined(self):
        """_trainer_fallback should be defined at module level."""
        source = _read_source()
        assert "_trainer_fallback = font.render" in source

    def test_trainer_fallback_used_in_character_select_selected(self):
        """Character-select selected card branch should reference _trainer_fallback."""
        source = _read_source()
        # Find the block between 'if is_sel:' and 'else:' that contains card_y + 40
        # It should use _trainer_fallback, not fb
        lines = source.splitlines()
        found = False
        for line in lines:
            if "_trainer_fallback" in line and "card_y + 40" in line:
                found = True
                break
        assert found, "Selected card branch should use _trainer_fallback with card_y + 40"

    def test_trainer_fallback_used_in_character_select_normal(self):
        """Character-select normal card branch should reference _trainer_fallback."""
        source = _read_source()
        lines = source.splitlines()
        found = False
        for line in lines:
            if "_trainer_fallback" in line and "card_y + 30" in line:
                found = True
                break
        assert found, "Normal card branch should use _trainer_fallback with card_y + 30"

    def test_trainer_fallback_used_in_gameplay(self):
        """Gameplay player-draw branch should reference _trainer_fallback."""
        source = _read_source()
        lines = source.splitlines()
        found = False
        for line in lines:
            if "_trainer_fallback" in line and "player_x" in line:
                found = True
                break
        assert found, "Gameplay fallback branch should blit _trainer_fallback at player_x"

    def test_total_trainer_fallback_usages(self):
        """_trainer_fallback should appear at least 4 times: 1 def + 3 blit usages."""
        source = _read_source()
        count = source.count("_trainer_fallback")
        assert count >= 4, (
            f"Expected >= 4 occurrences of _trainer_fallback, found {count}"
        )
