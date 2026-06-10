#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import random
import copy #盤面のコピー
import hasamiShogi

BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def in_bounds(r1, c1, r2, c2):
    return all(0 <= v < BOARD_SIZE for v in (r1, c1, r2, c2))

def parse_moves(s):
    s = s.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError("Move must be 4 digits")
    r1, c1, r2, c2 = map(int, s)
    if not in_bounds(r1, c1, r2, c2):
        raise ValueError("Move out of range")
    return r1, c1, r2, c2

def count_pieces(board, color): # 盤面上の自分の駒数と相手の駒数を数える
    count = 0
    for row in board:
        count += row.count(color)
    return count

def evaluate(engine, my_color, opp_color): # 評価関数
    board = engine.board

    my_count = count_pieces(board, my_color)
    opp_count = count_pieces(board, opp_color)

    score = (my_count - opp_count) * 100 # (自分の駒数 - 相手の駒数) * 100

    return score

def choose_best_move(engine, my_color, opp_color):
    legal_moves = engine.generate_legal_moves(my_color)

    best_score = -10**9
    best_moves = []

    for move in legal_moves:
        r1, c1, r2, c2 = move

        sim_engine = copy.deepcopy(engine)

        # 動かす前の相手駒数
        before_opp = count_pieces(sim_engine.board, opp_color)

        sim_engine.apply_move(r1, c1, r2, c2, my_color)

        # 動かした後の相手駒数
        after_opp = count_pieces(sim_engine.board, opp_color)

        # 取った駒数
        captured = before_opp - after_opp

        score = evaluate(sim_engine, my_color, opp_color)

        # 駒を取れているなら少しボーナス
        score += captured * 1000

        if score > best_score:
            best_score = score
            best_moves = [move]

        elif score == best_score:
            best_moves.append(move)

    # 最善手候補からランダムに選ぶ
    return random.choice(best_moves)

def main():
    line = sys.stdin.readline().strip()

    if not line.startswith("OK"):
        print("Expected 'OK?' line", file=sys.stderr)
        return

    print("SimpleAI", flush=True)

    line = sys.stdin.readline().strip()

    my_color = line[0].upper()
    opp = BLACK if my_color == WHITE else WHITE

    engine = hasamiShogi.HasamiShogi()

    skip_input = (my_color == BLACK)

    while True:

        if not skip_input:
            line = sys.stdin.readline().strip()

            if line.startswith("GAME_OVER"):
                break

            r1, c1, r2, c2 = parse_moves(line)

            engine.apply_move(r1, c1, r2, c2, opp)

        # 最善手選択
        r1, c1, r2, c2 = choose_best_move(engine, my_color, opp)

        engine.apply_move(r1, c1, r2, c2, my_color)

        print(f"{r1}{c1}{r2}{c2}", flush=True)

        skip_input = False

if __name__ == "__main__":
    main()