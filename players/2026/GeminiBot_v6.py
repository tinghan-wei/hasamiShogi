#!/usr/bin/env python3
import sys
import random
import hasamiShogi

def evaluate_board(game, my_color):
    """
    盤面そのものを採点する関数（V字・要塞バージョン）
    """
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    score = 0
    
    # 1. 駒の損得（最優先）
    score += (game.captures[my_color] - game.captures[opp]) * 1000
    
    # 2. 盤面全体の状況を評価
    for r in range(9):
        for c in range(9):
            piece = game.board[r][c]
            
            # 自分の駒と相手の駒で、点数の足し引き（プラスマイナス）を反転させるための係数
            if piece == my_color:
                multiplier = 1
            elif piece == opp:
                multiplier = -1
            else:
                continue

            # ==========================================
            # ★ 目標1：V字陣形（定石）の検出
            # ==========================================
            # 自分の斜め4方向に味方（相手なら相手の駒）がいるかチェック
            ul = 1 if (r-1 >= 0 and c-1 >= 0 and game.board[r-1][c-1] == piece) else 0 # 左上
            ur = 1 if (r-1 >= 0 and c+1 < 9 and game.board[r-1][c+1] == piece) else 0 # 右上
            dl = 1 if (r+1 < 9 and c-1 >= 0 and game.board[r+1][c-1] == piece) else 0 # 左下
            dr = 1 if (r+1 < 9 and c+1 < 9 and game.board[r+1][c+1] == piece) else 0 # 右下
            
            total_diagonals = ul + ur + dl + dr
            
            # ぴったり2つの駒と繋がっていて、それが「直線（／や＼）」ではなく「V字（角）」になっているか？
            if total_diagonals == 2:
                # 直線ではない＝V字である条件
                is_straight_line = (ul and dr) or (ur and dl)
                if not is_straight_line:
                    score += 50 * multiplier  # V字完成で超高得点（+50点）！
                    
            # V字を組む途中や、V字の端っことしての価値も残す（1ペアにつき +10点）
            score += total_diagonals * 10 * multiplier
            
            # ==========================================
            # ★ 目標2：中央支配（ベースの動き）
            # ==========================================
            distance_from_center = abs(4 - r) + abs(4 - c)
            score += (8 - distance_from_center) * 2 * multiplier
                
    return score

def minimax(game, depth, alpha, beta, is_maximizing, my_color):
    if depth == 0 or game.is_game_over() is not None:
        return evaluate_board(game, my_color), None
        
    current_turn_color = my_color if is_maximizing else (hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE)
    legal_moves = game.generate_legal_moves(current_turn_color)
    
    if not legal_moves:
        return evaluate_board(game, my_color), None
        
    best_move = None
    
    if is_maximizing:
        max_eval = -999999
        for (r1, c1, r2, c2) in legal_moves:
            g2 = hasamiShogi.HasamiShogi()
            g2.board = [row[:] for row in game.board]
            g2.captures = game.captures.copy()
            g2.turn = game.turn
            g2.apply_move(r1, c1, r2, c2, current_turn_color)
            
            eval_score, _ = minimax(g2, depth - 1, alpha, beta, False, my_color)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r1, c1, r2, c2)
                
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
        
    else:
        min_eval = 999999
        for (r1, c1, r2, c2) in legal_moves:
            g2 = hasamiShogi.HasamiShogi()
            g2.board = [row[:] for row in game.board]
            g2.captures = game.captures.copy()
            g2.turn = game.turn
            g2.apply_move(r1, c1, r2, c2, current_turn_color)
            
            eval_score, _ = minimax(g2, depth - 1, alpha, beta, True, my_color)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r1, c1, r2, c2)
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def main():
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        return
    print("GeminiBot_v5_Diagonal", flush=True)

    line = sys.stdin.readline().strip()
    if line.startswith("Black"):
        my_color = hasamiShogi.BLACK
        opp = hasamiShogi.WHITE
        skip_input = True
    else:
        my_color = hasamiShogi.WHITE
        opp = hasamiShogi.BLACK
        skip_input = False

    game = hasamiShogi.HasamiShogi()

    SEARCH_DEPTH = 3 

    while True:
        if not skip_input:
            line = sys.stdin.readline().strip()
            if line.startswith("GAME_OVER"):
                break
            r1, c1, r2, c2 = map(int, line)
            game.apply_move(r1, c1, r2, c2, opp)

        best_score, best_move = minimax(game, SEARCH_DEPTH, -999999, 999999, True, my_color)

        if best_move:
            r1, c1, r2, c2 = best_move
            game.apply_move(r1, c1, r2, c2, my_color)
            print(f"{r1}{c1}{r2}{c2}", flush=True)
        else:
            print("0000", flush=True)

        skip_input = False

if __name__ == "__main__":
    main()