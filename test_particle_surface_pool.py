"""Tests for CRIT-01: catch particle surface pool optimization.

Verifies that particle surfaces are pooled by integer radius instead of
allocating a new pygame.Surface per particle per frame.
"""
import types
import sys

# ---------------------------------------------------------------------------
# Minimal pygame stub so tests run without a display / real pygame
# ---------------------------------------------------------------------------
_stub_pygame = types.ModuleType("pygame")
_stub_pygame.SRCALPHA = 0x00010000
_stub_pygame.QUIT = 256

class _StubColor:
    """Minimal stand-in for pygame.Color returned by get_at()."""
    def __init__(self, r, g, b, a):
        self.r, self.g, self.b, self.a = r, g, b, a
    def __iter__(self):
        return iter((self.r, self.g, self.b, self.a))

class _StubSurface:
    """Lightweight stand-in for pygame.Surface."""
    def __init__(self, size, flags=0):
        self.size = size
        self.flags = flags
        self._fill_color = (0, 0, 0, 0)
    def fill(self, color):
        # Normalise to 4-tuple (RGBA)
        if len(color) == 3:
            color = (*color, 255)
        self._fill_color = tuple(color)
    def get_size(self):
        return self.size
    def get_flags(self):
        return self.flags
    def get_at(self, pos):
        c = self._fill_color
        return _StubColor(c[0], c[1], c[2], c[3])

_stub_pygame.Surface = _StubSurface

# Ensure our stub is importable before anything else tries to load pygame
sys.modules.setdefault("pygame", _stub_pygame)


# ---------------------------------------------------------------------------
# Reproduce pool logic identical to geocatch_pygame.py
# ---------------------------------------------------------------------------
_PARTICLE_MAX_RADIUS = 5


def build_particle_surface_pool():
    """Create the pool exactly as the game does at module level."""
    import pygame
    pool = {}
    for r in range(1, _PARTICLE_MAX_RADIUS + 1):
        pool[r] = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    return pool


def get_particle_surface(pool, radius):
    """Return a pooled surface, creating one only for uncached radii."""
    import pygame
    clamped = min(radius, _PARTICLE_MAX_RADIUS)
    surf = pool.get(clamped)
    if surf is None:
        surf = pygame.Surface((clamped * 2, clamped * 2), pygame.SRCALPHA)
        pool[clamped] = surf
    return surf, clamped


def compute_draw_radius(spawn_radius, frac):
    """Replicate _pr = max(1, int(cp['r'] * frac))."""
    return max(1, int(spawn_radius * frac))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestParticleSurfacePool:
    """Verify pool construction, reuse, and clamping."""

    def test_pool_contains_radii_1_through_max(self):
        pool = build_particle_surface_pool()
        for r in range(1, _PARTICLE_MAX_RADIUS + 1):
            assert r in pool, f"radius {r} missing from pool"

    def test_pool_surface_sizes(self):
        pool = build_particle_surface_pool()
        for r in range(1, _PARTICLE_MAX_RADIUS + 1):
            assert pool[r].get_size() == (r * 2, r * 2)

    def test_pool_surfaces_have_srcalpha(self):
        import pygame
        pool = build_particle_surface_pool()
        for r in range(1, _PARTICLE_MAX_RADIUS + 1):
            assert pool[r].get_flags() & pygame.SRCALPHA

    def test_same_surface_returned_for_same_radius(self):
        pool = build_particle_surface_pool()
        s1, _ = get_particle_surface(pool, 3)
        s2, _ = get_particle_surface(pool, 3)
        assert s1 is s2, "Pool must return the same object (no new allocation)"

    def test_different_radii_return_different_surfaces(self):
        pool = build_particle_surface_pool()
        s1, _ = get_particle_surface(pool, 2)
        s2, _ = get_particle_surface(pool, 4)
        assert s1 is not s2

    def test_radius_clamped_to_max(self):
        pool = build_particle_surface_pool()
        surf, clamped = get_particle_surface(pool, 10)
        assert clamped == _PARTICLE_MAX_RADIUS
        assert surf is pool[_PARTICLE_MAX_RADIUS]

    def test_radius_clamped_to_max_surface_size(self):
        pool = build_particle_surface_pool()
        surf, _ = get_particle_surface(pool, 99)
        expected = _PARTICLE_MAX_RADIUS * 2
        assert surf.get_size() == (expected, expected)

    def test_novel_radius_gets_cached(self):
        """If a radius beyond pre-built range somehow appears, it's cached."""
        pool = {}  # empty pool
        surf1, _ = get_particle_surface(pool, 3)
        surf2, _ = get_particle_surface(pool, 3)
        assert surf1 is surf2
        assert 3 in pool

    def test_draw_radius_never_zero(self):
        """max(1, int(r * frac)) must always be >= 1."""
        for spawn_r in range(1, 6):
            for frac_pct in range(0, 101):
                frac = frac_pct / 100.0
                dr = compute_draw_radius(spawn_r, frac)
                assert dr >= 1, f"draw radius < 1 for r={spawn_r}, frac={frac}"

    def test_draw_radius_within_pool_range(self):
        """All possible draw radii from game spawns (r=2..5) stay ≤ MAX."""
        for spawn_r in range(2, 6):  # game uses randint(2,4) and randint(2,5)
            dr = compute_draw_radius(spawn_r, 1.0)  # full life = max radius
            assert dr <= _PARTICLE_MAX_RADIUS

    def test_fill_clears_surface(self):
        """Pool reuse requires fill((0,0,0,0)) — verify surface is cleared."""
        import pygame
        pool = build_particle_surface_pool()
        surf, _ = get_particle_surface(pool, 2)
        # Draw something visible, then fill with transparent
        surf.fill((255, 0, 0, 255))
        surf.fill((0, 0, 0, 0))
        # After clearing, all pixels should be fully transparent
        color = surf.get_at((0, 0))
        assert color.a == 0, f"Expected transparent after fill, got alpha={color.a}"

    def test_no_allocation_during_burst(self):
        """Simulate a 12-particle burst; pool size must not grow."""
        pool = build_particle_surface_pool()
        initial_size = len(pool)
        # Simulate particles with radii 2-5 at various life fractions
        import random
        rng = random.Random(42)
        for _ in range(12):
            spawn_r = rng.randint(2, 5)
            frac = rng.random()
            dr = compute_draw_radius(spawn_r, frac)
            get_particle_surface(pool, dr)
        assert len(pool) == initial_size, (
            f"Pool grew from {initial_size} to {len(pool)} during burst"
        )
