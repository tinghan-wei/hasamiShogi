#!/usr/bin/env python3
import sys
import copy
import math
import traceback
import hasamiShogi

# ------------------------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------------------------
def get_opponent(color):
    """
    引数で受け取った駒色（'B'または'W'）の相手の色を返す。
    """
    if color == hasamiShogi.BLACK:
        return hasamiShogi.WHITE
    if color == hasamiShogi.WHITE:
        return hasamiShogi.BLACK
    return hasamiShogi.EMPTY

# ------------------------------------------------------------------------------
# AlphaBetaAIクラス: AIの思考ルーチン本体
# ------------------------------------------------------------------------------
class AlphaBetaAI:
    # --- 定数 ---
    # AIが何手先まで読むかを設定する。大きいほど強くなるが、思考時間が増加する。
    SEARCH_DEPTH = 2

    # --- 初期化 ---
    def __init__(self):
        """
        AIのインスタンスが作成されたときに一度だけ呼ばれる。
        """
        # 過去の盤面を記憶し、千日手（無意味な手の繰り返し）を防ぐための履歴セット
        self.history = set()

    # --- 内部メソッド ---
    def _get_board_tuple(self, board):
        """
        盤面を表すリストを、ハッシュ可能（setに追加可能）なタプルに変換する。
        """
        return tuple(map(tuple, board))

    def update_history(self, board):
        """
        現在の盤面を履歴に追加する。
        """
        self.history.add(self._get_board_tuple(board))

    # --- メインの思考メソッド ---
    def choose_move(self, game):
        """
        現在のゲーム状態（game）を受け取り、AIが最善と判断する手を返す。
        """
        best_move, best_value = None, -math.inf
        my_color = game.turn

        # ▼▼▼【重要】バグ対策：盤面を破壊する可能性のある generate_legal_moves を
        # 「使い捨てのコピー」に対して実行し、オリジナルの 'game' オブジェクトを守る。
        game_copy_for_move_gen = copy.deepcopy(game)
        legal_moves = game_copy_for_move_gen.generate_legal_moves(my_color)
        
        # 指せる手がなければ None を返す
        if not legal_moves:
            return None

        # --- 全ての合法手ループで評価 ---
        for move in legal_moves:
            # シミュレーションのために、現在の盤面のコピーを作成
            next_state = copy.deepcopy(game)
            # その手で盤面を進めてみる
            next_state.apply_move(*move, my_color)
            
            # 千日手防止ロジック
            repetition_penalty = 0
            board_tuple = self._get_board_tuple(next_state.board)
            # もし移動後の盤面が過去に出現したものであれば、大きなペナルティを課す
            if board_tuple in self.history:
                repetition_penalty = -200000 

            # その盤面の評価値をアルファベータ探索で計算
            move_value = self.alpha_beta(next_state, self.SEARCH_DEPTH - 1, -math.inf, math.inf, False, my_color)
            # 千日手ペナルティを評価値に加算
            move_value += repetition_penalty

            # これまでで最も評価値の高い手が見つかれば、それを記憶する
            if move_value > best_value:
                best_value = move_value
                best_move = move
        
        # 最も評価値の高かった手を返す（見つからなければ最初の手を返す）
        return best_move if best_move is not None else legal_moves[0]

    # --- アルファベータ探索 ---
    def alpha_beta(self, node, depth, alpha, beta, is_maximizing_player, my_color):
        """
        アルファベータ法を用いた探索で、盤面の評価値を計算する。
        node: 評価対象の盤面
        depth: 残りの探索の深さ
        alpha: Maximizing playerが保証できる最低スコア
        beta: Minimizing playerが保証できる最高スコア
        is_maximizing_player: AI自身の手番（スコアを最大化したい）かどうか
        my_color: AIの駒色
        """
        # 探索の深さに達したか、ゲームが終了していれば、その盤面の評価値を返す
        winner = node.is_game_over()
        if winner is not None or depth == 0:
            return self.evaluate_board(node, my_color)

        current_player = node.turn
        
        node_copy = copy.deepcopy(node)
        moves = node_copy.generate_legal_moves(current_player)

        if not moves:
            return self.evaluate_board(node, my_color)

        # AI自身の手番（評価値を最大化したい）
        if is_maximizing_player:
            max_eval = -math.inf
            for move in moves:
                child_node = copy.deepcopy(node)
                child_node.apply_move(*move, current_player)
                eval_score = self.alpha_beta(child_node, depth - 1, alpha, beta, False, my_color)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                # ベータカット：相手がこの枝を選ぶことはないと分かったので探索を打ち切る
                if beta <= alpha: break
            return max_eval
        # 相手の手番（評価値を最小化したい）
        else:
            min_eval = math.inf
            for move in moves:
                child_node = copy.deepcopy(node)
                child_node.apply_move(*move, current_player)
                eval_score = self.alpha_beta(child_node, depth - 1, alpha, beta, True, my_color)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                # アルファカット：自分がこの枝を選ぶことはないと分かったので探索を打ち切る
                if beta <= alpha: break
            return min_eval

    # --- 盤面評価関数 ---
    def evaluate_board(self, game, my_color):
        """
        盤面の良し悪しを数値（スコア）で評価する。正の数ならAI有利、負の数なら不利。
        """
        opp_color = get_opponent(my_color)
        winner = game.is_game_over()

        # 1. 勝利・敗北の判定（最優先）
        if winner == my_color: return 200000
        if winner == opp_color: return -200000

        # 2. 捕獲した駒の数の差（基本的な有利不利）
        my_captures = game.captures.get(my_color, 0)
        opp_captures = game.captures.get(opp_color, 0)
        score = (my_captures - opp_captures) * 1000

        my_positional_score = 0
        opp_positional_score = 0
        my_connectivity_score = 0
        opp_connectivity_score = 0
        
        for r in range(hasamiShogi.BOARD_SIZE):
            for c in range(hasamiShogi.BOARD_SIZE):
                piece = game.board[r][c]
                if piece == my_color:
                    # 3. 駒の前進度（相手陣地に近いほど高評価）
                    my_positional_score += r if my_color == hasamiShogi.BLACK else (hasamiShogi.BOARD_SIZE - 1 - r)
                    
                    # 4. 駒の連結性（味方の駒が隣接しているほど高評価）
                    for dr, dc in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
                        if game.in_bounds(r + dr, c + dc) and game.board[r + dr][c + dc] == my_color:
                            my_connectivity_score += 1

                elif piece == opp_color:
                    opp_positional_score += r if opp_color == hasamiShogi.BLACK else (hasamiShogi.BOARD_SIZE - 1 - r)
                    for dr, dc in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
                        if game.in_bounds(r + dr, c + dc) and game.board[r + dr][c + dc] == opp_color:
                            opp_connectivity_score += 1
        
        # 各評価値を重み付けして最終スコアに合算
        score += (my_positional_score - opp_positional_score) * 10
        score += (my_connectivity_score - opp_connectivity_score) * 50

        return score

# ------------------------------------------------------------------------------
# メインの通信ループ：アリーナと通信し、ゲームを進行させる
# ------------------------------------------------------------------------------
def parse_move(s):
    """
    "1234" のような文字列を (1, 2, 3, 4) のようなタプルに変換する。
    """
    return tuple(map(int, s.strip()))

def main():
    """
    プログラム実行時に最初に呼ばれるメイン関数。
    """
    # ゲームとAIのインスタンスを生成
    game = hasamiShogi.HasamiShogi()
    ai = AlphaBetaAI()
    # 初期盤面を履歴に登録
    ai.update_history(game.board)

    # --- アリーナとのハンドシェイク ---
    sys.stdin.readline() # アリーナからの "OK?" を待つ
    print("ConnectivityAI_V1") # 自分のAIの名前を返す
    sys.stdout.flush() # 出力を確定させる

    # --- 色の決定 ---
    color_line = sys.stdin.readline().strip() # "Black" または "White" を待つ
    my_color = hasamiShogi.BLACK if color_line.lower() == "black" else hasamiShogi.WHITE
    
    # --- 黒番（先手）の場合の初手処理 ---
    if my_color == hasamiShogi.BLACK:
        my_move = ai.choose_move(game)
        if my_move:
            game.apply_move(*my_move, my_color)
            ai.update_history(game.board)
            print(f"{my_move[0]}{my_move[1]}{my_move[2]}{my_move[3]}", flush=True)

    # --- メインの対局ループ ---
    while True:
        # 相手の手を待つ
        opp_move_str = sys.stdin.readline().strip()
        if not opp_move_str or opp_move_str.upper().startswith("GAME_OVER"): break
        try:
            # 相手の手を盤面に適用し、履歴を更新
            opp_move = parse_move(opp_move_str)
            game.apply_move(*opp_move, get_opponent(my_color))
            ai.update_history(game.board)
        except Exception: break

        # 自分の手を考え、適用し、出力する。履歴も更新。
        my_move = ai.choose_move(game)
        if my_move:
            game.apply_move(*my_move, my_color)
            ai.update_history(game.board)
            print(f"{my_move[0]}{my_move[1]}{my_move[2]}{my_move[3]}", flush=True)
        else: break

if __name__ == "__main__":
    try: 
        main()
    except Exception:
        # 万が一エラーでクラッシュした場合でも、何も出力せずに終了する
        pass
