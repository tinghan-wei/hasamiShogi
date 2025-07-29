#!/usr/bin/env python3
import sys
import random

BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

class HasamiShogi:
    def __init__(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        for c in range(BOARD_SIZE):
            self.board[0][c] = BLACK
            self.board[-1][c] = WHITE
        self.turn = BLACK

    def serialize(self):
        return '\n'.join(''.join(r) for r in self.board)

    def in_bounds(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def capture_from(self, r0, c0, dr, dc, me, opp):
        r, c = r0+dr, c0+dc
        captured = []
        while self.in_bounds(r,c) and self.board[r][c]==opp:
            captured.append((r,c))
            r += dr; c += dc
        if self.in_bounds(r,c) and self.board[r][c]==me and captured:
            for (rr,cc) in captured:
                self.board[rr][cc] = EMPTY

    def is_clear_path(self, r1, c1, r2, c2):
        """Return True if all squares strictly between (r1,c1) and (r2,c2) are EMPTY."""
        # must be straight-line
        if r1 == r2:
            step = 1 if c2 > c1 else -1
            for c in range(c1 + step, c2, step):
                if self.board[r1][c] != EMPTY:
                    return False
            return True
        elif c1 == c2:
            step = 1 if r2 > r1 else -1
            for r in range(r1 + step, r2, step):
                if self.board[r][c1] != EMPTY:
                    return False
            return True
        else:
            return False

    def is_legal_move(self, r1, c1, r2, c2, me):
        opp = BLACK if me == WHITE else WHITE

        # 1. In‑bounds
        if not (self.in_bounds(r1, c1) and self.in_bounds(r2, c2)):
            return False
        # 2. Must be moving your own piece to an empty square
        if self.board[r1][c1] != me or self.board[r2][c2] != EMPTY:
            return False
        # 3. Must move along row or column, and actually move
        if not ((r1 == r2 and c1 != c2) or (c1 == c2 and r1 != r2)):
            return False
        # 4. Path must be clear
        if not self.is_clear_path(r1, c1, r2, c2):
            return False

        return True

    def apply_move(self, r1, c1, r2, c2, me):
        """Validate, slide the piece like a rook, then perform captures."""
        if not self.is_legal_move(r1, c1, r2, c2, me):
            raise ValueError(f"Illegal move: from {(r1,c1)} to {(r2,c2)}")

        # 1. Slide
        self.board[r1][c1] = EMPTY
        self.board[r2][c2] = me

        # 2. Flank‐capture in all four orthogonal directions
        opp = BLACK if me == WHITE else WHITE
        for dr, dc in DIRECTIONS:
            self.capture_from(r2, c2, dr, dc, me, opp)

    def is_game_over(self):
        blacks = sum(r.count(BLACK) for r in self.board)
        whites = sum(r.count(WHITE) for r in self.board)
        if blacks <= 1: return WHITE
        if whites <= 1: return BLACK
        return None

    def find_legal_moves(self, color):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == color:
                    # slide like a rook in each direction
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        # keep going while the square is empty
                        while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == EMPTY:
                            moves.append((r, c, nr, nc))
                            nr += dr
                            nc += dc
        return moves

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

    engine = HasamiShogi()
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
        
        legal = engine.find_legal_moves(my_color)
        r1, c1, r2, c2 = random.choice(legal)
        engine.apply_move(r1, c1, r2, c2, my_color)
        print(f"{r1}{c1}{r2}{c2}", flush=True)
        skip_input = False

if __name__ == "__main__":
    main()
