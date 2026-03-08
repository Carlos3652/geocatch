import pygame
import random
import sys
import math
import os

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GeoCatch - Overland Park Edition 🗺️")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 24)
tiny_font = pygame.font.SysFont("Arial", 14)
prox_font = pygame.font.SysFont("Arial", 20)
title_font = pygame.font.SysFont("Arial", 52, bold=True)
hs_indicator_font = pygame.font.SysFont("Arial", 24, bold=True)

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
_cs_btn_rect = pygame.Rect(0, 0, 0, 0)  # LOW-01: clickable start button

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
bomb_cooldown = 0          # HIGH-03: frames remaining before next bomb hit registers
dt = 1 / 60                # CRIT-01: valid delta on the very first frame
is_new_high_score = False
score_saved = False
_go_cache = None  # MED-13: cached game_over static surfaces

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

def save_high_score(name, sc):
    global high_scores
    high_scores.append((name, sc))
    high_scores.sort(key=lambda x: x[1], reverse=True)
    high_scores = high_scores[:5]
    with open("highscores.txt", "w") as f:
        for n, s in high_scores:
            f.write(f"{n} {s}\n")

# Monsters — HIGH-08: load each image independently so one missing file doesn't kill all
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

# Pre-allocated type-coded base circle surfaces (one per creature type)
_type_circles = {}
for _ct in CREATURE_TYPES:
    _tc_color = CREATURE_COLORS[_ct["name"]]
    _tc_surf = pygame.Surface((56, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(_tc_surf, (*_tc_color, 110), (0, 0, 56, 18))
    _type_circles[_ct["name"]] = _tc_surf

# Pre-allocated Shadow Phantom glow surface (fixed max size, cleared+redrawn each frame)
_phantom_glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)

# MED-09: Pre-allocated pulse ring surface (max ring radius 58 → 120x120)
_pulse_ring_surf = pygame.Surface((124, 124), pygame.SRCALPHA)

# MED-10: Pre-allocated proximity label surfaces (max reasonable label size)
_prox_pill_surf = pygame.Surface((500, 40), pygame.SRCALPHA)
_prox_border_surf = pygame.Surface((500, 40), pygame.SRCALPHA)

creatures = []
rocks = [(200, 200), (700, 150), (300, 500), (800, 400), (150, 550), (650, 550)]
bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]

# Pre-compute per-rock crack geometry (fixed seed → stable layout)
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
    # School exterior
    (15, 48), (14, 230), (388, 38), (390, 262),
    # Disc golf / open corridor (north of 165th)
    (496, 76), (596, 128), (696, 58),
    # East of Antioch Rd
    (868, 72), (868, 228), (868, 448), (868, 612),
    # South open spaces
    (88, 438), (164, 556), (282, 626), (66, 266),
]

# Pre-compute per-tree berry positions (fixed seed → stable layout)
_rng_tree = random.Random(7)
_tree_data = []
for _tx, _ty in trees:
    _cx, _cy = _tx + 15, _ty + 20
    _berries = [
        (_cx + _rng_tree.randint(-18, 18), _cy + _rng_tree.randint(-20, 8))
        for _ in range(3)
    ]
    _tree_data.append({"pos": (_tx, _ty), "berries": _berries})

def draw_world(surf):
    """Draw the neighbourhood-themed game world onto surf (MED-08: supports pre-render)."""
    surf.fill(GRASS)

    # --- ANTIOCH RD (right side, vertical) ---
    pygame.draw.rect(surf, ROAD, (818, 0, 44, HEIGHT))

    # --- W 165TH ST (main horizontal, slight diagonal) ---
    pygame.draw.polygon(surf, ROAD, [
        (0, 334), (818, 324),
        (818, 368), (0, 372)
    ])

    # --- SCHOOL CAMPUS (upper-left circular loop road) ---
    pygame.draw.circle(surf, ROAD, (205, 155), 178)
    pygame.draw.circle(surf, SCHOOL_GROUND, (205, 155), 150)
    pygame.draw.rect(surf, (218, 218, 216), (96, 92, 118, 52))    # Cedar Hills
    pygame.draw.rect(surf, (218, 218, 216), (216, 105, 128, 56))  # Pleasant Ridge
    pygame.draw.rect(surf, ROAD, (100, 192, 198, 36))              # parking lot
    for _px in range(120, 294, 20):
        pygame.draw.line(surf, SCHOOL_GROUND, (_px, 193), (_px, 227), 1)

    # --- RESIDENTIAL STREETS (south of 165th) ---
    pygame.draw.rect(surf, ROAD, (420, 368, 26, 222))   # Grandview St
    pygame.draw.rect(surf, ROAD, (376, 418, 224, 24))   # 165th Terrace
    pygame.draw.rect(surf, ROAD, (535, 368, 26, 252))   # Eby St
    pygame.draw.rect(surf, ROAD, (720, 368, 26, 310))   # Slater St
    pygame.draw.circle(surf, ROAD,  (433, 590), 24)
    pygame.draw.circle(surf, GRASS, (433, 590), 14)
    pygame.draw.circle(surf, ROAD,  (548, 620), 24)
    pygame.draw.circle(surf, GRASS, (548, 620), 14)
    pygame.draw.circle(surf, ROAD,  (733, 678), 24)
    pygame.draw.circle(surf, GRASS, (733, 678), 14)

    # --- PONDS ---
    pygame.draw.ellipse(surf, LAKE, (378, 374, 58, 28))
    pygame.draw.ellipse(surf, LAKE, (358, 506, 52, 26))

    # --- HOUSES ---
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

    # --- DISC GOLF COURSE MARKER ---
    pygame.draw.circle(surf, (76, 175, 80), (555, 252), 9)
    pygame.draw.circle(surf, WHITE, (555, 252), 9, 2)
    _dg = tiny_font.render("Disc Golf", True, (70, 140, 70))
    surf.blit(_dg, (530, 265))

    # --- TREES ---
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
    """Return True if (x, y) falls inside either pond."""
    if (x - 407) ** 2 / 29 ** 2 + (y - 388) ** 2 / 14 ** 2 < 1.0:
        return True
    if (x - 384) ** 2 / 26 ** 2 + (y - 519) ** 2 / 13 ** 2 < 1.0:
        return True
    return False


# MED-08: pre-render static world once at startup (blit each frame instead of redrawing ~50 calls)
_world_surf = pygame.Surface((WIDTH, HEIGHT))
draw_world(_world_surf)


def spawn_creatures(n=8):
    global creatures
    creatures = []
    for _ in range(n):
        for _attempt in range(10):
            px = random.randint(80, WIDTH - 80)
            py = random.randint(80, HEIGHT - 80)
            # MED-01: also reject positions too close to rocks (creature would be unreachable)
            if not in_lake(px, py) and not any(math.hypot(px - rx, py - ry) < 65 for rx, ry in rocks):
                break
        else:
            px, py = WIDTH // 2, HEIGHT // 2  # fallback if all attempts fail
        creatures.append({
            "x": px,
            "y": py,
            "type": random.choice(CREATURE_TYPES),
            "phase": random.uniform(0, 2 * math.pi),
        })

def reset_game():
    global score, inventory, player_x, player_y, start_ticks, creatures, bombs, float_texts
    global bomb_flash_frames, bomb_cooldown, score_saved, is_new_high_score, name_input, game_time
    score = 0
    game_time = 60  # LOW-04: ensure game_time is reset
    inventory = []
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    start_ticks = pygame.time.get_ticks()
    spawn_creatures(8)
    bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]
    float_texts.clear()
    bomb_flash_frames = 0
    bomb_cooldown = 0
    name_input = ""          # CRIT-04: clear name between sessions
    score_saved = False
    is_new_high_score = False


# ── HIGH-07: Pre-cached character-select surfaces ─────────────────────────────
_CS_PANEL_W, _CS_PANEL_H = 760, 320
_cs_panel_x = WIDTH // 2 - _CS_PANEL_W // 2
_cs_panel_y = HEIGHT // 2 - 220
_CS_CARD_W, _CS_CARD_H, _CS_CARD_GAP = 140, 160, 16
_CS_MINI_Y = _cs_panel_y + _CS_PANEL_H + 12
_CS_MINI_H = HEIGHT - _CS_MINI_Y - 10
_CS_MINI_W = (_CS_PANEL_W - 10) // 2
_CS_LEFT_X  = _cs_panel_x
_CS_RIGHT_X = _cs_panel_x + _CS_MINI_W + 10

_cs_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_cs_overlay.fill((0, 0, 0, 158))

_cs_panel = pygame.Surface((_CS_PANEL_W, _CS_PANEL_H), pygame.SRCALPHA)
_cs_panel.fill((26, 26, 46, 235))
pygame.draw.rect(_cs_panel, (255, 107, 53, 100), (0, 0, _CS_PANEL_W, _CS_PANEL_H), width=1, border_radius=14)

_cs_how_surf = pygame.Surface((_CS_MINI_W, _CS_MINI_H), pygame.SRCALPHA)
_cs_how_surf.fill((26, 26, 46, 210))
_cs_hs_surf = pygame.Surface((_CS_MINI_W, _CS_MINI_H), pygame.SRCALPHA)
_cs_hs_surf.fill((26, 26, 46, 210))

_cs_card_normal = pygame.Surface((_CS_CARD_W, _CS_CARD_H), pygame.SRCALPHA)
_cs_card_normal.fill((255, 255, 255, 15))
pygame.draw.rect(_cs_card_normal, (255, 255, 255, 38), (0, 0, _CS_CARD_W, _CS_CARD_H), width=2, border_radius=10)

_cs_card_selected = pygame.Surface((_CS_CARD_W, _CS_CARD_H), pygame.SRCALPHA)
_cs_card_selected.fill((255, 107, 53, 30))
pygame.draw.rect(_cs_card_selected, (*ACCENT, 255), (0, 0, _CS_CARD_W, _CS_CARD_H), width=2, border_radius=10)

_cs_card_glow = pygame.Surface((_CS_CARD_W + 6, _CS_CARD_H + 6), pygame.SRCALPHA)
pygame.draw.rect(_cs_card_glow, (255, 107, 53, 60), (0, 0, _CS_CARD_W + 6, _CS_CARD_H + 6), width=3, border_radius=13)

_cs_title_shadow = title_font.render("GEOCATCH", True, ACCENT)
_cs_title        = title_font.render("GEOCATCH", True, WHITE)
_cs_subtitle     = tiny_font.render("OVERLAND PARK EDITION", True, (170, 170, 170))
_cs_divider      = tiny_font.render("— CHOOSE YOUR TRAINER —", True, (136, 136, 136))
_cs_how_title    = small_font.render("HOW TO PLAY", True, ACCENT)
_cs_hs_title_txt = small_font.render("TOP SCORES", True, ACCENT)

_CS_BULLET_SURFS = [
    tiny_font.render(f"• {bl}", True, (200, 200, 200)) for bl in [
        "Move with Arrow Keys or WASD",
        "SPACE near a creature to catch it",
        "Avoid bombs  (-100 pts)",
        "Fire Drake=50 | Water Sprite=40",
        "Forest Guardian=60 | Elec. Spark=45",
        "Shadow Phantom=70",
    ]
]
_cs_trainer_labels = [tiny_font.render(f"Trainer {i+1}", True, WHITE)  for i in range(4)]
_cs_trainer_hints  = [tiny_font.render(f"[{i+1}]",       True, ACCENT) for i in range(4)]
_cs_selected_text  = tiny_font.render("SELECTED", True, WHITE)
_cs_badge_w = _cs_selected_text.get_width() + 10
_cs_badge_h = _cs_selected_text.get_height() + 4
_cs_badge_surf = pygame.Surface((_cs_badge_w, _cs_badge_h), pygame.SRCALPHA)
_cs_badge_surf.fill((*ACCENT[:3], 220))
pygame.draw.rect(_cs_badge_surf, WHITE, (0, 0, _cs_badge_w, _cs_badge_h), width=1, border_radius=4)

_cs_btn_text_surf = small_font.render("PRESS ENTER OR [1-4] TO START", True, WHITE)
_cs_btn_w = _cs_btn_text_surf.get_width() + 32
_cs_btn_h = _cs_btn_text_surf.get_height() + 12
_cs_btn_surf = pygame.Surface((_cs_btn_w, _cs_btn_h), pygame.SRCALPHA)
_cs_btn_surf.fill((*ACCENT[:3], 230))
# ─────────────────────────────────────────────────────────────────────────────


def _make_float_text(text, x, y, color):
    """Pre-render a floating score label once (MED-07: avoids two surface allocs per frame)."""
    _ts = font.render(text, True, color)
    _as = pygame.Surface(_ts.get_size(), pygame.SRCALPHA)
    _as.blit(_ts, (0, 0))
    return {"x": x, "y": y, "timer": 1.0, "_surf": _as, "_w": _ts.get_width()}


running = True
while running:
    dt = clock.tick(60) / 1000.0   # CRIT-01: dt set at top of loop, always valid

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "character_select":
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    selected_char = int(event.unicode) - 1
                    game_state = "playing"
                    reset_game()
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    game_state = "playing"
                    reset_game()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # LOW-01: click the start button to begin
                if _cs_btn_rect.collidepoint(event.pos):
                    game_state = "playing"
                    reset_game()
                else:
                    for i, rect in enumerate(trainer_card_rects):
                        if rect.collidepoint(event.pos):
                            selected_char = i
                            break

        elif game_state == "playing":
            # HIGH-02: single KEYDOWN instead of held-key poll — prevents multi-catch per hold
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                for i in range(len(creatures) - 1, -1, -1):
                    c = creatures[i]
                    if math.hypot(player_x - c["x"], player_y - c["y"]) < 55:
                        caught = c["type"]
                        score += caught["points"]
                        inventory.append(caught["name"])
                        float_texts.append(_make_float_text(f"+{caught['points']}", c["x"], c["y"], SCORE_GOLD))
                        del creatures[i]

        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and score_saved:
                    game_state = "character_select"
                elif not score_saved and len(name_input) < 5 and event.unicode.isalnum():
                    name_input += event.unicode.upper()
                elif not score_saved and event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif not score_saved and event.key == pygame.K_RETURN and len(name_input) > 0:
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

        # HIGH-01: resolve each axis independently — no sticky-wall diagonal blocking
        if not any(math.hypot(new_x - rx, player_y - ry) < 55 for rx, ry in rocks):
            player_x = new_x
        if not any(math.hypot(player_x - rx, new_y - ry) < 55 for rx, ry in rocks):
            player_y = new_y

        player_x = max(40, min(WIDTH - 40, player_x))
        player_y = max(50, min(HEIGHT - 40, player_y))  # LOW-02: 50 prevents sprite clipping at top

        # HIGH-03: bomb collision with 1.5-second cooldown (90 frames)
        if bomb_cooldown > 0:
            bomb_cooldown -= 1
        for i in range(len(bombs) - 1, -1, -1):
            bx, by = bombs[i]
            if bomb_cooldown == 0 and math.hypot(player_x - bx, player_y - by) < 40:
                score = max(0, score - 100)
                float_texts.append(_make_float_text("\u2212100", bx, by, (255, 82, 82)))
                bomb_flash_frames = 3
                # HIGH-09: validate respawn — avoid lakes, rocks, and player
                for _ba in range(10):
                    _bx = random.randint(100, WIDTH - 100)
                    _by = random.randint(100, HEIGHT - 100)
                    if (not in_lake(_bx, _by)
                            and not any(math.hypot(_bx - rx, _by - ry) < 55 for rx, ry in rocks)
                            and math.hypot(_bx - player_x, _by - player_y) > 80):
                        break
                bombs[i] = (_bx, _by)
                bomb_cooldown = 90
                break  # one bomb per cooldown window

        for ft in float_texts:
            ft["timer"] -= dt
        float_texts[:] = [ft for ft in float_texts if ft["timer"] > 0]

        if len(creatures) == 0:
            spawn_creatures(8)

        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, int(game_time - elapsed))
        if time_left <= 0:
            # MED-11: don't show high score banner for score of 0
            is_new_high_score = score > 0 and ((len(high_scores) < 5 or score > min(s for _, s in high_scores)) if high_scores else True)
            game_state = "game_over"
            # MED-13: pre-render static game_over surfaces once
            _go_cache = {
                "go": font.render("TIME'S UP - GAME OVER", True, (255, 60, 60)),
                "final": font.render(f"Final Score: {score}", True, WHITE),
                "count": small_font.render(f"Creatures Caught: {len(inventory)}", True, (200, 200, 200)),
            }
            if is_new_high_score:
                glow_str = "★ NEW HIGH SCORE! ★"
                _go_cache["glow"] = hs_indicator_font.render(glow_str, True, (180, 140, 0))
                _go_cache["gold"] = hs_indicator_font.render(glow_str, True, SCORE_GOLD)

    # ── DRAW ──────────────────────────────────────────────────────────────────
    if game_state == "character_select":
        screen.blit(_world_surf, (0, 0))
        screen.blit(_cs_overlay, (0, 0))
        screen.blit(_cs_panel, (_cs_panel_x, _cs_panel_y))

        cx = WIDTH // 2
        ty = _cs_panel_y + 18
        tw = _cs_title.get_width()
        screen.blit(_cs_title_shadow, (cx - tw // 2 + 3, ty + 3))
        screen.blit(_cs_title,        (cx - tw // 2,     ty))
        ty += _cs_title.get_height() + 2
        screen.blit(_cs_subtitle, (cx - _cs_subtitle.get_width() // 2, ty))
        ty += _cs_subtitle.get_height() + 10
        screen.blit(_cs_divider,  (cx - _cs_divider.get_width()  // 2, ty))

        total_cards_w = 4 * _CS_CARD_W + 3 * _CS_CARD_GAP
        cards_start_x = cx - total_cards_w // 2
        cards_y = ty + _cs_divider.get_height() + 10

        trainer_card_rects.clear()
        for i in range(4):
            card_x = cards_start_x + i * (_CS_CARD_W + _CS_CARD_GAP)
            trainer_card_rects.append(pygame.Rect(card_x, cards_y, _CS_CARD_W, _CS_CARD_H))
            is_selected = (i == selected_char)

            if is_selected:
                screen.blit(_cs_card_glow,     (card_x - 3, cards_y - 3))
                screen.blit(_cs_card_selected, (card_x, cards_y))
            else:
                screen.blit(_cs_card_normal, (card_x, cards_y))

            img_x = card_x + _CS_CARD_W // 2 - 35
            img_y = cards_y + 10
            if trainer_images[i]:
                screen.blit(trainer_images[i], (img_x, img_y))
            else:
                fb = font.render("T", True, WHITE)
                screen.blit(fb, (card_x + _CS_CARD_W // 2 - fb.get_width() // 2, img_y + 20))

            lbl = _cs_trainer_labels[i]
            screen.blit(lbl, (card_x + _CS_CARD_W // 2 - lbl.get_width() // 2, img_y + 96))
            hnt = _cs_trainer_hints[i]
            screen.blit(hnt, (card_x + _CS_CARD_W // 2 - hnt.get_width() // 2, img_y + 112))

            if is_selected:
                badge_x = card_x + _CS_CARD_W // 2 - _cs_badge_w // 2
                badge_y = cards_y + _CS_CARD_H - _cs_badge_h - 6
                screen.blit(_cs_badge_surf,  (badge_x, badge_y))
                screen.blit(_cs_selected_text, (badge_x + 5, badge_y + 2))

        btn_y = cards_y + _CS_CARD_H + 12
        btn_x = cx - _cs_btn_w // 2
        _cs_btn_rect.update(btn_x, btn_y, _cs_btn_w, _cs_btn_h)  # LOW-01
        screen.blit(_cs_btn_surf, (btn_x, btn_y))
        pygame.draw.rect(screen, WHITE, (btn_x, btn_y, _cs_btn_w, _cs_btn_h), width=1, border_radius=8)
        screen.blit(_cs_btn_text_surf, (btn_x + 16, btn_y + 6))

        screen.blit(_cs_how_surf, (_CS_LEFT_X, _CS_MINI_Y))
        pygame.draw.rect(screen, (*ACCENT[:3], 80), (_CS_LEFT_X, _CS_MINI_Y, _CS_MINI_W, _CS_MINI_H), width=1, border_radius=8)
        screen.blit(_cs_how_title, (_CS_LEFT_X + 10, _CS_MINI_Y + 8))
        for bi, bl_surf in enumerate(_CS_BULLET_SURFS):
            screen.blit(bl_surf, (_CS_LEFT_X + 10, _CS_MINI_Y + 32 + bi * 18))

        screen.blit(_cs_hs_surf, (_CS_RIGHT_X, _CS_MINI_Y))
        pygame.draw.rect(screen, (*ACCENT[:3], 80), (_CS_RIGHT_X, _CS_MINI_Y, _CS_MINI_W, _CS_MINI_H), width=1, border_radius=8)
        screen.blit(_cs_hs_title_txt, (_CS_RIGHT_X + 10, _CS_MINI_Y + 8))
        if high_scores:
            for i, (n, s) in enumerate(high_scores):
                rank_color = SCORE_GOLD if i == 0 else (200, 200, 200)
                hs_line = small_font.render(f"{i + 1}.  {n}  —  {s}", True, rank_color)
                screen.blit(hs_line, (_CS_RIGHT_X + 10, _CS_MINI_Y + 36 + i * 26))
        else:
            no_scores = tiny_font.render("No scores yet — be the first!", True, (150, 150, 150))
            screen.blit(no_scores, (_CS_RIGHT_X + 10, _CS_MINI_Y + 38))

    elif game_state == "game_over":
        # HIGH-05: own branch — no world draw wasted before fill(BLACK)
        screen.fill(BLACK)
        go_y = 100

        # MED-13: use pre-rendered cached surfaces
        if is_new_high_score and _go_cache:
            screen.blit(_go_cache["glow"], (WIDTH // 2 - _go_cache["glow"].get_width() // 2 + 2, go_y - 36 + 2))
            screen.blit(_go_cache["gold"], (WIDTH // 2 - _go_cache["gold"].get_width() // 2, go_y - 36))

        screen.blit(_go_cache["go"], (WIDTH // 2 - _go_cache["go"].get_width() // 2, go_y))
        screen.blit(_go_cache["final"], (WIDTH // 2 - _go_cache["final"].get_width() // 2, go_y + 60))
        screen.blit(_go_cache["count"], (WIDTH // 2 - _go_cache["count"].get_width() // 2, go_y + 110))

        caught_count = len(inventory)

        if caught_count > 0:
            visible = inventory[:15]
            spacing = 28
            circle_radius = 10
            row_width = len(visible) * spacing - (spacing - circle_radius * 2)
            row_start_x = WIDTH // 2 - row_width // 2 + circle_radius
            row_y = go_y + 148
            for idx, creature_name in enumerate(visible):
                color = CREATURE_COLORS.get(creature_name, (200, 200, 200))
                pygame.draw.circle(screen, color, (row_start_x + idx * spacing, row_y), circle_radius)

        prompt_y = go_y + 185
        if score_saved:
            prompt = small_font.render("Score saved!  Press  R  to return to menu", True, WHITE)  # LOW-03
        else:
            # MED-12: hide cursor when at max length
            cursor = "" if len(name_input) >= 5 else "_"
            prompt = small_font.render(f"Enter name (5 chars): {name_input}{cursor}", True, WHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, prompt_y))

        if high_scores:
            hs_title = small_font.render("TOP 5 HIGH SCORES", True, WHITE)
            screen.blit(hs_title, (WIDTH // 2 - hs_title.get_width() // 2, go_y + 230))
            for i, (n, s) in enumerate(high_scores):
                line = small_font.render(f"{i+1}. {n} — {s}", True, WHITE)
                screen.blit(line, (WIDTH // 2 - line.get_width() // 2, go_y + 260 + i * 30))

    else:  # playing
        screen.blit(_world_surf, (0, 0))

        for rd in _rock_data:
            rx, ry = rd["pos"]
            screen.blit(_shad_rock, (rx - 22, ry + 15))
            pygame.draw.circle(screen, (138, 102, 60),  (rx, ry), 19)
            pygame.draw.circle(screen, (194, 154, 107), (rx, ry), 17)
            pygame.draw.circle(screen, (222, 188, 144), (rx - 5, ry - 5), 6)
            for (sx, sy), (ex, ey) in rd["cracks"]:
                pygame.draw.line(screen, (108, 72, 36), (sx, sy), (ex, ey), 1)

        _bt = pygame.time.get_ticks() / 1000.0
        for bx, by in bombs:
            screen.blit(_shad_bomb, (bx - 25, by + 20))
            pygame.draw.circle(screen, (50, 50, 50), (bx, by), 20)
            pygame.draw.circle(screen, (20, 20, 20), (bx, by), 18)
            pygame.draw.circle(screen, (80, 80, 80), (bx - 6, by - 6), 5)
            pygame.draw.line(screen, (110, 75, 35), (bx + 6, by - 16), (bx + 12, by - 22), 2)
            pygame.draw.line(screen, (110, 75, 35), (bx + 12, by - 22), (bx + 9, by - 29), 2)
            _flicker = math.sin(_bt * 14)
            _sx = bx + 9 + int(_flicker * 1.5)
            _sy = by - 29 - int(abs(math.cos(_bt * 10)) * 2)
            pygame.draw.circle(screen, (255, 140, 0), (_sx, _sy), 5)
            _core = (255, 255, 180) if int(_bt * 10) % 2 == 0 else (255, 220, 60)
            pygame.draw.circle(screen, _core, (_sx, _sy), 2)

        _t = pygame.time.get_ticks() / 1000.0
        for c in creatures:
            bob = int(math.sin(_t * 2.0 + c.get("phase", 0)) * 5)
            c["_bob"] = bob
            screen.blit(_shad_creature, (c["x"] - 25, c["y"] + 24))
            screen.blit(_type_circles[c["type"]["name"]], (c["x"] - 28, c["y"] + 14))
            if c["type"]["name"] == "Shadow Phantom":
                _glow_r = 34 + int(math.sin(_t * 3.0 + c.get("phase", 0)) * 5)
                _phantom_glow_surf.fill((0, 0, 0, 0))
                pygame.draw.circle(_phantom_glow_surf, (156, 39, 176, 90), (40, 40), _glow_r)
                screen.blit(_phantom_glow_surf, (c["x"] - 40, c["y"] + bob - 40))
            img = creature_images.get(c["type"]["image_key"])
            if img:
                screen.blit(img, (c["x"] - 30, c["y"] - 30 + bob))
            else:
                pygame.draw.circle(screen, WHITE, (c["x"], c["y"] + bob), 25)

        # Proximity creature label
        closest_c, closest_dist = None, 55
        for c in creatures:
            d = math.hypot(player_x - c["x"], player_y - c["y"])
            if d < closest_dist:
                closest_dist = d
                closest_c = c
        if closest_c is not None:
            label_str = f"{closest_c['type']['name']}  —  {closest_c['type']['points']} pts  |  SPACE to catch"
            label_text = prox_font.render(label_str, True, WHITE)
            lw, lh = label_text.get_width(), label_text.get_height()
            pad_x, pad_y = 10, 5
            lbl_x = closest_c["x"] - lw // 2 - pad_x
            lbl_x = max(4, min(WIDTH - lw - pad_x * 2 - 4, lbl_x))  # HIGH-10: clamp horizontal
            lbl_y = max(4, closest_c["y"] + closest_c.get("_bob", 0) - 50 - lh - pad_y * 2)  # HIGH-06
            # MED-10: reuse pre-allocated surfaces
            _pw, _ph = lw + pad_x * 2, lh + pad_y * 2
            _prox_pill_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(_prox_pill_surf, (0, 0, 0, 210), (0, 0, _pw, _ph))
            screen.blit(_prox_pill_surf, (lbl_x, lbl_y), area=pygame.Rect(0, 0, _pw, _ph))
            _prox_border_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(_prox_border_surf, (255, 215, 0, 128), (0, 0, _pw, _ph), width=1, border_radius=6)
            screen.blit(_prox_border_surf, (lbl_x, lbl_y), area=pygame.Rect(0, 0, _pw, _ph))
            screen.blit(label_text, (lbl_x + pad_x, lbl_y + pad_y))

        # MED-03: correct draw order — shadow → catch radius → pulse ring → sprite
        screen.blit(_shad_trainer, (player_x - 30, player_y + 40))

        # Catch radius indicator
        pygame.draw.circle(screen, (200, 200, 200), (player_x, player_y), 55, 1)

        # Trainer pulse ring — MED-09: reuse pre-allocated surface
        _pt = pygame.time.get_ticks() / 1000.0
        _pulse = (_pt * 1.2) % 1.0
        _ring_r = 30 + int(_pulse * 28)
        _ring_alpha = int(210 * (1 - _pulse))
        _pulse_ring_surf.fill((0, 0, 0, 0))
        pygame.draw.circle(_pulse_ring_surf, (*ACCENT, _ring_alpha), (62, 62), _ring_r, 2)
        screen.blit(_pulse_ring_surf, (player_x - 62, player_y - 10 - 62))

        if trainer_images[selected_char]:
            screen.blit(trainer_images[selected_char], (player_x - 28, player_y - 45))
        else:
            screen.blit(font.render("🏃‍♂️", True, WHITE), (player_x - 35, player_y - 45))

        if bomb_flash_frames > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 0, 0, 26))
            screen.blit(flash_surf, (0, 0))
            bomb_flash_frames -= 1

        for ft in float_texts:
            progress = 1.0 - ft["timer"]
            draw_y = int(ft["y"] - progress * 60)
            ft["_surf"].set_alpha(int(ft["timer"] * 255))
            screen.blit(ft["_surf"], (int(ft["x"]) - ft["_w"] // 2, draw_y))

        # Score pill (top-left)
        score_pill_rect = pygame.Rect(15, 12, 210, 44)
        pygame.draw.rect(screen, PANEL_BG, score_pill_rect, border_radius=22)
        pygame.draw.rect(screen, ACCENT,   score_pill_rect, width=2, border_radius=22)
        screen.blit(font.render(f"Score: {score}", True, SCORE_GOLD), (score_pill_rect.x + 16, score_pill_rect.y + 6))

        # Timer pill (top-right)
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, int(game_time - elapsed))
        is_urgent = time_left <= 10
        timer_pill_rect = pygame.Rect(WIDTH - 195, 12, 180, 44)
        pygame.draw.rect(screen, (80, 20, 20) if is_urgent else PANEL_BG,  timer_pill_rect, border_radius=22)
        pygame.draw.rect(screen, URGENT_RED  if is_urgent else ACCENT,     timer_pill_rect, width=2, border_radius=22)
        screen.blit(font.render(f"Time: {time_left}s", True, URGENT_RED if is_urgent else WHITE),
                    (timer_pill_rect.x + 14, timer_pill_rect.y + 6))

    pygame.display.flip()

pygame.quit()
sys.exit()
