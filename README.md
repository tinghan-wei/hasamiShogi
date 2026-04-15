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
- The game ends when a player's king (leader) is captured or can no longer move

## Project Structure

```
.
├── hasamiShogi.py          # Core game engine
├── arena.py                # Tournament arena for player matches
├── visualize.py            # Game visualization with Pygame
├── hasamiTest.py           # Unit tests
├── randomPlayer.py         # Simple random move player
├── Shimizu.py             # Example AI player
└── players/               # Directory of AI player implementations
    ├── Itoh.py
    ├── Tanimoto.py
    ├── Yamada.py
    ├── Shimizu.py
    └── Kumon Yoshikazu/   # C/C++ optimized implementation
        ├── alphabeta.c
        ├── alphabeta.h
        ├── my_ai.c
        └── shogi.c
    └── Matsumoto Shotaro/ # C++ advanced implementation
        ├── app/           # Source files
        └── include/       # Header files
```

## Key Files

### Core Components

- **hasamiShogi.py**: Game engine implementing board state, move generation, move validation, and victory conditions
- **arena.py**: Tournament system that orchestrates matches between players with visualization
- **visualize.py**: Pygame-based GUI for watching games in real-time

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
python arena.py randomPlayer randomPlayer
python arena.py players.Itoh players.Tanimoto
```

### Visualize a Game

Games played through the arena are automatically visualized using Pygame when available.

### Run Tests

```bash
python -m pytest hasamiTest.py
```

or

```bash
python hasamiTest.py
```

## Game Communication Protocol

Players interact with the arena through stdin/stdout using this protocol:

1. Arena sends: `OK?`
2. Player responds with: `<PlayerName>`
3. Arena sends: `<Color>` (B for Black, W for White)
4. Player receives moves as 4-digit strings: `r1c1r2c2` (from row-col to row-col)
5. Player outputs moves in same format
6. Game ends with: `GAME_OVER <Winner>`

## AI Implementation Examples

### Random Player

The simplest approach - generates all legal moves and picks one at random.

### Minimax with Alpha-Beta Pruning

More sophisticated implementations use minimax algorithm with alpha-beta pruning to evaluate moves several plies deep.

### Optimization Strategies

Some players implement:
- Orthogonal/diagonal move strategies
- Enhanced heuristic evaluations
- C/C++ implementations for performance

## Development

### Adding New AI Players

1. Create a new Python module in the `players/` directory
2. Implement move generation and selection logic
3. Follow the stdin/stdout communication protocol
4. Test against existing players using the arena

### Extending the Game Engine

The core game logic in `hasamiShogi.py` can be extended with:
- Move history tracking
- Performance statistics
- Additional validation rules
- Custom board initialization

## License

This project is developed for educational purposes at Kochi University of Technology and Kochi Prefecture University.

## Contributors

- Multiple student implementations in `players/` directory
- Game engine and arena framework

## Notes

- Tournament histories are saved in `history.pkl`
- Games can be replayed and analyzed from saved histories
- The `.dist/` directory is used for build artifacts
