<<<<<<< HEAD
"""Tests for catch burst particle effect."""
import math
import random


def spawn_catch_particles(x, y, color, bob=0, rng=None):
    """Reproduce the catch particle spawning logic from geocatch_pygame.py."""
    if rng is None:
        rng = random
    count = rng.randint(8, 12)
    particles = []
    for i in range(count):
        angle = 2 * math.pi * i / count + rng.uniform(-0.3, 0.3)
        speed = rng.uniform(60, 140)
        particles.append({
            "x": float(x),
            "y": float(y) + bob,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": 0.5,
            "max_life": 0.5,
            "color": color,
            "r": rng.randint(2, 4),
        })
    return particles


def update_particles(particles, dt):
    """Simulate one frame of particle update."""
    for cp in particles:
        cp["x"] += cp["vx"] * dt
        cp["y"] += cp["vy"] * dt
        cp["life"] -= dt
    return [cp for cp in particles if cp["life"] > 0]


class TestCatchParticles:
    """Test the catch burst particle system."""

    def test_spawn_count_in_range(self):
        """Should spawn between 8 and 12 particles."""
        for _ in range(50):
            particles = spawn_catch_particles(100, 200, (255, 107, 0))
            assert 8 <= len(particles) <= 12

    def test_particles_originate_at_catch_point(self):
        """All particles should start at the catch position."""
        particles = spawn_catch_particles(150, 250, (59, 159, 212))
        for p in particles:
            assert p["x"] == 150.0
            assert p["y"] == 250.0

    def test_bob_offset_applied(self):
        """Bob offset should shift the y start position."""
        particles = spawn_catch_particles(100, 200, (76, 175, 80), bob=5)
        for p in particles:
            assert p["y"] == 205.0

    def test_particles_radiate_outward(self):
        """After one update step, all particles should be farther from origin."""
        particles = spawn_catch_particles(300, 300, (255, 215, 0))
        dt = 0.016
        for p in particles:
            ox, oy = p["x"], p["y"]
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            dist = math.hypot(p["x"] - ox, p["y"] - oy)
            assert dist > 0, "Particle should move away from origin"

    def test_particles_have_velocity(self):
        """Each particle should have non-zero velocity (radial direction)."""
        particles = spawn_catch_particles(100, 200, (255, 107, 0))
        for p in particles:
            speed = math.hypot(p["vx"], p["vy"])
            assert 60 <= speed <= 140, f"Speed {speed} out of range [60, 140]"

    def test_velocities_spread_around_circle(self):
        """Particle angles should cover a full circle (rough check)."""
        rng = random.Random(42)
        particles = spawn_catch_particles(0, 0, (255, 0, 0), rng=rng)
        angles = [math.atan2(p["vy"], p["vx"]) for p in particles]
        angles.sort()
        # With 8-12 particles spread around 2π, max gap should be < π
        for i in range(1, len(angles)):
            gap = angles[i] - angles[i - 1]
            assert gap < math.pi, f"Gap {gap:.2f} too large between consecutive angles"

    def test_life_starts_at_half_second(self):
        """All particles should have 0.5s lifetime."""
        particles = spawn_catch_particles(100, 200, (255, 107, 0))
        for p in particles:
            assert p["life"] == 0.5
            assert p["max_life"] == 0.5

    def test_particles_expire_after_half_second(self):
        """All particles should be removed after 0.5 seconds of updates."""
        particles = spawn_catch_particles(100, 200, (255, 107, 0))
        dt = 0.016  # ~60fps
        steps = 0
        while particles:
            particles = update_particles(particles, dt)
            steps += 1
            assert steps <= 100, "Particles should expire within reasonable time"
        # 0.5 / 0.016 = 31.25, so should take ~32 steps
        assert 30 <= steps <= 33, f"Expected ~31 steps, got {steps}"

    def test_color_preserved(self):
        """Particles should store the creature's color."""
        color = (156, 39, 176)
        particles = spawn_catch_particles(100, 200, color)
        for p in particles:
            assert p["color"] == color

    def test_radius_in_range(self):
        """Particle radius should be between 2 and 4."""
        for _ in range(20):
            particles = spawn_catch_particles(100, 200, (255, 107, 0))
            for p in particles:
                assert 2 <= p["r"] <= 4

    def test_fade_color_modulation(self):
        """Color should fade to black as life approaches zero (RGB * life_frac)."""
        color = (200, 100, 50)
        particles = spawn_catch_particles(100, 200, color)
        p = particles[0]
        # At full life, frac = 1.0 → full color
        frac = p["life"] / p["max_life"]
        assert frac == 1.0
        modulated = (int(color[0] * frac), int(color[1] * frac), int(color[2] * frac))
        assert modulated == color
        # At half life, frac = 0.5 → half color
        p["life"] = 0.25
        frac = p["life"] / p["max_life"]
        modulated = (int(color[0] * frac), int(color[1] * frac), int(color[2] * frac))
        assert modulated == (100, 50, 25)
        # At zero life, frac = 0 → black
        p["life"] = 0.0
        frac = max(0.0, p["life"] / p["max_life"])
        modulated = (int(color[0] * frac), int(color[1] * frac), int(color[2] * frac))
        assert modulated == (0, 0, 0)

    def test_radius_shrinks_with_life(self):
        """Rendered radius should shrink as life fraction decreases."""
        p = {"r": 4, "life": 0.5, "max_life": 0.5}
        frac = p["life"] / p["max_life"]
        assert max(1, int(p["r"] * frac)) == 4
        p["life"] = 0.25
        frac = p["life"] / p["max_life"]
        assert max(1, int(p["r"] * frac)) == 2
        p["life"] = 0.05
        frac = p["life"] / p["max_life"]
        assert max(1, int(p["r"] * frac)) == 1

    def test_particle_dict_structure(self):
        """Validate expected particle dict fields."""
        particles = spawn_catch_particles(100, 200, (255, 0, 0))
        required_keys = {"x", "y", "vx", "vy", "life", "max_life", "color", "r"}
        for p in particles:
            assert set(p.keys()) == required_keys
=======
"""Tests for the catch particle burst effect."""
import math
import random
import unittest


class TestCatchParticles(unittest.TestCase):
    """Unit tests for catch particle spawning and lifecycle."""

    def _spawn_particles(self, cx, cy, color=(255, 107, 0)):
        """Simulate particle spawning logic from the game."""
        particles = []
        count = random.randint(8, 12)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 180)
            particles.append({
                "x": float(cx),
                "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 0.5,
                "max_life": 0.5,
                "color": (
                    min(255, color[0] + random.randint(-30, 30)),
                    min(255, color[1] + random.randint(-30, 30)),
                    min(255, color[2] + random.randint(-30, 30)),
                ),
                "r": random.randint(2, 5),
            })
        return particles

    def _update_particles(self, particles, dt):
        """Simulate particle update logic."""
        for cp in particles:
            cp["x"] += cp["vx"] * dt
            cp["y"] += cp["vy"] * dt
            cp["life"] -= dt
        return [cp for cp in particles if cp["life"] > 0]

    def test_spawn_count_range(self):
        """Spawns between 8 and 12 particles."""
        random.seed(42)
        for _ in range(50):
            particles = self._spawn_particles(100, 200)
            self.assertGreaterEqual(len(particles), 8)
            self.assertLessEqual(len(particles), 12)

    def test_particles_start_at_catch_point(self):
        """All particles start at the creature's position."""
        particles = self._spawn_particles(300, 400)
        for p in particles:
            self.assertAlmostEqual(p["x"], 300.0)
            self.assertAlmostEqual(p["y"], 400.0)

    def test_particles_have_outward_velocity(self):
        """Each particle has non-zero velocity (radiating outward)."""
        particles = self._spawn_particles(100, 100)
        for p in particles:
            speed = math.hypot(p["vx"], p["vy"])
            self.assertGreaterEqual(speed, 80)
            self.assertLessEqual(speed, 180)

    def test_particles_move_over_time(self):
        """Particles move away from spawn point after updates."""
        particles = self._spawn_particles(200, 200)
        dt = 1 / 60
        for _ in range(5):
            particles = self._update_particles(particles, dt)
        for p in particles:
            dist = math.hypot(p["x"] - 200, p["y"] - 200)
            self.assertGreater(dist, 0)

    def test_particles_expire_after_half_second(self):
        """All particles should be gone after 0.5 seconds."""
        particles = self._spawn_particles(100, 100)
        dt = 1 / 60
        frames = int(0.55 / dt)  # slightly more than 0.5s
        for _ in range(frames):
            particles = self._update_particles(particles, dt)
        self.assertEqual(len(particles), 0)

    def test_particles_alive_before_expiry(self):
        """Particles should still exist before 0.5 seconds."""
        particles = self._spawn_particles(100, 100)
        dt = 1 / 60
        frames = int(0.3 / dt)  # 0.3 seconds
        for _ in range(frames):
            particles = self._update_particles(particles, dt)
        self.assertGreater(len(particles), 0)

    def test_life_fraction_for_alpha(self):
        """Life fraction decreases linearly and drives alpha/size fade."""
        particles = self._spawn_particles(100, 100)
        dt = 1 / 60
        # After ~0.25s (half the lifetime)
        for _ in range(15):
            particles = self._update_particles(particles, dt)
        for p in particles:
            frac = p["life"] / p["max_life"]
            self.assertGreater(frac, 0.0)
            self.assertLess(frac, 1.0)

    def test_color_variation(self):
        """Particle colors vary slightly from base creature color."""
        random.seed(123)
        base = (255, 107, 0)
        particles = self._spawn_particles(100, 100, base)
        colors_differ = False
        for p in particles:
            if p["color"] != base:
                colors_differ = True
                break
        self.assertTrue(colors_differ, "At least some particles should have color variation")

    def test_particle_radius_range(self):
        """Particle radius should be between 2 and 5."""
        particles = self._spawn_particles(100, 100)
        for p in particles:
            self.assertGreaterEqual(p["r"], 2)
            self.assertLessEqual(p["r"], 5)


if __name__ == "__main__":
    unittest.main()
>>>>>>> mini-me/gc-02-catch-particles
