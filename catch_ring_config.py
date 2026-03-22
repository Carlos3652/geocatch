"""Catch ring constants and pulse computation.

Shared between geocatch_pygame.py (rendering) and tests so that the
source of truth lives in one place with no pygame dependency.
"""

# ── Catch Ring Constants ─────────────────────────────────────────────────────
RING_PULSE_SPEED = 1.2          # cycles per second
RING_MIN_RADIUS = 30            # inner radius at pulse start
RING_RADIUS_RANGE = 28          # radius expansion over one pulse cycle
RING_MAX_ALPHA = 240            # core alpha at pulse start (up from 210)
RING_CORE_WIDTH = 6             # core ring stroke width (up from 4)
RING_MID_WIDTH = 9              # mid-glow stroke width (up from 5)
RING_GLOW_WIDTH = 14            # outer-glow stroke width (up from 8)
RING_GLOW_RADIUS_OFFSET = 6    # outer glow drawn this many px beyond core
RING_MID_RADIUS_OFFSET = 2     # mid glow drawn this many px beyond core
RING_SURFACE_HALF = 92          # half-size of the pre-allocated surface
RING_SURFACE_SIZE = RING_SURFACE_HALF * 2  # full surface side length
RING_Y_OFFSET = -10             # vertical offset of pulse ring from player
RANGE_RING_RADIUS = 55          # static catch-range circle radius
RANGE_RING_WIDTH = 3            # static catch-range stroke width (up from 2)
RANGE_RING_ALPHA = 100          # static catch-range alpha (up from 70)

# ── Drop-shadow layer for contrast on light map backgrounds ──────────────────
RING_SHADOW_WIDTH = 18          # shadow ring stroke width (widest layer)
RING_SHADOW_RADIUS_OFFSET = 8  # shadow drawn this many px beyond core
RING_SHADOW_ALPHA_FACTOR = 0.35 # shadow alpha = core_alpha * factor
RANGE_RING_SHADOW_WIDTH = 6    # shadow for static range ring
RANGE_RING_SHADOW_ALPHA = 60   # alpha for static range ring shadow


def compute_ring_params(ticks_ms):
    """Compute catch-ring pulse parameters for a given timestamp.

    Returns a dict with all dynamic + constant values needed to draw
    the four-layer pulsing ring (shadow + glow + mid + core) and the
    static range ring with its shadow.
    """
    _pt = ticks_ms / 1000.0
    pulse = (_pt * RING_PULSE_SPEED) % 1.0
    radius = RING_MIN_RADIUS + int(pulse * RING_RADIUS_RANGE)
    core_alpha = int(RING_MAX_ALPHA * (1 - pulse))
    mid_alpha = max(0, core_alpha // 2)
    glow_alpha = max(0, core_alpha // 4)
    shadow_alpha = max(0, int(core_alpha * RING_SHADOW_ALPHA_FACTOR))
    return {
        "pulse": pulse,
        "radius": radius,
        "core_alpha": core_alpha,
        "core_width": RING_CORE_WIDTH,
        "mid_alpha": mid_alpha,
        "mid_width": RING_MID_WIDTH,
        "glow_alpha": glow_alpha,
        "glow_width": RING_GLOW_WIDTH,
        "glow_radius_offset": RING_GLOW_RADIUS_OFFSET,
        "mid_radius_offset": RING_MID_RADIUS_OFFSET,
        "shadow_alpha": shadow_alpha,
        "shadow_width": RING_SHADOW_WIDTH,
        "shadow_radius_offset": RING_SHADOW_RADIUS_OFFSET,
        "surface_size": RING_SURFACE_SIZE,
        "center": RING_SURFACE_HALF,
        "range_ring_width": RANGE_RING_WIDTH,
        "range_ring_alpha": RANGE_RING_ALPHA,
        "range_ring_shadow_width": RANGE_RING_SHADOW_WIDTH,
        "range_ring_shadow_alpha": RANGE_RING_SHADOW_ALPHA,
    }
