// alphabeta.c

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <float.h>
#include "alphabeta.h"

// --- 評価関数の重み（この値の調整がAIの強さに直結します）---
const double CAPTURE_WEIGHT = 10.0; // 捕獲した駒の価値
const double PIECE_COUNT_WEIGHT = 1.0;  // 盤上の駒の数の価値

// 盤面の中央ほど点数が高くなるように設定
static const int piece_square_table[BOARD_SIZE][BOARD_SIZE] = {
    {1, 1, 1, 1, 1, 1, 1, 1, 1},
    {1, 2, 2, 2, 2, 2, 2, 2, 1},
    {1, 2, 3, 3, 3, 3, 3, 2, 1},
    {1, 2, 3, 4, 4, 4, 3, 2, 1},
    {1, 2, 3, 4, 5, 4, 3, 2, 1}, // 中央が最も価値が高い
    {1, 2, 3, 4, 4, 4, 3, 2, 1},
    {1, 2, 3, 3, 3, 3, 3, 2, 1},
    {1, 2, 2, 2, 2, 2, 2, 2, 1},
    {1, 1, 1, 1, 1, 1, 1, 1, 1},
};

// --- プロトタイプ宣言 ---
double evaluate_board(GameState* state, char player_for_perspective);
double alphabeta(GameState* state, int depth, double alpha, double beta, bool maximizing_player, char root_player);

// 評価関数：盤面の有利さを数値化する
double evaluate_board(GameState* state, char player_for_perspective) {
    char opponent = (player_for_perspective == BLACK) ? WHITE : BLACK;
    
    char winner = is_game_over(state);
    if (winner == player_for_perspective) return DBL_MAX;
    if (winner == opponent) return -DBL_MAX;

    double score = 0.0;
    
    // 1. 捕獲した駒の数（既存）
    score += (state->captures[player_for_perspective] - state->captures[opponent]) * CAPTURE_WEIGHT;
    
    // 2. 盤上の駒の数と配置価値（修正）
    int my_pieces = 0;
    int opp_pieces = 0;
    double my_position_score = 0;
    double opp_position_score = 0;
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            if (state->board[r][c] == player_for_perspective) {
                my_pieces++;
                my_position_score += piece_square_table[r][c];
            } else if (state->board[r][c] == opponent) {
                opp_pieces++;
                opp_position_score += piece_square_table[r][c];
            }
        }
    }
    score += (my_pieces - opp_pieces) * PIECE_COUNT_WEIGHT;
    score += (my_position_score - opp_position_score) * POSITIONAL_WEIGHT;

    // 3. 機動力（モビリティ）の評価（新規追加）
    Move legal_moves[300];
    int my_mobility = generate_legal_moves(state, legal_moves);
    
    // 相手のターンに切り替えて、相手の機動力を計算
    GameState temp_state;
    copy_game_state(&temp_state, state);
    temp_state.turn = opponent;
    int opp_mobility = generate_legal_moves(&temp_state, legal_moves);
    
    score += (my_mobility - opp_mobility) * MOBILITY_WEIGHT;
    
    return score;
}


// アルファ・ベータ探索の本体（再帰関数）
double alphabeta(GameState* state, int depth, double alpha, double beta, bool maximizing_player, char root_player) {
    if (depth == 0 || is_game_over(state)) {
        return evaluate_board(state, root_player);
    }
    
    Move legal_moves[300];
    int num_moves = generate_legal_moves(state, legal_moves);

    if (maximizing_player) {
        double max_eval = -DBL_MAX;
        for (int i = 0; i < num_moves; ++i) {
            GameState child_state;
            copy_game_state(&child_state, state);
            apply_move(&child_state, &legal_moves[i]);
            
            double eval = alphabeta(&child_state, depth - 1, alpha, beta, false, root_player);
            if (eval > max_eval) max_eval = eval;
            if (eval > alpha) alpha = eval;
            if (beta <= alpha) {
                break; // βカット (枝刈り)
            }
        }
        return max_eval;
    } else { // Minimizing player
        double min_eval = DBL_MAX;
        for (int i = 0; i < num_moves; ++i) {
            GameState child_state;
            copy_game_state(&child_state, state);
            apply_move(&child_state, &legal_moves[i]);

            double eval = alphabeta(&child_state, depth - 1, alpha, beta, true, root_player);
            if (eval < min_eval) min_eval = eval;
            if (eval < beta) beta = eval;
            if (beta <= alpha) {
                break; // αカット (枝刈り)
            }
        }
        return min_eval;
    }
}


// 最善手を見つけるためのトップレベル関数
Move find_best_move(GameState* root_state) {
    Move best_move = {0,0,0,0};
    double max_score = -DBL_MAX;
    
    Move legal_moves[300];
    int num_moves = generate_legal_moves(root_state, legal_moves);

    if (num_moves == 0) {
        return best_move; // 動ける手がない
    }
    best_move = legal_moves[0]; // とりあえず初手を最善手としておく

    char root_player = root_state->turn;

    for (int i = 0; i < num_moves; ++i) {
        GameState child_state;
        copy_game_state(&child_state, root_state);
        apply_move(&child_state, &legal_moves[i]);
        
        // 次は相手（最小化プレイヤー）の手番
        double score = alphabeta(&child_state, SEARCH_DEPTH - 1, -DBL_MAX, DBL_MAX, false, root_player);
        
        if (score > max_score) {
            max_score = score;
            best_move = legal_moves[i];
        }
    }
    return best_move;
}