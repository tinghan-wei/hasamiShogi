# Hasami Shogi

A Python implementation of Hasami Shogi (Japanese chess variant) with AI players and tournament arena.

## Overview

Hasami Shogi is a two-player abstract strategy board game played on a 9×9 board. This project provides:

- **Game Engine**: Core rules and game logic implementation
- **Tournament Arena**: Framework for multiple AI players to compete
- **AI Players**: Various student-implemented AI strategies ranging from random to advanced minimax algorithms
- **Visualization**: Pygame-based visual display of games
- **Testing Suite**: Comprehensive unit tests for game mechanics

## Game Rules

Hasami Shogi is played on a 9×9 board with:
- Black pieces starting on the top row (row 0)
- White pieces starting on the bottom row (row 8)
- Players alternate turns moving pieces horizontally or vertically
- Pieces are captured when surrounded on opposite sides by opponent pieces
- When one player has at least three more pieces than their opponent, the opponent has one more turn to reduce the gap to within three pieces. If the opponent is unable to do so, the opponent loses the game.
- Alternatively, whichever player has five or more pieces than their opponent wins immediately.

## Project Structure

```
.
├── hasamiShogi.py          # Core game engine
├── arena.py                # Tournament arena for player matches
├── visualize.py            # Game visualization using play records
├── hasamiTest.py           # Unit tests
├── randomPlayer.py         # Simple random move player
└── players/                # Directory of AI player implementations
    ├── Itoh.py
    ├── Tanimoto.py
    ├── Yamada.py
    ├── Shimizu.py
    └── Kumon/   # C/C++
        ├── alphabeta.c
        ├── alphabeta.h
        ├── my_ai.c
        └── shogi.c
    └── Matsumoto/ # C++
        ├── app/           # Source files
        └── include/       # Header files
```

## Key Files

### Core Components

- **hasamiShogi.py**: Game engine implementing board state, move generation, move validation, and victory conditions
- **arena.py**: Tournament system that orchestrates matches between players with visualization
- **visualize.py**: Pygame-based GUI for watching games from records

### Testing

- **hasamiTest.py**: Unit tests for game logic validation

### Players

- **randomPlayer.py**: Baseline player making random legal moves
- **players/**: Directory containing AI implementations by different students using various strategies:
  - Python implementations with heuristic evaluation
  - C/C++ implementations with alpha-beta pruning for improved performance

## Installation

### Requirements

- Python 3.x
- pygame (for visualization)

### Setup

```bash
pip install pygame
```

For C/C++ player modules, compile as needed using their respective build systems.

## Usage

### Run a Match Between Two Players

```bash
python arena.py <player1_module> <player2_module>
```

Example:
```bash
python arena.py "python randomPlayer.py" "python randomPlayer.py"
python arena.py "python players/Itoh.py" "python players/Tanimoto.py"
```

### Run Tests
```bash
python hasamiTest.py
```

## Game Communication Protocol

Players interact with the arena through stdin/stdout using this protocol:

1. Arena sends: `OK?`
2. Player responds with: `<PlayerName>`
3. Arena sends: `<Color>` (Black or White)
4. Player receives moves as 4-digit strings: `r1c1r2c2` (from row-col to row-col)
5. Player outputs moves in same format
6. Game ends with: `GAME_OVER <Winner>`
