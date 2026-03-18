"""Tests that static tiny_font.render() calls have been pre-rendered outside the main loop."""

import re
import os
import pytest

SRC = os.path.join(os.path.dirname(__file__), "geocatch_pygame.py")


def _read_source():
    with open(SRC, encoding="utf-8") as f:
        return f.readlines()


def _find_line(lines, needle):
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return -1


class TestNoTinyFontRenderInMainLoop:
    """HIGH-03: No static tiny_font.render() inside the while running: main loop."""

    # These specific static strings must NOT be rendered inside the loop
    STATIC_STRINGS = ['"Your name"', "'Your name'", '"SUBMIT"', "'SUBMIT'",
                      '"ENTER or click SUBMIT"', "'ENTER or click SUBMIT'"]

    def test_no_static_tiny_font_render_after_while_running(self):
        lines = _read_source()
        loop_start = _find_line(lines, "while running:")
        assert loop_start > 0, "Could not find 'while running:' in source"
        for i in range(loop_start, len(lines)):
            line = lines[i]
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "tiny_font.render(" not in line:
                continue
            for s in self.STATIC_STRINGS:
                assert s not in line, (
                    f"Static tiny_font.render({s}) found inside main loop "
                    f"at line {i + 1}: {line.rstrip()}"
                )


class TestNoFontRenderInDrawWorld:
    """HIGH-04: No font.render() inside draw_world()."""

    def test_no_font_render_in_draw_world(self):
        lines = _read_source()
        start = _find_line(lines, "def draw_world(")
        assert start > 0, "Could not find draw_world() in source"
        # Scan until next top-level def/class (unindented)
        for i in range(start + 1, len(lines)):
            line = lines[i]
            # End of function: next top-level definition
            if line and not line[0].isspace() and (line.startswith("def ") or line.startswith("class ")):
                break
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            assert ".render(" not in stripped or "font" not in line, (
                f"font.render() found inside draw_world() at line {i + 1}: {line.rstrip()}"
            )


class TestPreRenderedCachesExist:
    """Verify pre-rendered surfaces are defined at module level."""

    @pytest.mark.parametrize("varname", [
        "_go_placeholder",
        "_go_submit_active",
        "_go_submit_inactive",
        "_go_enter_click_hint",
        "_disc_golf_label",
    ])
    def test_prerender_variable_defined(self, varname):
        lines = _read_source()
        found = any(line.startswith(f"{varname} =") or line.startswith(f"{varname}=") for line in lines)
        assert found, f"Pre-rendered variable {varname} not found at module level"
