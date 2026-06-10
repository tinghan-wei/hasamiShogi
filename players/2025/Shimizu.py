#!/usr/bin/env python3

import sys
import random
import hasamiShogi
import copy

# 定数
BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# 評価関数 (Evaluation Function)
def evaluate_board(board_obj, my_color, opp_color):
    score = 0
    board = board_obj.board
    captures_my = board_obj.captures[my_color]
    captures_opp = board_obj.captures[opp_color]

    # 1. キャプチャ数の評価
    score += (captures_my - captures_opp) * 200

    # 2. 駒の安全性の評価
    threatened_pieces = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == my_color:
                for dr, dc in DIRECTIONS:
                    r1, c1 = r - dr, c - dc
                    r2, c2 = r + dr, c + dc
                    if 0 <= r1 < BOARD_SIZE and 0 <= c1 < BOARD_SIZE and \
                       0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                        if board[r1][c1] == opp_color and board[r2][c2] == opp_color:
                            threatened_pieces += 1
    score -= threatened_pieces * 100

    # 3. 中央支配の評価
    center_score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == my_color:
                distance_to_center = abs(r - 4) + abs(c - 4)
                center_score += (10 - distance_to_center)
            elif board[r][c] == opp_color:
                distance_to_center = abs(r - 4) + abs(c - 4)
                center_score -= (10 - distance_to_center)
    score += center_score * 5

    return score

# ミニマックス法とアルファ・ベータ法
def minimax(board_obj, depth, is_maximizing, alpha, beta, my_color, opp_color):
    if depth == 0 or board_obj.is_game_over() is not None:
        return evaluate_board(board_obj, my_color, opp_color)

    if is_maximizing:
        max_eval = -sys.maxsize
        legal_moves = board_obj.generate_legal_moves(my_color)
        if not legal_moves:
            return -1000000 
        
        for move in legal_moves:
            temp_board_obj = copy.deepcopy(board_obj)
            temp_board_obj.apply_move(*move, my_color)
            eval = minimax(temp_board_obj, depth - 1, False, alpha, beta, my_color, opp_color)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = sys.maxsize
        legal_moves = board_obj.generate_legal_moves(opp_color)
        if not legal_moves:
            return 1000000

        for move in legal_moves:
            temp_board_obj = copy.deepcopy(board_obj)
            temp_board_obj.apply_move(*move, opp_color)
            eval = minimax(temp_board_obj, depth - 1, True, alpha, beta, my_color, opp_color)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def find_best_move(board_obj, my_color, opp_color, depth=3):
    best_eval = -sys.maxsize
    best_move = None
    
    legal_moves = board_obj.generate_legal_moves(my_color)
    if not legal_moves:
        return None
    
    random.shuffle(legal_moves)
    
    for move in legal_moves:
        temp_board_obj = copy.deepcopy(board_obj)
        temp_board_obj.apply_move(*move, my_color)
        
        eval = minimax(temp_board_obj, depth - 1, False, -sys.maxsize, sys.maxsize, my_color, opp_color)
        
        if eval > best_eval:
            best_eval = eval
            best_move = move

    return best_move

def main():
    def log(message):
        sys.stderr.write(f"[StrongAI] {message}\n")
        sys.stderr.flush()
    
    def parse_moves(s):
        s = s.strip()
        if len(s) != 4 or not s.isdigit():
            raise ValueError("Move must be 4 digits, e.g. '1234'")
        r1, c1, r2, c2 = map(int, s)
        return r1, c1, r2, c2

    try:
        log("Waiting for 'OK?' from arena...")
        while True:
            line = sys.stdin.readline().strip()
            if line == "OK?":
                log("Received 'OK?'. Sending name.")
                print("StrongAI", flush=True)
                break
            if not line:
                log("Received empty line (EOF) during handshake. Exiting.")
                return

        log("Waiting for color assignment...")
        while True:
            line = sys.stdin.readline().strip()
            if line == "Black":
                my_color = BLACK
                log("Assigned as Black.")
                break
            elif line == "White":
                my_color = WHITE
                log("Assigned as White.")
                break
            elif not line:
                log("Received empty line (EOF) during color assignment. Exiting.")
                return
            else:
                log(f"Ignoring unexpected line during color assignment: '{line}'")

        opp = BLACK if my_color == WHITE else WHITE
        engine = hasamiShogi.HasamiShogi()
        
        if my_color == BLACK:
            log("Entering main game loop as Black.")
            log("Calculating my next move...")
            best_move = find_best_move(engine, my_color, opp)
            if best_move:
                r1, c1, r2, c2 = best_move
                engine.apply_move(r1, c1, r2, c2, my_color)
                move_str = f"{r1}{c1}{r2}{c2}"
                print(move_str, flush=True)
                log(f"Sent my move: {move_str}")
            else:
                log("No legal moves found. Exiting.")
                return
        else:
            log("Entering main game loop as White.")

        while True:
            log(f"Waiting for opponent's move or GAME_OVER...")
            line = sys.stdin.readline().strip()
            
            if not line:
                log("Received empty line (EOF). Exiting.")
                break
    
            if line.startswith("GAME_OVER"):
                log("Received GAME_OVER. Exiting.")
                break

            try:
                r1, c1, r2, c2 = parse_moves(line)
                log(f"Received opponent's move: {line}. Applying to board.")
                engine.apply_move(r1, c1, r2, c2, opp)
            except ValueError:
                log(f"Error: Invalid move format received: '{line}'. Skipping this turn.")
                continue
            
            log("Calculating my next move...")
            best_move = find_best_move(engine, my_color, opp)
            
            if best_move:
                r1, c1, r2, c2 = best_move
                engine.apply_move(r1, c1, r2, c2, my_color)
                move_str = f"{r1}{c1}{r2}{c2}"
                print(move_str, flush=True)
                log(f"Sent my move: {move_str}")
            else:
                log("No legal moves found. Exiting.")
                break
                
    except BrokenPipeError:
        log("BrokenPipeError: Communication with arena.py failed. Exiting gracefully.")
    except Exception as e:
        log(f"An unexpected error occurred: {e}. Exiting gracefully.")

if __name__ == "__main__":
    main()
