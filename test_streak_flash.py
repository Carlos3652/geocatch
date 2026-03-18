"""Tests for streak milestone flash effect (#15)."""


# -- Extracted helpers matching geocatch_pygame.py logic --

STREAK_MILESTONES = {3, 5, 10}
STREAK_FLASH_DUR = 0.3
STREAK_FLASH_BORDER = 6


def should_trigger_flash(catch_streak):
    """Return True if the given streak count is a milestone."""
    return catch_streak in STREAK_MILESTONES


def compute_flash_alpha(timer, duration=STREAK_FLASH_DUR):
    """Compute the alpha value for the streak flash overlay.

    Returns an int in [0, 255] that fades linearly from 255 to 0
    as timer goes from duration down to 0.
    """
    if timer <= 0:
        return 0
    return int(255 * (timer / duration))


def decay_flash_timer(timer, dt):
    """Simulate one frame of flash timer decay. Returns new timer value."""
    if timer <= 0:
        return 0
    return max(0, timer - dt)


def simulate_catch_streak(catches, reset_at=None, dt=1 / 60):
    """Simulate a series of catches, optionally resetting at a given index.

    Returns a list of dicts with keys:
        - triggered: bool — whether this catch triggered a flash
        - streak: int — streak count after this catch
        - flash_timer: float — flash timer value after processing this catch

    If reset_at is provided, the streak resets to 0 at that index (bomb hit).
    Each step decays the flash timer by *dt* before processing the catch.
    """
    streak = 0
    flash_timer = 0.0
    results = []
    for i in range(catches):
        # Decay flash timer each step (simulates one frame between catches)
        flash_timer = decay_flash_timer(flash_timer, dt)
        if reset_at is not None and i == reset_at:
            streak = 0
        streak += 1
        triggered = should_trigger_flash(streak)
        if triggered:
            flash_timer = STREAK_FLASH_DUR
        results.append({
            "triggered": triggered,
            "streak": streak,
            "flash_timer": flash_timer,
        })
    return results


class TestStreakMilestones:
    """Test which streak counts trigger a flash."""

    def test_milestone_3(self):
        assert should_trigger_flash(3)

    def test_milestone_5(self):
        assert should_trigger_flash(5)

    def test_milestone_10(self):
        assert should_trigger_flash(10)

    def test_non_milestone_1(self):
        assert not should_trigger_flash(1)

    def test_non_milestone_2(self):
        assert not should_trigger_flash(2)

    def test_non_milestone_4(self):
        assert not should_trigger_flash(4)

    def test_non_milestone_6(self):
        assert not should_trigger_flash(6)

    def test_non_milestone_0(self):
        assert not should_trigger_flash(0)

    def test_non_milestone_7(self):
        assert not should_trigger_flash(7)

    def test_non_milestone_negative(self):
        """Negative values should never trigger a flash."""
        assert not should_trigger_flash(-1)

    def test_non_milestone_large(self):
        """Streak counts beyond defined milestones should not trigger."""
        assert not should_trigger_flash(11)
        assert not should_trigger_flash(20)
        assert not should_trigger_flash(100)

    def test_milestones_are_exact_set(self):
        """The milestone set must be exactly {3, 5, 10}."""
        assert STREAK_MILESTONES == {3, 5, 10}


class TestFlashAlpha:
    """Test the alpha fade curve for the flash effect."""

    def test_full_alpha_at_start(self):
        """At the moment the flash triggers, alpha should be 255."""
        assert compute_flash_alpha(STREAK_FLASH_DUR) == 255

    def test_zero_alpha_when_expired(self):
        """When timer reaches 0, alpha should be 0."""
        assert compute_flash_alpha(0) == 0

    def test_half_alpha_at_midpoint(self):
        """At halfway through the flash, alpha should be ~127."""
        alpha = compute_flash_alpha(STREAK_FLASH_DUR / 2)
        assert 126 <= alpha <= 128

    def test_negative_timer_gives_zero(self):
        """Negative timer should clamp to 0 alpha."""
        assert compute_flash_alpha(-0.1) == 0

    def test_alpha_decreases_monotonically(self):
        """Alpha should decrease as timer decreases."""
        steps = 20
        step = STREAK_FLASH_DUR / steps
        prev_alpha = 256
        for i in range(steps + 1):
            t = STREAK_FLASH_DUR - i * step
            alpha = compute_flash_alpha(max(0, t))
            assert alpha <= prev_alpha, f"Alpha increased at step {i}"
            prev_alpha = alpha

    def test_alpha_always_in_valid_range(self):
        """Alpha should always be between 0 and 255."""
        for i in range(100):
            t = STREAK_FLASH_DUR * i / 99
            alpha = compute_flash_alpha(t)
            assert 0 <= alpha <= 255

    def test_alpha_is_linear(self):
        """Alpha should be proportional to remaining timer fraction."""
        for frac in [0.1, 0.25, 0.5, 0.75, 0.9]:
            t = STREAK_FLASH_DUR * frac
            expected = int(255 * frac)
            assert abs(compute_flash_alpha(t) - expected) <= 1


class TestFlashDecay:
    """Test the timer decay behaviour."""

    def test_decay_reduces_timer(self):
        """Timer should decrease by dt each frame."""
        timer = STREAK_FLASH_DUR
        timer = decay_flash_timer(timer, 1 / 60)
        assert timer < STREAK_FLASH_DUR

    def test_decay_exact_reduction(self):
        """Timer should decrease by exactly dt when above dt."""
        timer = STREAK_FLASH_DUR
        dt = 1 / 60
        new_timer = decay_flash_timer(timer, dt)
        assert abs(new_timer - (STREAK_FLASH_DUR - dt)) < 1e-10

    def test_decay_clamps_to_zero(self):
        """Timer should never go below zero."""
        timer = 0.01
        timer = decay_flash_timer(timer, 0.05)
        assert timer == 0

    def test_full_decay_simulation(self):
        """Flash should fully decay within ~18 frames at 60fps."""
        timer = STREAK_FLASH_DUR
        dt = 1 / 60
        frames = 0
        while timer > 0:
            timer = decay_flash_timer(timer, dt)
            frames += 1
        assert 17 <= frames <= 19

    def test_decay_starts_at_full(self):
        """Starting alpha should be 255."""
        assert compute_flash_alpha(STREAK_FLASH_DUR) == 255

    def test_decay_ends_at_zero_alpha(self):
        """After full decay, alpha should be 0."""
        timer = STREAK_FLASH_DUR
        dt = 1 / 60
        while timer > 0:
            timer = decay_flash_timer(timer, dt)
        assert compute_flash_alpha(timer) == 0

    def test_duration_is_0_3_seconds(self):
        """Flash duration should be 0.3 seconds as specified."""
        assert STREAK_FLASH_DUR == 0.3

    def test_zero_timer_no_decay(self):
        """Decaying a zero timer should stay at zero."""
        assert decay_flash_timer(0, 1 / 60) == 0


class TestBorderConfig:
    """Test flash border configuration constants."""

    def test_border_width_is_6(self):
        """Flash border should be 6 pixels wide."""
        assert STREAK_FLASH_BORDER == 6

    def test_border_width_positive(self):
        """Border width must be a positive integer."""
        assert isinstance(STREAK_FLASH_BORDER, int)
        assert STREAK_FLASH_BORDER > 0


class TestStreakResetIntegration:
    """Test flash behaviour across streak resets (e.g., bomb hit)."""

    def test_flash_triggers_on_milestone_after_reset(self):
        """After a streak reset, reaching a milestone again should flash."""
        results = simulate_catch_streak(6, reset_at=2)
        # catches: 1,2 -> reset at index 2 -> 1,2,3,4
        # Streak 3 after reset (index 4) should trigger flash
        assert results[4]["triggered"] is True

    def test_no_flash_before_first_milestone(self):
        """Catches 1 and 2 should never trigger flash."""
        results = simulate_catch_streak(2)
        assert all(r["triggered"] is False for r in results)

    def test_consecutive_milestones_sequence(self):
        """Milestones 3, 5, 10 should all trigger in a single streak."""
        results = simulate_catch_streak(10)
        assert results[2]["triggered"] is True   # streak 3
        assert results[4]["triggered"] is True   # streak 5
        assert results[9]["triggered"] is True   # streak 10

    def test_no_flash_between_milestones(self):
        """Non-milestone catches should not trigger a flash."""
        results = simulate_catch_streak(10)
        for i in [0, 1, 3, 5, 6, 7, 8]:  # streaks 1,2,4,6,7,8,9
            assert results[i]["triggered"] is False, f"Unexpected flash at catch {i+1}"

    def test_flash_timer_resets_on_new_milestone(self):
        """Triggering a second milestone should restart the timer."""
        timer = STREAK_FLASH_DUR
        # Simulate decay partway through
        for _ in range(5):
            timer = decay_flash_timer(timer, 1 / 60)
        assert timer < STREAK_FLASH_DUR
        # New milestone resets timer
        timer = STREAK_FLASH_DUR
        assert compute_flash_alpha(timer) == 255

    def test_rich_state_includes_streak_count(self):
        """Each result should report the correct streak count."""
        results = simulate_catch_streak(5)
        assert [r["streak"] for r in results] == [1, 2, 3, 4, 5]

    def test_rich_state_streak_resets_correctly(self):
        """Streak count should reset to 1 after bomb hit at reset_at."""
        results = simulate_catch_streak(5, reset_at=2)
        # index 0: streak 1, index 1: streak 2,
        # index 2: reset->0 then +1 = streak 1,
        # index 3: streak 2, index 4: streak 3
        assert [r["streak"] for r in results] == [1, 2, 1, 2, 3]

    def test_flash_timer_nonzero_on_trigger(self):
        """When a flash triggers, timer should be set to STREAK_FLASH_DUR."""
        results = simulate_catch_streak(3)
        assert results[2]["triggered"] is True
        assert results[2]["flash_timer"] == STREAK_FLASH_DUR

    def test_flash_timer_decays_between_catches(self):
        """Timer should decay between catches that don't trigger."""
        results = simulate_catch_streak(5)
        # After catch 3 triggers, catch 4 decays it by dt
        assert results[3]["flash_timer"] < STREAK_FLASH_DUR
        assert results[3]["flash_timer"] > 0

    def test_bomb_hit_during_active_flash_preserves_timer_decay(self):
        """Bomb hit during an active flash should not zero the timer;
        it only resets the streak.  The flash timer keeps decaying normally."""
        # Trigger flash at catch 3 (streak milestone), then bomb at index 3
        results = simulate_catch_streak(5, reset_at=3)
        # index 2: streak 3 -> flash triggers, timer = 0.3
        assert results[2]["triggered"] is True
        # index 3: bomb resets streak, but flash_timer only decayed by dt
        assert results[3]["flash_timer"] > 0, "Flash timer should still be active after bomb"
        assert results[3]["streak"] == 1  # streak reset then +1

    def test_bomb_hit_during_active_flash_timer_value(self):
        """After bomb hit during active flash, timer should equal FLASH_DUR - dt."""
        dt = 1 / 60
        results = simulate_catch_streak(4, reset_at=3, dt=dt)
        # index 2 triggers flash (streak 3), timer = STREAK_FLASH_DUR
        # index 3: decay by dt, bomb resets streak, no new trigger
        expected_timer = STREAK_FLASH_DUR - dt
        assert abs(results[3]["flash_timer"] - expected_timer) < 1e-10
