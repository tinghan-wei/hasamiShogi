#!/usr/bin/env python3
import sys
import time
import math
import copy
import random
import hasamiShogi

# 設定
MAX_TIME = 28.0
INF = 999999
BOARD_SIZE = 9
CENTER = [(4,4),(4,3),(4,5),(3,4),(5,4)]

# グローバル変数
transposition_table = {}
killer_moves = [[] for _ in range(15)]
history_table = {}
last_moves = []
turn_count = 0
seen_states_count = {}

class TranspositionEntry:
    def __init__(self, value, depth, flag, best_move=None):
        self.value = value
        self.depth = depth
        self.flag = flag
        self.best_move = best_move

def zobrist_hash(game):
    """簡易ゾブリストハッシュ"""
    hash_val = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = game.board[r][c]
            if piece != hasamiShogi.EMPTY:
                hash_val ^= hash((r, c, piece, game.captures[hasamiShogi.BLACK], game.captures[hasamiShogi.WHITE]))
    return hash_val

def board_hash_with_turn(game, turn_color):
    """盤面＋手番を含めたハッシュ"""
    return (tuple(tuple(row) for row in game.board), turn_color)

def can_recover_within_depth(game, my_color, depth):
    """depth手以内に駒を取れるならTrue"""
    if depth <= 0:
        return False
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    my_moves = game.generate_legal_moves(my_color)
    for (r1, c1, r2, c2) in my_moves:
        g2 = copy.deepcopy(game)
        try:
            g2.apply_move(r1, c1, r2, c2, my_color)
            gain = g2.captures[my_color] - game.captures[my_color]
            loss = g2.captures[opp] - game.captures[opp]
            net_gain = gain - loss
            if net_gain > 0:
                return True
            if can_recover_within_depth(g2, my_color, depth - 1):
                return True
        except:
            continue
    return False

def will_be_captured_and_not_recoverable(game, my_color, max_depth=2):
    """相手が取ったあと、max_depth手以内に取り返せないならTrue"""
    opp = hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE
    opp_moves = game.generate_legal_moves(opp)
    for (r1, c1, r2, c2) in opp_moves:
        g2 = copy.deepcopy(game)
        try:
            g2.apply_move(r1, c1, r2, c2, opp)
            if g2.captures[opp] > game.captures[opp]:
                if not can_recover_within_depth(g2, my_color, max_depth):
                    return True
        except:
            continue
    return False

def evaluate_position(game, my_color, prev_caps=None, depth_from_root=0):
    """hasamiShogiMaster.pyの評価関数をベースに改良"""
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

    # 進展性ボーナス
    progress_bonus = 0
    for (r1, c1, r2, c2) in my_moves:
        if my_color == hasamiShogi.BLACK:
            if r2 > r1:
                progress_bonus += 0.3
        else:
            if r2 < r1:
                progress_bonus += 0.3

    base_score += progress_bonus

    # 敵駒の近くに移動できる手も加点
    for (r1, c1, r2, c2) in my_moves:
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r2 + dr, c2 + dc
            if 0 <= nr < 9 and 0 <= nc < 9:
                if game.board[nr][nc] == opp:
                    base_score += 0.5

    # 捕獲可能性ボーナス
    cap_moves = 0
    for (r1, c1, r2, c2) in my_moves:
        g2 = copy.deepcopy(game)
        try:
            g2.apply_move(r1, c1, r2, c2, my_color)
            if g2.captures[my_color] > game.captures[my_color]:
                cap_moves += 1
        except:
            continue

    # 交換価値評価
    gain = game.captures[my_color] - prev_caps[0] if prev_caps else 0
    loss = game.captures[opp] - prev_caps[1] if prev_caps else 0
    exchange_value = gain - loss

    if exchange_value == 0:
        if turn_count < 30:
            base_score -= 15
    elif exchange_value < 0:
        base_score -= 50
    else:
        base_score += exchange_value * 20

    # 駒損リスク評価
    if will_be_captured_and_not_recoverable(game, my_color, max_depth=1):
        if not can_recover_within_depth(game, my_color, 1):
            base_score -= 50
    elif will_be_captured_and_not_recoverable(game, my_color, max_depth=2):
        if not can_recover_within_depth(game, my_color, 2):
            base_score -= 25
    else:
        opp_moves = game.generate_legal_moves(opp)
        for (r1, c1, r2, c2) in opp_moves:
            g2 = copy.deepcopy(game)
            try:
                g2.apply_move(r1, c1, r2, c2, opp)
                if g2.captures[opp] > game.captures[opp]:
                    if can_recover_within_depth(g2, my_color, 1):
                        base_score -= 8
                        break
            except:
                continue

    # 往復運動ペナルティ
    if len(last_moves) >= 4:
        if last_moves[-1] == last_moves[-3] and last_moves[-2] == last_moves[-4]:
            base_score -= 120

    # 長期戦ブースト
    if turn_count >= 150:
        capture_diff = game.captures[my_color] - game.captures[opp]
        base_score += capture_diff * 200

    # 千日手ペナルティ
    state = board_hash_with_turn(game, my_color)
    if seen_states_count.get(state, 0) >= 2:
        base_score -= 50

    return base_score

def order_moves(game, moves, my_color, depth):
    """手順の並び替え"""
    if not moves:
        return []
    
    scored_moves = []
    
    for move in moves:
        score = 0
        r1, c1, r2, c2 = move
        
        # キラームーブ
        if depth < len(killer_moves) and move in killer_moves[depth]:
            score += 1000000
        
        # 履歴ヒューリスティック
        if move in history_table:
            score += history_table[move]
        
        # 捕獲手
        game_copy = copy.deepcopy(game)
        old_captures = game_copy.captures[my_color]
        try:
            game_copy.apply_move(r1, c1, r2, c2, my_color)
            captured = game_copy.captures[my_color] - old_captures
            score += captured * 100000
        except:
            continue
        
        # 中央移動
        center_bonus = 0
        for cr, cc in CENTER:
            if (r2, c2) == (cr, cc):
                center_bonus = 1000
                break
        score += center_bonus
        
        # 前進移動
        if my_color == hasamiShogi.BLACK and r2 > r1:
            score += 100
        elif my_color == hasamiShogi.WHITE and r2 < r1:
            score += 100
        
        scored_moves.append((score, move))
    
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return [move for _, move in scored_moves]

def alpha_beta_search(game, depth, alpha, beta, maximizing_player, my_color, start_time, original_depth=0):
    """改良されたアルファベータ探索"""
    global transposition_table
    
    # 時間切れチェック
    if time.time() - start_time > MAX_TIME * 0.95:
        return evaluate_position(game, my_color), None
    
    # 置換表チェック
    board_hash = zobrist_hash(game)
    if board_hash in transposition_table:
        entry = transposition_table[board_hash]
        if entry.depth >= depth:
            if entry.flag == 'exact':
                return entry.value, entry.best_move
            elif entry.flag == 'lower' and entry.value >= beta:
                return entry.value, entry.best_move
            elif entry.flag == 'upper' and entry.value <= alpha:
                return entry.value, entry.best_move
    
    # 終了条件
    winner = game.is_game_over()
    if winner == my_color:
        return INF - original_depth, None
    elif winner is not None:
        return -INF + original_depth, None
    
    if depth == 0:
        return evaluate_position(game, my_color, None, original_depth), None
    
    # 手の生成
    current_player = my_color if maximizing_player else (
        hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE)
    moves = game.generate_legal_moves(current_player)
    
    if not moves:
        return evaluate_position(game, my_color, None, original_depth), None
    
    # 置換表から最善手を取得
    tt_best_move = None
    if board_hash in transposition_table:
        tt_best_move = transposition_table[board_hash].best_move
    
    # 手順並び替え
    if tt_best_move and tt_best_move in moves:
        moves.remove(tt_best_move)
        moves.insert(0, tt_best_move)
    else:
        moves = order_moves(game, moves, current_player, original_depth - depth)
    
    best_move = None
    best_value = -INF if maximizing_player else INF
    
    for i, move in enumerate(moves):
        # Late Move Reduction
        reduction = 0
        if depth >= 3 and i >= 4:
            game_copy = copy.deepcopy(game)
            try:
                old_cap = game_copy.captures[current_player]
                game_copy.apply_move(*move, current_player)
                if game_copy.captures[current_player] == old_cap:  # 捕獲しない手
                    reduction = 1
            except:
                continue
        
        # 手を適用
        game_copy = copy.deepcopy(game)
        try:
            prev_caps = (game.captures[my_color], game.captures[hasamiShogi.BLACK if my_color == hasamiShogi.WHITE else hasamiShogi.WHITE])
            game_copy.apply_move(*move, current_player)
        except:
            continue
        
        # 再帰探索
        search_depth = depth - 1 - reduction
        value, _ = alpha_beta_search(
            game_copy, search_depth, alpha, beta, not maximizing_player, 
            my_color, start_time, original_depth
        )
        
        # LMRで削減した場合の再探索
        if reduction > 0 and (
            (maximizing_player and value > alpha) or 
            (not maximizing_player and value < beta)
        ):
            value, _ = alpha_beta_search(
                game_copy, depth - 1, alpha, beta, not maximizing_player, 
                my_color, start_time, original_depth
            )
        
        # 最善手更新
        if maximizing_player:
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
            if alpha >= beta:
                # キラームーブ更新
                update_killer_and_history(move, depth, original_depth)
                break
        else:
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, value)
            if alpha >= beta:
                update_killer_and_history(move, depth, original_depth)
                break
    
    # 置換表に保存
    flag = 'exact'
    if best_value <= alpha:
        flag = 'upper'
    elif best_value >= beta:
        flag = 'lower'
    
    transposition_table[board_hash] = TranspositionEntry(best_value, depth, flag, best_move)
    
    return best_value, best_move

def update_killer_and_history(move, depth, original_depth):
    """キラームーブとヒストリーテーブル更新"""
    depth_index = original_depth - depth
    if depth_index < len(killer_moves):
        if move not in killer_moves[depth_index]:
            killer_moves[depth_index].append(move)
            if len(killer_moves[depth_index]) > 2:
                killer_moves[depth_index].pop(0)
    
    if move not in history_table:
        history_table[move] = 0
    history_table[move] += depth * depth

def choose_best_move(game, my_color):
    """反復深化探索でベストムーブを選択"""
    start_time = time.time()
    best_move = None
    depth = 1
    
    # 最低限の手を確保
    legal_moves = game.generate_legal_moves(my_color)
    if legal_moves:
        best_move = legal_moves[0]
    
    try:
        while depth <= 15 and time.time() - start_time < MAX_TIME * 0.85:
            value, move = alpha_beta_search(
                game, depth, -INF, INF, True, my_color, start_time, depth
            )
            
            if move is not None:
                best_move = move
            
            elapsed = time.time() - start_time
            if elapsed > MAX_TIME * 0.7:
                break
                
            depth += 1
            
    except:
        pass
    
    return best_move

def main():
    global transposition_table, killer_moves, history_table, seen_states_count, turn_count, last_moves
    
    # 初期化
    transposition_table = {}
    killer_moves = [[] for _ in range(15)]
    history_table = {}
    seen_states_count = {}
    turn_count = 0
    last_moves = []
    
    # エンジン初期化
    line = sys.stdin.readline().strip()
    if not line.startswith("OK"):
        print("Expected 'OK?'", file=sys.stderr)
        return
    print("ImprovedStrongAI", flush=True)
    
    # 色の決定
    my_color = None
    opp = None
    game = hasamiShogi.HasamiShogi()
    skip_input = True
    
    line = sys.stdin.readline().strip()
    if line.startswith("Black"):
        my_color = hasamiShogi.BLACK
        opp = hasamiShogi.WHITE
        skip_input = True
    elif line.startswith("White"):
        my_color = hasamiShogi.WHITE
        opp = hasamiShogi.BLACK
        skip_input = False
    
    # メインループ
    while True:
        if not skip_input:
            line = sys.stdin.readline().strip()
            if line.startswith("GAME_OVER"):
                break
            
            try:
                r1, c1, r2, c2 = map(int, line)
                game.apply_move(r1, c1, r2, c2, opp)
                turn_count += 1
                
                # 相手手適用後に局面記録
                state = board_hash_with_turn(game, my_color)
                seen_states_count[state] = seen_states_count.get(state, 0) + 1
            except:
                break
        
        # 手を選択
        move = choose_best_move(game, my_color)
        
        if move is None:
            legal_moves = game.generate_legal_moves(my_color)
            move = random.choice(legal_moves) if legal_moves else (0, 0, 0, 0)
        
        # 手を適用して出力
        try:
            r1, c1, r2, c2 = move
            game.apply_move(r1, c1, r2, c2, my_color)
            turn_count += 1
            
            # 手を記録
            last_moves.append((r1, c1, r2, c2))
            if len(last_moves) > 4:
                last_moves.pop(0)
            
            # 自分手適用後に局面記録
            state = board_hash_with_turn(game, my_color)
            seen_states_count[state] = seen_states_count.get(state, 0) + 1
            
            print(f"{r1}{c1}{r2}{c2}", flush=True)
        except:
            print("0000", flush=True)
        
        skip_input = False
        
        # 置換表のサイズ制限
        if len(transposition_table) > 50000:
            transposition_table.clear()

if __name__ == "__main__":
    main()