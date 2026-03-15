"""Tests for HUD creature icons logic."""


CREATURE_TYPES = [
    {"name": "Fire Drake",       "image_key": "fire_drake",      "points": 50},
    {"name": "Water Sprite",     "image_key": "water_sprite",    "points": 40},
    {"name": "Forest Guardian",  "image_key": "forest_guardian", "points": 60},
    {"name": "Electric Spark",   "image_key": "electric_spark",  "points": 45},
    {"name": "Shadow Phantom",   "image_key": "shadow_phantom",  "points": 70},
]

HUD_ICON_SIZE = 28
HUD_ICON_GAP = 6
HUD_NEARBY_RANGE = 120
HUD_CATCH_FLASH_DUR = 1.0


def hud_icon_state(image_key, nearby_keys, caught_names):
    """Reproduce hud_icon_state from geocatch_pygame.py."""
    if image_key in nearby_keys:
        return "active"
    ct_name = None
    for ct in CREATURE_TYPES:
        if ct["image_key"] == image_key:
            ct_name = ct["name"]
            break
    if ct_name and ct_name in caught_names:
        return "caught"
    return "dim"


def compute_nearby_keys(creatures, player_x, player_y, nearby_range):
    """Reproduce nearby detection logic from the HUD rendering code."""
    nearby = set()
    for c in creatures:
        dx = player_x - c["x"]
        dy = player_y - c["y"]
        if (dx * dx + dy * dy) ** 0.5 < nearby_range:
            nearby.add(c["type"]["image_key"])
    return nearby


def decay_catch_flash(flash_dict, dt):
    """Reproduce catch flash timer decay logic."""
    for key in list(flash_dict):
        flash_dict[key] -= dt
        if flash_dict[key] <= 0:
            del flash_dict[key]


class TestHudIconState:
    """Test the icon state determination logic."""

    def test_nearby_creature_returns_active(self):
        """A creature within range should show as active."""
        state = hud_icon_state("fire_drake", {"fire_drake"}, set())
        assert state == "active"

    def test_caught_creature_returns_caught(self):
        """A caught creature (not nearby) should show as caught."""
        state = hud_icon_state("fire_drake", set(), {"Fire Drake"})
        assert state == "caught"

    def test_unseen_creature_returns_dim(self):
        """A creature neither nearby nor caught should be dim."""
        state = hud_icon_state("fire_drake", set(), set())
        assert state == "dim"

    def test_nearby_takes_priority_over_caught(self):
        """If creature is both nearby and caught, active wins."""
        state = hud_icon_state("fire_drake", {"fire_drake"}, {"Fire Drake"})
        assert state == "active"

    def test_all_creature_types_have_valid_states(self):
        """Every creature type should resolve to one of the three states."""
        for ct in CREATURE_TYPES:
            for nearby, caught, expected in [
                ({ct["image_key"]}, set(), "active"),
                (set(), {ct["name"]}, "caught"),
                (set(), set(), "dim"),
            ]:
                assert hud_icon_state(ct["image_key"], nearby, caught) == expected

    def test_unknown_image_key_returns_dim(self):
        """An unknown image key should default to dim."""
        state = hud_icon_state("unknown_creature", set(), set())
        assert state == "dim"


class TestNearbyDetection:
    """Test nearby creature detection for HUD icons."""

    def test_creature_within_range_is_nearby(self):
        """Creature at 100px should be within 120px range."""
        creatures = [{"x": 100, "y": 0, "type": {"image_key": "fire_drake"}}]
        keys = compute_nearby_keys(creatures, 0, 0, HUD_NEARBY_RANGE)
        assert "fire_drake" in keys

    def test_creature_outside_range_not_nearby(self):
        """Creature at 200px should be outside 120px range."""
        creatures = [{"x": 200, "y": 0, "type": {"image_key": "fire_drake"}}]
        keys = compute_nearby_keys(creatures, 0, 0, HUD_NEARBY_RANGE)
        assert "fire_drake" not in keys

    def test_creature_exactly_at_boundary_not_nearby(self):
        """Creature at exactly 120px should NOT be nearby (strict less-than)."""
        creatures = [{"x": 120, "y": 0, "type": {"image_key": "fire_drake"}}]
        keys = compute_nearby_keys(creatures, 0, 0, HUD_NEARBY_RANGE)
        assert "fire_drake" not in keys

    def test_multiple_creatures_same_type(self):
        """Multiple creatures of same type within range: key appears once."""
        creatures = [
            {"x": 50, "y": 0, "type": {"image_key": "fire_drake"}},
            {"x": 60, "y": 0, "type": {"image_key": "fire_drake"}},
        ]
        keys = compute_nearby_keys(creatures, 0, 0, HUD_NEARBY_RANGE)
        assert keys == {"fire_drake"}

    def test_multiple_types_nearby(self):
        """Multiple creature types within range detected."""
        creatures = [
            {"x": 50, "y": 0, "type": {"image_key": "fire_drake"}},
            {"x": 60, "y": 0, "type": {"image_key": "water_sprite"}},
            {"x": 200, "y": 0, "type": {"image_key": "shadow_phantom"}},
        ]
        keys = compute_nearby_keys(creatures, 0, 0, HUD_NEARBY_RANGE)
        assert keys == {"fire_drake", "water_sprite"}

    def test_empty_creatures_returns_empty(self):
        """No creatures means no nearby keys."""
        keys = compute_nearby_keys([], 100, 100, HUD_NEARBY_RANGE)
        assert keys == set()


class TestCatchFlashDecay:
    """Test the catch flash timer decay logic."""

    def test_flash_decays_over_time(self):
        """Flash timer decreases by dt each frame."""
        flash = {"fire_drake": 1.0}
        decay_catch_flash(flash, 0.1)
        assert abs(flash["fire_drake"] - 0.9) < 1e-9

    def test_flash_removed_when_expired(self):
        """Flash timer is removed when it reaches zero."""
        flash = {"fire_drake": 0.05}
        decay_catch_flash(flash, 0.1)
        assert "fire_drake" not in flash

    def test_multiple_flashes_decay_independently(self):
        """Multiple flash timers decay independently."""
        flash = {"fire_drake": 1.0, "water_sprite": 0.05}
        decay_catch_flash(flash, 0.1)
        assert "fire_drake" in flash
        assert "water_sprite" not in flash

    def test_empty_flash_dict_no_error(self):
        """Decaying an empty dict should not error."""
        flash = {}
        decay_catch_flash(flash, 0.1)
        assert flash == {}

    def test_flash_alpha_proportional(self):
        """Flash alpha should be proportional to remaining time."""
        remaining = 0.5
        alpha = int(255 * (remaining / HUD_CATCH_FLASH_DUR))
        assert alpha == 127

    def test_new_catch_resets_flash(self):
        """Catching a creature again should reset the flash timer."""
        flash = {"fire_drake": 0.3}
        # Simulate catching: set to full duration
        flash["fire_drake"] = HUD_CATCH_FLASH_DUR
        assert flash["fire_drake"] == 1.0


class TestHudLayout:
    """Test HUD icon row layout calculations."""

    def test_icon_count_matches_creature_types(self):
        """Should have one icon slot per creature type."""
        assert len(CREATURE_TYPES) == 5

    def test_total_row_width(self):
        """Row width: 5 icons * 28px + 4 gaps * 6px = 164px."""
        n = len(CREATURE_TYPES)
        total = n * HUD_ICON_SIZE + (n - 1) * HUD_ICON_GAP
        assert total == 164

    def test_icon_positions_non_overlapping(self):
        """Each icon position should not overlap the next."""
        positions = []
        for i in range(len(CREATURE_TYPES)):
            x = 15 + i * (HUD_ICON_SIZE + HUD_ICON_GAP)
            positions.append((x, x + HUD_ICON_SIZE))
        for i in range(len(positions) - 1):
            assert positions[i][1] <= positions[i + 1][0]

    def test_icon_size_positive(self):
        """Icon size must be positive."""
        assert HUD_ICON_SIZE > 0
        assert HUD_ICON_GAP >= 0
