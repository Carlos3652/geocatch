# GeoCatch — Visual Design Suggestions
*UX Designer Review — 2026-02-28 — Storybook Variant A*

---

## Priority Order (if time-limited)
1. Shadow ellipses under all sprites (trainers, creatures, rocks, trees, bombs)
2. Creature type-coded base circles
3. Layered tree canopies with outline stroke
4. Warm stone rocks with crack details
5. Bomb layering + animated fuse spark
6. Tree accent berries + trainer pulse ring

---

## 1. Trainer / Player Characters

**A. Ground Shadow Ellipse (highest priority)**
```python
# Draw BEFORE blitting trainer sprite
shadow_surface = pygame.Surface((60, 16), pygame.SRCALPHA)
pygame.draw.ellipse(shadow_surface, (0, 0, 0, 70), (0, 0, 60, 16))
screen.blit(shadow_surface, (trainer_x - 5, trainer_y + 82))  # just below feet
```
Shadow: 60px wide, 16px tall, opacity 70. Offset 5px left, 82px below sprite top.

**B. Warm Accent Ring (selected trainer)**
```python
# Draw before shadow — gold ring under selected trainer
pygame.draw.ellipse(screen, (255, 215, 0), (trainer_x - 8, trainer_y + 80, 70, 20), 3)
# Pulse: vary radius ±2px using sine wave on timer tick
```

**C. Contrast Backing (if PNG edges are rough)**
```python
# Warm cream circle behind sprite — storybook sticker aesthetic
pygame.draw.circle(screen, (255, 248, 220), (trainer_x + 35, trainer_y + 45), 38)
# #FFF8DC cornsilk — warm, not cold white
```

---

## 2. Creature / Monster Sprites

**A. Type-Coded Color Base Ring**
```python
TYPE_COLORS = {
    "Fire Drake":      (255, 107,  53),   # #FF6B35 — orange accent
    "Water Sprite":    ( 59, 159, 212),   # #3B9FD4 — sky blue
    "Forest Guardian": (126, 200,  80),   # #7EC850 — lighter sage (avoids blending into grass)
    "Electric Spark":  (255, 215,   0),   # #FFD700 — gold
    "Shadow Phantom":  ( 60,  20,  80),   # #3C1450 — deep purple
}

# Draw base circle BEFORE sprite
pygame.draw.circle(screen, TYPE_COLORS[creature_name], (cx + 30, cy + 30), 34)
# Ground shadow on top of base circle
shadow_surface = pygame.Surface((50, 12), pygame.SRCALPHA)
pygame.draw.ellipse(shadow_surface, (0, 0, 0, 80), (0, 0, 50, 12))
screen.blit(shadow_surface, (cx + 5, cy + 52))
# Then blit sprite
screen.blit(creature_sprite, (cx, cy))
```

**B. Idle Bobbing Animation**
```python
bob_offset = int(math.sin(pygame.time.get_ticks() / 400) * 3)
screen.blit(creature_sprite, (cx, cy + bob_offset))
```
±3px vertical sine wave — makes creatures feel alive, no sprite sheet needed.

**C. Pulsing Glow Ring — Shadow Phantom only**
```python
# Purple ring, radius 38, 2px stroke, opacity pulses 120–220 via sine
tick = pygame.time.get_ticks()
ring_alpha = int(170 + math.sin(tick / 300) * 50)
ring_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
pygame.draw.circle(ring_surf, (155, 89, 182, ring_alpha), (40, 40), 38, 2)
screen.blit(ring_surf, (cx - 10, cy - 10))
```

---

## 3. Bombs

**Layered construction with animated fuse spark:**
```python
bx, by = bomb_center_x, bomb_center_y

# Warning shadow (red-tinted, not neutral black)
shadow_surface = pygame.Surface((50, 14), pygame.SRCALPHA)
pygame.draw.ellipse(shadow_surface, (180, 0, 0, 80), (0, 0, 50, 14))
screen.blit(shadow_surface, (bx - 25, by + 16))

# Layer 1: dark red halo
pygame.draw.circle(screen, (139, 0, 0), (bx, by), 20)       # #8B0000
# Layer 2: near-black body
pygame.draw.circle(screen, (30, 30, 30), (bx, by), 18)
# Layer 3: gray glint highlight
pygame.draw.circle(screen, (90, 90, 90), (bx - 5, by - 5), 5)
# Layer 4: danger red stroke
pygame.draw.circle(screen, (200, 0, 0), (bx, by), 18, 2)

# Two-segment curved fuse
pygame.draw.line(screen, (255, 215, 0), (bx + 10, by - 16), (bx + 14, by - 28), 3)
pygame.draw.line(screen, (255, 215, 0), (bx + 14, by - 28), (bx + 18, by - 36), 2)

# Animated fuse spark (flickers every 300ms)
tick = pygame.time.get_ticks()
spark_color = (255, 215, 0) if (tick // 300) % 2 == 0 else (255, 140, 0)
pygame.draw.circle(screen, spark_color, (bx + 18, by - 36), 4)
```

---

## 4. Rocks

**Warm sandstone with crack details:**
```python
rx, ry = rock_x, rock_y

# Ground shadow
shadow_surface = pygame.Surface((44, 12), pygame.SRCALPHA)
pygame.draw.ellipse(shadow_surface, (0, 0, 0, 60), (0, 0, 44, 12))
screen.blit(shadow_surface, (rx - 22, ry + 15))

# Base — warm tan (not cold gray)
pygame.draw.circle(screen, (160, 120, 80), (rx, ry), 19)    # #A07850
# Mid-tone body
pygame.draw.circle(screen, (140, 100, 65), (rx, ry), 17)    # #8C6441
# Highlight glint
pygame.draw.circle(screen, (200, 170, 130), (rx - 5, ry - 5), 6)  # #C8AA82
# Crack texture
pygame.draw.line(screen, (90, 60, 30), (rx - 4, ry + 2), (rx + 2, ry + 8), 2)
pygame.draw.line(screen, (90, 60, 30), (rx + 2, ry - 3), (rx + 6, ry + 4), 1)
# Impassable separation halo
pygame.draw.circle(screen, (255, 255, 255), (rx, ry), 21, 1)
```

**Optional: Size variation** — small (r=12), medium (r=17), large (r=22) for natural clusters.

---

## 5. Trees

**Three-layer canopy with outline stroke + accent berries:**
```python
tx, ty = tree_base_x, tree_base_y

# Ground shadow
shadow_surface = pygame.Surface((50, 14), pygame.SRCALPHA)
pygame.draw.ellipse(shadow_surface, (0, 0, 0, 55), (0, 0, 50, 14))
screen.blit(shadow_surface, (tx - 25, ty + 2))

# Trunk with bark highlight
trunk_rect = pygame.Rect(tx - 6, ty - 30, 12, 32)
pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
pygame.draw.line(screen, (140, 90, 50), (tx - 2, ty - 28), (tx - 2, ty - 2), 2)

# Canopy — outline pass first, then filled layers
pygame.draw.circle(screen, (20, 60, 20),   (tx, ty - 44), 23)   # dark outline
pygame.draw.circle(screen, (34, 100, 48),  (tx, ty - 36), 22)   # Layer 1 — dark base
pygame.draw.circle(screen, (58, 125, 68),  (tx, ty - 44), 20)   # Layer 2 — main
pygame.draw.circle(screen, (100, 180, 80), (tx, ty - 50), 13)   # Layer 3 — highlight
pygame.draw.circle(screen, (150, 220, 110),(tx - 6, ty - 56), 5) # bright glint

# Accent berries/blossoms (store as fixed offsets per tree at generation time)
# tree_accents = [(tx+8, ty-52, (255,80,80)), (tx-10, ty-47, (255,180,0)), (tx+3, ty-60, (255,120,120))]
for ax, ay, acolor in tree_accents:
    pygame.draw.circle(screen, acolor, (ax, ay), 4)
    pygame.draw.circle(screen, (255, 255, 255), (ax - 1, ay - 1), 1)  # glint
```

---

## Color Reference Table

| Element | Current | Suggested | Reason |
|---|---|---|---|
| Trainer backing | None | Cornsilk #FFF8DC circle | Warm neutral grounding |
| Rock color | Cold gray | Warm tan #A07850 | Harmonizes with orange accent |
| Tree canopy | Single #3A7D44 | Three-layer #226430/#3A7D44/#64B450 | Depth without new assets |
| Bomb fuse | Flat gold line | Animated #FF8C00/#FFD700 spark | Danger signal + movement |
| Creature base | None | Type-coded circle per creature | Instant type readability |
| Forest Guardian base | — | Lighter sage #7EC850 | Avoids blending into grass |

---

## Universal Shadow Rule
Every grounded element (trainers, creatures, rocks, trees, bombs) needs a shadow ellipse drawn **before** it using `pygame.SRCALPHA`. Keep opacity between **55–80**. This single consistency rule will unify the entire scene more than any individual element change.
