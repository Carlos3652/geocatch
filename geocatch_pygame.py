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
    buf = _array.array('h', [0] * n)
    fe = freq_end if freq_end else freq
    for i in range(n):
        t = i / sr
        f = freq + (fe - freq) * (i / n)
        fade = 1.0
        fs = int(n * 0.75)
        if i > fs and n > fs:
            fade = (n - i) / (n - fs)
        val = int(volume * 32767 * math.sin(2 * math.pi * f * t) * fade)
        buf[i] = max(-32768, min(32767, val))
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

# #3: Catch streak multiplier
catch_streak = 0
streak_multiplier = 1.0

# #6: Catch pop animations
catch_animations = []

# #8: Screen shake
shake_frames = 0
shake_magnitude = 0

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

# Pre-allocated game-over surfaces
_go_flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_go_flash_surf.fill((255, 140, 0, 80))
_go_bg_pulse_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Pre-allocated bomb flash surface
_bomb_flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_bomb_flash_surf.fill((255, 0, 0, 26))

# Pre-allocated fade sticker surface (#9) + alpha modulation surface
_fade_sticker_surf = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)
_alpha_mod_surf = pygame.Surface((_STICKER_SIZE, _STICKER_SIZE), pygame.SRCALPHA)

# Pre-allocated proximity label surfaces
_prox_pill_surf = pygame.Surface((500, 40), pygame.SRCALPHA)
_prox_border_surf = pygame.Surface((500, 40), pygame.SRCALPHA)

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
    global catch_streak, streak_multiplier, catch_animations, shake_frames, shake_magnitude
    global _total_paused_ms, _pause_start_ms, _escalation_triggered, _bob_speed
    global _spawn_delay_timer, _last_tick_second
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
    shake_frames = 0
    shake_magnitude = 0
    _total_paused_ms = 0
    _pause_start_ms = 0
    _escalation_triggered = False
    _bob_speed = 2.0
    _spawn_delay_timer = 0.0
    _last_tick_second = -1


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
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        selected_char = int(event.unicode) - 1
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
                            _eff_alpha = min(_eff_alpha, max(50, 255 - (_fd - 100) * 2.05))
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
                if event.key == pygame.K_r and (score_saved or score == 0):
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
                            break
            elif beh == "drifter":
                _nx = c["x"] + c.get("vx", 0) * dt
                _ny = c["y"] + c.get("vy", 0) * dt
                # Bounce off bounds, lakes, and rocks
                if _nx < 80 or _nx > 800 or in_lake(_nx, c["y"]) or any(math.hypot(_nx - rx, c["y"] - ry) < 65 for rx, ry in rocks):
                    c["vx"] = -c.get("vx", 0)
                else:
                    c["x"] = _nx
                if _ny < 80 or _ny > HEIGHT - 80 or in_lake(c["x"], _ny) or any(math.hypot(c["x"] - rx, _ny - ry) < 65 for rx, ry in rocks):
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
            # Init celebration animation
            _go_anim_score = 0
            _go_anim_done = False
            _go_anim_timer = 0.0
            _go_flash_timer = 0.5 if is_new_high_score else 0.0
            _bubble_colors = list(CREATURE_COLORS.values())
            _go_bubbles = []
            for _ in range(14):
                _brx = random.randint(10, 22)
                _bry = random.randint(7, 15)
                _bcol = random.choice(_bubble_colors)
                _bsurf = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.ellipse(_bsurf, (*_bcol, 90),
                                    (25 - _brx, 25 - _bry, _brx * 2, _bry * 2))
                _go_bubbles.append({
                    "x": random.randint(20, WIDTH - 20),
                    "y": HEIGHT + random.randint(10, 80),
                    "speed": random.randint(30, 80),
                    "_surf": _bsurf,
                })
            _go_cache = {
                "go": font.render("TIME'S UP - GAME OVER", True, (255, 60, 60)),
                "final": font.render(f"Final Score: {score}", True, WHITE),
                "count": small_font.render(f"Creatures Caught: {len(inventory)}", True, (200, 200, 200)),
            }
            if is_new_high_score:
                glow_str = "NEW HIGH SCORE!"
                _go_cache["glow"] = hs_indicator_font.render(glow_str, True, (180, 140, 0))
                _go_cache["gold"] = hs_indicator_font.render(glow_str, True, SCORE_GOLD)

    elif game_state == "game_over":
        if not _go_anim_done:
            _go_anim_timer += dt
            _go_anim_score = min(score, int(_go_anim_timer * 200))
            if _go_anim_score >= score:
                _go_anim_score = score
                _go_anim_done = True
        if _go_flash_timer > 0:
            _go_flash_timer = max(0, _go_flash_timer - dt)
        for b in _go_bubbles:
            b["y"] -= b["speed"] * dt
            if b["y"] < -30:
                b["y"] = HEIGHT + random.randint(10, 60)
                b["x"] = random.randint(20, WIDTH - 20)

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
                    fb = font.render("T", True, WHITE)
                    screen.blit(fb, (cur_x + cw // 2 - fb.get_width() // 2, card_y + 40))
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
                    fb = font.render("T", True, WHITE)
                    screen.blit(fb, (cur_x + cw // 2 - fb.get_width() // 2, card_y + 30))
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
        # Celebration Mode background
        screen.fill((12, 12, 24))
        _ticks = pygame.time.get_ticks() / 1000.0
        _pulse_alpha = int(5 + 10 * abs(math.sin(_ticks * 0.8)))
        _go_bg_pulse_surf.fill((0, 0, 0, 0))
        _go_bg_pulse_surf.fill((20, 20, 40, _pulse_alpha))
        screen.blit(_go_bg_pulse_surf, (0, 0))

        for b in _go_bubbles:
            screen.blit(b["_surf"], (int(b["x"]) - 25, int(b["y"]) - 25))

        if _go_flash_timer > 0:
            _go_flash_surf.set_alpha(int((_go_flash_timer / 0.5) * 80))
            screen.blit(_go_flash_surf, (0, 0))

        cx = WIDTH // 2
        go_y = 60

        if is_new_high_score and _go_cache:
            screen.blit(_go_cache["glow"], (cx - _go_cache["glow"].get_width() // 2 + 2, go_y - 36 + 2))
            screen.blit(_go_cache["gold"], (cx - _go_cache["gold"].get_width() // 2, go_y - 36))

        if _go_cache:
            screen.blit(_go_cache["go"], (cx - _go_cache["go"].get_width() // 2, go_y))

        # Cache score text after animation completes to avoid per-frame render
        if _go_anim_done and _go_cache and "_score_final" not in _go_cache:
            _go_cache["_score_final"] = score_big_font.render(str(_go_anim_score), True, SCORE_GOLD)
        if _go_cache and "_score_final" in _go_cache:
            _score_text = _go_cache["_score_final"]
        else:
            _score_text = score_big_font.render(str(_go_anim_score), True, SCORE_GOLD)
        screen.blit(_score_text, (cx - _score_text.get_width() // 2, go_y + 45))

        if _go_cache:
            screen.blit(_go_cache["count"], (cx - _go_cache["count"].get_width() // 2, go_y + 125))

        # Creature dots row
        caught_count = len(inventory)
        if caught_count > 0:
            visible = inventory[:15]
            spacing = 28
            circle_radius = 10
            row_width = len(visible) * spacing - (spacing - circle_radius * 2)
            row_start_x = cx - row_width // 2 + circle_radius
            row_y = go_y + 158
            for idx, creature_name in enumerate(visible):
                color = CREATURE_COLORS.get(creature_name, (200, 200, 200))
                pygame.draw.circle(screen, color, (row_start_x + idx * spacing, row_y), circle_radius)

        # #11: Personal best with this trainer
        _tk = str(selected_char)
        _pb = _stats.get("trainer_bests", {}).get(_tk, 0)
        _pb_text = tiny_font.render(f"Trainer {selected_char + 1} personal best: {_pb}", True, (170, 170, 170))
        screen.blit(_pb_text, (cx - _pb_text.get_width() // 2, go_y + 178))

        # #14: All-time cumulative catch count
        _total_all_time = sum(_stats.get("total_catches", {}).values())
        _at_text = tiny_font.render(f"All-time creatures caught: {_total_all_time}", True, (140, 140, 160))
        screen.blit(_at_text, (cx - _at_text.get_width() // 2, go_y + 196))

        # Name entry pill or saved message
        prompt_y = go_y + 220
        if score_saved:
            _saved_text = small_font.render("Score saved!  Press  R  to return to menu", True, WHITE)
            screen.blit(_saved_text, (cx - _saved_text.get_width() // 2, prompt_y))
        else:
            _pill_w, _pill_h = 320, 44
            _pill_x = cx - _pill_w // 2
            _pill_y = prompt_y
            pygame.draw.rect(screen, (40, 40, 60), (_pill_x, _pill_y, _pill_w, _pill_h), border_radius=20)
            pygame.draw.rect(screen, ACCENT, (_pill_x, _pill_y, _pill_w, _pill_h), width=2, border_radius=20)
            _lbl = tiny_font.render("Enter name (5 chars):", True, (180, 180, 180))
            screen.blit(_lbl, (cx - _lbl.get_width() // 2, _pill_y - 20))
            cursor = "" if len(name_input) >= 5 else ("|" if int(_ticks * 2) % 2 == 0 else " ")
            _name_surf = small_font.render(f"{name_input}{cursor}", True, WHITE)
            screen.blit(_name_surf, (cx - _name_surf.get_width() // 2, _pill_y + 10))

        # Top 5 scores
        if high_scores:
            _hs_y = go_y + 285
            hs_title = small_font.render("TOP 5 HIGH SCORES", True, WHITE)
            screen.blit(hs_title, (cx - hs_title.get_width() // 2, _hs_y))
            for i, (n, s) in enumerate(high_scores):
                line = small_font.render(f"{i+1}. {n} -- {s}", True, WHITE)
                screen.blit(line, (cx - line.get_width() // 2, _hs_y + 30 + i * 30))

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
                fader_alpha = int(max(50, min(255, 255 - (dist - 100) * 2.05)))
                _c_alpha = min(_c_alpha, fader_alpha)

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

        # Proximity creature label
        closest_c, closest_dist = None, 55
        for c in creatures:
            d = math.hypot(player_x - c["x"], player_y - c["y"])
            if d < closest_dist:
                closest_dist = d
                closest_c = c
        if closest_c is not None:
            label_str = f"{closest_c['type']['name']}  --  {closest_c['type']['points']} pts  |  SPACE to catch"
            label_text = prox_font.render(label_str, True, WHITE)
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
        pygame.draw.circle(screen, (200, 200, 200), (player_x + _shake_ox, player_y + _shake_oy), 55, 1)

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
            screen.blit(font.render("T", True, WHITE), (player_x - 35 + _shake_ox, player_y - 45 + _shake_oy))

        if bomb_flash_frames > 0:
            screen.blit(_bomb_flash_surf, (0, 0))
            bomb_flash_frames -= 1

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

        # #3: Streak multiplier pill (below score)
        if streak_multiplier > 1.0:
            _streak_color = SCORE_GOLD if streak_multiplier >= 2.0 else ACCENT
            _streak_text = small_font.render(f"x{streak_multiplier:.1f}", True, _streak_color)
            _streak_pill = pygame.Rect(15, 60, _streak_text.get_width() + 20, 28)
            pygame.draw.rect(screen, PANEL_BG, _streak_pill, border_radius=14)
            pygame.draw.rect(screen, _streak_color, _streak_pill, width=2, border_radius=14)
            screen.blit(_streak_text, (_streak_pill.x + 10, _streak_pill.y + 2))

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
