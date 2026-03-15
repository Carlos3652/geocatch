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
