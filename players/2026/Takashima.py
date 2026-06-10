#!/usr/bin/env python3
import sys
import random
import hasamiShogi
import copy

EMPTY, BLACK, WHITE = '.', 'B', 'W'
def main():
    # PlayerName
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        print("Expected 'OK?' line", file=sys.stderr)
        return
    print("Ta", flush=True)

    # 自分の色（Black か White）を確認
    line = sys.stdin.readline().strip()
    #Black か White の先頭一文字を取り出し、(それが小文字なら)大文字にする
    my_color = line[0].upper()
    opp = BLACK if my_color == WHITE else WHITE

    
    # ルールエンジンを準備
    game = hasamiShogi.HasamiShogi()

    if my_color == BLACK:
        skip_input = True
    else:
        skip_input = False

    # 对局ループ
    while True:
        if not skip_input:
         # 相手の手や終了合図(GAME_OVER)を受け取る
            opp_move = sys.stdin.readline().strip()
            if "GAME_OVER" in opp_move:
                break
            # 相手が動いたなら、自分の盤面にも反映
            if len(opp_move) == 4:
                # 文字を整数に変換し、各変数に代入する
                r1, c1, r2, c2 = map(int, opp_move)
                game.apply_move(r1, c1, r2, c2, hasamiShogi.WHITE if my_color == hasamiShogi.BLACK else hasamiShogi.BLACK)
                
        # 自分の番：ルール上動かせる手をリストアップ
        legal_moves = game.generate_legal_moves(my_color)
        
        if legal_moves:
            move = choose_best_move(game, my_color)
            r1, c1, r2, c2 = move
            
            # 自分の盤面に反映してから、審判に伝える
            game.apply_move(r1, c1, r2, c2, my_color)
            print(f"{r1}{c1}{r2}{c2}", flush=True)
        else:
            print("0000", flush=True)
        skip_input = False


def evaluate_board(game, my_color):
    """盤面の強さを評価するパラメータ（評価関数）"""
    opp_color = WHITE if my_color == BLACK else BLACK
    # 「自分の取った数」から「相手に取られた数」を引いた純粋な点数差を返す
    return game.captures[my_color] - game.captures[opp_color]


def minimax(game, depth, alpha, beta, is_maximizing, my_color):
    """アルファベータ法を組み合わせたミニマックス探索"""
    opp_color = WHITE if my_color == BLACK else BLACK
    current_turn = my_color if is_maximizing else opp_color
    
    # 指定した深さまで読んだか、動かせる手がないなら盤面を点数化する
    legal_moves = game.generate_legal_moves(current_turn)
    if depth == 0 or not legal_moves:
        return evaluate_board(game, my_color)

    if is_maximizing:
        # 自分の番：スコアを最大にしたい
        max_eval = -999
        for move in legal_moves:
            r1, c1, r2, c2 = move
            game_copy = copy.deepcopy(game)
            game_copy.apply_move(r1, c1, r2, c2, my_color)
            
            evaluation = minimax(game_copy, depth - 1, alpha, beta, False, my_color)
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # 相手が選ぶ可能性の低い無駄なルートなので探索を打ち切る
        return max_eval
    else:
        # 相手の番：相手は自分を最小のスコアに追い込みたい
        min_eval = 999
        for move in legal_moves:
            r1, c1, r2, c2 = move
            game_copy = copy.deepcopy(game)
            game_copy.apply_move(r1, c1, r2, c2, opp_color)
            
            evaluation = minimax(game_copy, depth - 1, alpha, beta, True, my_color)
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # 自分が選ぶ可能性の低い無駄なルートなので探索を打ち切る
        return min_eval

#ミニマックス法、αβ法、ビーム探索を用いる
def choose_best_move(game, my_color):
    legal_moves = game.generate_legal_moves(my_color)
    if not legal_moves:
        return None

    # --- ステップ1: depth = 1 で全選択肢のスコアをとりあえず調べる ---
    move_scores = []
    for move in legal_moves:
        r1, c1, r2, c2 = move
        game_copy = copy.deepcopy(game)
        game_copy.apply_move(r1, c1, r2, c2, my_color)
        
        # 1手先だけの評価値を出す
        score = evaluate_board(game_copy, my_color)
        move_scores.append((score, move))
     
    random.shuffle(move_scores)  # 一度ランダムに並び替える(スコアが同一だった場合、ランダムに選択させるため)
    # --- ステップ2: スコアが高い順（降順）に並び替える ---
    move_scores.sort(key=lambda x: x[0], reverse=True)

    # --- ステップ3: 上位3手（または5手など）だけをピックアップする ---
    best_candidates = move_scores[:3]  # 候補を絞り込む

    # --- ステップ4: 絞り込んだ優秀な手だけを深く掘り下げる ---
    best_moves = []
    best_score = -999

    for score, move in best_candidates:
        r1, c1, r2, c2 = move
        game_copy = copy.deepcopy(game)
        game_copy.apply_move(r1, c1, r2, c2, my_color)
        
        # 絞った候補だけを深く先読み
        deep_score = minimax(game_copy, 3, -999, 999, False, my_color)
        
        if deep_score > best_score:
            best_score = deep_score
            best_moves = [move]
        elif deep_score == best_score:
            best_moves.append(move)
    
    return random.choice(best_moves)


if __name__ == "__main__":
    main()