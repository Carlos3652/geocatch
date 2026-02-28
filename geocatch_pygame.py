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
emoji_font = pygame.font.SysFont("Segoe UI Emoji", 50)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRASS = (34, 139, 34)
ROAD = (139, 69, 19)
LAKE = (30, 144, 255)
TREE_TRUNK = (139, 69, 19)

# Your trainers
trainer_images = []
for i in range(1, 5):
    try:
        img = pygame.transform.scale(pygame.image.load(f"trainer{i}.png"), (70, 90))
        trainer_images.append(img)
    except:
        trainer_images.append(None)

selected_char = 0
game_state = "character_select"

player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 6
score = 0
inventory = []
game_time = 60
start_ticks = 0
name_input = ""

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
    creature_images["fire_drake"] = pygame.transform.scale(pygame.image.load("fire_drake.png"), (60, 60))
    creature_images["water_sprite"] = pygame.transform.scale(pygame.image.load("water_sprite.png"), (60, 60))
    creature_images["forest_guardian"] = pygame.transform.scale(pygame.image.load("forest_guardian.png"), (60, 60))
    creature_images["electric_spark"] = pygame.transform.scale(pygame.image.load("electric_spark.png"), (60, 60))
    creature_images["shadow_phantom"] = pygame.transform.scale(pygame.image.load("shadow_phantom.png"), (60, 60))
except:
    pass

CREATURE_TYPES = [
    {"name": "Fire Drake", "image_key": "fire_drake", "points": 50},
    {"name": "Water Sprite", "image_key": "water_sprite", "points": 40},
    {"name": "Forest Guardian", "image_key": "forest_guardian", "points": 60},
    {"name": "Electric Spark", "image_key": "electric_spark", "points": 45},
    {"name": "Shadow Phantom", "image_key": "shadow_phantom", "points": 70},
]

creatures = []
rocks = [(200, 200), (700, 150), (300, 500), (800, 400), (150, 550), (650, 550)]
bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]

trees = []
for tx in range(80, WIDTH, 130):
    for ty in range(80, HEIGHT, 130):
        if random.random() < 0.7:
            trees.append((tx, ty))

def spawn_creatures(n=8):
    global creatures
    creatures = []
    for _ in range(n):
        creatures.append({
            "x": random.randint(80, WIDTH - 80),
            "y": random.randint(80, HEIGHT - 80),
            "type": random.choice(CREATURE_TYPES)
        })

def reset_game():
    global score, inventory, player_x, player_y, start_ticks, creatures, bombs
    score = 0
    inventory = []
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    start_ticks = pygame.time.get_ticks()
    spawn_creatures(8)
    bombs = [(450, 250), (550, 450), (250, 350), (750, 300)]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "character_select":
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    selected_char = int(event.unicode) - 1
                    game_state = "playing"
                    reset_game()

        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = "character_select"
                elif len(name_input) < 5 and event.unicode.isalnum():
                    name_input += event.unicode.upper()
                elif event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif event.key == pygame.K_RETURN and len(name_input) > 0:
                    save_high_score(name_input, score)
                    name_input = ""
                    game_state = "character_select"

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
                bombs[i] = (random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100))

        if keys[pygame.K_SPACE]:
            for i in range(len(creatures)-1, -1, -1):
                c = creatures[i]
                dist = math.hypot(player_x - c["x"], player_y - c["y"])
                if dist < 55:
                    caught = c["type"]
                    score += caught["points"]
                    inventory.append(caught["name"])
                    del creatures[i]

        if len(creatures) == 0:
            spawn_creatures(8)

        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, int(game_time - elapsed))
        if time_left <= 0:
            game_state = "game_over"

    # Draw
    screen.fill(GRASS)
    pygame.draw.rect(screen, ROAD, (0, 320, WIDTH, 60))
    pygame.draw.rect(screen, ROAD, (480, 0, 60, HEIGHT))
    pygame.draw.ellipse(screen, LAKE, (150, 150, 300, 180))

    for tx, ty in trees:
        pygame.draw.rect(screen, TREE_TRUNK, (tx + 8, ty + 25, 14, 35))
        pygame.draw.circle(screen, (0, 180, 0), (tx + 15, ty + 18), 28)

    for rx, ry in rocks:
        screen.blit(emoji_font.render("🪨", True, WHITE), (rx - 25, ry - 35))

    for bx, by in bombs:
        screen.blit(emoji_font.render("💣", True, (255, 0, 0)), (bx - 25, by - 35))  # Bright red

    for c in creatures:
        img = creature_images.get(c["type"]["image_key"])
        if img:
            screen.blit(img, (c["x"] - 30, c["y"] - 30))
        else:
            pygame.draw.circle(screen, WHITE, (c["x"], c["y"]), 25)

    if trainer_images[selected_char]:
        screen.blit(trainer_images[selected_char], (player_x - 28, player_y - 45))
    else:
        screen.blit(font.render("🏃‍♂️", True, WHITE), (player_x - 35, player_y - 45))

    if game_state == "playing":
        time_text = font.render(f"Time: {time_left}s", True, WHITE)
        screen.blit(time_text, (WIDTH - 200, 20))
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (30, 20))

    if game_state == "character_select":
        screen.fill(BLACK)
        title = font.render("CHOOSE YOUR TRAINER", True, WHITE)
        screen.blit(title, (WIDTH//2 - 220, 80))

        for i in range(4):
            x = 160 + i * 170
            color = (255, 255, 0) if i == selected_char else WHITE
            if trainer_images[i]:
                screen.blit(trainer_images[i], (x, 220))
            else:
                screen.blit(font.render("🏃‍♂️", True, color), (x + 10, 230))
            num = small_font.render(f"{i+1}", True, color)
            screen.blit(num, (x + 40, 350))

        instr = small_font.render("Press 1 - 4 to choose", True, WHITE)
        screen.blit(instr, (WIDTH//2 - 140, 510))

        how = small_font.render("HOW TO PLAY", True, WHITE)
        screen.blit(how, (50, 560))
        screen.blit(small_font.render("• Move with ↑↓←→ or WASD", True, WHITE), (50, 590))
        screen.blit(small_font.render("• Press SPACE near monsters to catch", True, WHITE), (50, 615))
        screen.blit(small_font.render("Points: Fire Drake=50 | Water=40 | Forest=60 | Electric=45 | Shadow=70", True, WHITE), (50, 640))

        hs_title = small_font.render("TOP 5 HIGH SCORES", True, WHITE)
        screen.blit(hs_title, (WIDTH//2 - 110, 420))
        for i, (n, s) in enumerate(high_scores):
            line = small_font.render(f"{i+1}. {n} — {s}", True, WHITE)
            screen.blit(line, (WIDTH//2 - 100, 450 + i*30))

    if game_state == "game_over":
        screen.fill(BLACK)
        go = font.render("TIME'S UP - GAME OVER", True, (255, 60, 60))
        screen.blit(go, (WIDTH//2 - 240, 100))
        final = font.render(f"Final Score: {score}", True, WHITE)
        screen.blit(final, (WIDTH//2 - 160, 180))

        if len(name_input) < 5:
            prompt = small_font.render(f"Enter name (5 chars): {name_input}_", True, WHITE)
            screen.blit(prompt, (WIDTH//2 - 200, 260))
        else:
            prompt = small_font.render("Name saved! Press R to play again", True, WHITE)
            screen.blit(prompt, (WIDTH//2 - 220, 260))

        hs_title = small_font.render("TOP 5 HIGH SCORES", True, WHITE)
        screen.blit(hs_title, (WIDTH//2 - 110, 340))
        for i, (n, s) in enumerate(high_scores):
            line = small_font.render(f"{i+1}. {n} — {s}", True, WHITE)
            screen.blit(line, (WIDTH//2 - 100, 370 + i*30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()