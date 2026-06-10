#!/usr/bin/env python3
import sys
import random
import copy
import hasamiShogi

BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# 指定された座標がすべて盤面内に収まっているか判定する
def in_bounds(r1, c1, r2, c2):
    return all(0 <= v < BOARD_SIZE for v in (r1, c1, r2, c2))

# 4桁の文字列をパースし，4つの整数値に変換
def parse_moves(s):
    s = s.strip()
    # 文字列の長さチェック
    if len(s) != 4 or not s.isdigit():
        raise ValueError("Move must be 4 digits, e.g. '1234'")
    r1, c1, r2, c2 = map(int, s)
    # 数値チェック
    if not in_bounds(r1, c1, r2, c2):
        raise ValueError("Move out of range")    
    return r1, c1, r2, c2

def evaluate_board(engine, my_color, opp):
    # ゲームオーバーの判定
    winner = engine.is_game_over()
    if winner == my_color:
        return 100000
    elif winner == opp:
        return -100000
    score = 0
    # 駒の数の評価
    my_captures = engine.captures[my_color]
    opp_captures = engine.captures[opp]
    score += (my_captures - opp_captures) * 100
    # 猶予ルール(王手)の評価
    if engine.pending_leader == my_color:
        score += 50
    elif engine.pending_leader == opp:
        score -= 50
    # 盤面の陣形評価
    for r in range(9):
        for c in range(9):
            piece = engine.board[r][c]
            if piece == my_color:
                neighbors = 0
                # 上下左右にmy_colorが何枚あるか
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r + dr, c +dc
                    if 0 <= nr < 9 and 0 <= nc < 9:
                        if engine.board[nr][nc] == my_color:
                            neighbors += 1
                if neighbors >= 1:
                    score += 5
                else:
                    score -= 10
    return score

def select_best_move(current_engine, legal_moves, my_color, opp):
    best_moves = []
    max_score = -float('inf')

    for move in legal_moves:
        r1, c1, r2, c2 = move
        # 現在の盤面の状態を仮のエンジンにコピー
        temp_engine = copy.deepcopy(current_engine)
        # 手を仮に適用してみる
        temp_engine.apply_move(r1, c1, r2, c2, my_color)
        # 動かした後の盤面がどれくらい有利かを評価関数で評価
        score = evaluate_board(temp_engine, my_color, opp)
        # 最高得点の更新
        if score > max_score:
            max_score = score
            best_moves = [move]         # 新しい最高点でリストをリセット
        elif score == max_score:
            best_moves.append(move)     # 同点なら候補に追加(千日手対策)
   
    # 最高点の手の中からランダムに1つ選んで返す
    return random.choice(best_moves)

def main():
    line = sys.stdin.readline().strip()    
    # 接続確認
    if not line.startswith("OK"):
        print("Expected 'OK?' line", file=sys.stderr)
        return
    print("Random", flush=True)

    # 手番の決定
    line = sys.stdin.readline().strip()
    my_color = line[0].upper()
    opp = BLACK if my_color == WHITE else WHITE

    # 内部エンジンの初期化
    engine = hasamiShogi.HasamiShogi()
    # 先手・後手の分岐(最初の入力読込をスキップする)フラグ
    if my_color == BLACK:
        skip_input = True
    else:
        skip_input = False

    # 対局ループ
    while True:
        if not skip_input:
            # 相手の指し手を受信
            line = sys.stdin.readline().strip()
            
            # GAME OVERなら終了
            if line.startswith("GAME_OVER"):
                break
            
            # 相手の指し手を内部エンジンに適用
            r1,c1,r2,c2 = parse_moves(line)
            engine.apply_move(r1, c1, r2, c2, opp)

        # 自分の合法手を全て生成
        legal = engine.generate_legal_moves(my_color)
        if not legal:
            break
        # 自分で作った関数にengineと合法手リストを渡して最高の手を選ばせる
        r1, c1, r2, c2 = select_best_move(engine, legal, my_color, opp)
        # 選んだ手を内部エンジンに適用
        engine.apply_move(r1, c1, r2, c2, my_color)
        # 選んだ手を出力
        print(f"{r1}{c1}{r2}{c2}", flush=True)
        # 次からは必ず相手の入力を待つ
        skip_input = False

if __name__ == "__main__":
    main()
