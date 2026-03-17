import pygame
import random
import sys
import math
import os
import json
import array as _array

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GeoCatch - Overland Park Edition")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 24)
tiny_font = pygame.font.SysFont("Arial", 14)
prox_font = pygame.font.SysFont("Arial", 20)
title_font = pygame.font.SysFont("Arial", 52, bold=True)
hs_indicator_font = pygame.font.SysFont("Arial", 24, bold=True)
score_big_font = pygame.font.SysFont("Arial", 72, bold=True)
tier_font = pygame.font.SysFont("Arial", 40, bold=True)
nav_font = pygame.font.SysFont("Arial", 18)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRASS = (200, 230, 202)
ROAD = (210, 210, 210)
LAKE = (59, 159, 212)
TREE_TRUNK = (101, 67, 33)
SCHOOL_GROUND = (185, 215, 188)
HOUSE_COLOR = (230, 230, 228)
ACCENT = (255, 107, 53)
SCORE_GOLD = (255, 215, 0)
URGENT_RED = (255, 59, 48)
PANEL_BG = (26, 26, 46)

# ── #1: Sound Effects (programmatic generation) ──────────────────────────────
def _gen_tone(freq, duration_ms=100, volume=0.3, freq_end=None):
    sr = 44100
    n = int(sr * duration_ms / 1000)
    if n == 0:
        return None
    fe = freq_end if freq_end else freq
    fs = int(n * 0.75)
    inv_sr = 1.0 / sr
    inv_n = 1.0 / n if n > 0 else 0
    inv_fade = 1.0 / (n - fs) if n > fs else 1.0
    amp = volume * 32767
    two_pi = 2 * math.pi
    buf = _array.array('h', [
        max(-32768, min(32767, int(
            amp * math.sin(two_pi * (freq + (fe - freq) * i * inv_n) * i * inv_sr)
            * (((n - i) * inv_fade) if i > fs else 1.0)
        ))) for i in range(n)
    ])
    return pygame.mixer.Sound(buffer=buf)

try:
    _snd_catch = _gen_tone(660, 120, 0.25, 880)
    _snd_bomb = _gen_tone(180, 200, 0.3)
    _snd_tick = _gen_tone(1000, 50, 0.15)
    _snd_gameover = _gen_tone(440, 400, 0.25, 220)
except Exception:
    _snd_catch = _snd_bomb = _snd_tick = _snd_gameover = None

def _play(snd):
    if snd:
        try:
            snd.play()
        except Exception:
            pass

def _fader_alpha(dist):
    """Consistent fader alpha calculation — HIGH-03 shared helper."""
    return int(max(50, min(255, 255 - (dist - 100) * 2.05)))

# Your trainers
trainer_images = []
for i in range(1, 5):
    try:
        img = pygame.transform.smoothscale(pygame.image.load(f"trainer{i}.png"), (70, 90))
        trainer_images.append(img)
    except (FileNotFoundError, pygame.error):
        trainer_images.append(None)

selected_char = 0
game_state = "character_select"
trainer_card_rects = []
_cs_btn_rect = pygame.Rect(0, 0, 0, 0)

player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 6
score = 0
inventory = []
game_time = 60
start_ticks = 0
name_input = ""
float_texts = []
bomb_flash_frames = 0
bomb_cooldown = 0.0
dt = 1 / 60
is_new_high_score = False
score_saved = False
_go_cache = None
_go_anim_score = 0
_go_anim_done = False
_go_anim_timer = 0.0
_go_flash_timer = 0.0
_go_bubbles = []
_go_fireworks = []  # firework particles for high score
_go_caught_keys = set()  # image_keys of caught creatures this round

# #3: Catch streak multiplier
catch_streak = 0
streak_multiplier = 1.0

# #6: Catch pop animations
catch_animations = []

# Catch particle burst effect
catch_particles = []

# #8: Screen shake
shake_frames = 0
shake_magnitude = 0

# #15: Streak milestone flash
_streak_flash_timer = 0.0
_STREAK_FLASH_DUR = 0.3
_STREAK_MILESTONES = {3, 5, 10}

# #10: Pause
_total_paused_ms = 0
_pause_start_ms = 0
_pause_screenshot = pygame.Surface((WIDTH, HEIGHT))

# #4: Late-game escalation
_escalation_triggered = False
_bob_speed = 2.0

# #13: Spawn delay after wave clear
_spawn_delay_timer = 0.0

# #1: Countdown tick tracking
_last_tick_second = -1

# High scores — CRIT-03: hardened parser
high_scores = []
if os.path.exists("highscores.txt"):
    try:
        with open("highscores.txt") as f:
            parsed = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.rsplit(maxsplit=1)
                if len(parts) == 2:
                    parsed.append((parts[0], int(parts[1])))
            high_scores = sorted(parsed, key=lambda x: x[1], reverse=True)[:5]
    except (ValueError, OSError):
        high_scores = []

# #14: Cumulative stats + #11: Per-trainer personal bests
_stats_file = "stats.json"
_stats = {"total_catches": {}, "trainer_bests": {}}
if os.path.exists(_stats_file):
    try:
        with open(_stats_file) as f:
            _stats = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
if "total_catches" not in _stats:
    _stats["total_catches"] = {}
if "trainer_bests" not in _stats:
    _stats["trainer_bests"] = {}

def save_high_score(name, sc):
    global high_scores
    high_scores.append((name, sc))
    high_scores.sort(key=lambda x: x[1], reverse=True)
    high_scores = high_scores[:5]
    try:
        with open("highscores.txt", "w") as f:
            for n, s in high_scores:
                f.write(f"{n} {s}\n")
    except OSError:
        pass
    _build_scores_popup()

def _save_stats():
    try:
        with open(_stats_file, "w") as f:
            json.dump(_stats, f, indent=2)
    except OSError:
        pass

# Monsters — HIGH-08: load each image independently
creature_images = {}
for _ckey, _cfile in [
    ("fire_drake", "fire_drake.png"),
    ("water_sprite", "water_sprite.png"),
    ("forest_guardian", "forest_guardian.png"),
    ("electric_spark", "electric_spark.png"),
    ("shadow_phantom", "shadow_phantom.png"),
]:
    try:
        creature_images[_ckey] = pygame.transform.smoothscale(pygame.image.load(_cfile), (60, 60))
    except (FileNotFoundError, pygame.error):
        pass

CREATURE_TYPES = [
    {"name": "Fire Drake",       "image_key": "fire_drake",      "points": 50},
    {"name": "Water Sprite",     "image_key": "water_sprite",    "points": 40},
    {"name": "Forest Guardian",  "image_key": "forest_guardian", "points": 60},
    {"name": "Electric Spark",   "image_key": "electric_spark",  "points": 45},
    {"name": "Shadow Phantom",   "image_key": "shadow_phantom",  "points": 70},
]

CREATURE_COLORS = {
    "Fire Drake":      (255, 107, 0),
    "Water Sprite":    (59, 159, 212),
    "Forest Guardian": (76, 175, 80),
    "Electric Spark":  (255, 215, 0),
    "Shadow Phantom":  (156, 39, 176),
}

# #5: Behavior archetypes
CREATURE_BEHAVIORS = {
    "Fire Drake": "pacer",
    "Water Sprite": "blinker",
    "Forest Guardian": "static",
    "Electric Spark": "drifter",
    "Shadow Phantom": "fader",
}

# #15: Type initials for colorblind accessibility
CREATURE_INITIALS = {
    "Fire Drake": "F",
    "Water Sprite": "W",
    "Forest Guardian": "G",
    "Electric Spark": "E",
    "Shadow Phantom": "S",
}

# Pre-baked "sticker look" creature surfaces + #15 colorblind initials
_STICKER_R = 34
_STICKER_SIZE = _STICKER_R * 2 + 4
_sticker_surfs = {}
for _ct in CREATURE_TYPES:
    _st_surf = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)
    _st_cx, _st_cy = _STICKER_SIZE // 2, _STICKER_SIZE // 2
    pygame.draw.circle(_st_surf, (255, 255, 255, 220), (_st_cx, _st_cy), _STICKER_R)
    _st_color = CREATURE_COLORS[_ct["name"]]
    pygame.draw.circle(_st_surf, (*_st_color, 200), (_st_cx, _st_cy), _STICKER_R, 3)
    _st_img = creature_images.get(_ct["image_key"])
    if _st_img:
        _st_surf.blit(_st_img, (_st_cx - 30, _st_cy - 30))
    else:
        pygame.draw.circle(_st_surf, _st_color, (_st_cx, _st_cy), 20)
    # #15: small type initial in bottom-right corner
    _init_surf = tiny_font.render(CREATURE_INITIALS[_ct["name"]], True, (60, 60, 60))
    _st_surf.blit(_init_surf, (_st_cx + 10, _st_cy + 10))
    _sticker_surfs[_ct["image_key"]] = _st_surf

# Grey sticker surfaces for uncaught creatures on end screen
_grey_sticker_surfs = {}
for _ct in CREATURE_TYPES:
    _gs = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)
    _gs_cx, _gs_cy = _STICKER_SIZE // 2, _STICKER_SIZE // 2
    pygame.draw.circle(_gs, (60, 60, 70, 180), (_gs_cx, _gs_cy), _STICKER_R)
    pygame.draw.circle(_gs, (90, 90, 100, 200), (_gs_cx, _gs_cy), _STICKER_R, 3)
    _q = small_font.render("?", True, (140, 140, 150))
    _gs.blit(_q, (_gs_cx - _q.get_width() // 2, _gs_cy - _q.get_height() // 2))
    _grey_sticker_surfs[_ct["image_key"]] = _gs

# Larger sticker surfaces for end screen showcase (1.4x)
_SHOWCASE_SCALE = 1.4
_SHOWCASE_SIZE = int(_STICKER_SIZE * _SHOWCASE_SCALE)
_showcase_stickers = {}
_showcase_grey = {}
for _ct in CREATURE_TYPES:
    _showcase_stickers[_ct["image_key"]] = pygame.transform.smoothscale(
        _sticker_surfs[_ct["image_key"]], (_SHOWCASE_SIZE, _SHOWCASE_SIZE))
    _showcase_grey[_ct["image_key"]] = pygame.transform.smoothscale(
        _grey_sticker_surfs[_ct["image_key"]], (_SHOWCASE_SIZE, _SHOWCASE_SIZE))

# Checkmark surface for caught creatures on end screen
_check_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
pygame.draw.line(_check_surf, (80, 220, 80), (3, 10), (8, 16), 3)
pygame.draw.line(_check_surf, (80, 220, 80), (8, 16), (17, 4), 3)

# Pre-rendered creature name labels for end screen (caught + uncaught variants)
_showcase_names_caught = {}
_showcase_names_grey = {}
for _ct in CREATURE_TYPES:
    _first = _ct["name"].split()[0]
    _showcase_names_caught[_ct["image_key"]] = tiny_font.render(_first, True, (180, 180, 190))
    _showcase_names_grey[_ct["image_key"]] = tiny_font.render(_first, True, (90, 90, 100))

# Pre-created shadow surfaces (allocated once, reused every frame)
_shad_tree     = pygame.Surface((50, 14), pygame.SRCALPHA)
pygame.draw.ellipse(_shad_tree,     (0, 0, 0, 55),  (0, 0, 50, 14))
_shad_rock     = pygame.Surface((44, 12), pygame.SRCALPHA)
pygame.draw.ellipse(_shad_rock,     (0, 0, 0, 60),  (0, 0, 44, 12))
_shad_bomb     = pygame.Surface((50, 14), pygame.SRCALPHA)
pygame.draw.ellipse(_shad_bomb,     (0, 0, 0, 70),  (0, 0, 50, 14))
_shad_creature = pygame.Surface((50, 12), pygame.SRCALPHA)
pygame.draw.ellipse(_shad_creature, (0, 0, 0, 80),  (0, 0, 50, 12))
_shad_trainer  = pygame.Surface((60, 16), pygame.SRCALPHA)
pygame.draw.ellipse(_shad_trainer,  (0, 0, 0, 70),  (0, 0, 60, 16))

# Pre-allocated type-coded base circle surfaces
_type_circles = {}
for _ct in CREATURE_TYPES:
    _tc_color = CREATURE_COLORS[_ct["name"]]
    _tc_surf = pygame.Surface((56, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(_tc_surf, (*_tc_color, 110), (0, 0, 56, 18))
    _type_circles[_ct["name"]] = _tc_surf

_phantom_glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
_pulse_ring_surf = pygame.Surface((124, 124), pygame.SRCALPHA)

# Pre-baked static range ring (CRIT-02: constant dimensions, drawn once at startup)
_RANGE_RING_RADIUS = 55
_range_ring_surf = pygame.Surface((_RANGE_RING_RADIUS * 2 + 2, _RANGE_RING_RADIUS * 2 + 2), pygame.SRCALPHA)
pygame.draw.circle(_range_ring_surf, (200, 200, 200, 255),
                   (_RANGE_RING_RADIUS + 1, _RANGE_RING_RADIUS + 1), _RANGE_RING_RADIUS, 1)

# Pre-allocated game-over surfaces — CRIT-02: non-SRCALPHA so set_alpha() works
_go_flash_surf = pygame.Surface((WIDTH, HEIGHT))
_go_flash_surf.fill((255, 140, 0))
_go_bg_pulse_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Pre-allocated bomb flash surface
_bomb_flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_bomb_flash_surf.fill((255, 0, 0, 26))

# #15: Pre-allocated streak flash surface — gold border, colorkey for set_alpha() compat
_STREAK_FLASH_BORDER = 6
_streak_flash_surf = pygame.Surface((WIDTH, HEIGHT))
_streak_flash_surf.set_colorkey((0, 0, 0))
pygame.draw.rect(_streak_flash_surf, SCORE_GOLD, (0, 0, WIDTH, HEIGHT), width=_STREAK_FLASH_BORDER, border_radius=4)

# Pre-allocated fade sticker surface (#9) + alpha modulation surface
_fade_sticker_surf = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)
_alpha_mod_surf = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)

# Pre-allocated proximity label surfaces
_prox_pill_surf = pygame.Surface((500, 40), pygame.SRCALPHA)
_prox_border_surf = pygame.Surface((500, 40), pygame.SRCALPHA)

# CRIT-03: Pre-rendered proximity label text surfaces (one per creature type)
_prox_labels = {}
for _ct in CREATURE_TYPES:
    _plbl = f"{_ct['name']}  --  {_ct['points']} pts  |  SPACE to catch"
    _prox_labels[_ct["name"]] = prox_font.render(_plbl, True, WHITE)

# HIGH-05: Pre-baked streak multiplier pill surfaces
_streak_pills = {}
for _sv, _sc in [(1.5, ACCENT), (2.0, SCORE_GOLD)]:
    _st = small_font.render(f"x{_sv:.1f}", True, _sc)
    _sp_w, _sp_h = _st.get_width() + 20, 28
    _sp_surf = pygame.Surface((_sp_w, _sp_h), pygame.SRCALPHA)
    pygame.draw.rect(_sp_surf, PANEL_BG, (0, 0, _sp_w, _sp_h), border_radius=14)
    pygame.draw.rect(_sp_surf, _sc, (0, 0, _sp_w, _sp_h), width=2, border_radius=14)
    _sp_surf.blit(_st, (10, 2))
    _streak_pills[_sv] = _sp_surf

# MED-03/05: Pre-rendered static end screen text
_go_no_scores = tiny_font.render("No scores yet!", True, (120, 120, 130))
_go_saved = small_font.render("Saved!", True, (100, 230, 100))
_go_saved_hint = tiny_font.render("Press R to play again", True, (180, 180, 190))
_go_noscore = small_font.render("No score", True, (160, 160, 170))
_go_noscore_hint = tiny_font.render("Press R to try again", True, (140, 140, 150))
_go_enter_hint = tiny_font.render("Press ENTER to save", True, (140, 200, 140))
_go_save_title = tiny_font.render("SAVE YOUR SCORE", True, SCORE_GOLD)
_go_name_lbl = tiny_font.render("Name (max 5 chars):", True, (160, 160, 170))
_trainer_fallback = font.render("T", True, WHITE)  # LOW-01: pre-rendered trainer fallback

# Pre-allocated pause overlay surfaces (#10)
_pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_pause_overlay.fill((0, 0, 0, 160))
_pause_title = font.render("PAUSED", True, WHITE)
_pause_hint_esc = small_font.render("Press ESC to resume", True, (200, 200, 200))
_pause_hint_q = small_font.render("Press Q to quit to menu", True, (200, 200, 200))

creatures = []
rocks = [(200, 200), (700, 150), (300, 500), (800, 400), (150, 550), (650, 550)]
bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]

# Pre-compute per-rock crack geometry (fixed seed)
_rng_rock = random.Random(13)
_rock_data = []
for _rx, _ry in rocks:
    _cracks = []
    for _ in range(2):
        sx = _rx + _rng_rock.randint(-9, 9)
        sy = _ry + _rng_rock.randint(-7, 7)
        ex = sx + _rng_rock.randint(-7, 7)
        ey = sy + _rng_rock.randint(-7, 7)
        _cracks.append(((sx, sy), (ex, ey)))
    _rock_data.append({"pos": (_rx, _ry), "cracks": _cracks})

trees = [
    (15, 48), (14, 230), (388, 38), (390, 262),
    (496, 76), (596, 128), (696, 58),
    (868, 72), (868, 228), (868, 448), (868, 612),
    (88, 438), (164, 556), (282, 626), (66, 266),
]

_rng_tree = random.Random(7)
_tree_data = []
for _tx, _ty in trees:
    _cx, _cy = _tx + 15, _ty + 20
    _berries = [
        (_cx + _rng_tree.randint(-18, 18), _cy + _rng_tree.randint(-20, 8))
        for _ in range(3)
    ]
    _tree_data.append({"pos": (_tx, _ty), "berries": _berries})

# Pond centers for zone-based spawning (#7)
_POND_CENTERS = [(407, 388), (384, 519)]

def draw_world(surf):
    """Draw the neighbourhood-themed game world onto surf."""
    surf.fill(GRASS)
    pygame.draw.rect(surf, ROAD, (818, 0, 44, HEIGHT))
    pygame.draw.polygon(surf, ROAD, [
        (0, 334), (818, 324), (818, 368), (0, 372)
    ])
    pygame.draw.circle(surf, ROAD, (205, 155), 178)
    pygame.draw.circle(surf, SCHOOL_GROUND, (205, 155), 150)
    pygame.draw.rect(surf, (218, 218, 216), (96, 92, 118, 52))
    pygame.draw.rect(surf, (218, 218, 216), (216, 105, 128, 56))
    pygame.draw.rect(surf, ROAD, (100, 192, 198, 36))
    for _px in range(120, 294, 20):
        pygame.draw.line(surf, SCHOOL_GROUND, (_px, 193), (_px, 227), 1)
    pygame.draw.rect(surf, ROAD, (420, 368, 26, 222))
    pygame.draw.rect(surf, ROAD, (376, 418, 224, 24))
    pygame.draw.rect(surf, ROAD, (535, 368, 26, 252))
    pygame.draw.rect(surf, ROAD, (720, 368, 26, 310))
    pygame.draw.circle(surf, ROAD,  (433, 590), 24)
    pygame.draw.circle(surf, GRASS, (433, 590), 14)
    pygame.draw.circle(surf, ROAD,  (548, 620), 24)
    pygame.draw.circle(surf, GRASS, (548, 620), 14)
    pygame.draw.circle(surf, ROAD,  (733, 678), 24)
    pygame.draw.circle(surf, GRASS, (733, 678), 14)
    pygame.draw.ellipse(surf, LAKE, (378, 374, 58, 28))
    pygame.draw.ellipse(surf, LAKE, (358, 506, 52, 26))
    for _hx in range(450, 808, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (_hx, 300, 20, 17))
    for _hx in range(378, 418, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (_hx, 450, 20, 17))
    for _hy in range(450, 582, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (450, _hy, 20, 17))
    for _hy in range(450, 616, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (508, _hy, 20, 17))
    for _hy in range(450, 616, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (564, _hy, 20, 17))
    for _hy in range(395, 668, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (694, _hy, 20, 17))
    for _hy in range(395, 668, 26):
        pygame.draw.rect(surf, HOUSE_COLOR, (749, _hy, 20, 17))
    pygame.draw.circle(surf, (76, 175, 80), (555, 252), 9)
    pygame.draw.circle(surf, WHITE, (555, 252), 9, 2)
    _dg = tiny_font.render("Disc Golf", True, (70, 140, 70))
    surf.blit(_dg, (530, 265))
    for td in _tree_data:
        tx, ty = td["pos"]
        cx, cy = tx + 15, ty + 20
        surf.blit(_shad_tree, (tx - 10, ty + 56))
        pygame.draw.rect(surf, TREE_TRUNK, (tx + 8, ty + 25, 14, 35))
        pygame.draw.circle(surf, (18, 76, 18),  (cx, cy), 30)
        pygame.draw.circle(surf, (34, 130, 34), (cx, cy), 28)
        pygame.draw.circle(surf, (18, 76, 18),  (cx - 9, cy - 11), 23)
        pygame.draw.circle(surf, (50, 155, 50), (cx - 9, cy - 11), 21)
        pygame.draw.circle(surf, (18, 76, 18),  (cx + 9, cy - 8), 19)
        pygame.draw.circle(surf, (70, 180, 55), (cx + 9, cy - 8), 17)
        for bx, by in td["berries"]:
            pygame.draw.circle(surf, (210, 45, 45), (bx, by), 3)


def in_lake(x, y):
    if (x - 407) ** 2 / 29 ** 2 + (y - 388) ** 2 / 14 ** 2 < 1.0:
        return True
    if (x - 384) ** 2 / 26 ** 2 + (y - 519) ** 2 / 13 ** 2 < 1.0:
        return True
    return False


_world_surf = pygame.Surface((WIDTH, HEIGHT))
draw_world(_world_surf)


def _spawn_bomb_random():
    """#2: Generate a valid random bomb position."""
    for _ in range(10):
        bx = random.randint(100, WIDTH - 100)
        by = random.randint(100, HEIGHT - 100)
        if (not in_lake(bx, by)
                and not any(math.hypot(bx - rx, by - ry) < 55 for rx, ry in rocks)
                and math.hypot(bx - player_x, by - player_y) > 80):
            return (bx, by)
    # Fallback: still try to avoid lake at minimum
    for _ in range(5):
        fbx = random.randint(100, WIDTH - 100)
        fby = random.randint(100, HEIGHT - 100)
        if not in_lake(fbx, fby):
            return (fbx, fby)
    return (random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100))


def spawn_creatures(n=8):
    """Spawn creatures with #7 zone weighting, #9 fade-in, #12 restricted bounds."""
    global creatures
    creatures = []
    for _ in range(n):
        for _attempt in range(10):
            px = random.randint(80, 800)   # #12: exclude east wall corridor (Antioch Rd)
            py = random.randint(80, HEIGHT - 80)
            if not in_lake(px, py) and not any(math.hypot(px - rx, py - ry) < 65 for rx, ry in rocks):
                break
        else:
            px, py = WIDTH // 2, HEIGHT // 2

        # #7: Zone-based creature type weighting
        near_pond = any(math.hypot(px - pcx, py - pcy) < 80 for pcx, pcy in _POND_CENTERS)
        near_tree = any(math.hypot(px - (tx + 15), py - (ty + 20)) < 60 for tx, ty in trees)
        in_school = px < 350 and py < 300
        weights = []
        for ct in CREATURE_TYPES:
            w = 1.0
            if ct["name"] == "Water Sprite" and near_pond:
                w = 3.0
            elif ct["name"] == "Forest Guardian" and near_tree:
                w = 3.0
            elif ct["name"] == "Shadow Phantom" and in_school:
                w = 3.0
            weights.append(w)
        chosen_type = random.choices(CREATURE_TYPES, weights=weights, k=1)[0]

        # #5: Behavior-specific spawn data
        behavior = CREATURE_BEHAVIORS[chosen_type["name"]]
        c = {
            "x": px, "y": py,
            "type": chosen_type,
            "phase": random.uniform(0, 2 * math.pi),
            "behavior": behavior,
            "spawn_alpha": 0.0,   # #9: fade-in from 0
        }
        if behavior == "pacer":
            c["orbit_cx"] = px
            c["orbit_cy"] = py
            c["orbit_angle"] = random.uniform(0, 2 * math.pi)
            c["orbit_r"] = 30
            c["orbit_speed"] = 1.0
        elif behavior == "blinker":
            c["blink_timer"] = random.uniform(2.0, 4.0)
        elif behavior == "drifter":
            angle = random.uniform(0, 2 * math.pi)
            c["vx"] = math.cos(angle) * 40
            c["vy"] = math.sin(angle) * 40
        creatures.append(c)


def reset_game():
    global score, inventory, player_x, player_y, start_ticks, creatures, bombs, float_texts
    global bomb_flash_frames, bomb_cooldown, score_saved, is_new_high_score, name_input, game_time
    global catch_streak, streak_multiplier, catch_animations, catch_particles, shake_frames, shake_magnitude
    global _streak_flash_timer
    global _total_paused_ms, _pause_start_ms, _escalation_triggered, _bob_speed
    global _spawn_delay_timer, _last_tick_second
    global _go_cache, _go_fireworks, _go_caught_keys, _cs_popup
    score = 0
    game_time = 60
    inventory = []
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    start_ticks = pygame.time.get_ticks()
    spawn_creatures(8)
    # #2: Randomize bomb starting positions
    bombs = [_spawn_bomb_random() for _ in range(4)]
    float_texts.clear()
    bomb_flash_frames = 0
    bomb_cooldown = 0.0
    name_input = ""
    score_saved = False
    is_new_high_score = False
    catch_streak = 0
    streak_multiplier = 1.0
    catch_animations = []
    catch_particles = []
    shake_frames = 0
    shake_magnitude = 0
    _streak_flash_timer = 0.0
    _total_paused_ms = 0
    _pause_start_ms = 0
    _escalation_triggered = False
    _bob_speed = 2.0
    _spawn_delay_timer = 0.0
    _last_tick_second = -1
    _go_cache = None
    _go_fireworks = []
    _go_caught_keys = set()
    _cs_popup = None


# ── Card Spotlight start screen surfaces ──────────────────────────────────────
_CS_CARD_W, _CS_CARD_H = 100, 140
_CS_SEL_W, _CS_SEL_H = 200, 240
_CS_CARD_GAP = 14

_cs_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_cs_overlay.fill((0, 0, 0, 158))

_cs_card_normal = pygame.Surface((_CS_CARD_W, _CS_CARD_H), pygame.SRCALPHA)
_cs_card_normal.fill((255, 255, 255, 15))
pygame.draw.rect(_cs_card_normal, (255, 255, 255, 38), (0, 0, _CS_CARD_W, _CS_CARD_H), width=2, border_radius=10)

_cs_card_sel_big = pygame.Surface((_CS_SEL_W, _CS_SEL_H), pygame.SRCALPHA)
_cs_card_sel_big.fill((255, 107, 53, 30))
pygame.draw.rect(_cs_card_sel_big, (*ACCENT, 255), (0, 0, _CS_SEL_W, _CS_SEL_H), width=2, border_radius=12)

_cs_card_glow_big = pygame.Surface((_CS_SEL_W + 8, _CS_SEL_H + 8), pygame.SRCALPHA)
pygame.draw.rect(_cs_card_glow_big, (255, 107, 53, 50), (0, 0, _CS_SEL_W + 8, _CS_SEL_H + 8), width=4, border_radius=15)

_cs_trainer_big = []
for i in range(4):
    if trainer_images[i]:
        _cs_trainer_big.append(pygame.transform.smoothscale(trainer_images[i], (90, 110)))
    else:
        _cs_trainer_big.append(None)

_cs_title_shadow = title_font.render("GEOCATCH", True, ACCENT)
_cs_title        = title_font.render("GEOCATCH", True, WHITE)
_cs_subtitle     = tiny_font.render("OVERLAND PARK EDITION", True, (170, 170, 170))
_cs_trainer_labels = [tiny_font.render(f"Trainer {i+1}", True, WHITE) for i in range(4)]
_CS_FLAVORS = ["Ready to explore!", "Born to catch!", "Always adventurous!", "Fearless hunter!"]
_cs_flavor_texts = [tiny_font.render(f, True, (200, 200, 200)) for f in _CS_FLAVORS]
_cs_selected_text = tiny_font.render("SELECTED", True, WHITE)
_cs_badge_w = _cs_selected_text.get_width() + 10
_cs_badge_h = _cs_selected_text.get_height() + 4
_cs_badge_surf = pygame.Surface((_cs_badge_w, _cs_badge_h), pygame.SRCALPHA)
_cs_badge_surf.fill((*ACCENT[:3], 220))
pygame.draw.rect(_cs_badge_surf, WHITE, (0, 0, _cs_badge_w, _cs_badge_h), width=1, border_radius=4)

_cs_btn_text_surf = small_font.render("START GAME", True, WHITE)
_cs_btn_w = _cs_btn_text_surf.get_width() + 48
_cs_btn_h = _cs_btn_text_surf.get_height() + 14
_cs_btn_surf = pygame.Surface((_cs_btn_w, _cs_btn_h), pygame.SRCALPHA)
_cs_btn_surf.fill((*ACCENT[:3], 230))

_cs_arrow_hint  = tiny_font.render("< A/D or Arrow Keys to browse >", True, (120, 120, 120))
_cs_link_how    = tiny_font.render("[?] How to Play", True, (150, 150, 150))
_cs_link_scores = tiny_font.render("[*] Best Scores", True, (150, 150, 150))
_cs_link_how_rect    = pygame.Rect(0, 0, 0, 0)
_cs_link_scores_rect = pygame.Rect(0, 0, 0, 0)
_cs_popup = None

_CS_POPUP_W, _CS_POPUP_H = 380, 220
_cs_popup_how = pygame.Surface((_CS_POPUP_W, _CS_POPUP_H), pygame.SRCALPHA)
_cs_popup_how.fill((26, 26, 46, 240))
pygame.draw.rect(_cs_popup_how, (*ACCENT[:3], 160), (0, 0, _CS_POPUP_W, _CS_POPUP_H), width=2, border_radius=10)
_how_title = small_font.render("HOW TO PLAY", True, ACCENT)
_cs_popup_how.blit(_how_title, (_CS_POPUP_W // 2 - _how_title.get_width() // 2, 14))
_how_bullets = [
    "Move with Arrow Keys or WASD",
    "SPACE near a creature to catch it",
    "Avoid bombs  (-100 pts)",
    "Fire Drake=50 | Water Sprite=40",
    "Forest Guardian=60 | Elec. Spark=45",
    "Shadow Phantom=70",
]
for _bi, _bt_str in enumerate(_how_bullets):
    _bl = tiny_font.render(f"  {_bt_str}", True, (200, 200, 200))
    _cs_popup_how.blit(_bl, (20, 48 + _bi * 24))

_cs_popup_rect = pygame.Rect(0, 0, _CS_POPUP_W, _CS_POPUP_H)

# Pre-rendered scores popup (rebuilt when scores change)
_cs_popup_scores = None
_cs_popup_scores_ver = -1  # tracks len(high_scores) to detect changes

def _build_scores_popup():
    global _cs_popup_scores, _cs_popup_scores_ver
    _cs_popup_scores_ver = len(high_scores)
    _sp = pygame.Surface((_CS_POPUP_W, _CS_POPUP_H), pygame.SRCALPHA)
    _sp.fill((26, 26, 46, 240))
    pygame.draw.rect(_sp, (*ACCENT[:3], 160), (0, 0, _CS_POPUP_W, _CS_POPUP_H), width=2, border_radius=10)
    _st = small_font.render("BEST SCORES", True, ACCENT)
    _sp.blit(_st, (_CS_POPUP_W // 2 - _st.get_width() // 2, 14))
    if high_scores:
        for _si, (_sn, _ss) in enumerate(high_scores[:5]):
            _sc = SCORE_GOLD if _si == 0 else (200, 200, 200)
            _sl = small_font.render(f"{_si+1}.  {_sn}  --  {_ss}", True, _sc)
            _sp.blit(_sl, (40, 50 + _si * 30))
    else:
        _ne = tiny_font.render("No scores yet -- be the first!", True, (150, 150, 150))
        _sp.blit(_ne, (_CS_POPUP_W // 2 - _ne.get_width() // 2, 80))
    _cs_popup_scores = _sp

_build_scores_popup()
# ─────────────────────────────────────────────────────────────────────────────


def _make_float_text(text, x, y, color):
    _ts = font.render(text, True, color)
    _as = pygame.Surface(_ts.get_size(), pygame.SRCALPHA)
    _as.blit(_ts, (0, 0))
    return {"x": x, "y": y, "timer": 1.0, "_surf": _as, "_w": _ts.get_width()}


running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "character_select":
            if event.type == pygame.KEYDOWN:
                if _cs_popup is not None:
                    if event.key == pygame.K_ESCAPE:
                        _cs_popup = None
                else:
                    _char_keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
                    if event.key in _char_keys:
                        selected_char = _char_keys[event.key]
                        game_state = "playing"
                        reset_game()
                    elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                        game_state = "playing"
                        reset_game()
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        selected_char = (selected_char + 1) % 4
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        selected_char = (selected_char - 1) % 4
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if _cs_popup is not None:
                    if not _cs_popup_rect.collidepoint(event.pos):
                        _cs_popup = None
                elif _cs_btn_rect.collidepoint(event.pos):
                    game_state = "playing"
                    reset_game()
                elif _cs_link_how_rect.collidepoint(event.pos):
                    _cs_popup = "how"
                elif _cs_link_scores_rect.collidepoint(event.pos):
                    _cs_popup = "scores"
                else:
                    for i, rect in enumerate(trainer_card_rects):
                        if rect.collidepoint(event.pos):
                            selected_char = i
                            break

        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                # #10: Pause on ESC
                if event.key == pygame.K_ESCAPE:
                    _pause_start_ms = pygame.time.get_ticks()
                    _pause_screenshot.blit(screen, (0, 0))
                    game_state = "paused"
                elif event.key == pygame.K_SPACE:
                    for i in range(len(creatures) - 1, -1, -1):
                        c = creatures[i]
                        # #9: can't catch creatures still fading in (<50% alpha)
                        # Also check fader behavior alpha (invisible phantoms)
                        _eff_alpha = c.get("spawn_alpha", 1.0) * 255
                        if c.get("behavior") == "fader":
                            _fd = math.hypot(c["x"] - player_x, c["y"] - player_y)
                            _eff_alpha = min(_eff_alpha, _fader_alpha(_fd))
                        if _eff_alpha < 128:
                            continue
                        if math.hypot(player_x - c["x"], player_y - c["y"]) < 55:
                            caught = c["type"]
                            # #3: Increment streak first, then apply multiplier
                            catch_streak += 1
                            if catch_streak >= 6:
                                streak_multiplier = 2.0
                            elif catch_streak >= 3:
                                streak_multiplier = 1.5
                            # #15: Streak milestone flash
                            if catch_streak in _STREAK_MILESTONES:
                                _streak_flash_timer = _STREAK_FLASH_DUR
                            base_pts = caught["points"]
                            pts = int(base_pts * streak_multiplier)
                            score += pts
                            inventory.append(caught["name"])
                            float_texts.append(_make_float_text(f"+{pts}", c["x"], c["y"], SCORE_GOLD))
                            # #14: Update cumulative stats
                            _stats["total_catches"][caught["name"]] = _stats["total_catches"].get(caught["name"], 0) + 1
                            # #6: Catch pop animation instead of instant removal
                            catch_animations.append({
                                "x": c["x"], "y": c["y"],
                                "image_key": caught["image_key"],
                                "timer": 0.15,
                                "bob": c.get("_bob", 0),
                            })
                            # Catch particle burst — spawn 8-12 colored dots
                            _pc = CREATURE_COLORS.get(caught["name"], ACCENT)
                            for _pi in range(random.randint(8, 12)):
                                _angle = random.uniform(0, 2 * math.pi)
                                _speed = random.uniform(80, 180)
                                catch_particles.append({
                                    "x": float(c["x"]),
                                    "y": float(c["y"]),
                                    "vx": math.cos(_angle) * _speed,
                                    "vy": math.sin(_angle) * _speed,
                                    "life": 0.5,
                                    "max_life": 0.5,
                                    "color": (
                                        min(255, _pc[0] + random.randint(-30, 30)),
                                        min(255, _pc[1] + random.randint(-30, 30)),
                                        min(255, _pc[2] + random.randint(-30, 30)),
                                    ),
                                    "r": random.randint(2, 5),
                                })
                            _play(_snd_catch)  # #1
                            del creatures[i]
                            break  # one catch per press

        # #10: Pause state event handling
        elif game_state == "paused":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    _total_paused_ms += pygame.time.get_ticks() - _pause_start_ms
                    game_state = "playing"
                elif event.key == pygame.K_q:
                    _total_paused_ms += pygame.time.get_ticks() - _pause_start_ms
                    _save_stats()
                    game_state = "character_select"

        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = "character_select"
                elif event.key == pygame.K_q:
                    game_state = "character_select"
                elif not score_saved and score > 0 and len(name_input) < 5 and event.unicode.isalnum():
                    name_input += event.unicode.upper()
                elif not score_saved and event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif not score_saved and score > 0 and event.key == pygame.K_RETURN and len(name_input) > 0:
                    save_high_score(name_input, score)
                    name_input = ""
                    score_saved = True
                    # Rebuild leaderboard cache
                    if _go_cache is not None:
                        _go_cache["lb_lines"] = []
                        for _li, (_ln, _ls) in enumerate(high_scores[:5]):
                            _lc = (255, 215, 100) if _li == 0 else (200, 200, 210) if _li < 3 else (160, 160, 170)
                            _go_cache["lb_lines"].append(tiny_font.render(f"{_li+1}. {_ln}  {_ls}", True, _lc))

    # ── UPDATE ────────────────────────────────────────────────────────────────
    if game_state == "playing":
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y

        if keys[pygame.K_UP]    or keys[pygame.K_w]: new_y -= player_speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: new_y += player_speed
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: new_x -= player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: new_x += player_speed

        if not any(math.hypot(new_x - rx, player_y - ry) < 55 for rx, ry in rocks):
            player_x = new_x
        if not any(math.hypot(player_x - rx, new_y - ry) < 55 for rx, ry in rocks):
            player_y = new_y

        player_x = max(40, min(WIDTH - 40, player_x))
        player_y = max(50, min(HEIGHT - 40, player_y))

        # Bomb collision (time-based cooldown)
        if bomb_cooldown > 0:
            bomb_cooldown = max(0.0, bomb_cooldown - dt)
        for i in range(len(bombs) - 1, -1, -1):
            bx, by = bombs[i]
            if bomb_cooldown <= 0 and math.hypot(player_x - bx, player_y - by) < 40:
                score = max(0, score - 100)
                float_texts.append(_make_float_text("\u2212100", bx, by, (255, 82, 82)))
                bomb_flash_frames = 3
                # #3: Bomb hit resets streak
                catch_streak = 0
                streak_multiplier = 1.0
                # #8: Screen shake
                shake_frames = 6
                shake_magnitude = 8
                _play(_snd_bomb)  # #1
                bombs[i] = _spawn_bomb_random()
                bomb_cooldown = 1.5
                break

        for ft in float_texts:
            ft["timer"] -= dt
        float_texts[:] = [ft for ft in float_texts if ft["timer"] > 0]

        # #5: Update creature behaviors
        for c in creatures:
            beh = c.get("behavior", "static")
            if beh == "pacer":
                c["orbit_angle"] += c.get("orbit_speed", 1.0) * dt
                c["x"] = c["orbit_cx"] + math.cos(c["orbit_angle"]) * c.get("orbit_r", 30)
                c["y"] = c["orbit_cy"] + math.sin(c["orbit_angle"]) * c.get("orbit_r", 30)
            elif beh == "blinker":
                c["blink_timer"] -= dt
                if c["blink_timer"] <= 0:
                    c["blink_timer"] = random.uniform(2.0, 4.0)
                    # Try up to 5 positions to avoid lake/rocks
                    for _ba in range(5):
                        _nx = c["x"] + random.randint(-40, 40)
                        _ny = c["y"] + random.randint(-40, 40)
                        _nx = max(80, min(800, _nx))
                        _ny = max(80, min(HEIGHT - 80, _ny))
                        if not in_lake(_nx, _ny) and not any(math.hypot(_nx - rx, _ny - ry) < 65 for rx, ry in rocks):
                            c["x"], c["y"] = _nx, _ny
                            c["spawn_alpha"] = 0.3  # LOW-03: fade in at new position
                            break
            elif beh == "drifter":
                _ox, _oy = c["x"], c["y"]  # HIGH-04: preserve original pos for both axis checks
                _nx = _ox + c.get("vx", 0) * dt
                _ny = _oy + c.get("vy", 0) * dt
                # Bounce off bounds, lakes, and rocks
                if _nx < 80 or _nx > 800 or in_lake(_nx, _oy) or any(math.hypot(_nx - rx, _oy - ry) < 65 for rx, ry in rocks):
                    c["vx"] = -c.get("vx", 0)
                else:
                    c["x"] = _nx
                if _ny < 80 or _ny > HEIGHT - 80 or in_lake(_ox, _ny) or any(math.hypot(_ox - rx, _ny - ry) < 65 for rx, ry in rocks):
                    c["vy"] = -c.get("vy", 0)
                else:
                    c["y"] = _ny
            # #9: fade-in alpha
            if c.get("spawn_alpha", 1.0) < 1.0:
                c["spawn_alpha"] = min(1.0, c.get("spawn_alpha", 0.0) + dt / 0.4)

        # #6: Update catch animations
        for ca in catch_animations:
            ca["timer"] -= dt
        catch_animations[:] = [ca for ca in catch_animations if ca["timer"] > 0]

        # Update catch particles
        for cp in catch_particles:
            cp["x"] += cp["vx"] * dt
            cp["y"] += cp["vy"] * dt
            cp["life"] -= dt
        catch_particles[:] = [cp for cp in catch_particles if cp["life"] > 0]

        # #15: Decay streak milestone flash
        if _streak_flash_timer > 0:
            _streak_flash_timer = max(0, _streak_flash_timer - dt)

        # #8: Decay screen shake
        if shake_frames > 0:
            shake_frames -= 1
            shake_magnitude = max(0, shake_magnitude - 1)

        # #13: Spawn delay after wave clear
        if len(creatures) == 0:
            _spawn_delay_timer += dt
            if _spawn_delay_timer >= 0.8:
                _spawn_delay_timer = 0.0
                spawn_creatures(10 if _escalation_triggered else 8)
        else:
            _spawn_delay_timer = 0.0

        elapsed = (pygame.time.get_ticks() - start_ticks - _total_paused_ms) / 1000
        time_left = max(0, int(game_time - elapsed))

        # #4: Late-game escalation at 15s remaining
        if time_left < 15 and not _escalation_triggered:
            _escalation_triggered = True
            _bob_speed = 3.5
            bombs.append(_spawn_bomb_random())

        # #1: Countdown tick for final 5 seconds
        if 0 < time_left <= 5 and time_left != _last_tick_second:
            _last_tick_second = time_left
            _play(_snd_tick)

        if time_left <= 0:
            is_new_high_score = score > 0 and ((len(high_scores) < 5 or score > min(s for _, s in high_scores)) if high_scores else True)
            game_state = "game_over"
            _play(_snd_gameover)  # #1
            # #11: Update trainer personal best
            _tk = str(selected_char)
            if score > _stats.get("trainer_bests", {}).get(_tk, 0):
                _stats.setdefault("trainer_bests", {})[_tk] = score
            _save_stats()  # #14: save cumulative stats
            # Init Creature Showcase end screen
            _go_anim_score = 0
            _go_anim_done = False
            _go_anim_timer = 0.0
            _go_flash_timer = 0.5 if is_new_high_score else 0.0
            # Track which creature types were caught
            _go_caught_keys = set()
            for cname in inventory:
                for ct in CREATURE_TYPES:
                    if ct["name"] == cname:
                        _go_caught_keys.add(ct["image_key"])
            # Tier message based on unique types caught
            _unique_caught = len(_go_caught_keys)
            if _unique_caught >= 5:
                _tier_msg, _tier_color = "LEGENDARY EXPLORER!", (255, 215, 0)
            elif _unique_caught >= 4:
                _tier_msg, _tier_color = "AMAZING RUN!", (100, 220, 255)
            elif _unique_caught >= 2:
                _tier_msg, _tier_color = "GREAT JOB!", (120, 230, 120)
            elif _unique_caught == 1:
                _tier_msg, _tier_color = "GOOD START!", (180, 200, 220)
            else:
                _tier_msg, _tier_color = "NICE TRY!", (200, 200, 210)
            # Fireworks particles (high score only)
            _go_fireworks = []
            if is_new_high_score:
                for _ in range(30):
                    _fw_color = random.choice(list(CREATURE_COLORS.values()))
                    _fw_life = random.uniform(1.5, 3.0)
                    _go_fireworks.append({
                        "x": random.randint(50, WIDTH - 50),
                        "y": random.randint(30, HEIGHT // 2),
                        "vx": random.uniform(-60, 60),
                        "vy": random.uniform(-80, 20),
                        "life": _fw_life,
                        "max_life": _fw_life,
                        "color": _fw_color,
                        "r": random.randint(2, 5),
                    })
            _go_cache = {
                "tier": tier_font.render(_tier_msg, True, _tier_color),
                "tier_shadow": tier_font.render(_tier_msg, True, (0, 0, 0)),
                "count": small_font.render(f"Caught {len(inventory)} creature{'s' if len(inventory) != 1 else ''} ({_unique_caught}/5 types)", True, (200, 200, 210)),
                "nav_r": nav_font.render("[R] Play Again", True, (180, 180, 180)),
                "nav_q": nav_font.render("[Q] Menu", True, (180, 180, 180)),
            }
            if is_new_high_score:
                _go_cache["hs"] = hs_indicator_font.render("NEW HIGH SCORE!", True, SCORE_GOLD)
                _go_cache["hs_glow"] = hs_indicator_font.render("NEW HIGH SCORE!", True, (180, 140, 0))
            # Cache stats text
            _tk = str(selected_char)
            _pb = _stats.get("trainer_bests", {}).get(_tk, 0)
            _go_cache["pb"] = tiny_font.render(f"Personal best: {_pb}", True, (150, 150, 160))
            _total_all = sum(_stats.get("total_catches", {}).values())
            _go_cache["at"] = tiny_font.render(f"All-time catches: {_total_all}", True, (130, 130, 145))
            # Cache leaderboard lines
            _go_cache["lb_title"] = tiny_font.render("TOP 5 HIGH SCORES", True, SCORE_GOLD)
            _go_cache["lb_lines"] = []
            for _li, (_ln, _ls) in enumerate(high_scores[:5]):
                _lm = f"{_li+1}."
                _lc = (255, 215, 100) if _li == 0 else (200, 200, 210) if _li < 3 else (160, 160, 170)
                _go_cache["lb_lines"].append(tiny_font.render(f"{_lm} {_ln}  {_ls}", True, _lc))

    elif game_state == "game_over":
        if not _go_anim_done:
            _go_anim_timer += dt
            # Cap count-up at ~2 seconds max
            _speed = max(200, score / 2.0) if score > 0 else 200
            _go_anim_score = min(score, int(_go_anim_timer * _speed))
            if _go_anim_score >= score:
                _go_anim_score = score
                _go_anim_done = True
        if _go_flash_timer > 0:
            _go_flash_timer = max(0, _go_flash_timer - dt)
        # Update firework particles
        for fw in _go_fireworks:
            fw["x"] += fw["vx"] * dt
            fw["y"] += fw["vy"] * dt
            fw["vy"] += 30 * dt  # gravity
            fw["life"] -= dt
        _go_fireworks = [fw for fw in _go_fireworks if fw["life"] > 0]

    # ── DRAW ──────────────────────────────────────────────────────────────────
    if game_state == "character_select":
        screen.blit(_world_surf, (0, 0))
        screen.blit(_cs_overlay, (0, 0))

        cx = WIDTH // 2

        ty = 50
        tw = _cs_title.get_width()
        screen.blit(_cs_title_shadow, (cx - tw // 2 + 3, ty + 3))
        screen.blit(_cs_title,        (cx - tw // 2,     ty))
        ty += _cs_title.get_height() + 4
        screen.blit(_cs_subtitle, (cx - _cs_subtitle.get_width() // 2, ty))
        ty += _cs_subtitle.get_height() + 24

        total_w = 3 * _CS_CARD_W + _CS_SEL_W + 3 * _CS_CARD_GAP
        row_x = cx - total_w // 2
        cards_mid_y = ty + _CS_SEL_H // 2

        trainer_card_rects.clear()
        cur_x = row_x
        for i in range(4):
            is_sel = (i == selected_char)
            cw = _CS_SEL_W if is_sel else _CS_CARD_W
            ch = _CS_SEL_H if is_sel else _CS_CARD_H
            card_y = cards_mid_y - ch // 2

            if is_sel:
                screen.blit(_cs_card_glow_big, (cur_x - 4, card_y - 4))
                screen.blit(_cs_card_sel_big, (cur_x, card_y))
                if _cs_trainer_big[i]:
                    screen.blit(_cs_trainer_big[i], (cur_x + cw // 2 - 45, card_y + 12))
                else:
                    screen.blit(_trainer_fallback, (cur_x + cw // 2 - _trainer_fallback.get_width() // 2, card_y + 40))
                lbl = _cs_trainer_labels[i]
                screen.blit(lbl, (cur_x + cw // 2 - lbl.get_width() // 2, card_y + 130))
                fl = _cs_flavor_texts[i]
                screen.blit(fl, (cur_x + cw // 2 - fl.get_width() // 2, card_y + 150))
                badge_x = cur_x + cw // 2 - _cs_badge_w // 2
                badge_y = card_y + ch - _cs_badge_h - 10
                screen.blit(_cs_badge_surf, (badge_x, badge_y))
                screen.blit(_cs_selected_text, (badge_x + 5, badge_y + 2))
            else:
                screen.blit(_cs_card_normal, (cur_x, card_y))
                if trainer_images[i]:
                    screen.blit(trainer_images[i], (cur_x + cw // 2 - 35, card_y + 10))
                else:
                    screen.blit(_trainer_fallback, (cur_x + cw // 2 - _trainer_fallback.get_width() // 2, card_y + 30))
                lbl = _cs_trainer_labels[i]
                screen.blit(lbl, (cur_x + cw // 2 - lbl.get_width() // 2, card_y + 108))

            trainer_card_rects.append(pygame.Rect(cur_x, card_y, cw, ch))
            cur_x += cw + _CS_CARD_GAP

        btn_y = ty + _CS_SEL_H + 20
        btn_x = cx - _cs_btn_w // 2
        _cs_btn_rect.update(btn_x, btn_y, _cs_btn_w, _cs_btn_h)
        screen.blit(_cs_btn_surf, (btn_x, btn_y))
        pygame.draw.rect(screen, WHITE, (btn_x, btn_y, _cs_btn_w, _cs_btn_h), width=1, border_radius=8)
        _btx = btn_x + (_cs_btn_w - _cs_btn_text_surf.get_width()) // 2
        _bty = btn_y + (_cs_btn_h - _cs_btn_text_surf.get_height()) // 2
        screen.blit(_cs_btn_text_surf, (_btx, _bty))

        link_y = btn_y + _cs_btn_h + 14
        gap = 40
        total_link_w = _cs_link_how.get_width() + gap + _cs_link_scores.get_width()
        lx = cx - total_link_w // 2
        screen.blit(_cs_link_how, (lx, link_y))
        _cs_link_how_rect.update(lx, link_y, _cs_link_how.get_width(), _cs_link_how.get_height())
        lx2 = lx + _cs_link_how.get_width() + gap
        screen.blit(_cs_link_scores, (lx2, link_y))
        _cs_link_scores_rect.update(lx2, link_y, _cs_link_scores.get_width(), _cs_link_scores.get_height())

        screen.blit(_cs_arrow_hint, (cx - _cs_arrow_hint.get_width() // 2, link_y + 22))

        if _cs_popup == "how":
            px = cx - _CS_POPUP_W // 2
            py = HEIGHT // 2 - _CS_POPUP_H // 2
            _cs_popup_rect.update(px, py, _CS_POPUP_W, _CS_POPUP_H)
            screen.blit(_cs_popup_how, (px, py))
        elif _cs_popup == "scores":
            px = cx - _CS_POPUP_W // 2
            py = HEIGHT // 2 - _CS_POPUP_H // 2
            _cs_popup_rect.update(px, py, _CS_POPUP_W, _CS_POPUP_H)
            screen.blit(_cs_popup_scores, (px, py))

    elif game_state == "game_over":
        _ticks = pygame.time.get_ticks() / 1000.0
        # Background — dark navy with subtle gradient feel
        screen.fill((14, 16, 32))
        # Subtle animated top gradient band
        _pulse_alpha = int(8 + 6 * abs(math.sin(_ticks * 0.6)))
        _go_bg_pulse_surf.fill((25, 30, 55, _pulse_alpha))
        screen.blit(_go_bg_pulse_surf, (0, 0))

        # Orange flash on high score
        if _go_flash_timer > 0:
            _go_flash_surf.set_alpha(int((_go_flash_timer / 0.5) * 80))
            screen.blit(_go_flash_surf, (0, 0))

        # Firework particles (high score only) — HIGH-02: modulate RGB by life fraction
        for fw in _go_fireworks:
            _fw_frac = max(0.0, min(1.0, fw["life"] / fw["max_life"]))
            _fw_col = (int(fw["color"][0] * _fw_frac), int(fw["color"][1] * _fw_frac), int(fw["color"][2] * _fw_frac))
            pygame.draw.circle(screen, _fw_col, (int(fw["x"]), int(fw["y"])), fw["r"])
            if _fw_frac < 0.8:
                pygame.draw.circle(screen, _fw_col, (int(fw["x"] - fw["vx"] * 0.02), int(fw["y"] - fw["vy"] * 0.02)), max(1, fw["r"] - 1))

        cx = WIDTH // 2
        go_y = 20

        # ── Tier message (top) ──
        if _go_cache:
            _tier_s = _go_cache["tier_shadow"]
            _tier_t = _go_cache["tier"]
            screen.blit(_tier_s, (cx - _tier_s.get_width() // 2 + 2, go_y + 2))
            screen.blit(_tier_t, (cx - _tier_t.get_width() // 2, go_y))

        # ── NEW HIGH SCORE banner ──
        if is_new_high_score and _go_cache and "hs" in _go_cache:
            _hs_y = go_y + 48
            _hs_pulse = int(3 * math.sin(_ticks * 4))
            screen.blit(_go_cache["hs_glow"], (cx - _go_cache["hs_glow"].get_width() // 2 + 2, _hs_y + 2))
            screen.blit(_go_cache["hs"], (cx - _go_cache["hs"].get_width() // 2, _hs_y + _hs_pulse))

        # ── Creature Showcase Row ── MED-04: dynamic y to avoid HS banner overlap
        _showcase_y = go_y + 100 if is_new_high_score else go_y + 70
        _stk_spacing = _SHOWCASE_SIZE + 16
        _row_w = 5 * _stk_spacing - 16
        _row_x = cx - _row_w // 2
        for i, ct in enumerate(CREATURE_TYPES):
            _sx = _row_x + i * _stk_spacing
            _caught = ct["image_key"] in _go_caught_keys
            if _caught:
                # Gentle bob animation
                _bob = int(4 * math.sin(_ticks * 2.5 + i * 1.2))
                screen.blit(_showcase_stickers[ct["image_key"]], (_sx, _showcase_y + _bob))
                # Green checkmark below
                screen.blit(_check_surf, (_sx + _SHOWCASE_SIZE // 2 - 10, _showcase_y + _SHOWCASE_SIZE + 2 + _bob))
            else:
                screen.blit(_showcase_grey[ct["image_key"]], (_sx, _showcase_y))
            # Creature name label (pre-cached)
            _nm_surf = _showcase_names_caught[ct["image_key"]] if _caught else _showcase_names_grey[ct["image_key"]]
            screen.blit(_nm_surf, (_sx + _SHOWCASE_SIZE // 2 - _nm_surf.get_width() // 2, _showcase_y + _SHOWCASE_SIZE + 18))

        # ── Middle section: trainer + score ──
        _mid_y = _showcase_y + _SHOWCASE_SIZE + 44
        # Trainer sprite (left side of center)
        _trainer_img = trainer_images[selected_char] if selected_char < len(trainer_images) else None
        _score_card_w = 240
        _trainer_area_w = 90
        _total_mid_w = _trainer_area_w + 20 + _score_card_w
        _mid_left = cx - _total_mid_w // 2
        if _trainer_img:
            screen.blit(_trainer_img, (_mid_left + _trainer_area_w // 2 - 35, _mid_y))
        else:
            pygame.draw.circle(screen, (100, 100, 120), (_mid_left + _trainer_area_w // 2, _mid_y + 45), 30)
            screen.blit(_trainer_fallback, (_mid_left + _trainer_area_w // 2 - _trainer_fallback.get_width() // 2, _mid_y + 32))

        # Score card (right of trainer)
        _sc_x = _mid_left + _trainer_area_w + 20
        _sc_h = 92
        pygame.draw.rect(screen, (26, 28, 48), (_sc_x, _mid_y, _score_card_w, _sc_h), border_radius=12)
        pygame.draw.rect(screen, (60, 65, 90), (_sc_x, _mid_y, _score_card_w, _sc_h), width=1, border_radius=12)
        # Animated score — CRIT-01: cache by displayed value to avoid per-frame 72pt render
        if _go_cache:
            _displayed = str(_go_anim_score)
            if _go_cache.get("_score_val") != _displayed:
                _go_cache["_score_val"] = _displayed
                _go_cache["_score_surf"] = score_big_font.render(_displayed, True, SCORE_GOLD)
            _score_text = _go_cache["_score_surf"]
        else:
            _score_text = score_big_font.render(str(_go_anim_score), True, SCORE_GOLD)
        screen.blit(_score_text, (_sc_x + _score_card_w // 2 - _score_text.get_width() // 2, _mid_y + 4))
        # Caught count line
        if _go_cache:
            _ct_surf = _go_cache["count"]
            screen.blit(_ct_surf, (_sc_x + _score_card_w // 2 - _ct_surf.get_width() // 2, _mid_y + 66))

        # ── Personal best + all-time stats (cached) ──
        _stats_y = _mid_y + _sc_h + 8
        if _go_cache:
            screen.blit(_go_cache["pb"], (cx - 10 - _go_cache["pb"].get_width(), _stats_y))
            screen.blit(_go_cache["at"], (cx + 10, _stats_y))

        # ── Two-column bottom: leaderboard left, name entry right ──
        _bot_y = _stats_y + 24
        _col_w = 240
        _col_gap = 40
        _left_x = cx - _col_gap // 2 - _col_w
        _right_x = cx + _col_gap // 2

        # Left column: Top 5 leaderboard (cached surfaces)
        pygame.draw.rect(screen, (22, 24, 42), (_left_x, _bot_y, _col_w, 170), border_radius=10)
        pygame.draw.rect(screen, (50, 55, 80), (_left_x, _bot_y, _col_w, 170), width=1, border_radius=10)
        if _go_cache:
            screen.blit(_go_cache["lb_title"], (_left_x + _col_w // 2 - _go_cache["lb_title"].get_width() // 2, _bot_y + 8))
            if _go_cache["lb_lines"]:
                for i, _line in enumerate(_go_cache["lb_lines"]):
                    screen.blit(_line, (_left_x + 20, _bot_y + 30 + i * 26))
            else:
                screen.blit(_go_no_scores, (_left_x + _col_w // 2 - _go_no_scores.get_width() // 2, _bot_y + 60))

        # Right column: Name entry
        pygame.draw.rect(screen, (22, 24, 42), (_right_x, _bot_y, _col_w, 170), border_radius=10)
        pygame.draw.rect(screen, (50, 55, 80), (_right_x, _bot_y, _col_w, 170), width=1, border_radius=10)
        if score_saved:
            screen.blit(_go_saved, (_right_x + _col_w // 2 - _go_saved.get_width() // 2, _bot_y + 50))
            screen.blit(_go_saved_hint, (_right_x + _col_w // 2 - _go_saved_hint.get_width() // 2, _bot_y + 85))
        elif score == 0:
            screen.blit(_go_noscore, (_right_x + _col_w // 2 - _go_noscore.get_width() // 2, _bot_y + 55))
            screen.blit(_go_noscore_hint, (_right_x + _col_w // 2 - _go_noscore_hint.get_width() // 2, _bot_y + 85))
        else:
            screen.blit(_go_save_title, (_right_x + _col_w // 2 - _go_save_title.get_width() // 2, _bot_y + 12))
            screen.blit(_go_name_lbl, (_right_x + _col_w // 2 - _go_name_lbl.get_width() // 2, _bot_y + 40))
            # Pill input
            _pill_w, _pill_h = 180, 38
            _pill_x = _right_x + _col_w // 2 - _pill_w // 2
            _pill_y = _bot_y + 62
            pygame.draw.rect(screen, (36, 38, 56), (_pill_x, _pill_y, _pill_w, _pill_h), border_radius=18)
            pygame.draw.rect(screen, ACCENT, (_pill_x, _pill_y, _pill_w, _pill_h), width=2, border_radius=18)
            cursor = "" if len(name_input) >= 5 else ("|" if int(_ticks * 2) % 2 == 0 else " ")
            _name_surf = small_font.render(f"{name_input}{cursor}", True, WHITE)
            screen.blit(_name_surf, (_pill_x + _pill_w // 2 - _name_surf.get_width() // 2, _pill_y + 7))
            if len(name_input) > 0:
                screen.blit(_go_enter_hint, (_right_x + _col_w // 2 - _go_enter_hint.get_width() // 2, _bot_y + 108))

        # ── Always-visible navigation ──
        if _go_cache:
            _nav_y = HEIGHT - 28
            screen.blit(_go_cache["nav_r"], (cx - _go_cache["nav_r"].get_width() - 20, _nav_y))
            screen.blit(_go_cache["nav_q"], (cx + 20, _nav_y))

    # #10: Pause screen
    elif game_state == "paused":
        screen.blit(_pause_screenshot, (0, 0))
        screen.blit(_pause_overlay, (0, 0))
        screen.blit(_pause_title, (WIDTH // 2 - _pause_title.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(_pause_hint_esc, (WIDTH // 2 - _pause_hint_esc.get_width() // 2, HEIGHT // 2))
        screen.blit(_pause_hint_q, (WIDTH // 2 - _pause_hint_q.get_width() // 2, HEIGHT // 2 + 30))

    else:  # playing
        # #8: Screen shake offset
        _shake_ox, _shake_oy = 0, 0
        if shake_frames > 0:
            _shake_ox = random.randint(-shake_magnitude, shake_magnitude)
            _shake_oy = random.randint(-shake_magnitude, shake_magnitude)

        screen.blit(_world_surf, (_shake_ox, _shake_oy))

        for rd in _rock_data:
            rx, ry = rd["pos"]
            screen.blit(_shad_rock, (rx - 22 + _shake_ox, ry + 15 + _shake_oy))
            pygame.draw.circle(screen, (138, 102, 60),  (rx + _shake_ox, ry + _shake_oy), 19)
            pygame.draw.circle(screen, (194, 154, 107), (rx + _shake_ox, ry + _shake_oy), 17)
            pygame.draw.circle(screen, (222, 188, 144), (rx - 5 + _shake_ox, ry - 5 + _shake_oy), 6)
            for (sx, sy), (ex, ey) in rd["cracks"]:
                pygame.draw.line(screen, (108, 72, 36), (sx + _shake_ox, sy + _shake_oy), (ex + _shake_ox, ey + _shake_oy), 1)

        _bt = pygame.time.get_ticks() / 1000.0
        for bx, by in bombs:
            _bsx, _bsy = bx + _shake_ox, by + _shake_oy
            screen.blit(_shad_bomb, (_bsx - 25, _bsy + 20))
            pygame.draw.circle(screen, (50, 50, 50), (_bsx, _bsy), 20)
            pygame.draw.circle(screen, (20, 20, 20), (_bsx, _bsy), 18)
            pygame.draw.circle(screen, (80, 80, 80), (_bsx - 6, _bsy - 6), 5)
            pygame.draw.line(screen, (110, 75, 35), (_bsx + 6, _bsy - 16), (_bsx + 12, _bsy - 22), 2)
            pygame.draw.line(screen, (110, 75, 35), (_bsx + 12, _bsy - 22), (_bsx + 9, _bsy - 29), 2)
            _flicker = math.sin(_bt * 14)
            _sx = _bsx + 9 + int(_flicker * 1.5)
            _sy = _bsy - 29 - int(abs(math.cos(_bt * 10)) * 2)
            pygame.draw.circle(screen, (255, 140, 0), (_sx, _sy), 5)
            _core = (255, 255, 180) if int(_bt * 10) % 2 == 0 else (255, 220, 60)
            pygame.draw.circle(screen, _core, (_sx, _sy), 2)

        _t = pygame.time.get_ticks() / 1000.0
        for c in creatures:
            bob = int(math.sin(_t * _bob_speed + c.get("phase", 0)) * 5)
            c["_bob"] = bob
            _cx = int(c["x"]) + _shake_ox
            _cy = int(c["y"]) + _shake_oy
            screen.blit(_shad_creature, (_cx - 25, _cy + 24))
            screen.blit(_type_circles[c["type"]["name"]], (_cx - 28, _cy + 14))
            if c["type"]["name"] == "Shadow Phantom":
                _glow_r = 34 + int(math.sin(_t * 3.0 + c.get("phase", 0)) * 5)
                _phantom_glow_surf.fill((0, 0, 0, 0))
                pygame.draw.circle(_phantom_glow_surf, (156, 39, 176, 90), (40, 40), _glow_r)
                screen.blit(_phantom_glow_surf, (_cx - 40, _cy + bob - 40))

            # Compute creature alpha (#9 fade-in + #5 fader behavior)
            _c_alpha = int(c.get("spawn_alpha", 1.0) * 255)
            if c.get("behavior") == "fader":
                dist = math.hypot(c["x"] - player_x, c["y"] - player_y)
                _c_alpha = min(_c_alpha, _fader_alpha(dist))

            _stk = _sticker_surfs.get(c["type"]["image_key"])
            if _stk:
                if _c_alpha < 255:
                    _fade_sticker_surf.fill((0, 0, 0, 0))
                    _fade_sticker_surf.blit(_stk, (0, 0))
                    _alpha_mod_surf.fill((255, 255, 255, _c_alpha))
                    _fade_sticker_surf.blit(_alpha_mod_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(_fade_sticker_surf, (_cx - _STICKER_SIZE // 2, _cy - _STICKER_SIZE // 2 + bob))
                else:
                    screen.blit(_stk, (_cx - _STICKER_SIZE // 2, _cy - _STICKER_SIZE // 2 + bob))
            else:
                pygame.draw.circle(screen, WHITE, (_cx, _cy + bob), 25)

        # #6: Draw catch pop animations
        for ca in catch_animations:
            scale = ca["timer"] / 0.15
            if scale > 0:
                size = max(1, int(_STICKER_SIZE * scale))
                _stk = _sticker_surfs.get(ca["image_key"])
                if _stk:
                    scaled = pygame.transform.smoothscale(_stk, (size, size))
                    screen.blit(scaled, (int(ca["x"]) + _shake_ox - size // 2,
                                         int(ca["y"]) + _shake_oy - size // 2 + ca.get("bob", 0)))

        # Draw catch particles
        for cp in catch_particles:
            _frac = cp["life"] / cp["max_life"]
            _alpha = int(255 * _frac)
            _pr = max(1, int(cp["r"] * _frac))
            _pcol = (min(255, max(0, cp["color"][0])),
                     min(255, max(0, cp["color"][1])),
                     min(255, max(0, cp["color"][2])))
            _ps = pygame.Surface((_pr * 2, _pr * 2), pygame.SRCALPHA)
            pygame.draw.circle(_ps, (*_pcol, _alpha), (_pr, _pr), _pr)
            screen.blit(_ps, (int(cp["x"]) + _shake_ox - _pr,
                              int(cp["y"]) + _shake_oy - _pr))

        # Proximity creature label
        closest_c, closest_dist = None, 55
        for c in creatures:
            d = math.hypot(player_x - c["x"], player_y - c["y"])
            if d < closest_dist:
                closest_dist = d
                closest_c = c
        if closest_c is not None:
            label_text = _prox_labels[closest_c['type']['name']]
            lw, lh = label_text.get_width(), label_text.get_height()
            pad_x, pad_y = 10, 5
            lbl_x = int(closest_c["x"]) + _shake_ox - lw // 2 - pad_x
            lbl_x = max(4, min(WIDTH - lw - pad_x * 2 - 4, lbl_x))
            lbl_y = max(4, int(closest_c["y"]) + _shake_oy + closest_c.get("_bob", 0) - 50 - lh - pad_y * 2)
            _pw, _ph = lw + pad_x * 2, lh + pad_y * 2
            _prox_pill_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(_prox_pill_surf, (0, 0, 0, 210), (0, 0, _pw, _ph))
            screen.blit(_prox_pill_surf, (lbl_x, lbl_y), area=pygame.Rect(0, 0, _pw, _ph))
            _prox_border_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(_prox_border_surf, (255, 215, 0, 128), (0, 0, _pw, _ph), width=1, border_radius=6)
            screen.blit(_prox_border_surf, (lbl_x, lbl_y), area=pygame.Rect(0, 0, _pw, _ph))
            screen.blit(label_text, (lbl_x + pad_x, lbl_y + pad_y))

        screen.blit(_shad_trainer, (player_x - 30 + _shake_ox, player_y + 40 + _shake_oy))
        screen.blit(_range_ring_surf, (player_x + _shake_ox - _RANGE_RING_RADIUS - 1,
                                       player_y + _shake_oy - _RANGE_RING_RADIUS - 1))

        _pt = pygame.time.get_ticks() / 1000.0
        _pulse = (_pt * 1.2) % 1.0
        _ring_r = 30 + int(_pulse * 28)
        _ring_alpha = int(210 * (1 - _pulse))
        _pulse_ring_surf.fill((0, 0, 0, 0))
        pygame.draw.circle(_pulse_ring_surf, (*ACCENT, _ring_alpha), (62, 62), _ring_r, 2)
        screen.blit(_pulse_ring_surf, (player_x - 62 + _shake_ox, player_y - 10 - 62 + _shake_oy))

        if trainer_images[selected_char]:
            screen.blit(trainer_images[selected_char], (player_x - 28 + _shake_ox, player_y - 45 + _shake_oy))
        else:
            screen.blit(_trainer_fallback, (player_x - 35 + _shake_ox, player_y - 45 + _shake_oy))

        if bomb_flash_frames > 0:
            screen.blit(_bomb_flash_surf, (0, 0))
            bomb_flash_frames -= 1

        # #15: Streak milestone gold border flash
        if _streak_flash_timer > 0:
            _sf_alpha = int(255 * (_streak_flash_timer / _STREAK_FLASH_DUR))
            _streak_flash_surf.set_alpha(_sf_alpha)
            screen.blit(_streak_flash_surf, (0, 0))

        for ft in float_texts:
            progress = 1.0 - ft["timer"]
            draw_y = int(ft["y"] - progress * 60)
            ft["_surf"].set_alpha(int(ft["timer"] * 255))
            screen.blit(ft["_surf"], (int(ft["x"]) - ft["_w"] // 2, draw_y))

        # Score pill (top-left) — cached render
        score_pill_rect = pygame.Rect(15, 12, 210, 44)
        pygame.draw.rect(screen, PANEL_BG, score_pill_rect, border_radius=22)
        pygame.draw.rect(screen, ACCENT,   score_pill_rect, width=2, border_radius=22)
        if not hasattr(reset_game, '_sc_cache') or reset_game._sc_cache[0] != score:
            reset_game._sc_cache = (score, font.render(f"Score: {score}", True, SCORE_GOLD))
        screen.blit(reset_game._sc_cache[1], (score_pill_rect.x + 16, score_pill_rect.y + 6))

        # #3: Streak multiplier pill (below score) — HIGH-05: pre-baked surfaces
        if streak_multiplier > 1.0:
            _sp = _streak_pills.get(streak_multiplier)
            if _sp:
                screen.blit(_sp, (15, 60))

        # Timer pill (top-right)
        elapsed = (pygame.time.get_ticks() - start_ticks - _total_paused_ms) / 1000
        time_left = max(0, int(game_time - elapsed))
        is_urgent = time_left <= 10
        timer_pill_rect = pygame.Rect(WIDTH - 195, 12, 180, 44)
        pygame.draw.rect(screen, (80, 20, 20) if is_urgent else PANEL_BG,  timer_pill_rect, border_radius=22)
        pygame.draw.rect(screen, URGENT_RED  if is_urgent else ACCENT,     timer_pill_rect, width=2, border_radius=22)
        if not hasattr(reset_game, '_tm_cache') or reset_game._tm_cache[0] != (time_left, is_urgent):
            reset_game._tm_cache = ((time_left, is_urgent), font.render(f"Time: {time_left}s", True, URGENT_RED if is_urgent else WHITE))
        screen.blit(reset_game._tm_cache[1], (timer_pill_rect.x + 14, timer_pill_rect.y + 6))

    pygame.display.flip()

pygame.quit()
sys.exit()
