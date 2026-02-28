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
    except:
        trainer_images.append(None)

selected_char = 0
game_state = "character_select"
trainer_card_rects = []  # updated each frame during character_select draw for mouse hit-testing

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
dt = 0
is_new_high_score = False
score_saved = False

# High scores
high_scores = []
if os.path.exists("highscores.txt"):
    try:
        with open("highscores.txt") as f:
            high_scores = [(line.split()[0], int(line.split()[1])) for line in f.readlines()]
        high_scores.sort(key=lambda x: x[1], reverse=True)
        high_scores = high_scores[:5]
    except:
        high_scores = []

def save_high_score(name, sc):
    global high_scores
    high_scores.append((name, sc))
    high_scores.sort(key=lambda x: x[1], reverse=True)
    high_scores = high_scores[:5]
    with open("highscores.txt", "w") as f:
        for n, s in high_scores:
            f.write(f"{n} {s}\n")

# Monsters
creature_images = {}
try:
    creature_images["fire_drake"] = pygame.transform.smoothscale(pygame.image.load("fire_drake.png"), (60, 60))
    creature_images["water_sprite"] = pygame.transform.smoothscale(pygame.image.load("water_sprite.png"), (60, 60))
    creature_images["forest_guardian"] = pygame.transform.smoothscale(pygame.image.load("forest_guardian.png"), (60, 60))
    creature_images["electric_spark"] = pygame.transform.smoothscale(pygame.image.load("electric_spark.png"), (60, 60))
    creature_images["shadow_phantom"] = pygame.transform.smoothscale(pygame.image.load("shadow_phantom.png"), (60, 60))
except:
    pass

CREATURE_TYPES = [
    {"name": "Fire Drake", "image_key": "fire_drake", "points": 50},
    {"name": "Water Sprite", "image_key": "water_sprite", "points": 40},
    {"name": "Forest Guardian", "image_key": "forest_guardian", "points": 60},
    {"name": "Electric Spark", "image_key": "electric_spark", "points": 45},
    {"name": "Shadow Phantom", "image_key": "shadow_phantom", "points": 70},
]

CREATURE_COLORS = {
    "Fire Drake": (255, 107, 0),
    "Water Sprite": (59, 159, 212),
    "Forest Guardian": (76, 175, 80),
    "Electric Spark": (255, 215, 0),
    "Shadow Phantom": (156, 39, 176),
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

def draw_world():
    """Draw the neighbourhood-themed game world."""
    screen.fill(GRASS)

    # --- ANTIOCH RD (right side, vertical) ---
    pygame.draw.rect(screen, ROAD, (818, 0, 44, HEIGHT))

    # --- W 165TH ST (main horizontal, slight diagonal) ---
    pygame.draw.polygon(screen, ROAD, [
        (0, 334), (818, 324),
        (818, 368), (0, 372)
    ])

    # --- SCHOOL CAMPUS (upper-left circular loop road) ---
    pygame.draw.circle(screen, ROAD, (205, 155), 178)           # outer road ring
    pygame.draw.circle(screen, SCHOOL_GROUND, (205, 155), 150)  # campus interior
    pygame.draw.rect(screen, (218, 218, 216), (96, 92, 118, 52))    # Cedar Hills
    pygame.draw.rect(screen, (218, 218, 216), (216, 105, 128, 56))  # Pleasant Ridge
    pygame.draw.rect(screen, ROAD, (100, 192, 198, 36))              # parking lot
    for _px in range(120, 294, 20):
        pygame.draw.line(screen, SCHOOL_GROUND, (_px, 193), (_px, 227), 1)

    # --- RESIDENTIAL STREETS (south of 165th) ---
    pygame.draw.rect(screen, ROAD, (420, 368, 26, 222))   # Grandview St
    pygame.draw.rect(screen, ROAD, (376, 418, 224, 24))   # 165th Terrace
    pygame.draw.rect(screen, ROAD, (535, 368, 26, 252))   # Eby St
    pygame.draw.rect(screen, ROAD, (720, 368, 26, 310))   # Slater St
    # Cul-de-sac bulbs
    pygame.draw.circle(screen, ROAD, (433, 590), 24)
    pygame.draw.circle(screen, GRASS, (433, 590), 14)
    pygame.draw.circle(screen, ROAD, (548, 620), 24)
    pygame.draw.circle(screen, GRASS, (548, 620), 14)
    pygame.draw.circle(screen, ROAD, (733, 678), 24)
    pygame.draw.circle(screen, GRASS, (733, 678), 14)

    # --- PONDS ---
    pygame.draw.ellipse(screen, LAKE, (378, 374, 58, 28))    # main pond (south of 165th)
    pygame.draw.ellipse(screen, LAKE, (358, 506, 52, 26))    # south pond

    # --- HOUSES ---
    for _hx in range(450, 808, 26):    # north side of 165th
        pygame.draw.rect(screen, HOUSE_COLOR, (_hx, 300, 20, 17))
    for _hx in range(378, 418, 26):    # west of Grandview, south of terrace
        pygame.draw.rect(screen, HOUSE_COLOR, (_hx, 450, 20, 17))
    for _hy in range(450, 582, 26):    # east side of Grandview
        pygame.draw.rect(screen, HOUSE_COLOR, (450, _hy, 20, 17))
    for _hy in range(450, 616, 26):    # west side of Eby
        pygame.draw.rect(screen, HOUSE_COLOR, (508, _hy, 20, 17))
    for _hy in range(450, 616, 26):    # east side of Eby
        pygame.draw.rect(screen, HOUSE_COLOR, (564, _hy, 20, 17))
    for _hy in range(395, 668, 26):    # west side of Slater
        pygame.draw.rect(screen, HOUSE_COLOR, (694, _hy, 20, 17))
    for _hy in range(395, 668, 26):    # east side of Slater
        pygame.draw.rect(screen, HOUSE_COLOR, (749, _hy, 20, 17))

    # --- DISC GOLF COURSE MARKER ---
    pygame.draw.circle(screen, (76, 175, 80), (555, 252), 9)
    pygame.draw.circle(screen, WHITE, (555, 252), 9, 2)
    _dg = tiny_font.render("Disc Golf", True, (70, 140, 70))
    screen.blit(_dg, (530, 265))

    # --- TREES ---
    for td in _tree_data:
        tx, ty = td["pos"]
        cx, cy = tx + 15, ty + 20
        screen.blit(_shad_tree, (tx - 10, ty + 56))
        pygame.draw.rect(screen, TREE_TRUNK, (tx + 8, ty + 25, 14, 35))
        pygame.draw.circle(screen, (18, 76, 18), (cx, cy), 30)
        pygame.draw.circle(screen, (34, 130, 34), (cx, cy), 28)
        pygame.draw.circle(screen, (18, 76, 18), (cx - 9, cy - 11), 23)
        pygame.draw.circle(screen, (50, 155, 50), (cx - 9, cy - 11), 21)
        pygame.draw.circle(screen, (18, 76, 18), (cx + 9, cy - 8), 19)
        pygame.draw.circle(screen, (70, 180, 55), (cx + 9, cy - 8), 17)
        for bx, by in td["berries"]:
            pygame.draw.circle(screen, (210, 45, 45), (bx, by), 3)


def in_lake(x, y):
    """Return True if (x, y) falls inside either pond."""
    if (x - 407) ** 2 / 29 ** 2 + (y - 388) ** 2 / 14 ** 2 < 1.0:
        return True
    if (x - 384) ** 2 / 26 ** 2 + (y - 519) ** 2 / 13 ** 2 < 1.0:
        return True
    return False


def spawn_creatures(n=8):
    global creatures
    creatures = []
    for _ in range(n):
        for _attempt in range(10):
            px = random.randint(80, WIDTH - 80)
            py = random.randint(80, HEIGHT - 80)
            if not in_lake(px, py):
                break
        creatures.append({
            "x": px,
            "y": py,
            "type": random.choice(CREATURE_TYPES),
            "phase": random.uniform(0, 2 * math.pi),
        })

def reset_game():
    global score, inventory, player_x, player_y, start_ticks, creatures, bombs, float_texts, bomb_flash_frames
    global score_saved, is_new_high_score
    score = 0
    inventory = []
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    start_ticks = pygame.time.get_ticks()
    spawn_creatures(8)
    bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]
    float_texts.clear()
    bomb_flash_frames = 0
    score_saved = False
    is_new_high_score = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "character_select":
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    # Keys 1-4: select AND start immediately (backward compat)
                    selected_char = int(event.unicode) - 1
                    game_state = "playing"
                    reset_game()
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    # Enter: start with currently selected trainer
                    game_state = "playing"
                    reset_game()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Click on a trainer card: select only, do not start
                for i, rect in enumerate(trainer_card_rects):
                    if rect.collidepoint(event.pos):
                        selected_char = i
                        break

        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = "character_select"
                elif not score_saved and len(name_input) < 5 and event.unicode.isalnum():
                    name_input += event.unicode.upper()
                elif not score_saved and event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif not score_saved and event.key == pygame.K_RETURN and len(name_input) > 0:
                    save_high_score(name_input, score)
                    name_input = ""
                    score_saved = True

    if game_state == "playing":
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y

        if keys[pygame.K_UP] or keys[pygame.K_w]: new_y -= player_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: new_y += player_speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: new_x -= player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: new_x += player_speed

        blocked = False
        for rx, ry in rocks:
            if math.hypot(new_x - rx, new_y - ry) < 55:
                blocked = True
                break
        if not blocked:
            player_x, player_y = new_x, new_y

        player_x = max(40, min(WIDTH - 40, player_x))
        player_y = max(40, min(HEIGHT - 40, player_y))

        for i in range(len(bombs)-1, -1, -1):
            bx, by = bombs[i]
            if math.hypot(player_x - bx, player_y - by) < 40:
                score = max(0, score - 100)
                float_texts.append({"text": "\u2212100", "x": bx, "y": by, "timer": 1.0, "color": (255, 82, 82)})
                bomb_flash_frames = 3
                bombs[i] = (random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100))

        if keys[pygame.K_SPACE]:
            for i in range(len(creatures)-1, -1, -1):
                c = creatures[i]
                dist = math.hypot(player_x - c["x"], player_y - c["y"])
                if dist < 55:
                    caught = c["type"]
                    score += caught["points"]
                    inventory.append(caught["name"])
                    float_texts.append({"text": f"+{caught['points']}", "x": c["x"], "y": c["y"], "timer": 1.0, "color": SCORE_GOLD})
                    del creatures[i]

        for ft in float_texts:
            ft["timer"] -= dt
        float_texts[:] = [ft for ft in float_texts if ft["timer"] > 0]

        if len(creatures) == 0:
            spawn_creatures(8)

        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, int(game_time - elapsed))
        if time_left <= 0:
            is_new_high_score = (len(high_scores) < 5 or score > min(s for _, s in high_scores)) if high_scores else True
            game_state = "game_over"

    # Draw
    if game_state == "character_select":
        # --- Storybook Variant A: world background + overlay ---
        draw_world()

        # Full-screen dark overlay (~62% opacity)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 158))
        screen.blit(overlay, (0, 0))

        # --- Main center panel (760x320, centered) ---
        PANEL_W, PANEL_H = 760, 320
        panel_x = WIDTH // 2 - PANEL_W // 2
        panel_y = HEIGHT // 2 - 220
        panel_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel_surf.fill((26, 26, 46, 235))
        screen.blit(panel_surf, (panel_x, panel_y))
        # Panel border
        border_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (255, 107, 53, 100), (0, 0, PANEL_W, PANEL_H), width=1, border_radius=14)
        screen.blit(border_surf, (panel_x, panel_y))

        cx = WIDTH // 2
        ty = panel_y + 18

        # Title "GEOCATCH" with drop shadow
        title_surf_shadow = title_font.render("GEOCATCH", True, ACCENT)
        title_surf = title_font.render("GEOCATCH", True, WHITE)
        tw = title_surf.get_width()
        screen.blit(title_surf_shadow, (cx - tw // 2 + 3, ty + 3))
        screen.blit(title_surf, (cx - tw // 2, ty))

        # Subtitle
        ty += title_surf.get_height() + 2
        sub_surf = tiny_font.render("OVERLAND PARK EDITION", True, (170, 170, 170))
        screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, ty))

        # Section divider
        ty += sub_surf.get_height() + 10
        div_surf = tiny_font.render("— CHOOSE YOUR TRAINER —", True, (136, 136, 136))
        screen.blit(div_surf, (cx - div_surf.get_width() // 2, ty))

        # Trainer cards: 4 cards, 140px wide, 16px gap, centered inside panel
        CARD_W, CARD_H = 140, 160
        CARD_GAP = 16
        total_cards_w = 4 * CARD_W + 3 * CARD_GAP
        cards_start_x = cx - total_cards_w // 2
        cards_y = ty + div_surf.get_height() + 10

        trainer_card_rects.clear()
        for i in range(4):
            card_x = cards_start_x + i * (CARD_W + CARD_GAP)
            card_rect = pygame.Rect(card_x, cards_y, CARD_W, CARD_H)
            trainer_card_rects.append(card_rect)

            is_selected = (i == selected_char)

            # Card background
            card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            if is_selected:
                card_surf.fill((255, 107, 53, 30))
            else:
                card_surf.fill((255, 255, 255, 15))
            screen.blit(card_surf, (card_x, cards_y))

            # Card border (selected = ACCENT glow, normal = faint white)
            border_col = ACCENT if is_selected else (255, 255, 255, 38)
            border_s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            border_alpha = 255 if is_selected else 38
            pygame.draw.rect(border_s, (*ACCENT[:3], border_alpha) if is_selected else (255, 255, 255, 38),
                             (0, 0, CARD_W, CARD_H), width=2, border_radius=10)
            screen.blit(border_s, (card_x, cards_y))

            # Selected glow: extra outer rect slightly larger
            if is_selected:
                glow_s = pygame.Surface((CARD_W + 6, CARD_H + 6), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (255, 107, 53, 60), (0, 0, CARD_W + 6, CARD_H + 6), width=3, border_radius=13)
                screen.blit(glow_s, (card_x - 3, cards_y - 3))

            # Trainer image centered (70x90), top portion of card
            img_x = card_x + CARD_W // 2 - 35
            img_y = cards_y + 10
            if trainer_images[i]:
                screen.blit(trainer_images[i], (img_x, img_y))
            else:
                fallback = font.render("T", True, WHITE)
                screen.blit(fallback, (card_x + CARD_W // 2 - fallback.get_width() // 2, img_y + 20))

            # Trainer label
            label_surf = tiny_font.render(f"Trainer {i + 1}", True, WHITE)
            screen.blit(label_surf, (card_x + CARD_W // 2 - label_surf.get_width() // 2, img_y + 96))

            # Number hint "[1]" in ACCENT
            hint_surf = tiny_font.render(f"[{i + 1}]", True, ACCENT)
            screen.blit(hint_surf, (card_x + CARD_W // 2 - hint_surf.get_width() // 2, img_y + 112))

            # "SELECTED" badge on selected card
            if is_selected:
                badge_text = tiny_font.render("SELECTED", True, WHITE)
                badge_w = badge_text.get_width() + 10
                badge_h = badge_text.get_height() + 4
                badge_x = card_x + CARD_W // 2 - badge_w // 2
                badge_y = cards_y + CARD_H - badge_h - 6
                badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
                badge_surf.fill((*ACCENT[:3], 220))
                pygame.draw.rect(badge_surf, WHITE, (0, 0, badge_w, badge_h), width=1, border_radius=4)
                screen.blit(badge_surf, (badge_x, badge_y))
                screen.blit(badge_text, (badge_x + 5, badge_y + 2))

        # "PRESS ENTER OR CLICK TO START" button below cards
        btn_y = cards_y + CARD_H + 12
        btn_text = small_font.render("PRESS ENTER OR CLICK [1-4] TO START", True, WHITE)
        btn_w = btn_text.get_width() + 32
        btn_h = btn_text.get_height() + 12
        btn_x = cx - btn_w // 2
        btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        btn_surf.fill((*ACCENT[:3], 230))
        screen.blit(btn_surf, (btn_x, btn_y))
        pygame.draw.rect(screen, WHITE, (btn_x, btn_y, btn_w, btn_h), width=1, border_radius=8)
        screen.blit(btn_text, (btn_x + 16, btn_y + 6))

        # --- Two mini-panels below the main panel ---
        MINI_Y = panel_y + PANEL_H + 12
        MINI_H = HEIGHT - MINI_Y - 10
        MINI_W = (PANEL_W - 10) // 2  # slight gap between the two
        LEFT_X = panel_x
        RIGHT_X = panel_x + MINI_W + 10

        # How to Play panel (left)
        how_surf = pygame.Surface((MINI_W, MINI_H), pygame.SRCALPHA)
        how_surf.fill((26, 26, 46, 210))
        screen.blit(how_surf, (LEFT_X, MINI_Y))
        pygame.draw.rect(screen, (*ACCENT[:3], 80), (LEFT_X, MINI_Y, MINI_W, MINI_H), width=1, border_radius=8)
        how_title = small_font.render("HOW TO PLAY", True, ACCENT)
        screen.blit(how_title, (LEFT_X + 10, MINI_Y + 8))
        bullet_lines = [
            "Move with Arrow Keys or WASD",
            "SPACE near a creature to catch it",
            "Avoid bombs  (-100 pts)",
            "Fire Drake=50 | Water Sprite=40",
            "Forest Guardian=60 | Elec. Spark=45",
            "Shadow Phantom=70",
        ]
        for bi, bl in enumerate(bullet_lines):
            bl_surf = tiny_font.render(f"• {bl}", True, (200, 200, 200))
            screen.blit(bl_surf, (LEFT_X + 10, MINI_Y + 32 + bi * 18))

        # Top Scores panel (right)
        hs_surf = pygame.Surface((MINI_W, MINI_H), pygame.SRCALPHA)
        hs_surf.fill((26, 26, 46, 210))
        screen.blit(hs_surf, (RIGHT_X, MINI_Y))
        pygame.draw.rect(screen, (*ACCENT[:3], 80), (RIGHT_X, MINI_Y, MINI_W, MINI_H), width=1, border_radius=8)
        hs_title_surf = small_font.render("TOP SCORES", True, ACCENT)
        screen.blit(hs_title_surf, (RIGHT_X + 10, MINI_Y + 8))
        if high_scores:
            for i, (n, s) in enumerate(high_scores):
                rank_color = SCORE_GOLD if i == 0 else (200, 200, 200)
                hs_line = small_font.render(f"{i + 1}.  {n}  —  {s}", True, rank_color)
                screen.blit(hs_line, (RIGHT_X + 10, MINI_Y + 36 + i * 26))
        else:
            no_scores = tiny_font.render("No scores yet — be the first!", True, (150, 150, 150))
            screen.blit(no_scores, (RIGHT_X + 10, MINI_Y + 38))

    else:
        # Playing or game_over: draw the world then game objects
        draw_world()

        for rd in _rock_data:
            rx, ry = rd["pos"]
            screen.blit(_shad_rock, (rx - 22, ry + 15))
            # Dark outline
            pygame.draw.circle(screen, (138, 102, 60), (rx, ry), 19)
            # Warm sandstone base
            pygame.draw.circle(screen, (194, 154, 107), (rx, ry), 17)
            # Warm highlight
            pygame.draw.circle(screen, (222, 188, 144), (rx - 5, ry - 5), 6)
            # Crack details
            for (sx, sy), (ex, ey) in rd["cracks"]:
                pygame.draw.line(screen, (108, 72, 36), (sx, sy), (ex, ey), 1)

        _bt = pygame.time.get_ticks() / 1000.0
        for bx, by in bombs:
            screen.blit(_shad_bomb, (bx - 25, by + 16))
            # Layered bomb body
            pygame.draw.circle(screen, (50, 50, 50), (bx, by), 20)       # outline
            pygame.draw.circle(screen, (20, 20, 20), (bx, by), 18)       # body
            pygame.draw.circle(screen, (80, 80, 80), (bx - 6, by - 6), 5) # highlight
            # Fuse cord (two-segment S-curve)
            pygame.draw.line(screen, (110, 75, 35), (bx + 6, by - 16), (bx + 12, by - 22), 2)
            pygame.draw.line(screen, (110, 75, 35), (bx + 12, by - 22), (bx + 9, by - 29), 2)
            # Animated spark at fuse tip
            _flicker = math.sin(_bt * 14)
            _sx = bx + 9 + int(_flicker * 1.5)
            _sy = by - 29 - int(abs(math.cos(_bt * 10)) * 2)
            pygame.draw.circle(screen, (255, 140, 0), (_sx, _sy), 5)     # orange glow
            _core = (255, 255, 180) if int(_bt * 10) % 2 == 0 else (255, 220, 60)
            pygame.draw.circle(screen, _core, (_sx, _sy), 2)             # bright core

        _t = pygame.time.get_ticks() / 1000.0
        for c in creatures:
            bob = int(math.sin(_t * 2.0 + c.get("phase", 0)) * 5)
            c["_bob"] = bob
            # Shadow and type circle stay on the ground (no bob)
            screen.blit(_shad_creature, (c["x"] - 25, c["y"] + 24))
            screen.blit(_type_circles[c["type"]["name"]], (c["x"] - 28, c["y"] + 14))
            # Shadow Phantom ethereal glow (bobs with sprite)
            if c["type"]["name"] == "Shadow Phantom":
                _glow_r = 34 + int(math.sin(_t * 3.0 + c.get("phase", 0)) * 5)
                _glow_surf = pygame.Surface((_glow_r * 2, _glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(_glow_surf, (156, 39, 176, 90), (_glow_r, _glow_r), _glow_r)
                screen.blit(_glow_surf, (c["x"] - _glow_r, c["y"] + bob - _glow_r))
            # Sprite bobs
            img = creature_images.get(c["type"]["image_key"])
            if img:
                screen.blit(img, (c["x"] - 30, c["y"] - 30 + bob))
            else:
                pygame.draw.circle(screen, WHITE, (c["x"], c["y"] + bob), 25)

        # --- Priority #6: Proximity creature label ---
        # Find the single closest creature within catch radius (55px)
        if game_state == "playing":
            closest_c = None
            closest_dist = 55  # only show within catch radius
            for c in creatures:
                d = math.hypot(player_x - c["x"], player_y - c["y"])
                if d < closest_dist:
                    closest_dist = d
                    closest_c = c
            if closest_c is not None:
                label_str = f"{closest_c['type']['name']}  —  {closest_c['type']['points']} pts  |  SPACE to catch"
                label_text = prox_font.render(label_str, True, WHITE)
                lw = label_text.get_width()
                lh = label_text.get_height()
                pad_x, pad_y = 10, 5
                lbl_x = closest_c["x"] - lw // 2 - pad_x
                lbl_y = closest_c["y"] + closest_c.get("_bob", 0) - 50 - lh - pad_y * 2

                # Dark pill background
                pill_surf = pygame.Surface((lw + pad_x * 2, lh + pad_y * 2), pygame.SRCALPHA)
                pill_surf.fill((0, 0, 0, 210))
                screen.blit(pill_surf, (lbl_x, lbl_y))

                # Gold border
                border_s = pygame.Surface((lw + pad_x * 2, lh + pad_y * 2), pygame.SRCALPHA)
                pygame.draw.rect(border_s, (255, 215, 0, 128),
                                 (0, 0, lw + pad_x * 2, lh + pad_y * 2), width=1, border_radius=6)
                screen.blit(border_s, (lbl_x, lbl_y))

                screen.blit(label_text, (lbl_x + pad_x, lbl_y + pad_y))

        # Catch radius indicator drawn before player sprite so player appears on top
        if game_state == "playing":
            pygame.draw.circle(screen, (200, 200, 200), (player_x, player_y), 55, 1)

        # Trainer pulse ring (playing state only)
        if game_state == "playing":
            _pt = pygame.time.get_ticks() / 1000.0
            _pulse = (_pt * 1.2) % 1.0
            _ring_r = 30 + int(_pulse * 28)
            _ring_alpha = int(210 * (1 - _pulse))
            _ring_surf = pygame.Surface((_ring_r * 2 + 4, _ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_ring_surf, (*ACCENT, _ring_alpha), (_ring_r + 2, _ring_r + 2), _ring_r, 2)
            screen.blit(_ring_surf, (player_x - _ring_r - 2, player_y - 10 - _ring_r - 2))

        screen.blit(_shad_trainer, (player_x - 30, player_y + 40))
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
            alpha = int(ft["timer"] / 1.0 * 255)
            text_surf = font.render(ft["text"], True, ft["color"])
            alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(text_surf, (0, 0))
            alpha_surf.set_alpha(alpha)
            screen.blit(alpha_surf, (int(ft["x"]) - text_surf.get_width() // 2, draw_y))

        if game_state == "playing":
            # --- Score pill (top-left) ---
            score_pill_rect = pygame.Rect(15, 12, 210, 44)
            pygame.draw.rect(screen, PANEL_BG, score_pill_rect, border_radius=22)
            pygame.draw.rect(screen, ACCENT, score_pill_rect, width=2, border_radius=22)
            score_text = font.render(f"Score: {score}", True, SCORE_GOLD)
            screen.blit(score_text, (score_pill_rect.x + 16, score_pill_rect.y + 6))

            # --- Timer pill (top-right) ---
            elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
            time_left = max(0, int(game_time - elapsed))
            is_urgent = time_left <= 10
            timer_bg_color = (80, 20, 20) if is_urgent else PANEL_BG
            timer_border_color = URGENT_RED if is_urgent else ACCENT
            timer_text_color = URGENT_RED if is_urgent else WHITE
            timer_pill_rect = pygame.Rect(WIDTH - 195, 12, 180, 44)
            pygame.draw.rect(screen, timer_bg_color, timer_pill_rect, border_radius=22)
            pygame.draw.rect(screen, timer_border_color, timer_pill_rect, width=2, border_radius=22)
            time_text = font.render(f"Time: {time_left}s", True, timer_text_color)
            screen.blit(time_text, (timer_pill_rect.x + 14, timer_pill_rect.y + 6))

        if game_state == "game_over":
            screen.fill(BLACK)

            go_y = 100

            # New high score indicator drawn above TIME'S UP title
            if is_new_high_score:
                glow_str = "★ NEW HIGH SCORE! ★"
                glow_surf = hs_indicator_font.render(glow_str, True, (180, 140, 0))
                glow_w = glow_surf.get_width()
                screen.blit(glow_surf, (WIDTH // 2 - glow_w // 2 + 2, go_y - 36 + 2))
                gold_surf = hs_indicator_font.render(glow_str, True, SCORE_GOLD)
                gold_w = gold_surf.get_width()
                screen.blit(gold_surf, (WIDTH // 2 - gold_w // 2, go_y - 36))

            go = font.render("TIME'S UP - GAME OVER", True, (255, 60, 60))
            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, go_y))

            final = font.render(f"Final Score: {score}", True, WHITE)
            screen.blit(final, (WIDTH // 2 - final.get_width() // 2, go_y + 60))

            # Creatures caught recap
            caught_count = len(inventory)
            count_surf = small_font.render(f"Creatures Caught: {caught_count}", True, (200, 200, 200))
            screen.blit(count_surf, (WIDTH // 2 - count_surf.get_width() // 2, go_y + 110))

            if caught_count > 0:
                visible = inventory[:15]
                circle_diameter = 20
                circle_radius = circle_diameter // 2
                spacing = 28
                row_width = len(visible) * spacing - (spacing - circle_diameter)
                row_start_x = WIDTH // 2 - row_width // 2 + circle_radius
                row_y = go_y + 148
                for idx, creature_name in enumerate(visible):
                    cx_pos = row_start_x + idx * spacing
                    color = CREATURE_COLORS.get(creature_name, (200, 200, 200))
                    pygame.draw.circle(screen, color, (cx_pos, row_y), circle_radius)

            # Name input / score saved prompt
            prompt_y = go_y + 185
            if score_saved:
                prompt = small_font.render("Score saved! Press R to play again", True, WHITE)
                screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, prompt_y))
            else:
                prompt_str = f"Enter name (5 chars): {name_input}_"
                prompt = small_font.render(prompt_str, True, WHITE)
                screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, prompt_y))

            hs_title = small_font.render("TOP 5 HIGH SCORES", True, WHITE)
            screen.blit(hs_title, (WIDTH // 2 - hs_title.get_width() // 2, go_y + 230))
            for i, (n, s) in enumerate(high_scores):
                line = small_font.render(f"{i+1}. {n} — {s}", True, WHITE)
                screen.blit(line, (WIDTH // 2 - line.get_width() // 2, go_y + 260 + i * 30))

    pygame.display.flip()
    dt = clock.tick(60) / 1000.0

pygame.quit()
sys.exit()
