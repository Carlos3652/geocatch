# GeoCatch 🌍

A Pokémon GO-style creature catching game set in **Overland Park, Kansas**. Explore the map, encounter wild creatures, and catch them all!

## Versions

### Pygame (Desktop)
A full desktop game with character selection, timed rounds, and a high score board.

```bash
pip install pygame
python geocatch_pygame.py
```

### Streamlit (Web)
A browser-based version you can run locally.

```bash
pip install streamlit
streamlit run geocatch.py
```

## Gameplay

- Choose one of **4 trainer characters** to play as
- Move around the map and encounter wild creatures
- Catch them before the **60-second timer** runs out
- Avoid **rocks** and **bombs** on the map
- Score is based on how many creatures you catch and their rarity

## Creatures

| Creature | Points |
|---|---|
| Fire Drake | 50 |
| Water Sprite | 40 |
| Forest Guardian | 60 |
| Electric Spark | 45 |
| Shadow Phantom | 70 |

## High Scores

| Player | Score |
|---|---|
| DAD | 2270 |
| LEO | 475 |
| LEO | 355 |
| LEO | 240 |

## Requirements

- Python 3.x
- `pygame` (desktop version)
- `streamlit` (web version)
