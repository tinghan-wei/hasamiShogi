#!/usr/bin/env python3
import sys, time, math
import copy
import hasamiShogi

MAX_TIME = 1.0  # テスト用に短く（動作確認後に30.0に戻す）
INF = 10**9
CENTER = [(4,4),(4,3),(4,5),(3,4),(5,4)]
last_moves = []  # 履歴保存（最大4手くらい）
turn_count = 0   # 手数カウンター

# 局面の出現回数を記録
seen_states_count = {}

def board_hash_with_turn(game, turn_color):
    """盤面＋手番を含めたハッシュ（同じ盤面でも手番が違えば別扱い）"""
    return (tuple(tuple(row) for row in game.board), turn_color)

# --- 局面繰り返し検出用 ---
seen_states = set()

def board_hash(game):
    """盤面をタプル化してハッシュ可能にする"""
    return tuple(tuple(row) for row in game.board)

def can_recover_within_depth(game, my_color, depth):
    """depth手以内に駒を取れるならTrue"""
    if depth <= 0:
        return False
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    my_moves = game.generate_legal_moves(my_color)
    for (r1, c1, r2, c2) in my_moves:
        g2 = copy.deepcopy(game)
        g2.apply_move(r1, c1, r2, c2, my_color)
        # 取れたら即OK
        gain = g2.captures[my_color] - game.captures[my_color]
        loss = g2.captures[opp] - game.captures[opp]
        net_gain = gain - loss
        if net_gain > 0:  # 有利交換のみOK
            return True
        # まだなら深さを減らして再帰
        if can_recover_within_depth(g2, my_color, depth - 1):
            return True
    return False

def will_be_captured_and_not_recoverable(game, my_color, max_depth=2):
    """相手が取ったあと、max_depth手以内に取り返せないならTrue"""
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    opp_moves = game.generate_legal_moves(opp)
    for (r1, c1, r2, c2) in opp_moves:
        g2 = copy.deepcopy(game)
        g2.apply_move(r1, c1, r2, c2, opp)
        if g2.captures[opp] > game.captures[opp]:
            # 相手が取った後、自分が回収できるか
            if not can_recover_within_depth(g2, my_color, max_depth):
                return True
    return False


def evaluate(game, my_color, prev_caps=None, depth_from_root=0):
    global turn_count
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE

    # 基本評価（駒差）
    base_score = (game.captures[my_color] - game.captures[opp]) * 100

    # 捕獲差分による攻撃評価
    if prev_caps is not None:
        my_diff = game.captures[my_color] - prev_caps[0]
        opp_diff = game.captures[opp] - prev_caps[1]
        depth_weight = 1.5 / (depth_from_root + 1)
        base_score += (my_diff - opp_diff) * 100 * depth_weight

    # 中央支配
    for (r, c) in CENTER:
        if game.board[r][c] == my_color:
            base_score += 3
        elif game.board[r][c] == opp:
            base_score -= 3

    # モビリティ（合法手数差）
    my_moves = game.generate_legal_moves(my_color)
    opp_moves = game.generate_legal_moves(opp)
    base_score += (len(my_moves) - len(opp_moves)) * 0.5

    # --- 進展性ボーナス ---
    progress_bonus = 0
    for (r1, c1, r2, c2) in my_moves:
        # 自分の色によって「前進方向」が違う
        if my_color == hasamiShogi.BLACK:
            # 黒は下方向に進むと加点
            if r2 > r1:
                progress_bonus += 0.3
        else:
            # 白は上方向に進むと加点
            if r2 < r1:
                progress_bonus += 0.3

    base_score += progress_bonus

    # 敵駒の近くに移動できる手も加点（捕獲筋準備）
    for (r1, c1, r2, c2) in my_moves:
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r2 + dr, c2 + dc
            if 0 <= nr < 9 and 0 <= nc < 9:
                if game.board[nr][nc] == opp:
                    base_score += 0.5

    # --- 捕獲可能性ボーナス ---
    cap_moves = 0
    for (r1, c1, r2, c2) in my_moves:
        g2 = copy.deepcopy(game)  # ゲーム全体をコピー
        g2.apply_move(r1, c1, r2, c2, my_color)
        if g2.captures[my_color] > game.captures[my_color]:
            cap_moves += 1

    # --- 交換価値評価 ---
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    gain = game.captures[my_color] - prev_caps[0] if prev_caps else 0
    loss = game.captures[opp] - prev_caps[1] if prev_caps else 0
    exchange_value = gain - loss

    if exchange_value == 0:
        if turn_count < 30:  # 序盤だけペナルティ
            base_score -= 15
    elif exchange_value < 0:
        base_score -= 50
    else:
        base_score += exchange_value * 20

    # 危険手判定（この手を打つとすぐ取られるか）
    danger_penalty = 0
    # --- 駒損リスク評価 ---
    # --- 駒損リスク評価 ---
    if will_be_captured_and_not_recoverable(game, my_color, max_depth=1):
        # ただし、取られた直後に有利交換できるなら許容
        if not can_recover_within_depth(game, my_color, 1):
            base_score -= 50
    elif will_be_captured_and_not_recoverable(game, my_color, max_depth=2):
        if not can_recover_within_depth(game, my_color, 2):
            base_score -= 25
    else:
        # 取り返せる場合（交換）でも頻発は抑える
        opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
        opp_moves = game.generate_legal_moves(opp)
        for (r1, c1, r2, c2) in opp_moves:
            g2 = copy.deepcopy(game)
            g2.apply_move(r1, c1, r2, c2, opp)
            if g2.captures[opp] > game.captures[opp]:
                if can_recover_within_depth(g2, my_color, 1):
                    base_score -= 8  # 小さなマイナス
                    break


    # 往復運動ペナルティ
    if len(last_moves) >= 4:
        # 4手前と同じ動きの繰り返しをペナルティ
        if last_moves[-1] == last_moves[-3] and last_moves[-2] == last_moves[-4]:
            base_score -= 120

    # --- 長期戦ブースト ---
    if turn_count >= 150:  # 150手目から攻撃性アップ
        capture_diff = game.captures[my_color] - game.captures[opp]
        base_score += capture_diff * 200

    # --- 千日手（同一局面繰り返し）ペナルティ ---
    state = board_hash_with_turn(game, my_color)
    if seen_states_count.get(state, 0) >= 2:  # 3回目以降の出現
        base_score -= 50

    return base_score

def order_moves(game, moves, my_color):
    scored = []
    for mv in moves:
        g2 = copy.deepcopy(game)
        g2.apply_move(*mv, my_color)

        cap_gain = g2.captures[my_color] - game.captures[my_color]
        center_bonus = -abs(4 - mv[2]) - abs(4 - mv[3])

        # 並び替え用の軽い危険度判定（探索深度で詳細に評価される）
        danger_penalty = 0
        if will_be_captured_and_not_recoverable(g2, my_color, max_depth=1):
            danger_penalty = -10  # 並び替え用なので軽め

        scored.append((cap_gain*10 + center_bonus + danger_penalty, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]

def minimax(game, depth, alpha, beta, maximizing, my_color, start_time, prev_caps=None, depth_from_root=0):
    if time.time() - start_time > MAX_TIME * 0.95:
        return evaluate(game, my_color, prev_caps, depth_from_root), None

    winner = game.is_game_over()
    if winner == my_color:
        return INF, None
    elif winner is not None:
        return -INF, None

    if depth == 0:
        return evaluate(game, my_color, prev_caps, depth_from_root), None

    player = my_color if maximizing else (hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE)
    moves = order_moves(game, game.generate_legal_moves(player), player)
    if not moves:
        return evaluate(game, my_color, prev_caps, depth_from_root), None

    best_move = None
    if maximizing:
        value = -INF
        for mv in moves:
            g2 = hasamiShogi.HasamiShogi()
            g2.board = [row[:] for row in game.board]
            g2.captures = game.captures.copy()
            g2.turn = game.turn
            g2.apply_move(*mv, player)

            opp_color = hasamiShogi.BLACK if player == hasamiShogi.WHITE else hasamiShogi.WHITE

            eval_val, _ = minimax(
                g2, depth-1, alpha, beta, False, my_color, start_time,
                prev_caps=(game.captures[my_color], game.captures[opp_color]),
                depth_from_root=depth_from_root + 1
            )

            if eval_val > value:
                value = eval_val
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = INF
        for mv in moves:
            g2 = hasamiShogi.HasamiShogi()
            g2.board = [row[:] for row in game.board]
            g2.captures = game.captures.copy()
            g2.turn = game.turn
            g2.apply_move(*mv, player)

            opp_color = hasamiShogi.BLACK if player == hasamiShogi.WHITE else hasamiShogi.WHITE

            eval_val, _ = minimax(
                g2, depth-1, alpha, beta, True, my_color, start_time,
                prev_caps=(game.captures[my_color], game.captures[opp_color]),
                depth_from_root=depth_from_root + 1
            )

            if eval_val < value:
                value = eval_val
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def choose_best_move(game, my_color):
    start_time = time.time()
    best_move = None
    depth = 1
    while True:
        if time.time() - start_time > MAX_TIME * 0.9:
            break
        value, move = minimax(game, depth, -INF, INF, True, my_color, start_time)
        if time.time() - start_time > MAX_TIME * 0.9:
            break
        if move is not None:
            best_move = move
        depth += 1

    # 保険: 評価値が高い合法手を選ぶ
    if best_move is None:
        legal_moves = game.generate_legal_moves(my_color)
        if legal_moves:
            best_score = -INF
            for mv in legal_moves:
                g2 = copy.deepcopy(game)
                g2.apply_move(*mv, my_color)
                score = evaluate(g2, my_color)  # 評価関数でスコア計算
                if score > best_score:
                    best_score = score
                    best_move = mv

    return best_move

def main():
    global seen_states_count, turn_count
    # 最初のOK? 受信
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        print("Expected 'OK?'", file=sys.stderr)
        return
    print("StrongestAI", flush=True)

    # 色の受信
    my_color = None
    opp = None
    game = hasamiShogi.HasamiShogi()
    skip_input = True

    # --- 追加: 局面出現回数記録用 ---
    global seen_states_count
    seen_states_count = {}

    line = sys.stdin.readline().strip()
    if line.startswith("Black"):
        my_color = hasamiShogi.BLACK
        opp = hasamiShogi.WHITE
        skip_input = True
    elif line.startswith("White"):
        my_color = hasamiShogi.WHITE
        opp = hasamiShogi.BLACK
        skip_input = False

    # 対局ループ
    while True:
        if not skip_input:
            line = sys.stdin.readline().strip()
            if line.startswith("GAME_OVER"):
                break
            r1,c1,r2,c2 = map(int, line)
            game.apply_move(r1,c1,r2,c2, opp)

            turn_count += 1     # 手数カウンターを増やす

            # 相手手適用後に局面記録
            state = board_hash_with_turn(game, my_color)
            seen_states_count[state] = seen_states_count.get(state, 0) + 1

        move = choose_best_move(game, my_color)
        if move is None:
            print("0000", flush=True)
        else:
            r1,c1,r2,c2 = move
            game.apply_move(r1,c1,r2,c2, my_color)

            turn_count += 1     # 手数カウンターを増やす
            
            # 手を記録
            last_moves.append((r1, c1, r2, c2))
            if len(last_moves) > 4:
                last_moves.pop(0)

            # 自分手適用後に局面記録
            state = board_hash_with_turn(game, my_color)
            seen_states_count[state] = seen_states_count.get(state, 0) + 1

            print(f"{r1}{c1}{r2}{c2}", flush=True)

        skip_input = False

if __name__ == "__main__":
    main()
