#!/usr/bin/env python3
import sys
import random
import hasamiShogi

BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def in_bounds(r1, c1, r2, c2):
    return all(0 <= v < BOARD_SIZE for v in (r1, c1, r2, c2))

def parse_moves(s):
    s = s.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError("Move must be 4 digits, e.g. '1234'")
    r1, c1, r2, c2 = map(int, s)
    if not in_bounds(r1, c1, r2, c2):
        raise ValueError("Move out of range")
    return r1, c1, r2, c2

def main():
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        print("Expected 'OK?' line", file=sys.stderr)
        return
    print("Random")

    line = sys.stdin.readline().strip()
    my_color = line[0].upper()
    opp = BLACK if my_color == WHITE else WHITE

    engine = hasamiShogi.HasamiShogi()
    if my_color == BLACK:
        skip_input = True
    else:
        skip_input = False

    while True:
        if not skip_input:
            line = sys.stdin.readline().strip()
            
            r1,c1,r2,c2 = parse_moves(line)
            engine.apply_move(r1, c1, r2, c2, opp)

        if line.startswith("GAME_OVER"):
            break
        
        legal = engine.generate_legal_moves(my_color)
        r1, c1, r2, c2 = random.choice(legal)
        engine.apply_move(r1, c1, r2, c2, my_color)
        print(f"{r1}{c1}{r2}{c2}", flush=True)
        skip_input = False

if __name__ == "__main__":
    main()
