# GeoCatch

A creature catching game inspired by Pokemon GO, set in Overland Park, Kansas. Available as both a Pygame desktop app and a Streamlit web app.

## Overview

GeoCatch drops you into a stylized map of Overland Park where you explore, encounter wild creatures, and catch them before the timer runs out. Choose from 4 trainer characters, navigate around roads, houses, lakes, and trees, and build the highest score by catching rare creatures while avoiding hazards.

## Tech Stack

- **Language:** Python 3
- **Desktop version:** Pygame (1000x700 window)
- **Web version:** Streamlit
- **Audio:** Programmatic tone generation (no external audio files)
- **Tests:** pytest (12+ test files)

## Prerequisites

- Python 3.10+
- Pygame (for desktop version)
- Streamlit (for web version)

## Installation and Running

### Desktop (Pygame)

```bash
pip install pygame

python geocatch_pygame.py
```

### Web (Streamlit)

```bash
pip install streamlit

streamlit run geocatch.py
```

## Gameplay

- Choose one of **4 trainer characters** at the start screen
- Move around the map and encounter wild creatures
- Catch creatures before the **60-second timer** runs out
- Avoid **rocks** and **bombs** on the map
- Score based on creature rarity and catch streak

### Creatures

| Creature | Points |
|----------|--------|
| Fire Drake | 50 |
| Water Sprite | 40 |
| Forest Guardian | 60 |
| Electric Spark | 45 |
| Shadow Phantom | 70 |

## Current Status

Core game is complete and playable. A **22-item UI polish roadmap** (gc-01 through gc-21) is tracked on the Mini-Me task board.

## Completed Features

- Full game loop: trainer select, timed gameplay, score screen
- 5 creature types with rarity-based spawning
- Catch animation with expanding ring mechanic
- Catch ring visibility and pulse effects
- Streak scoring with milestone flash
- HUD with creature icons, timer, score display
- High score leaderboard with name entry
- Particle effects for catches
- Sound effects (programmatic generation)
- All CRIT/HIGH/MED/LOW issues from tech lead and QA reviews resolved

## What's Next (UI Polish Roadmap)

**HIGH priority (6 tasks):** Catch animation expand-implode, catch particles, catch ring visibility, name entry elevation, HUD creature icons, streak milestone flash.

**MED priority (9 tasks):** Pause frosted card, zero score tip, behaviour hints, leaderboard medals, title screen polish, escalation tint, wave clear flash, pacer orbit trail, minimap.

**LOW priority (6 tasks):** Pulse ring origin fix, pond shimmer, house colours, blinker particles, timer shake, road polish.

## Project Structure

```
geocatch/
  geocatch_pygame.py       -- Desktop game (Pygame, single-file)
  geocatch.py              -- Web version (Streamlit)
  catch_ring_config.py     -- Catch ring constants and computation
  name_entry_layout.py     -- Name entry screen layout
  trainer1-4.png           -- Trainer character sprites
  fire_drake.png           -- Creature sprites
  water_sprite.png
  forest_guardian.png
  electric_spark.png
  shadow_phantom.png
  highscores.txt           -- Saved high scores
  stats.json               -- Game statistics
  test_*.py                -- Test files (12+ modules)
```

## Running Tests

```bash
python -m pytest test_*.py -v
```

## License

All rights reserved.
