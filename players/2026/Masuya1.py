#!/usr/bin/env python3
import sys
import random
import hasamiShogi
import copy


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

def evaluate(engine: hasamiShogi.HasamiShogi, my_color):
    board = engine.board  # 実際の実装に合わせて
    my_count = 0
    opp_count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == my_color:
                my_count += 1
            elif board[r][c] != EMPTY:
                opp_count += 1
    # 自分の駒が多いほど良い、相手の駒が少ないほど良い
    return my_count - opp_count

def choose_best_move(engine, my_color):
    legal = engine.generate_legal_moves(my_color)
    best_score = -10**9
    best_moves = []

    for (r1, c1, r2, c2) in legal:
        # 盤面をコピーして仮想的にその手を指す
        tmp = copy.deepcopy(engine)  
        tmp.apply_move(r1, c1, r2, c2, my_color)
        score = evaluate(tmp, my_color)

        if score > best_score:
            best_score = score
            best_moves = [(r1, c1, r2, c2)]
        elif score == best_score:
            best_moves.append((r1, c1, r2, c2))

    # 同じスコアの中からランダムに選ぶ
    return random.choice(best_moves)

def main():
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        print("Expected 'OK?' line", file=sys.stderr)
        return
    print("MM", flush=True)

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
            
            if line.startswith("GAME_OVER"):
                break
            
            r1,c1,r2,c2 = parse_moves(line)
            engine.apply_move(r1, c1, r2, c2, opp)

        
        
        r1, c1, r2, c2 = choose_best_move(engine, my_color)
        engine.apply_move(r1, c1, r2, c2, my_color)
        print(f"{r1}{c1}{r2}{c2}", flush=True)
        skip_input = False

if __name__ == "__main__":
    main()
